# 宠物多形象选择功能 - 设计文档

> **状态**: 待审批
> **日期**: 2026-03-28

---

## 概述

用户希望丰富桌面宠物的功能：
1. 在右键菜单中让用户可以选择不同的宠物形象
2. 保留当前默认的橙色小猫形象
3. 添加螃蟹形象（用户已在 crab.py 中提供原型）
4. 支持用户导入自己设计的形象（后续实现）

---

## 皮肤模块格式

每个皮肤是一个 Python 模块，需要导出：

```python
# assets/skins/{skin_name}/__init__.py

META = {
    "name": "显示名称",
    "id": "unique_id",
}

ROWS = 6  # 帧的行数
COLS = 8  # 帧的列数

FRAMES = { ... }           # dict[state] -> list of frames
FRAME_INTERVALS = { ... }  # dict[state] -> ms
STATE_MOTION = { ... }     # dict[state] -> "float"|"shake"|"tremble"|"none"
```

### 必需状态

每个皮肤必须支持以下 7 种状态：

| 状态 | 描述 |
|------|------|
| `unconfigured` | 未配置项目时的静态外观 |
| `idle` | 空闲状态，通常有眨眼动画 |
| `thinking` | Claude 思考中，Agent/Task 工具使用 |
| `reading` | Claude 读取文件，Read/Glob/Grep 工具 |
| `writing` | Claude 写入文件，Edit/Write 工具 |
| `executing` | Claude 执行命令，Bash 工具 |
| `waiting` | Claude 等待用户确认，Notification 事件 |

---

## 文件结构

```
assets/
├── frames.py              # 保留，向后兼容
└── skins/
    ├── __init__.py
    ├── default/           # 默认小猫
    │   ├── __init__.py
    │   └── frames.py
    └── crab/              # 螃蟹
        ├── __init__.py
        └── frames.py

~/.claude/
├── pet-config.json        # 新增 "skin" 字段
└── pet-skins/             # 用户自定义皮肤目录（后续）
```

---

## 配置文件格式

```json
{
  "project": "/path/to/project",
  "skin": "default"
}
```

---

## 修改文件列表

| 文件 | 修改内容 |
|------|----------|
| `src/skin_registry.py` | **新建** - 扫描和加载皮肤模块 |
| `src/renderer.py` | 改为实例属性接收 rows/cols |
| `src/animator.py` | 添加 `set_skin()` 方法，动态切换帧数据源 |
| `src/pet.py` | 添加皮肤选择菜单、皮肤切换逻辑、配置读写更新 |
| `assets/skins/default/` | **新建** - 从 frames.py 提取默认皮肤 |
| `assets/skins/crab/` | **新建** - 螃蟹皮肤 |

---

## 螃蟹形象设计

基于 crab.py 原型：
- 尺寸：10行 x 16列
- 身体：橙色 `#D27855`
- 眼睛：黑色 `#000000`

需要设计的动画：
| 状态 | 动画效果 |
|------|----------|
| idle | 身体轻微上下浮动，眼睛眨眼 |
| thinking | 眼睛左右移动，钳子轻微摆动 |
| reading | 眼睛从左扫到右 |
| writing | 身体上显示进度条 |
| executing | 整体抖动，钳子开合 |
| waiting | 眼睛闪烁红色 |
| unconfigured | 灰暗身体，静止 |

---

## 向后兼容

1. 保留 `assets/frames.py` 文件，确保旧代码仍可导入
2. 默认皮肤 ID 为 `"default"`
3. 配置文件中 `skin` 字段可选，默认为 `"default"`
