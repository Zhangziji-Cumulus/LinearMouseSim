"""
转向算法模块
实现鼠标位置到方向盘角度的映射，包含多种灵敏度曲线和滤波算法

核心功能：
1. 绝对位置模式：方向盘角度 = (当前鼠标X - 基准点X) × 灵敏度系数
2. 线性插值平滑：current_angle = alpha * raw_angle + (1-alpha) * previous_angle
3. 死区过滤：如果delta_x < deadzone，保持当前角度不变
4. 最大舵角限制：clamp(angle, -max_angle, +max_angle)
5. 可选回正惯性：当鼠标停止移动时，angle *= (1 - return_speed)
6. 四种灵敏度曲线：线性、指数、对数、S型曲线
7. 三段式灵敏度分区：死区、线性区、饱和区

输出：处理后的方向盘角度（浮点数）
"""

import math


class SteeringAlgorithm:
    """
    转向算法核心类
    
    将鼠标水平位移转换为方向盘角度，支持多种灵敏度曲线和滤波算法
    
    DPI联动换算机制：
    - 不同DPI的鼠标在相同物理移动距离下产生的像素位移不同
    - 高DPI鼠标移动相同距离会产生更多像素，导致转向更灵敏
    - 换算公式：effective_sensitivity = base_sensitivity / (dpi / 800)
    - 以800DPI为基准，高DPI自动降低有效灵敏度，低DPI自动提高有效灵敏度
    - 确保不同DPI鼠标在相同物理移动距离下产生相同的转向角度
    """
    
    def __init__(self, **kwargs):
        """
        初始化转向算法参数
        
        参数：
            sensitivity: 灵敏度系数 (0.1-5.0)，默认1.0
            smoothing_factor: 平滑系数 (0.0-1.0)，默认0.3
            deadzone: 死区大小 (0-20像素)，默认3
            max_angle: 最大舵角 (30-180度)，默认90
            return_speed: 回正速度 (0.0-1.0)，默认0.0（不回正）
            curve_type: 曲线类型 (linear/exponential/logarithmic/s_curve)，默认linear
            exponential_power: 指数曲线幂次 (1.0-3.0)，默认1.5
            deadzone_start: 死区起始 (像素)，默认0
            deadzone_end: 死区结束 (像素)，默认3
            linear_start: 线性区起始 (像素)，默认3
            linear_end: 线性区结束 (像素)，默认500
            saturation_start: 饱和区起始 (像素)，默认500
            saturation_end: 饱和区结束 (像素)，默认1000
            dpi: 鼠标DPI (100-25600)，默认800（基准DPI）
        """
        # 灵敏度参数
        self.base_sensitivity = self._clamp(kwargs.get('sensitivity', 1.0), 0.1, 5.0)
        self.smoothing_factor = self._clamp(kwargs.get('smoothing_factor', 0.3), 0.0, 1.0)
        self.deadzone = self._clamp(kwargs.get('deadzone', 3), 0, 20)
        
        # DPI参数（用于灵敏度自动换算）
        # 基准DPI为800，不同DPI会自动调整有效灵敏度
        self.dpi = self._clamp(kwargs.get('dpi', 800), 100, 25600)
        
        # 角度限制参数
        self.max_angle = self._clamp(kwargs.get('max_angle', 90), 30, 180)
        
        # 回正惯性参数
        self.return_speed = self._clamp(kwargs.get('return_speed', 0.0), 0.0, 1.0)
        
        # 曲线类型参数
        self.curve_type = kwargs.get('curve_type', 'linear')
        self.exponential_power = self._clamp(kwargs.get('exponential_power', 1.5), 1.0, 3.0)
        
        # 三段式灵敏度分区参数
        self.deadzone_start = max(0, kwargs.get('deadzone_start', 0))
        self.deadzone_end = max(self.deadzone_start, kwargs.get('deadzone_end', 3))
        self.linear_start = max(self.deadzone_end, kwargs.get('linear_start', 3))
        self.linear_end = max(self.linear_start, kwargs.get('linear_end', 500))
        self.saturation_start = max(self.linear_end, kwargs.get('saturation_start', 500))
        self.saturation_end = max(self.saturation_start, kwargs.get('saturation_end', 1000))
        
        # 状态变量
        self.previous_angle = 0.0
        self.base_x = None
        
        # 验证曲线类型
        valid_curves = ['linear', 'exponential', 'logarithmic', 's_curve']
        if self.curve_type not in valid_curves:
            self.curve_type = 'linear'
    
    @property
    def sensitivity(self):
        """
        计算经过DPI换算后的有效灵敏度
        
        换算公式：effective_sensitivity = base_sensitivity / (dpi / 800)
        
        数学原理：
        - 假设基准DPI=800，灵敏度=1.0
        - 当DPI=1600（2倍基准），鼠标移动相同物理距离会产生2倍像素
        - 需要将灵敏度除以2，才能保持相同的转向角度
        - 反之，DPI=400（0.5倍基准），需要将灵敏度乘以2
        
        返回：
            经过DPI换算后的有效灵敏度系数
        """
        return self.base_sensitivity / (self.dpi / 800.0)
    
    def _clamp(self, value, min_val, max_val):
        """
        将值限制在指定范围内
        
        参数：
            value: 输入值
            min_val: 最小值
            max_val: 最大值
            
        返回：
            限制后的值
        """
        return max(min_val, min(max_val, value))
    
    def set_base_x(self, base_x: int):
        """
        设置基准鼠标X坐标
        
        参数：
            base_x: 基准X坐标
        """
        self.base_x = base_x
    
    def reset(self):
        """
        重置状态，角度归零
        """
        self.previous_angle = 0.0
    
    def set_parameter(self, param_name: str, value):
        """
        动态设置参数
        
        参数：
            param_name: 参数名称
            value: 参数值
        """
        if param_name == 'sensitivity':
            self.base_sensitivity = self._clamp(value, 0.1, 5.0)
        elif param_name == 'dpi':
            self.dpi = self._clamp(value, 100, 25600)
        elif param_name == 'smoothing_factor':
            self.smoothing_factor = self._clamp(value, 0.0, 1.0)
        elif param_name == 'deadzone':
            self.deadzone = self._clamp(value, 0, 20)
        elif param_name == 'max_angle':
            self.max_angle = self._clamp(value, 30, 180)
        elif param_name == 'return_speed':
            self.return_speed = self._clamp(value, 0.0, 1.0)
        elif param_name == 'curve_type':
            valid_curves = ['linear', 'exponential', 'logarithmic', 's_curve']
            self.curve_type = value if value in valid_curves else 'linear'
        elif param_name == 'exponential_power':
            self.exponential_power = self._clamp(value, 1.0, 3.0)
        elif param_name == 'deadzone_start':
            self.deadzone_start = max(0, value)
        elif param_name == 'deadzone_end':
            self.deadzone_end = max(self.deadzone_start, value)
        elif param_name == 'linear_start':
            self.linear_start = max(self.deadzone_end, value)
        elif param_name == 'linear_end':
            self.linear_end = max(self.linear_start, value)
        elif param_name == 'saturation_start':
            self.saturation_start = max(self.linear_end, value)
        elif param_name == 'saturation_end':
            self.saturation_end = max(self.saturation_start, value)
    
    def _apply_curve(self, normalized_input: float) -> float:
        """
        应用灵敏度曲线，对归一化输入进行非线性变换
        
        参数：
            normalized_input: 归一化输入值 (-1.0 到 1.0)
            
        返回：
            应用曲线后的归一化输出值 (-1.0 到 1.0)
            
        四种曲线类型：
        1. linear: 线性曲线，输出等于输入
        2. exponential: 指数曲线，y = sign(x) * |x|^n
        3. logarithmic: 对数曲线，y = sign(x) * (1 - exp(-k|x|)) / (1 - exp(-k))
        4. s_curve: S型曲线，使用tanh函数实现平滑过渡
        """
        if normalized_input == 0:
            return 0.0
            
        abs_input = abs(normalized_input)
        sign = 1 if normalized_input >= 0 else -1
        
        if self.curve_type == 'linear':
            # 线性曲线：y = x
            return normalized_input
            
        elif self.curve_type == 'exponential':
            # 指数曲线：y = sign(x) * |x|^n
            # 特点：小位移时变化平缓，大位移时变化急剧
            return sign * math.pow(abs_input, self.exponential_power)
            
        elif self.curve_type == 'logarithmic':
            # 对数曲线：y = sign(x) * (1 - exp(-k|x|)) / (1 - exp(-k))
            # 特点：小位移时变化灵敏，大位移时趋于饱和
            k = 5.0  # 曲线陡峭度系数
            return sign * (1 - math.exp(-k * abs_input)) / (1 - math.exp(-k))
            
        elif self.curve_type == 's_curve':
            # S型曲线：使用tanh函数实现平滑过渡
            # 特点：两端平缓，中间线性，适合精确控制
            # tanh(3x) 在x=0时接近0，x=1时接近1，中间近似线性
            return math.tanh(3 * normalized_input)
            
        else:
            return normalized_input
    
    def _apply_three_zone(self, delta_x: int) -> float:
        """
        三段式灵敏度分区处理，基于delta_x计算原始角度
        
        参数：
            delta_x: 鼠标位移量（像素）
            
        返回：
            经过分区处理后的角度值
            
        分区定义：
        1. 死区 [deadzone_start, deadzone_end]: 输出0，过滤微小抖动
        2. 线性区 [linear_start, linear_end]: 线性映射，精确控制
        3. 饱和区 [saturation_start, saturation_end]: 渐进饱和，防止角度突变
        """
        abs_delta = abs(delta_x)
        sign = 1 if delta_x >= 0 else -1
        
        # 计算线性区斜率：确保线性区结束时达到最大角度的80%
        linear_range = self.linear_end - self.deadzone_end
        if linear_range <= 0:
            linear_slope = self.max_angle / 100.0
        else:
            linear_slope = (self.max_angle * 0.8) / linear_range
        
        if abs_delta <= self.deadzone_end:
            # 死区：输出0
            return 0.0
            
        elif abs_delta <= self.linear_end:
            # 线性区：线性映射
            effective_delta = abs_delta - self.deadzone_end
            return sign * effective_delta * linear_slope
            
        elif abs_delta <= self.saturation_end:
            # 饱和区：渐进饱和
            # 使用cos函数实现平滑饱和过渡
            # 输入范围：[linear_end, saturation_end] -> [0, pi/2]
            t = (abs_delta - self.linear_end) / (self.saturation_end - self.linear_end)
            # cos(t * pi/2) 在t=0时为1，t=1时为0
            saturation_factor = math.cos(t * math.pi / 2)
            
            # 基础值为线性区最大角度
            base_angle = (self.linear_end - self.deadzone_end) * linear_slope
            
            # 剩余增量按饱和因子衰减
            remaining_delta = abs_delta - self.linear_end
            additional_angle = remaining_delta * linear_slope * saturation_factor
            
            return sign * min(self.max_angle, base_angle + additional_angle)
            
        else:
            # 超出饱和区：直接输出最大角度
            return sign * self.max_angle
    
    def update(self, mouse_x: int, base_x: int = None, is_moving: bool = True) -> float:
        """
        主更新方法，计算方向盘角度
        
        参数：
            mouse_x: 当前鼠标X坐标
            base_x: 基准鼠标X坐标（可选，若为None则使用内部存储的base_x）
            is_moving: 鼠标是否正在移动（用于回正惯性判断）
            
        返回：
            处理后的方向盘角度（浮点数，范围：-max_angle 到 +max_angle）
            
        处理流程：
        1. 计算鼠标位移（绝对位置模式）
        2. 死区过滤（如果delta_x < deadzone，保持当前角度不变）
        3. 三段式灵敏度分区计算原始角度
        4. 归一化原始角度并应用灵敏度曲线
        5. 线性插值平滑
        6. 最大舵角限制
        7. 回正惯性（如果鼠标停止移动）
        """
        # 使用传入的base_x或内部存储的base_x
        current_base_x = base_x if base_x is not None else self.base_x
        
        if current_base_x is None:
            # 未设置基准点，返回0
            return 0.0
            
        # 步骤1：计算鼠标位移（绝对位置模式）
        # 方向盘角度 = (当前鼠标X - 基准点X) × 灵敏度系数
        delta_x = mouse_x - current_base_x
        abs_delta = abs(delta_x)
        
        # 步骤2：死区过滤
        # 如果delta_x < deadzone，保持当前角度不变
        if abs_delta < self.deadzone:
            # 应用回正惯性（如果鼠标停止移动）
            if not is_moving and self.return_speed > 0:
                self.previous_angle *= (1 - self.return_speed)
                # 防止角度过小导致的抖动
                if abs(self.previous_angle) < 0.01:
                    self.previous_angle = 0.0
            return self.previous_angle
            
        # 步骤3：三段式灵敏度分区计算原始角度
        raw_angle = self._apply_three_zone(delta_x)
        
        # 步骤4：归一化原始角度并应用灵敏度曲线
        # 将原始角度归一化到 [-1, 1] 范围
        if self.max_angle > 0:
            normalized_angle = raw_angle / self.max_angle
            # 应用灵敏度曲线
            normalized_angle = self._apply_curve(normalized_angle)
            # 映射回角度范围
            raw_angle = normalized_angle * self.max_angle
        
        # 步骤4.5：应用经过DPI换算的有效灵敏度系数
        # 有效灵敏度 = 基础灵敏度 / (DPI / 800)
        # 确保不同DPI鼠标在相同物理移动距离下产生相同的转向角度
        raw_angle *= self.sensitivity
            
        # 步骤5：线性插值平滑
        # current_angle = alpha * raw_angle + (1-alpha) * previous_angle
        # alpha越小，平滑效果越强，但延迟越大
        current_angle = self.smoothing_factor * raw_angle + \
                        (1 - self.smoothing_factor) * self.previous_angle
        
        # 步骤6：最大舵角限制
        # clamp(angle, -max_angle, +max_angle)
        current_angle = self._clamp(current_angle, -self.max_angle, self.max_angle)
        
        # 步骤7：回正惯性（如果鼠标停止移动）
        # 当鼠标停止移动时，angle *= (1 - return_speed)
        if not is_moving and self.return_speed > 0:
            current_angle *= (1 - self.return_speed)
            # 防止角度过小导致的抖动
            if abs(current_angle) < 0.01:
                current_angle = 0.0
        
        # 更新状态
        self.previous_angle = current_angle
        
        return current_angle


