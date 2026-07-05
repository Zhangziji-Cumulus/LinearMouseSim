# 鼠标模拟方向盘线性输入工具 - 实现计划

## 一、项目研究结论

### 当前项目状态
- 项目目录：`e:\WorkSpace\WorkProject\CodeWS\DeskTopProject\LinearMouseSim`
- 当前文件：仅包含需求文档和空README，无代码实现
- 目标：实现鼠标水平移动 → 游戏方向盘线性转向

### 技术依赖与风险评估

| 依赖项 | 风险等级 | 说明 |
|--------|----------|------|
| vJoy (虚拟摇杆) | **高** | 必须验证能否写入轴信号并被游戏识别 |
| pyvjoy (Python绑定) | **高** | 需要确认安装和兼容性 |
| Win32 Raw Input API | 中 | 用于获取鼠标增量位移 |
| ClipCursor + SetCursorPos | 中 | 光标锁定与释放，需处理异常情况 |
| tkinter GUI | 低 | Python标准库，无需额外安装 |
| keyboard 库 | 低 | 全局热键监听 |

### 核心状态机设计
```
OFF → ON (记录基准点 + 锁定光标 + 绝对位置映射 + 写入vJoy) → OFF (释放光标 + 清零vJoy轴)
```

### 核心转向逻辑（用户确认）
**绝对位置模式**：开启模拟后以当前鼠标位置为基准点，鼠标相对位移直接映射为方向盘角度，鼠标停住方向盘保持当前角度，不会自动回中。

| 场景 | 方向盘状态 |
|------|------------|
| 鼠标左移 | 方向盘逆时针旋转（角度增加） |
| 鼠标右移 | 方向盘顺时针旋转（角度减少） |
| 鼠标停住 | 方向盘保持当前角度（**不回中**） |
| 关闭模拟 | 方向盘归零，鼠标恢复正常 |

**关键机制**：
- 开启时记录基准点：`base_x = 当前鼠标X坐标`
- 方向盘角度：`angle = (current_x - base_x) × sensitivity`
- 光标锁定：定期将光标重置到中心位置，实现"无限平移"效果
- 回正惯性：作为可选参数，用户可选择是否启用轻微回正效果

---

## 二、文件与模块结构

```
LinearMouseSim/
├── main.py                    # 程序入口，主循环
├── core/
│   ├── __init__.py
│   ├── mouse_capture.py       # 鼠标增量采样 (Win32 Raw Input)
│   ├── steering_algorithm.py  # 转向算法 (平滑、阻尼、死区、曲线)
│   ├── vjoy_output.py         # 虚拟摇杆输出
│   └── state_machine.py       # 状态管理 (ON/OFF切换)
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # 主窗口 + 方向盘可视化
│   ├── parameter_panel.py     # 参数调节面板
│   └── status_bar.py          # 状态指示
├── config/
│   ├── __init__.py
│   ├── config_manager.py      # 配置文件读写
│   └── presets.py             # 游戏类型预设
├── hotkey/
│   ├── __init__.py
│   └── hotkey_manager.py      # 全局热键管理
└── utils/
    ├── __init__.py
    └── os_utils.py            # 系统工具 (管理员权限、开机自启)
```

---

## 三、阶段化实现步骤

### Layer 1：MVP核心循环（最低可行产品）

**目标**：实现鼠标绝对位置映射 → vJoy轴输出的基本闭环

| 步骤 | 文件 | 内容 |
|------|------|------|
| 1.1 | `core/mouse_capture.py` | 获取鼠标绝对X坐标，记录基准点 |
| 1.2 | `core/vjoy_output.py` | 集成pyvjoy，实现轴值写入 (0-32767范围) |
| 1.3 | `core/state_machine.py` | 实现ON/OFF状态切换，包含基准点记录、光标锁定/释放 |
| 1.4 | `main.py` | 组装主循环：获取位置 → 计算相对位移 → 映射角度 → 输出 |

**关键验证点**：
- 鼠标移动时vJoy轴值线性变化
- 鼠标停住时方向盘保持当前角度（不回中）
- 游戏能识别虚拟摇杆输入

### Layer 2：转向算法优化

**目标**：消除阶梯感，实现丝滑转向

| 步骤 | 文件 | 内容 |
|------|------|------|
| 2.1 | `core/steering_algorithm.py` | 实现线性插值平滑 |
| 2.2 | `core/steering_algorithm.py` | 实现死区过滤 |
| 2.3 | `core/steering_algorithm.py` | 实现转向阻尼（可选回正惯性） |
| 2.4 | `core/steering_algorithm.py` | 实现最大舵角限制 |

**算法公式**（绝对位置模式）：
- 基础角度：`raw_angle = (current_x - base_x) × sensitivity`
- 平滑：`current_angle = alpha * raw_angle + (1-alpha) * previous_angle`
- 死区：`if |delta_x| < deadzone: 保持当前角度不变`
- 回正惯性：可选参数，默认关闭；启用时 `angle *= (1 - return_speed)` 仅在用户停止输入时生效
- 最大舵角：`angle = clamp(angle, -max_angle, +max_angle)`

### Layer 3：UI可视化方向盘

