# LinearMouseSim - 快捷键冲突与角度映射修复 PRD

## Overview
- **Summary**: 修复三个核心问题：1) 快捷键 `=` 与参数加减冲突；2) 缺少快捷键配置界面；3) 鼠标移动映射角度不正确（开启时未归零、移动时角度几乎不变、关闭后移动再开启角度突变）
- **Purpose**: 提升用户体验，解决关键功能缺陷，使鼠标方向盘模拟功能正常工作
- **Target Users**: 使用 LinearMouseSim 的赛车游戏玩家

## Goals
- 修复快捷键冲突，将切换快捷键改为 `}`
- 添加快捷键配置界面，支持用户自定义所有热键
- 修复鼠标角度映射问题，确保：
  - 开启模拟时角度归零
  - 鼠标移动时角度正常变化
  - 关闭后移动鼠标再开启不会导致角度突变

## Non-Goals (Out of Scope)
- 添加新的灵敏度曲线类型
- 优化性能或降低延迟
- 添加新的 UI 动画效果
- 打包或发布相关工作

## Background & Context
- 当前 `toggle` 快捷键是 `=`，`increase_sensitivity` 是 `+`，两者共享同一物理键（Shift+=）
- 当前 UI 没有热键配置界面，用户只能手动修改 config.json
- 角度映射逻辑存在缺陷：`base_x` 设置为开启时的鼠标位置，但光标锁定循环会立即将鼠标拉回中心，导致 `delta_x` 计算错误

## Functional Requirements
- **FR-1**: 将默认 toggle 快捷键从 `=` 改为 `}`
- **FR-2**: 在 UI 参数面板中添加热键配置区域，显示当前热键并支持修改
- **FR-3**: 开启模拟时，确保方向盘角度归零
- **FR-4**: 鼠标移动时，方向盘角度应随位移正常变化
- **FR-5**: 关闭模拟后移动鼠标，再次开启时不应出现角度突变

## Non-Functional Requirements
- **NFR-1**: 热键修改后立即生效，无需重启程序
- **NFR-2**: 热键配置应持久化到 config.json
- **NFR-3**: 角度响应延迟不超过 50ms

## Constraints
- **Technical**: Python 3.x, Tkinter UI, keyboard 库处理热键
- **Dependencies**: vJoy 驱动必须安装

## Assumptions
- 用户使用标准美式键盘布局
- 用户已安装 vJoy 驱动
- 程序以管理员身份运行

## Acceptance Criteria

### AC-1: 快捷键冲突修复
- **Given**: 默认配置中 toggle 热键为 `=`
- **When**: 修改默认配置并重启程序
- **Then**: toggle 热键变为 `}`，与 `+`/`-` 参数调节热键无冲突
- **Verification**: `human-judgment`

### AC-2: 热键配置界面
- **Given**: UI 参数面板已打开
- **When**: 用户查看参数面板
- **Then**: 面板中显示热键配置区域，包含四个热键的当前值和修改按钮
- **Verification**: `human-judgment`

### AC-3: 修改热键功能
- **Given**: 用户点击热键修改按钮
- **When**: 用户按下新的按键组合
- **Then**: 热键立即更新并保存到配置文件
- **Verification**: `human-judgment`

### AC-4: 开启时角度归零
- **Given**: 当前角度不为 0，模拟处于 OFF 状态
- **When**: 用户开启模拟（toggle）
- **Then**: 方向盘角度立即归零，UI 显示 0°
- **Verification**: `programmatic`

### AC-5: 鼠标移动角度正常变化
- **Given**: 模拟处于 ON 状态，角度为 0°
- **When**: 用户移动鼠标（左右滑动）
- **Then**: 方向盘角度随鼠标移动而线性变化，移动越多角度越大
- **Verification**: `human-judgment`

### AC-6: 关闭后移动再开启无突变
- **Given**: 模拟处于 OFF 状态，用户移动鼠标到屏幕边缘
- **When**: 用户开启模拟
- **Then**: 方向盘角度从零开始，不会出现突变到较大角度
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要支持组合键（Ctrl+Key, Alt+Key）作为热键？
- [ ] 是否需要热键冲突检测（提示用户某个热键已被占用）？