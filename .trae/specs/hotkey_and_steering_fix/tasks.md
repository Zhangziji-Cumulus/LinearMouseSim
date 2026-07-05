# LinearMouseSim - 快捷键冲突与角度映射修复实现计划

## [x] Task 1: 修改默认 toggle 快捷键为 `}`
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 修改 `config/config_manager.py` 中的 DEFAULT_CONFIG，将 `hotkeys.toggle` 从 `=` 改为 `}`
  - 修改 `config.json` 中的 toggle 热键值
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgement` TR-1.1: 启动程序后，按 `}` 键可以切换模拟状态，按 `=` 键不会触发切换
  - `human-judgement` TR-1.2: 按 `+` 键可以增加灵敏度，无冲突

## [x] Task 2: 修复角度映射核心逻辑（开启时归零 + 移动时正常变化 + 关闭后再开启无突变）
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 修改 `core/state_machine.py` 的 `turn_on()` 方法：
    - 将 `base_x` 设置为屏幕中心（`self.center_x`）而非当前鼠标位置
    - 添加 `mouse_delta_x` 累积变量用于追踪相对位移
  - 修改 `core/state_machine.py` 的 `_cursor_lock_loop()` 方法：
    - 累积鼠标偏移到 `mouse_delta_x`
  - 修改 `main.py` 的 `on_toggle()` 方法：
    - 在开启时调用 `steering_algorithm.reset()` 确保角度归零
  - 修改 `main.py` 的 `main_loop()` 方法：
    - 使用累积的 `mouse_delta_x` 计算有效鼠标位置
- **Acceptance Criteria Addressed**: AC-4, AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-2.1: 开启模拟时，`steering_algorithm.previous_angle` 为 0
  - `human-judgement` TR-2.2: 开启模拟后，UI 显示角度为 0°
  - `human-judgement` TR-2.3: 开启模拟后移动鼠标，角度随移动正常变化
  - `human-judgement` TR-2.4: 关闭模拟后移动鼠标到边缘，再开启时角度从零开始

## [x] Task 3: 在 UI 参数面板中添加热键配置区域
- **Priority**: medium
- **Depends On**: Task 1
- **Description**: 
  - 修改 `ui/parameter_panel.py`，添加热键配置区域
  - 创建热键显示组件，显示当前热键值
  - 添加热键修改按钮，点击后进入录制模式
  - 实现热键录制逻辑，捕获用户按下的按键
  - 调用 `hotkey_manager.set_hotkey()` 更新热键并保存配置
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `human-judgement` TR-3.1: 参数面板中显示热键配置区域，包含四个热键
  - `human-judgement` TR-3.2: 点击修改按钮后，提示用户按下新按键
  - `human-judgement` TR-3.3: 按下新按键后，热键立即更新并生效
  - `human-judgement` TR-3.4: 关闭程序后重启，热键配置保持不变

## [x] Task 4: 更新 main.py 中的热键回调注册
- **Priority**: medium
- **Depends On**: Task 2, Task 3
- **Description**: 
  - 在 `on_toggle()` 回调中调用 `steering_algorithm.reset()`
  - 将 hotkey_manager 传递给参数面板
- **Acceptance Criteria Addressed**: AC-4, AC-3
- **Test Requirements**:
  - `human-judgement` TR-4.1: 切换模拟状态时角度正确归零
  - `human-judgement` TR-4.2: UI 修改热键后立即生效

## [x] Task 5: 测试与验证
- **Priority**: high
- **Depends On**: Task 1, Task 2, Task 3, Task 4
- **Description**: 
  - 测试所有修复功能
  - 验证快捷键无冲突
  - 验证角度映射正常工作
  - 验证热键配置持久化
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `human-judgement` TR-5.1: 所有功能正常工作
  - `human-judgement` TR-5.2: 无明显的性能问题或延迟