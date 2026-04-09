# 多会话监听方案

## Context

当前桌宠只能监听单个 Claude Code 项目——所有项目的 hook 写入同一个 `pet-state.json`（后写覆盖前写），`pet-config.json` 也只存一个项目路径。用户经常同时开多个 Claude 会话，需要桌宠能同时感知所有活跃会话的状态。

**设计选择**：单宠物优先级显示 + 被动监听。外观不变，展示所有项目中最活跃的状态；右键菜单/悬停可查看全部项目状态列表。无需手动管理项目列表。

---

## 核心思路

将单文件 `pet-state.json` 改为目录 `pet-states/`，每个项目写入独立的状态文件（以项目路径哈希命名），消除写竞争。桌宠轮询该目录，聚合所有项目状态，展示优先级最高的。

---

## Step 1: hook_writer.py — 按项目写独立状态文件

**文件**: `scripts/hook_writer.py`

改动：
1. 将 `STATE_FILE` 常量替换为 `STATES_DIR = ~/.claude/pet-states/`
2. 新增 `state_file_for_project(project_path)` 函数：对路径做 `normpath + abspath` 规范化后取 `sha1[:16]` 作为文件名
3. `write_state()` 改为写入 `STATES_DIR/{hash}.json`，增加 `project_name`（basename）字段方便显示
4. `main()` 无需改动（已经传了 `project=cwd`）

状态文件格式：
```json
{
  "state": "reading",
  "tool": "Grep",
  "project": "/abs/path/to/project",
  "project_name": "project",
  "timestamp": "ISO8601"
}
```

**关键**：每个项目写自己的文件，不存在跨项目竞争。`os.replace` 原子写保持不变。

---

## Step 2: pet.py — 轮询目录 + 优先级聚合

**文件**: `src/pet.py`

### 2a. 新常量与数据结构

```python
STATES_DIR = Path.home() / ".claude" / "pet-states"

STATE_PRIORITY = {
    "writing": 6, "executing": 5, "reading": 4,
    "thinking": 3, "waiting": 2, "idle": 1, "unconfigured": 0,
}
```

### 2b. 替换实例变量

移除：`_project`, `_last_timestamp`, `_last_update_time`

新增：
- `_project_states: dict[str, dict]` — hash → {state data + last_seen}
- `_effective_state: str` — 当前展示的状态
- `_effective_project: str | None` — 当前驱动展示的项目名

### 2c. 重写 `_poll_state()`

1. 扫描 `STATES_DIR/*.json`
2. 逐文件读取，与 `_project_states` 中的 timestamp 对比，有变更则更新 `last_seen`
3. 删除已消失文件的条目
4. 超过 30 秒未更新的项目标记为 idle
5. 调用 `_resolve_effective_state()` 确定最终显示状态

### 2d. 新增 `_resolve_effective_state()`

遍历 `_project_states`，选 `STATE_PRIORITY` 最高的状态驱动 animator。保留 `MIN_STATE_DURATION` 防抖逻辑（idle 降级需等 2 秒）。处理 waiting→通知 和 bubble 显隐。

### 2e. 简化配置

- `_load_config()` 只加载 skin，不再加载 project；启动状态为 idle
- `_save_config()` 只保存 skin
- 移除 `_configure_project()`、`_remove_hooks()`、`_clear_stale_waiting_state()`
- `--project` 参数改为：对该项目执行 `inject_hooks` 但不存配置

### 2f. Tooltip

每次 poll 结束更新 tooltip，显示所有项目及状态列表（按优先级降序）。

---

## Step 3: 右键菜单改造

**文件**: `src/pet.py` `contextMenuEvent()`

```
📊 监听 3 个项目，2 个活跃     (disabled header)
─────────────────────────
✏️ project-A — writing
📖 project-B — reading
💤 project-C — idle
─────────────────────────
配置新项目 Hooks…               → 文件夹选择器 → inject_hooks
切换形象 >
导入 SVG 皮肤…
─────────────────────────
退出
```

- "配置新项目 Hooks…" 替代原来的 "切换项目…"，只做 hook 注入，不记录到配置
- "移除当前项目 Hooks" 移除（被动模式不需要）

---

## Step 4: 启动时清理过期文件

**文件**: `src/pet.py`

`__init__` 中调用 `_cleanup_stale_files()`：删除 `pet-states/` 下 timestamp 超过 24 小时的文件，防止无限增长。

---

## Step 5: 更新测试

**文件**: `tests/test_hook_writer.py`
- 适配 `STATES_DIR` 替代 `STATE_FILE`
- 新增：`state_file_for_project` 确定性和路径规范化测试
- 新增：`project_name` 字段测试

**新文件**: `tests/test_multi_project.py`（可选）
- 测试优先级排序逻辑
- 测试全 idle 返回 idle
- 测试过期清理

---

## Step 6: 更新 CLAUDE.md

更新架构文档中的数据流、状态文件说明、运行时文件列表。

---

## 涉及的关键文件

| 文件 | 改动类型 |
|------|----------|
| `scripts/hook_writer.py` | 重写状态文件路径逻辑 |
| `src/pet.py` | 重写轮询、配置、菜单 |
| `tests/test_hook_writer.py` | 适配新路径 |
| `CLAUDE.md` | 更新文档 |

## 向后兼容

- 旧 `pet-state.json` 不删除、不读取，自然失效
- 旧 `pet-config.json` 中的 `project` 字段被忽略，`skin` 保留
- 已配置 hook 的旧项目需重新运行 setup_hooks（或通过右键菜单"配置新项目"）

## 验证方式

1. 启动桌宠 `python src/pet.py`，确认无报错，初始 idle
2. 对项目 A 运行 `python scripts/setup_hooks.py /path/to/projectA`
3. 在项目 A 启动 Claude 会话，确认桌宠响应状态变化
4. 对项目 B 也配置 hook 并启动会话，确认桌宠展示最高优先级状态
5. 右键菜单确认能看到两个项目的状态列表
6. 悬停确认 tooltip 显示项目状态摘要
7. 两个会话都停止 30 秒后，确认桌宠回到 idle
8. `python -m pytest` 全部通过