# ========== 测试代码 ==========
if __name__ == '__main__':
    print("=== 转向算法测试 ===")
    
    # 创建转向算法实例
    sa = SteeringAlgorithm(
        sensitivity=0.5,
        smoothing_factor=0.3,
        deadzone=3,
        max_angle=90,
        return_speed=0.05,
        curve_type='linear',
        exponential_power=1.5
    )
    
    # 设置基准点
    sa.set_base_x(500)
    
    # 测试场景1：鼠标在基准点附近移动（死区测试）
    print("\n--- 测试场景1：死区过滤 ---")
    test_points = [500, 501, 502, 503, 504, 499, 498, 497, 496]
    for x in test_points:
        angle = sa.update(x)
        print(f"鼠标X={x}, delta_x={x-500}, 角度={angle:.2f}")
    
    # 测试场景2：鼠标快速移动（最大角度测试）
    print("\n--- 测试场景2：最大角度限制 ---")
    sa.reset()
    for i in range(0, 1500, 100):
        angle = sa.update(500 + i)
        print(f"鼠标X={500+i}, delta_x={i}, 角度={angle:.2f}")
    
    # 测试场景3：回正惯性测试
    print("\n--- 测试场景3：回正惯性 ---")
    sa.reset()
    # 快速移动到600
    for _ in range(10):
        sa.update(600, is_moving=True)
    angle = sa.update(600, is_moving=True)
    print(f"移动到600后的角度: {angle:.2f}")
    
    # 停止移动，测试回正
    for i in range(10):
        angle = sa.update(600, is_moving=False)
        print(f"回正第{i+1}帧: 角度={angle:.2f}")
    
    # 测试场景4：四种曲线类型对比
    print("\n--- 测试场景4：曲线类型对比 ---")
    curves = ['linear', 'exponential', 'logarithmic', 's_curve']
    test_delta = 200
    
    for curve in curves:
        sa_test = SteeringAlgorithm(
            sensitivity=0.5,
            max_angle=90,
            curve_type=curve,
            smoothing_factor=1.0  # 禁用平滑以便看清曲线效果
        )
        sa_test.set_base_x(500)
        angle = sa_test.update(500 + test_delta)
        print(f"曲线类型={curve}, delta_x={test_delta}, 角度={angle:.2f}")
    
    # 测试场景5：平滑效果测试
    print("\n--- 测试场景5：平滑效果测试 ---")
    sa_smooth = SteeringAlgorithm(
        sensitivity=0.5,
        max_angle=90,
        curve_type='linear',
        smoothing_factor=0.1  # 强平滑
    )
    sa_smooth.set_base_x(500)
    
    # 模拟抖动输入
    for i, x in enumerate([550, 548, 552, 549, 551, 550]):
        angle = sa_smooth.update(x)
        print(f"第{i+1}帧: 鼠标X={x}, delta_x={x-500}, 角度={angle:.2f}")
    
    # 测试场景6：指数曲线幂次测试
    print("\n--- 测试场景6：指数曲线幂次测试 ---")
    for power in [1.0, 1.5, 2.0, 2.5, 3.0]:
        sa_exp = SteeringAlgorithm(
            sensitivity=0.5,
            max_angle=90,
            curve_type='exponential',
            exponential_power=power,
            smoothing_factor=1.0
        )
        sa_exp.set_base_x(500)
        angle = sa_exp.update(500 + 200)
        print(f"指数幂次={power}, delta_x=200, 角度={angle:.2f}")
    
    # 测试场景7：DPI联动换算测试
    print("\n--- 测试场景7：DPI联动换算测试 ---")
    print("基础灵敏度=1.0，基准DPI=800")
    print("换算公式：effective_sensitivity = base_sensitivity / (dpi / 800)")
    print("-" * 60)
    
    test_dpis = [400, 800, 1200, 1600, 3200, 6400]
    for dpi in test_dpis:
        sa_dpi = SteeringAlgorithm(
            sensitivity=1.0,
            dpi=dpi,
            max_angle=90,
            smoothing_factor=1.0  # 禁用平滑以便看清灵敏度效果
        )
        sa_dpi.set_base_x(500)
        # 计算理论有效灵敏度
        expected_sensitivity = 1.0 / (dpi / 800.0)
        print(f"DPI={dpi}, 基础灵敏度={sa_dpi.base_sensitivity:.2f}, 有效灵敏度={sa_dpi.sensitivity:.4f}, 理论值={expected_sensitivity:.4f}")
    
    # 测试场景8：不同DPI下手感一致性测试
    print("\n--- 测试场景8：不同DPI下手感一致性测试 ---")
    print("模拟相同物理移动距离（假设800DPI下移动100像素）")
    print("-" * 60)
    
    # 基准情况：800DPI，移动100像素
    sa_800 = SteeringAlgorithm(sensitivity=1.0, dpi=800, max_angle=90, smoothing_factor=1.0)
    sa_800.set_base_x(500)
    angle_800 = sa_800.update(600)  # delta_x = 100
    print(f"DPI=800, 移动100像素, 角度={angle_800:.2f}")
    
    # 高DPI情况：1600DPI，移动200像素（相同物理距离）
    sa_1600 = SteeringAlgorithm(sensitivity=1.0, dpi=1600, max_angle=90, smoothing_factor=1.0)
    sa_1600.set_base_x(500)
    angle_1600 = sa_1600.update(700)  # delta_x = 200（相同物理距离）
    print(f"DPI=1600, 移动200像素（相同物理距离）, 角度={angle_1600:.2f}")
    
    # 低DPI情况：400DPI，移动50像素（相同物理距离）
    sa_400 = SteeringAlgorithm(sensitivity=1.0, dpi=400, max_angle=90, smoothing_factor=1.0)
    sa_400.set_base_x(500)
    angle_400 = sa_400.update(550)  # delta_x = 50（相同物理距离）
    print(f"DPI=400, 移动50像素（相同物理距离）, 角度={angle_400:.2f}")
    
    # 测试场景9：动态修改DPI参数测试
    print("\n--- 测试场景9：动态修改DPI参数测试 ---")
    sa_dynamic = SteeringAlgorithm(sensitivity=1.0, dpi=800, max_angle=90, smoothing_factor=1.0)
    sa_dynamic.set_base_x(500)
    
    print(f"初始DPI={sa_dynamic.dpi}, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('dpi', 1600)
    print(f"修改DPI=1600后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('dpi', 400)
    print(f"修改DPI=400后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('sensitivity', 2.0)
    print(f"修改基础灵敏度=2.0后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    print("\n=== 测试完成 ===")
