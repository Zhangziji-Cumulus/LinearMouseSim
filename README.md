# LinearMouseSim

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/License-Personal%20Use-green.svg)](#许可证)

> 将鼠标转换为线性方向盘输入的 Windows 桌面工具，专为尘埃拉力赛 2.0 等赛车游戏设计

## 简介

LinearMouseSim 是一个 Windows 桌面应用程序，能够将鼠标的水平移动转换为线性方向盘输入信号。它通过模拟 Xbox 360 虚拟手柄，让没有方向盘设备的玩家也能使用鼠标获得线性转向体验。

### 为什么需要这个工具？

- 方向盘设备价格昂贵，不是每个人都负担得起
- 键盘/手柄的数字输入无法实现平滑的线性转向
- 鼠标天然具备高精度的水平定位能力
- 本工具将鼠标移动直接映射为方向盘角度，实现真正的线性控制

## 功能特性

### 核心功能

| 功能 | 说明 |
|------|------|
| **鼠标模拟方向盘** | 将鼠标水平移动转换为方向盘角度，支持最高 540° 转向 |
| **虚拟 Xbox 360 手柄** | 使用 ViGEmBus 模拟标准手柄，游戏原生支持 |
| **油门/刹车控制** | 右键按住为油门，左键按住为刹车 |
| **智能辅助回中** | 三状态机设计，解决大角度回打时的卡顿问题 |

### 高级配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 灵敏度 | 0.2 | 鼠标移动到角度的转换系数 |
| 平滑度 | 0.25 | 角度变化的平滑程度 |
| 死区 | 0 px | 忽略的微小移动范围 |
| 最大角度 | 180° | 方向盘最大转向角度 |
| DPI | 800 | 鼠标 DPI 基准值 |
| 指数曲线幂 | 1.8 | 非线性转向曲线的弯曲程度 |

### 界面特性

- **实时方向盘动画** - 可视化显示当前转向角度和方向
- **参数配置面板** - 5 个标签页，20+ 可调参数
- **自定义预设** - 保存/加载/切换多套配置方案
- **全局快捷键** - 所有热键均可自定义
- **OSD 叠加显示** - 实时显示灵敏度变化等信息
- **系统托盘** - 最小化到托盘，支持后台运行

## 安装说明

### 系统要求

- **操作系统**: Windows 10/11 (64-bit)
- **驱动**: ViGEmBus (首次运行会自动提示安装)

### 下载安装

1. 从 [Releases](https://github.com/Zhangziji-Cumulus/LinearMouseSim/releases) 下载最新版本
2. 解压后运行 `LinearMouseSim.exe`
3. 首次运行时，程序会检测 ViGEmBus 驱动
4. 如未安装，点击弹窗中的"是"打开下载页面
5. 安装 ViGEmBus 驱动后重启程序

### ViGEmBus 驱动安装

ViGEmBus 是一个虚拟手柄驱动，允许程序模拟 Xbox 360 手柄。

1. 访问 [ViGEmBus Releases](https://github.com/ViGEm/ViGEmBus/releases)
2. 下载最新版 `.exe` 安装程序
3. 运行安装程序，按提示完成安装
4. 安装完成后重启 LinearMouseSim

## 使用说明

### 基本操作

```
1. 启动 LinearMouseSim
2. 按 } 键开启模拟（状态栏绿色 LED 亮起）
3. 左右移动鼠标控制方向盘转向
4. 右键按住 = 油门
5. 左键按住 = 刹车
6. 按 0 键重置方向盘到中心
7. 按 } 键关闭模拟
```

### 默认快捷键

| 按键 | 功能 |
|------|------|
| `}` | 开启/关闭模拟 |
| `+` | 增加灵敏度 |
| `-` | 降低灵敏度 |
| `0` | 重置方向盘到中心 |
| `F5` | 切换到灵敏度预设 1 |
| `F6` | 切换到灵敏度预设 2 |
| `F7` | 切换到灵敏度预设 3 |
| `Shift` (按住) | 临时半灵敏度 |
| `Ctrl` + 滚轮上 | 增加灵敏度 |
| `Ctrl` + 滚轮下 | 降低灵敏度 |

### 界面说明

程序界面分为两个主要区域：

**左侧 - 参数面板**
- 基本设置：灵敏度、平滑度、死区、最大角度、DPI
- 辅助回中：回打检测参数、归中速度
- 方向盘回中：自动回中模式（延迟/立即/连续）
- 映射参数：像素到角度的映射终点
- 快捷键：自定义热键配置

**右侧 - 方向盘显示**
- 实时显示当前转向角度
- 橙色标记显示 12 点钟位置
- 绿色箭头显示转向方向

### 配置预设

1. 调整参数到满意的效果
2. 点击预设下拉框旁的 `...` 按钮
3. 选择"保存当前配置"
4. 输入预设名称
5. 下次可直接从下拉框切换

## 技术架构

```
LinearMouseSim/
├── main.py                    # 程序入口，主循环
├── core/
│   ├── mouse_capture.py       # Win32 鼠标捕获
│   ├── state_machine.py       # 状态机（开/关）
│   ├── steering_algorithm.py  # 转向算法（核心）
│   ├── vgamepad_output.py     # ViGEmBus 虚拟手柄
│   └── vjoy_output.py         # vJoy 备用方案
├── ui/
│   ├── main_window.py         # 主窗口
│   ├── parameter_panel.py     # 参数面板
│   ├── status_bar.py          # 状态栏
│   ├── osd_manager.py         # OSD 显示
│   └── tray_manager.py        # 系统托盘
├── config/
│   ├── config_manager.py      # 配置管理
│   └── presets.py             # 预设管理
├── hotkey/
│   └── hotkey_manager.py      # 快捷键管理
└── utils/
    └── os_utils.py            # 系统工具
```

### 核心算法

转向算法采用增量累积模型：

1. 读取鼠标水平位移增量
2. 应用灵敏度和 DPI 缩放
3. 通过死区过滤微小移动
4. 累积到内部状态变量
5. 应用曲线变换（线性或指数）
6. 平滑处理输出角度
7. 限制在最大角度范围内

辅助回中算法使用三状态机：
- **普通态**: 正常累积鼠标位移
- **归中态**: 检测到大幅回打，按比例衰减累积值
- **中心检测态**: 锁定在中心位置，等待用户确认

## 构建开发

### 环境准备

```bash
# 克隆仓库
git clone https://github.com/Zhangziji-Cumulus/LinearMouseSim.git
cd LinearMouseSim

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 运行开发

```bash
python main.py
```

### 打包为 exe

```bash
pyinstaller LinearMouseSim.spec --clean
```

生成文件位于 `dist/LinearMouseSim.exe`

## 依赖列表

| 包名 | 版本 | 用途 |
|------|------|------|
| keyboard | 0.13.5 | 全局热键注册 |
| pillow | 12.3.0 | 托盘图标生成 |
| pyvjoy | 1.0.1 | vJoy 虚拟手柄（备用） |
| vgamepad | 0.1.0 | ViGEmBus 虚拟手柄 |

### 系统依赖

- ViGEmBus 驱动 - 虚拟 Xbox 360 手柄支持

## 已知问题

- 仅支持 Windows 平台（依赖 Win32 API）
- 需要安装 ViGEmBus 驱动才能使用虚拟手柄功能
- 部分游戏可能需要手动调整控制映射
- 高 DPI 显示器可能需要调整系统缩放设置

## 更新日志

### v0.0.1 (2026-07-19)
- 初始测试版本
- 实现鼠标模拟方向盘核心功能
- 集成 ViGEmBus 虚拟 Xbox 360 手柄
- 实现辅助回中三状态机算法
- 完成参数配置界面和预设系统
- 支持全局快捷键和系统托盘
- 支持 PyInstaller 打包分发

详细更新日志请查看 [CHANGELOG.md](CHANGELOG.md)

## 许可证

本项目仅供学习和个人使用，不得用于商业目的。

## 致谢

- [ViGEmBus](https://github.com/ViGEm/ViGEmBus) - 虚拟手柄驱动框架
- [vgamepad](https://github.com/yannbouteiller/vgamepad) - Python 虚拟手柄库
- [keyboard](https://github.com/boppreh/keyboard) - Python 全局热键库
- [PyInstaller](https://pyinstaller.org/) - Python 打包工具

## 贡献

欢迎提交 Issue 和 Pull Request。本项目在开发过程中使用了 AI Agent 辅助编程。

---

**注意**: 本工具仅供学习和个人使用。使用鼠标模拟方向盘可能会影响游戏体验，请根据实际情况调整参数。