**目标**：实时展示转向角度，便于调试

| 步骤 | 文件 | 内容 |
|------|------|------|
| 3.1 | `ui/main_window.py` | 创建tkinter主窗口 |
| 3.2 | `ui/main_window.py` | Canvas绘制方向盘图形（带刻度） |
| 3.3 | `ui/main_window.py` | 实时旋转动画同步游戏输入 |
| 3.4 | `ui/status_bar.py` | 状态指示灯（绿色开启/红色关闭） |

### Layer 4：热键与配置

**目标**：支持自定义开关热键，参数自动保存

| 步骤 | 文件 | 内容 |
|------|------|------|
| 4.1 | `hotkey/hotkey_manager.py` | 全局热键监听（支持单键/组合键） |
| 4.2 | `hotkey/hotkey_manager.py` | 热键防误触（短按生效、防抖） |
| 4.3 | `config/config_manager.py` | JSON配置文件读写 |
| 4.4 | `config/config_manager.py` | 热键配置持久化 |

### Layer 5：参数调节面板

**目标**：所有参数可视化调节，实时生效

| 步骤 | 文件 | 内容 |
|------|------|------|
| 5.1 | `ui/parameter_panel.py` | 创建滑块控件 |
| 5.2 | `ui/parameter_panel.py` | 绑定参数：灵敏度、平滑系数、死区、最大舵角、回正速度 |
| 5.3 | `config/config_manager.py` | 参数自动保存 |

### Layer 6：高级功能

**目标**：完整灵敏度体系、预设配置、实时调节

| 步骤 | 文件 | 内容 |
|------|------|------|
| 6.1 | `core/steering_algorithm.py` | 四种灵敏度曲线（线性/指数/对数/S型） |
| 6.2 | `core/steering_algorithm.py` | 三段式灵敏度分区（死区/线性区/饱和区） |
| 6.3 | `config/presets.py` | 游戏类型预设（5种） |
| 6.4 | `hotkey/hotkey_manager.py` | 实时灵敏度调节热键 |
| 6.5 | `config/config_manager.py` | 多套配置方案管理 |

---

## 四、关键技术实现细节

### 4.1 鼠标增量采样（Win32 Raw Input）
```python
# 使用ctypes调用Win32 API
# RegisterRawInputDevices → GetRawInputData
# 获取MOUSE_MOVE_RELATIVE位移
```

### 4.2 光标锁定与释放
```python
# 开启时：ClipCursor锁定区域 + SetCursorPos居中
# 关闭时：ClipCursor(NULL)释放 + 恢复原光标位置
# 异常处理：确保程序崩溃时也能释放光标
```

### 4.3 vJoy轴值映射
```python
# 方向盘角度 (-max_angle ~ +max_angle) → vJoy轴值 (0 ~ 32767)
# 线性映射：axis_value = ((angle / max_angle) + 1) * 16383.5
```

### 4.4 灵敏度曲线公式
| 曲线 | 公式 |
|------|------|
| 线性 | `angle = delta * sensitivity` |
| 指数 | `angle = k * delta^n` (n=1.5) |
| 对数 | `angle = k * log(delta + 1)` |
| S型 | `angle = max_angle * sigmoid(delta * k)` |

---

## 五、风险处理与安全措施

### 5.1 光标锁定安全
- 异常捕获：`try/except`确保任何情况下都能释放光标
- 定时检测：后台线程检测主程序状态，异常时强制释放
- 备用释放：提供备用热键强制关闭

### 5.2 vJoy未安装处理
- 启动时检测vJoy是否安装
- 未安装时提示用户下载安装
- 提供静默安装方案

### 5.3 管理员权限
- 启动时检测管理员权限
- 无权限时自动请求提升
- 在UAC弹窗中说明原因

### 5.4 热键冲突
- 检测系统热键冲突
- 提供冲突提示和解决方案
- 支持自定义热键避免冲突

---

## 六、测试策略

### 6.1 单元测试
- 转向算法：测试各曲线输出是否符合预期
- 参数映射：测试不同参数组合的效果
- 状态机：测试ON/OFF切换的正确性

### 6.2 集成测试
- 鼠标输入 → vJoy输出闭环测试
- 热键触发状态切换测试
- 配置保存/加载测试

### 6.3 游戏测试
- 尘埃拉力赛2.0（目标游戏）
- 神力科莎
- 地平线系列
- 欧洲卡车模拟

---

## 七、开发顺序建议

```
1. Spike验证：vJoy + pyvjoy轴写入测试
2. Layer 1：MVP核心循环
3. Layer 2：转向算法
4. Layer 3：UI方向盘
5. Layer 4：热键与配置
6. Layer 5：参数面板
7. Layer 6：高级功能
8. 测试与调试
```

---

## 八、预期产出

### Python原型阶段
- `main.py`：完整可运行程序
- `core/`：核心算法模块
- `ui/`：可视化界面模块
- `config/`：配置管理模块
- `hotkey/`：热键管理模块
- `config.json`：默认配置文件

### 后续C#迁移阶段
- 将Python算法1:1迁移至C#
- 使用P/Invoke替代ctypes
- 生成可分发EXE文件
