# 修复计划：恢复原快捷键并修复鼠标锁定隐藏

## 问题分析

### 问题1：快捷键需要恢复为原来的配置
当前配置使用 F12/F9/F10/F11，但用户需要原来的 `}`、`+`、`-`、`0` 快捷键。

### 问题2：鼠标锁定和隐藏功能失效
- `turn_on()` 方法中没有调用 `cursor_manager.lock_to_center()` 来锁定鼠标区域
- `hide_cursor_force()` 创建的空光标在调用 `SetCursorPos` 后可能被系统覆盖
- 缺少持续的光标锁定机制

## 修改方案

### 文件列表

| 文件 | 修改内容 |
|------|----------|
| `config.json` | 恢复原来的快捷键配置 |
| `core/state_machine.py` | 在 `turn_on()` 中添加光标锁定调用，优化锁定循环 |
| `core/mouse_capture.py` | 优化鼠标隐藏函数，确保持续隐藏 |
| `hotkey/hotkey_manager.py` | 修复轮询方案中特殊字符的处理 |

### 修改步骤

#### 步骤1：恢复快捷键配置（config.json）
- 将 `toggle` 改为 `}`
- 将 `increase_sensitivity` 改为 `+`
- 将 `decrease_sensitivity` 改为 `-`
- 将 `reset_steering` 改为 `0`

#### 步骤2：修复鼠标锁定（state_machine.py）
- 在 `turn_on()` 中添加 `self.cursor_manager.lock_to_center()` 调用
- 在 `_cursor_lock_loop` 中确保每帧都调用锁定和隐藏

#### 步骤3：优化鼠标隐藏（mouse_capture.py）
- 修改 `hide_cursor_force()` 返回空光标句柄并保存
- 添加持续隐藏机制，防止系统覆盖

## 技术细节

### 光标锁定实现要点
- 使用 `ClipCursor` 将鼠标限制在中心区域（1x1像素）
- 配合 `SetCursorPos` 确保鼠标始终在中心
- 在锁定循环中每帧调用锁定和隐藏

### 特殊字符快捷键处理
- `}` 对应 VK_OEM_6 (0xDD)，需要按 Shift+]
- `+` 对应 VK_OEM_PLUS (0xBB)，需要按 Shift+=
- 轮询方案使用 `GetAsyncKeyState` 检测按键状态

## 风险处理

- **兼容性风险**：不同键盘布局可能影响特殊字符检测
- **性能风险**：高频锁定循环可能影响性能，需控制频率
- **系统冲突**：光标锁定可能与其他应用冲突，需确保关闭时完全释放