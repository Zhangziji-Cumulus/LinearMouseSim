# UI 实现计划

## 概述
创建三个UI模块文件，使用tkinter实现赛车游戏方向盘模拟工具的界面。

## 实施步骤

### 1. 创建 ui/main_window.py
- 创建主窗口类 `MainWindow`
- 使用Canvas绘制方向盘图形
- 方向盘刻度：每15度一个刻度
- 中心点提示
- 鼠标移动事件绑定：左移逆时针旋转，右移顺时针旋转
- 角度范围：0°居中，±90°最大转向
- 实时旋转动画
- 禁止鼠标拖拽UI

### 2. 创建 ui/status_bar.py
- 创建状态栏类 `StatusBar`
- 开关状态指示灯（绿色开启/红色关闭）
- 当前角度显示
- 模拟状态文字提示

### 3. 创建 ui/parameter_panel.py
- 创建参数面板类 `ParameterPanel`
- 滑块控件：灵敏度、平滑系数、死区、最大舵角、回正速度
- 数值显示标签
- 实时生效回调

### 4. 更新 ui/__init__.py
- 导出三个模块类

## 技术规范
- 使用tkinter
- 界面风格：简洁现代，深色主题
- 响应式布局
- 高DPI支持

## 文件结构
```
ui/
├── __init__.py
├── main_window.py
├── status_bar.py
└── parameter_panel.py
```
