# 宠物多形象选择功能 - 实现计划

> **状态**: 待执行
> **日期**: 2026-03-28

---

## 任务列表

### Task 1: 提取默认皮肤

**文件**: `assets/skins/default/__init__.py`, `assets/skins/default/frames.py`

**内容**:
- 从现有 `assets/frames.py` 复制帧数据
- 添加 META 信息
- 保持向后兼容

**验收标准**:
- [ ] 皮肤模块可被正确导入
- [ ] 包含所有 7 种状态的帧数据
- [ ] 帧数据与原始 frames.py 一致

---

### Task 2: 创建皮肤注册中心

**文件**: `src/skin_registry.py`

**内容**:
- `SkinRegistry` 类
- 扫描 `assets/skins/` 内置皮肤
- 扫描 `~/.claude/pet-skins/` 用户皮肤
- `get_skin(id)` 和 `list_skins()` 方法
- 皮肤验证逻辑

**验收标准**:
- [ ] 能扫描并加载所有内置皮肤
- [ ] `get_skin("default")` 返回默认皮肤
- [ ] `list_skins()` 返回皮肤列表
- [ ] 无效皮肤 ID 返回默认皮肤

---

### Task 3: 修改动画器支持动态皮肤

**文件**: `src/animator.py`

**内容**:
- 移除静态导入 `from frames import ...`
- 添加 `_skin_data` 属性
- 添加 `set_skin(skin_module)` 方法
- 所有 FRAMES/FRAME_INTERVALS/STATE_MOTION 访问改为 `self._skin_data.XXX`

**验收标准**:
- [ ] `set_skin()` 可切换皮肤
- [ ] 切换后帧数据正确更新
- [ ] 信号正确发出

---

### Task 4: 修改渲染器支持动态尺寸

**文件**: `src/renderer.py`

**内容**:
- `ROWS` 和 `COLS` 改为实例属性
- `widget_width()` 和 `widget_height()` 改为实例方法
- 添加 `set_dimensions(rows, cols)` 方法

**验收标准**:
- [ ] 实例化时可指定 rows/cols
- [ ] `set_dimensions()` 可动态调整尺寸
- [ ] 默认值保持 6x8 兼容现有代码

---

### Task 5: 修改主窗口添加皮肤选择功能

**文件**: `src/pet.py`

**内容**:
- 初始化时加载皮肤配置
- 添加右键菜单子菜单 "切换形象"
- 实现 `_switch_skin(skin_id)` 方法
- 更新 `_load_config()` 和 `_save_config()` 处理 skin 字段
- 切换皮肤时调整窗口大小

**验收标准**:
- [ ] 右键菜单显示 "切换形象" 子菜单
- [ ] 选择形象后宠物立即切换
- [ ] 重启后保持形象选择

---

### Task 6: 创建螃蟹皮肤

**文件**: `assets/skins/crab/__init__.py`, `assets/skins/crab/frames.py`

**内容**:
- 将 crab.py 转换为皮肤格式
- 设计各状态动画帧
- 螃蟹尺寸：10行 x 16列

**验收标准**:
- [ ] 皮肤模块可被正确导入
- [ ] 包含所有 7 种状态的帧数据
- [ ] 动画效果符合设计

---

### Task 7: 集成测试

**内容**:
- 启动宠物，确认默认小猫形象正常
- 右键菜单选择螃蟹形象，确认切换成功
- 重启宠物，确认形象选择被保存
- 测试各状态动画是否正常

**验收标准**:
- [ ] 默认形象正常显示
- [ ] 螃蟹形象正常切换
- [ ] 配置保存和加载正常
- [ ] 所有状态动画正常

---

## 执行顺序

```
Task 1 (提取默认皮肤)
    ↓
Task 2 (创建皮肤注册中心)
    ↓
Task 3 (修改动画器) ─────────┬──→ Task 5 (修改主窗口)
                            │
Task 4 (修改渲染器) ─────────┘
    ↓
Task 6 (创建螃蟹皮肤)
    ↓
Task 7 (集成测试)
```

Task 3 和 Task 4 可以并行执行，Task 6 可以与 Task 3-4 并行。
