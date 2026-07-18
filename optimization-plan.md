# LinearMouseSim 重构与优化计划

## 目标

1. **UI现代化** — 更好看的拉力赛方向盘、自定义滑块、现代视觉风格
2. **代码重构** — 拆分上帝类、状态枚举、清理死代码、配置化
3. **手感优化** — 平滑算法改进、响应性提升、帧率无关的时间感知

---

## 智能体分工

### 🎨 UI工程师
**职责：** UI设计与视觉优化

**参考Skill：** `ui-ux-pro-max:ui-ux-pro-max`

**任务清单：**

#### 任务1：拉力赛方向盘重绘
- **文件：** `ui/main_window.py` → `_create_wheel_elements()`
- **当前问题：** 简陋的圆形方向盘，像玩具
- **改进方案：**
  - 深色金属质感外圈（#1a1a2e）
  - Alcantara 三段式握把，带高光纹理
  - 三个梯形辐条，带减重圆孔
  - 碳纤维中心盘，带螺栓装饰
  - 12点钟黄色标记（拉力赛标志）
  - 完整刻度盘，±max_angle 内红色高亮
- **输出：** 新的 `_create_wheel_elements` 方法代码

#### 任务2：自定义 ModernSlider 组件
- **新建：** `ui/widgets/modern_slider.py`
- **当前问题：** 使用系统原生 `ttk.Scale`，外观不统一
- **改进方案：**
  - Canvas 自绘圆形手柄，悬停高亮
  - 渐变填充轨道，显示当前值占比
  - 数值标签实时跟随手柄位置
  - 支持键盘方向键微调
- **输出：** ModernSlider 类代码

#### 任务3：参数面板布局优化
- **文件：** `ui/parameter_panel.py`
- **改进方案：**
  - 用 ModernSlider 替换所有 ttk.Scale
  - 参数分组用卡片样式（圆角+阴影背景）
  - 添加 section 折叠/展开功能

#### 任务4：主题系统更新
- **文件：** `ui/theme.py`
- **改进方案：**
  - 新增动画时长 token
  - 新增阴影层级（3级）
  - 新增状态色（hover/pressed/disabled）
  - 增大圆角到 8-12px

---

### 🏗️ 底层架构师
**职责：** 代码重构与架构优化

**参考Skill：** `superpowers:writing-plans`, `superpowers:systematic-debugging`

**任务清单：**

#### 任务5：状态枚举 + Bug修复
- **文件：** `core/state_machine.py`, `core/steering_algorithm.py`
- **改进方案：**
  - 创建 `SimulationState(Enum): ON, OFF`
  - 修复 deadzone 双重赋值 bug
  - 清理未使用的 imports（5处）
  - 修复裸 except 子句
- **输出：** 修改后的 state_machine.py 和 steering_algorithm.py

#### 任务6：拆分 LinearMouseSim 上帝类
- **文件：** `main.py`
- **当前问题：** 323行的 god class，做太多事
- **改进方案：**
  - 提取 `EventDispatcher` 类处理热键回调
  - 提取 `SimulationEngine` 类处理主循环
  - `LinearMouseSim` 只负责初始化和组装
- **输出：** 重构后的 main.py

#### 任务7：灵敏度预设统一处理
- **文件：** `main.py`
- **当前问题：** 5个重复的 `on_sensitivity_preset_X` 方法
- **改进方案：**
  - 创建 `_apply_sensitivity(value)` 统一方法
  - 5个回调调用此方法
- **输出：** 修改后的 main.py

#### 任务8：配置化硬编码值
- **文件：** `config/config_manager.py`
- **当前问题：** 13+ 硬编码值无法配置
- **改进方案：** 新增配置项
  ```python
  'app': {
      'sensitivity_presets': [1.0, 2.0, 3.0],
      'sensitivity_step': 0.1,
      'wheel_sensitivity_factor': 1.1,
      'main_loop_interval': 0.005,
      'hotkey_cooldown_ms': 200,
  }
  ```
- **输出：** 修改后的 config_manager.py

#### 任务9：修复跨层导入
- **文件：** `ui/parameter_panel.py`
- **当前问题：** UI 层直接导入 config 层
- **改进方案：** 通过依赖注入传入 presets
- **输出：** 修改后的 parameter_panel.py

---

### 🧪 测试工程师
**职责：** 验证所有改动是否合格

**参考Skill：** `superpowers:verification-before-completion`, `superpowers:test-driven-development`

**任务清单：**

#### 验证检查点

每个任务完成后，测试工程师检查：

1. **编译检查**
   ```bash
   python -c "from core.steering_algorithm import SteeringAlgorithm; print('OK')"
   python -c "from ui.main_window import MainWindow; print('OK')"
   python -c "from config.config_manager import ConfigManager; print('OK')"
   ```

2. **功能验证**
   - 程序启动无报错
   - 快捷键开关正常
   - 参数调节正常
   - 手动输入参数生效
   - 辅助回中正常工作

3. **视觉验证**
   - 方向盘旋转动画流畅
   - 新设计渲染正确
   - 刻度盘标记清晰

4. **回归测试**
   - 现有功能不被破坏
   - 配置文件兼容

**不合格处理：**
- 发现问题 → 记录到问题清单
- 通知对应智能体修复
- 重新验证直到通过

---

## 执行流程

```
Phase 1 (架构基础):
  任务5 (bug修复+枚举) → 任务7 (去重) → 任务8 (配置化) → 任务9 (依赖修复)
  ↓ 测试工程师验证

Phase 2 (UI优化):
  任务4 (主题) → 任务1 (方向盘) → 任务2 (ModernSlider) → 任务3 (面板)
  ↓ 测试工程师验证

Phase 3 (最终验证):
  测试工程师完整回归测试
  ↓ 全部通过后同步到原始项目
```

---

## 需要的 Skill

| Skill | 用途 |
|-------|------|
| `ui-ux-pro-max:ui-ux-pro-max` | UI设计指导 |
| `superpowers:writing-plans` | 编写实现计划 |
| `superpowers:systematic-debugging` | 调试问题 |
| `superpowers:verification-before-completion` | 完成前验证 |
| `superpowers:test-driven-development` | 测试驱动开发 |

---

## 文件结构

```
修改的文件：
├── ui/main_window.py          # 方向盘重绘
├── ui/parameter_panel.py      # 面板布局优化
├── ui/theme.py                # 主题更新
├── ui/widgets/modern_slider.py # 新建：自定义滑块
├── core/steering_algorithm.py  # Bug修复
├── core/state_machine.py       # 状态枚举
├── main.py                     # 拆分上帝类
├── config/config_manager.py    # 配置化
└── hotkey/hotkey_manager.py    # 清理未使用代码
```
