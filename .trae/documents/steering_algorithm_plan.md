# 转向算法实现计划

## 1. 需求分析

创建 `core/steering_algorithm.py` 文件，实现以下转向算法功能：

### 核心功能
1. **绝对位置模式**：方向盘角度 = (当前鼠标X - 基准点X) × 灵敏度系数
2. **线性插值平滑**：current_angle = alpha * raw_angle + (1-alpha) * previous_angle
3. **死区过滤**：如果delta_x < deadzone，保持当前角度不变
4. **最大舵角限制**：clamp(angle, -max_angle, +max_angle)
5. **可选回正惯性**：当鼠标停止移动时，angle *= (1 - return_speed)
6. **四种灵敏度曲线**：线性、指数(n=1.5)、对数、S型曲线
7. **三段式灵敏度分区**：死区、线性区、饱和区

### 参数列表
| 参数名 | 类型 | 范围 | 默认值 | 说明 |
|--------|------|------|--------|------|
| sensitivity | float | 0.1-5.0 | 1.0 | 灵敏度系数 |
| smoothing_factor | float | 0.0-1.0 | 0.3 | 平滑系数(alpha) |
| deadzone | int | 0-20 | 3 | 死区大小(像素) |
| max_angle | int | 30-180 | 90 | 最大舵角(度) |
| return_speed | float | 0.0-1.0 | 0.0 | 回正速度(0表示不回正) |
| curve_type | str | linear/exponential/logarithmic/s_curve | linear | 曲线类型 |
| exponential_power | float | 1.0-3.0 | 1.5 | 指数曲线幂次 |
| deadzone_start | int | >=0 | 0 | 死区起始(像素) |
| deadzone_end | int | >=0 | 3 | 死区结束(像素) |
| linear_start | int | >=0 | 3 | 线性区起始(像素) |
| linear_end | int | >=0 | 500 | 线性区结束(像素) |
| saturation_start | int | >=0 | 500 | 饱和区起始(像素) |
| saturation_end | int | >=0 | 1000 | 饱和区结束(像素) |

### 输出
处理后的方向盘角度（浮点数，范围：-max_angle 到 +max_angle）

---

## 2. 实现方案

### 2.1 类设计

创建 `SteeringAlgorithm` 类，包含以下核心方法：

```python
class SteeringAlgorithm:
    def __init__(self, **kwargs):
        # 初始化所有参数
        
    def update(self, mouse_x: int, base_x: int = None, is_moving: bool = True) -> float:
        # 主更新方法，返回处理后的方向盘角度
        
    def _apply_curve(self, value: float) -> float:
        # 应用灵敏度曲线
        
    def _apply_three_zone(self, delta_x: int) -> float:
        # 三段式灵敏度分区处理
        
    def reset(self):
        # 重置状态（角度归零）
        
    def set_parameter(self, param_name: str, value):
        # 动态设置参数
```

### 2.2 算法实现细节

#### 2.2.1 绝对位置模式
```python
delta_x = mouse_x - base_x
raw_angle = delta_x * self.sensitivity
```

#### 2.2.2 线性插值平滑
```python
current_angle = self.smoothing_factor * raw_angle + (1 - self.smoothing_factor) * self.previous_angle
```

#### 2.2.3 死区过滤
```python
if abs(delta_x) < self.deadzone:
    return self.previous_angle
```

#### 2.2.4 最大舵角限制
```python
current_angle = max(-self.max_angle, min(self.max_angle, current_angle))
```

#### 2.2.5 回正惯性
```python
if not is_moving and self.return_speed > 0:
    current_angle *= (1 - self.return_speed)
```

#### 2.2.6 灵敏度曲线

**线性曲线**：
```python
return value
```

**指数曲线**：
```python
return math.copysign(math.pow(abs(value), self.exponential_power), value)
```

**对数曲线**：
```python
return math.copysign(math.log(abs(value) + 1), value) * self.sensitivity
```

**S型曲线**：
```python
# 使用 tanh 函数实现 S 型曲线
return math.tanh(value / self.saturation_end) * self.max_angle
```

#### 2.2.7 三段式灵敏度分区
```python
# 死区：[deadzone_start, deadzone_end] -> 输出0
# 线性区：[linear_start, linear_end] -> 线性映射
# 饱和区：[saturation_start, saturation_end] -> 渐进饱和
```

### 2.3 状态管理

- `previous_angle`: 上一帧的角度值（用于平滑插值）
- `base_x`: 基准鼠标X坐标（用于绝对位置模式）

---

## 3. 文件结构

```
core/
├── __init__.py        # 导出 SteeringAlgorithm 类
├── mouse_capture.py   # 现有文件
├── state_machine.py   # 现有文件
├── vjoy_output.py     # 现有文件
└── steering_algorithm.py  # 新建文件
```

---

## 4. 测试验证

创建简单的单元测试逻辑，验证：
- 死区过滤是否正常工作
- 最大舵角限制是否生效
- 平滑插值是否消除抖动
- 四种曲线类型是否正确实现
- 回正惯性是否按预期工作

---

## 5. 后续扩展

- 添加更多曲线类型（如自定义曲线）
- 添加阻尼效果
- 添加角度限制的缓动效果
- 支持相对位移模式（增量模式）
