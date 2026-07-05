# 修改总结

## 一、输入方案切换：vJoy → ViGEmBus

### 背景
原来的方案使用 vJoy + pyvjoy 将方向盘角度映射为虚拟手柄输入。但 vJoy 设备在部分游戏中兼容性不佳，需要用户在游戏中手动配置控制映射，体验不够顺滑。

### 新方案
改用 **ViGEmBus + vgamepad**，模拟 Xbox 360 手柄。

#### 优势
- 游戏**原生支持** Xbox 手柄，无需额外配置
- 游戏会自动识别为 Xbox 360 有线手柄
- 方向盘角度映射为左摇杆 X 轴
- 支持同时控制多个轴（摇杆 + 扳机）

#### 实现文件

**`core/vgamepad_output.py`** — 虚拟手柄输出类

```python
VGamepadOutput
├── initialize()      # 创建虚拟 Xbox 360 手柄
├── set_steering_angle()  # 方向盘角度 → 左摇杆 X 轴
├── set_axes()        # 同时设置所有轴（方向盘+油门+刹车）
├── press_button()    # 手柄按键（扩展用）
├── reset()           # 所有输入回中
└── close()           # 释放资源
```

#### 映射关系

| 鼠标操作 | 手柄信号 | 游戏效果 |
|---|---|---|
| 左右移动 | 左摇杆 X 轴 (-1.0 ~ 1.0) | 方向盘转向 |
| 右键按住 | 右扳机 (0.0 ~ 1.0) | 油门 |
| 左键按住 | 左扳机 (0.0 ~ 1.0) | 刹车 |

#### 安装依赖

```bash
pip install vgamepad
```

同时需要安装 ViGEmBus 驱动（vgamepad 会自动处理）。

---

## 二、辅助回中功能

### 问题描述

使用鼠标模拟方向盘时，从大角度（如 500°）突然向反方向回打时，存在两个问题：

1. **手感沉重**：accumulated_x 超出饱和区后，回打需要先"消化"多余累积位移，角度才变化
2. **难以定位中心**：回打到中心附近后容易冲过头，继续往反方向加速

### 三状态机设计

```
普通态 ──大幅快速回打──→ 归中态 ──进入±50°──→ 中心检测态(500ms)
  ↑                                                       │
  └────────────── 释放（累计位移>200 或 500ms到）───────────┘
```

#### 状态 A — 普通态
- 正常累积：`accumulated_x += delta_x × sensitivity`
- 检测触发条件：
  - **回打位移累计 ≥ 阈值**（默认 200px，不受灵敏度影响）
  - 基于**原始鼠标位移**（`abs(delta_x)`）检测，不经过灵敏度/曲线处理
- 满足条件 → 进入状态 B

#### 状态 B — 归中态
- 暂停正常累积
- 每帧按比例缩减：`accumulated_x *= (1 - 0.20)`
- 角度越大每帧缩减绝对值越大，接近中心时自然变缓
- 当 `abs(accumulated_x) < 50` → 进入状态 C

#### 状态 C — 中心检测态（500ms）
- `accumulated_x` 锁定为 0
- 后台累计用户持续位移
- 500ms 后判断：
  - 累计位移 > 200 → 用户确实想继续转向 → 释放到状态 A
  - 累计位移 ≤ 200 → 保持中心

### 解决的其他问题

#### accumulated_x 超限导致回打卡顿
**问题**：`_apply_three_zone` 的饱和区在到达 `saturation_end` 前就已输出 max_angle，导致 accumulated_x 超出有效范围后回打无响应。

**解决**：自动计算 `_max_useful_acc`（`_apply_three_zone` 首次到达 max_angle 时的累积位移），每帧将 accumulated_x 钳位到此范围内。默认值 637（@max_angle=90），使回打第一帧即产生角度变化。

#### 检测与灵敏度解耦
**问题**：基于角度变化率的检测受灵敏度影响，低灵敏度时角度变化慢，难以触发。

**解决**：改为基于**原始鼠标位移累加**，不经过任何处理：

```
检测流程:
  检测到回打开始 → 持续累加 abs(delta_x)
                → 累计 ≥ 阈值 → 触发辅助
                → 用户换向 → 重置累计
```

测试验证（阈值 200px，窗口 0.10s）：

| 灵敏度 | 触发帧 | 是否正常 |
|---|---|---|
| 0.2 | 帧4 | ✅ |
| 0.5 | 帧4 | ✅ |
| 1.0 | 帧4 | ✅ |
| 3.0 | 帧4 | ✅ |
| 5.0 | 帧4 | ✅ |

所有灵敏度完全一致，慢速微调不触发 ✅

#### Bug 修复：历史清理顺序
**问题**：历史记录的清理发生在比较之前，回打前的角度记录被提前删除，导致变化量永远不够阈值。

**解决**：改为先比较再清理。

### 核心算法文件

**`core/steering_algorithm.py`**

#### `__init__` 新增参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `assist_threshold` | 300° | 辅助触发角度阈值（当前仅保留作兼容） |
| `assist_rate_threshold` | 200 | 回打位移累计阈值（px） |
| `assist_rate_window` | 0.10s | 检测窗口（当前仅保留作兼容） |
| `assist_return_rate` | 0.20 | 归中态每帧缩减比例 |
| `near_center_threshold` | 50.0 | 进入中心检测的边界（px） |
| `center_hold_ms` | 500 | 中心检测时长（ms） |
| `center_release_threshold` | 200 | 检测期间释放阈值（px） |

#### 状态变量

| 变量 | 说明 |
|---|---|
| `_assist_active` | 是否在状态 B 或 C |
| `_assist_from_direction` | 进入 B 时的 delta_x 方向 |
| `_hold_delta_sum` | 状态 C 期间累计位移 |
| `_hold_start_time` | 状态 C 开始时间 |
| `_reversal_sum` | 当前回打累计位移 |
| `_reversal_start_time` | 回打开始时间 |
| `_reversal_direction` | 回打方向 |
| `_max_useful_acc` | accumulated_x 有效上限 |

#### `_compute_max_useful_acc()`
自动计算 `_apply_three_zone` 首次达到 max_angle 时的 accumulated_x 值，通过二分查找在 `[linear_end, saturation_end]` 区间内定位。

---

## 三、涉及文件清单

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `core/vgamepad_output.py` | 新增 | ViGEmBus 虚拟手柄输出 |
| `core/vjoy_output.py` | 保留 | 作为备用输出方案 |
| `core/__init__.py` | 修改 | 导出 VGamepadOutput |
| `core/steering_algorithm.py` | 重写 | 辅助回中三状态机 + 超限钳位 |
| `main.py` | 修改 | 切换输出层 + 鼠标按键控制 |
| `ui/parameter_panel.py` | 修改 | 新增辅助回中参数控件 |
| `ui/main_window.py` | 修改 | 参数显示同步 |
| `ui/status_bar.py` | 修改 | 新增手柄状态指示 |
| `config/config_manager.py` | 修改 | 新增辅助参数默认值 |
| `config.json` | 修改 | 配置同步 |
