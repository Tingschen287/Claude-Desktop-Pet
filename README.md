# Claude Desktop Pet

一个浮动在桌面上的像素风宠物，实时反映 Claude Code 当前正在做什么。

当 Claude 在读文件、写代码、执行命令、等待你确认时，宠物会切换不同的动画状态——让你在专注其他事情时也能一眼感知 AI 的工作进展。

---

## 效果预览

> *(TODO: 录制 GIF 放在这里)*

---

## 功能特性

- **实时状态感知**：通过 Claude Code 的 Hooks 机制接收事件，500ms 内同步更新动画
- **7 种动画状态**：idle / thinking / reading / writing / executing / waiting / unconfigured，各有独特动画
- **系统通知**：Claude 需要你确认时，宠物变红并弹出系统通知
- **始终置顶 + 可拖拽**：悬浮在所有窗口之上，可自由拖到任意位置
- **右键菜单**：切换项目、移除 Hooks、退出
- **幂等安装**：重复运行 `setup_hooks.py` 不会产生重复 Hook 配置

---

## 环境要求

- Python 3.10+
- [Claude Code](https://claude.ai/code) CLI（用于触发 Hooks）

---

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Tingschen287/Claude-Desktop-Pet.git
cd Claude-Desktop-Pet

# 2. 安装依赖
pip install -r requirements.txt
```

---

## 使用

### 方式一：GUI 启动（推荐新用户）

```bash
python src/pet.py
```

首次启动时，宠物处于 `unconfigured` 状态（颜色暗淡）。左键单击宠物，在弹出窗口中选择你的 Claude Code 项目文件夹，确认后自动完成 Hooks 注入。

### 方式二：命令行指定项目

```bash
python src/pet.py --project /path/to/your/project
```

跳过 GUI 配置，直接注入 Hooks 并启动。适合脚本或已知项目路径的场景。

### 手动注入 / 移除 Hooks

```bash
# 注入
python scripts/setup_hooks.py inject /path/to/your/project

# 移除
python scripts/setup_hooks.py remove /path/to/your/project
```

---

## 状态说明

| 状态 | 触发时机 | 眼睛颜色 | 动画 |
|---|---|---|---|
| `unconfigured` | 未配置项目 | 暗灰 | 静止，颜色变暗 |
| `idle` | 工具调用完成 / 停止 / 超过 30s 无更新 | 白色 | 缓慢浮动，偶尔眨眼 |
| `thinking` | 调用 Agent / Task 类工具 | 紫色 | 眼睛旋转，轻微颤抖 |
| `reading` | 调用 Read / Glob / Grep | 黄色 | 眼睛左右扫视 |
| `writing` | 调用 Edit / Write | 绿色 | 眨眼，底部进度条流动 |
| `executing` | 调用 Bash | 宽黄 | 快速抖动 |
| `waiting` | Notification 事件（需要确认） | 红色闪烁 | 红色闪烁 + 系统通知 |

---

## 架构

```
Claude Code 会话
  │
  │  Hooks（PreToolUse / PostToolUse / Notification / Stop）
  ▼
scripts/hook_writer.py  ──写入──▶  ~/.claude/pet-state.json
                                           │
                                   每 500ms 轮询
                                           │
                                      src/pet.py
                                  （PyQt6 浮动窗口）
                                           │
                          ┌────────────────┼──────────────┐
                      renderer.py      animator.py    notifier.py
                     （像素绘制）      （状态机）      （系统通知）
```

### 关键文件

| 文件 | 职责 |
|---|---|
| `src/pet.py` | 主窗口。轮询定时器、拖拽逻辑、右键菜单、项目配置 |
| `src/animator.py` | 状态机。维护当前状态和帧索引，发出 `frame_changed` / `motion_changed` 信号 |
| `src/renderer.py` | 用 `QPainter.fillRect` 绘制 6×8 像素网格，每格 12×12px，间距 1px |
| `src/bubble_overlay.py` | 铃铛气泡 overlay，`waiting` 状态时展示在宠物上方 |
| `src/notifier.py` | 系统通知封装（plyer），所有异常静默处理 |
| `assets/frames.py` | 全部帧数据。`FRAMES[state]`、`FRAME_INTERVALS[state]`、`STATE_MOTION[state]` |
| `scripts/hook_writer.py` | 被 Claude Code Hooks 调用。读取 stdin JSON，映射事件到状态，原子写入 `pet-state.json` |
| `scripts/setup_hooks.py` | 向项目的 `.claude/settings.json` 注入 / 移除 Hook 配置，幂等 |

### 运行时文件

- `~/.claude/pet-state.json` — 由 `hook_writer.py` 写入，由 `pet.py` 读取
- `~/.claude/pet-config.json` — 存储上次选择的项目路径，由 `pet.py` 写入

---

## 开发

### 运行测试

```bash
# 全部测试
python -m pytest

# 单个测试文件
python -m pytest tests/test_animator.py -v

# 单个测试
python -m pytest tests/test_setup_hooks.py::test_inject_is_idempotent -v
```

### 新增状态

1. 在 `assets/frames.py` 中添加 `FRAMES["new_state"]` 帧数据
2. 在 `FRAME_INTERVALS` 和 `STATE_MOTION` 中添加对应条目
3. 在 `scripts/hook_writer.py` 中将 Hook 事件 / 工具名映射到新状态

Animator 和 Renderer 自动感知，无需其他改动。

---

## 依赖

| 包 | 用途 |
|---|---|
| `PyQt6` | GUI 窗口、绘图、定时器 |
| `plyer` | 跨平台系统通知 |

---

## License

MIT
