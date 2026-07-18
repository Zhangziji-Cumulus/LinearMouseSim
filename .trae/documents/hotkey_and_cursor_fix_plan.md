# 修复计划：游戏窗口快捷键和鼠标隐藏问题

## 问题分析

### 问题1：进入游戏窗口不能使用快捷键
当前使用 `keyboard` 库注册热键，但该库在游戏窗口（特别是全屏游戏、使用DirectInput/raw input的游戏）中可能无法正确捕获按键事件。这是因为：
- 游戏可能独占输入设备
- `keyboard` 库依赖全局钩子，但某些游戏会拦截低级键盘钩子
- 需要使用更底层的 Windows API（LowLevelKeyboardProc）来确保全局捕获

### 问题2：鼠标在开启模拟时没有隐藏
虽然已实现 `hide_cursor()` 函数，但 `_cursor_lock_loop` 中每次调用 `set_mouse_position()` 后，系统可能会自动显示鼠标指针。需要在每次重置位置后重新隐藏鼠标。

## 修改方案

### 文件列表

| 文件 | 修改内容 |
|------|----------|
| `hotkey/hotkey_manager.py` | 使用 Windows 低级键盘钩子替代 keyboard 库 |
| `core/mouse_capture.py` | 添加更可靠的鼠标隐藏方法 |
| `core/state_machine.py` | 在光标锁定循环中每次设置位置后重新隐藏鼠标 |

### 修改步骤

#### 步骤1：重构热键管理器（hotkey_manager.py）
- 使用 `ctypes` 调用 Windows API 设置全局键盘钩子
- 实现 `LowLevelKeyboardProc` 回调函数
- 保留原有 API 接口，确保兼容性

#### 步骤2：优化鼠标隐藏（mouse_capture.py）
- 添加 `hide_cursor_force()` 函数，使用多种方法确保鼠标隐藏
- 考虑使用空光标方案作为备选

#### 步骤3：修复光标锁定循环（state_machine.py）
- 在 `_cursor_lock_loop` 的每次迭代中，设置鼠标位置后立即调用隐藏函数
- 确保鼠标持续保持隐藏状态

## 技术细节

### 低级键盘钩子实现要点
- 使用 `user32.SetWindowsHookExW` 设置 `WH_KEYBOARD_LL` 钩子
- 回调函数中检查按键并触发相应动作
- 使用 `user32.CallNextHookEx` 传递事件
- 确保钩子线程消息循环正常运行

### 鼠标隐藏实现要点
- 每次 `SetCursorPos` 后调用 `ShowCursor(False)`
- 考虑使用空光标资源替换系统光标

## 风险处理

- **兼容性风险**：不同游戏可能有不同的输入处理方式，需要测试多种游戏
- **性能风险**：全局钩子可能影响系统性能，需要优化钩子处理逻辑
- **线程安全**：确保钩子回调与主程序之间的线程安全