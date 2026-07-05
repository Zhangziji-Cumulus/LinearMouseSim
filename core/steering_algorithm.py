"""
转向算法模块
实现鼠标增量位移到方向盘角度的映射，包含多种灵敏度曲线和滤波算法

核心功能：
1. 增量累积模式：accumulated_x += delta_x × 灵敏度系数
2. 线性插值平滑：current_angle = alpha * raw_angle + (1-alpha) * previous_angle
3. 死区过滤：如果delta_x < deadzone，不累积增量
4. 最大舵角限制：clamp(angle, -max_angle, +max_angle)
5. 回正衰减：当鼠标停止移动时，accumulated_x *= (1 - return_speed)
6. 四种灵敏度曲线：线性、指数、对数、S型曲线
7. 三段式灵敏度分区：死区、线性区、饱和区

输出：处理后的方向盘角度（浮点数）

增量累积模型原理：
- 当光标锁定到中心后，无法使用绝对位置计算角度
- 每帧获取鼠标增量位移 delta_x，累加到 accumulated_x
- accumulated_x 作为虚拟位移，映射到方向盘角度
- 松手后通过衰减系数实现自动回正
- 本质是速度积分 + 阻尼衰减模型
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
        self.max_angle = self._clamp(kwargs.get('max_angle', 90), 30, 720)
        
        # 回正惯性参数
        self.return_speed = self._clamp(kwargs.get('return_speed', 0.0), 0.0, 1.0)
        
        # 曲线类型参数
        self.curve_type = kwargs.get('curve_type', 'linear')
        self.exponential_power = self._clamp(kwargs.get('exponential_power', 1.5), 1.0, 3.0)
        
        # 方向反转参数
        self.reverse_direction = kwargs.get('reverse_direction', False)

        # 辅助回中参数
        # 当用户从大角度向中心回打时，额外加速归中，帮助找到中心位置
        self.assist_threshold = kwargs.get('assist_threshold', 80.0)    # 累积位移超过此值才启用
        self.assist_strength = kwargs.get('assist_strength', 2.5)       # 回中辅助倍率
        self.assist_near_center = kwargs.get('assist_near_center', 15.0)# 进入此范围后停止辅助
        
        # 三段式灵敏度分区参数
        self.deadzone_start = max(0, kwargs.get('deadzone_start', 0))
        self.deadzone_end = max(self.deadzone_start, kwargs.get('deadzone_end', 3))
        self.linear_start = max(self.deadzone_end, kwargs.get('linear_start', 3))
        self.linear_end = max(self.linear_start, kwargs.get('linear_end', 500))
        self.saturation_start = max(self.linear_end, kwargs.get('saturation_start', 500))
        self.saturation_end = max(self.saturation_start, kwargs.get('saturation_end', 1000))
        
        # 状态变量
        self.previous_angle = 0.0
        self.accumulated_x = 0.0
        
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
    
    def reset(self):
        """
        重置状态，角度归零
        """
        self.previous_angle = 0.0
        self.accumulated_x = 0.0
    
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
            self.max_angle = self._clamp(value, 30, 720)
        elif param_name == 'return_speed':
            self.return_speed = self._clamp(value, 0.0, 1.0)
        elif param_name == 'curve_type':
            valid_curves = ['linear', 'exponential', 'logarithmic', 's_curve']
            self.curve_type = value if value in valid_curves else 'linear'
        elif param_name == 'exponential_power':
            self.exponential_power = self._clamp(value, 1.0, 3.0)
        elif param_name == 'reverse_direction':
            self.reverse_direction = bool(value)
        elif param_name == 'assist_threshold':
            self.assist_threshold = max(0.0, value)
        elif param_name == 'assist_strength':
            self.assist_strength = max(1.0, value)
        elif param_name == 'assist_near_center':
            self.assist_near_center = max(0.0, value)
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
    
    def update(self, delta_x: int, is_moving: bool = True) -> float:
        """
        主更新方法，计算方向盘角度（增量累积模式）
        
        参数：
            delta_x: 鼠标增量位移（像素），由外部传入累积的帧间位移
            is_moving: 鼠标是否正在移动（用于回正衰减判断）
            
        返回：
            处理后的方向盘角度（浮点数，范围：-max_angle 到 +max_angle）
            
        处理流程：
        0. 方向反转：如果启用反向，反转 delta_x 符号
        1. 死区过滤：如果|delta_x| < deadzone，不累积增量
        2. 增量累积：accumulated_x += delta_x × 灵敏度系数
        3. 回正衰减：当鼠标停止移动时，accumulated_x *= (1 - return_speed)
        4. 三段式灵敏度分区计算原始角度（基于accumulated_x）
        5. 归一化并应用灵敏度曲线
        6. 线性插值平滑
        7. 最大舵角限制
        
        增量累积模型原理：
        - 光标锁定到中心后，每帧只能获取微小的增量位移
        - 将这些增量累积起来形成虚拟位移 accumulated_x
        - accumulated_x 映射到方向盘角度
        - 松手后通过衰减系数实现自动回正
        """
        if self.reverse_direction:
            delta_x = -delta_x
            
        abs_delta = abs(delta_x)
        
        # 步骤1：死区过滤
        # 如果|delta_x| < deadzone，不累积增量，保持当前状态
        if abs_delta < self.deadzone:
            # 步骤3：回正衰减（如果鼠标停止移动）
            if not is_moving and self.return_speed > 0:
                self.accumulated_x *= (1 - self.return_speed)
                if abs(self.accumulated_x) < 0.01:
                    self.accumulated_x = 0.0
            
            # 使用 accumulated_x 计算当前角度
            raw_angle = self._apply_three_zone(self.accumulated_x)
            
            if self.max_angle > 0:
                normalized_angle = raw_angle / self.max_angle
                normalized_angle = self._apply_curve(normalized_angle)
                raw_angle = normalized_angle * self.max_angle
            
            current_angle = self.smoothing_factor * raw_angle + \
                            (1 - self.smoothing_factor) * self.previous_angle
            current_angle = self._clamp(current_angle, -self.max_angle, self.max_angle)
            
            self.previous_angle = current_angle
            return current_angle
            
        # 步骤2：增量累积
        # 将增量位移乘以灵敏度系数后累加到 accumulated_x
        # 灵敏度系数已包含DPI换算，确保不同DPI鼠标手感一致
        self.accumulated_x += delta_x * self.sensitivity

        # 辅助回中：当从大角度向中心回打时，额外加速归中
        # 目的是帮助用户更容易找到中心位置，同时不影响从中心向外打的操控
        if abs(self.accumulated_x) > self.assist_threshold:
            # 判断是否正在回中：delta_x 与 accumulated_x 方向相反
            moving_toward_center = (delta_x < 0 and self.accumulated_x > 0) or (delta_x > 0 and self.accumulated_x < 0)
            if moving_toward_center:
                # 额外减少 accumulated_x，加速归中
                assist_extra = abs(delta_x) * self.sensitivity * (self.assist_strength - 1.0)
                if self.accumulated_x > 0:
                    self.accumulated_x -= assist_extra
                else:
                    self.accumulated_x += assist_extra

                # 如果辅助后已进入近中心区，直接归零
                if abs(self.accumulated_x) < self.assist_near_center:
                    self.accumulated_x = 0.0
        
        # 步骤3：回正衰减（如果鼠标停止移动）
        # 即使有增量输入，停止移动时也应用衰减防止角度过大
        if not is_moving and self.return_speed > 0:
            self.accumulated_x *= (1 - self.return_speed)
        
        # 步骤4：三段式灵敏度分区计算原始角度
        # 使用累积位移 accumulated_x 而非原始 delta_x
        raw_angle = self._apply_three_zone(self.accumulated_x)
        
        # 步骤5：归一化并应用灵敏度曲线
        if self.max_angle > 0:
            normalized_angle = raw_angle / self.max_angle
            normalized_angle = self._apply_curve(normalized_angle)
            raw_angle = normalized_angle * self.max_angle
        
        # 步骤6：线性插值平滑
        # current_angle = alpha * raw_angle + (1-alpha) * previous_angle
        current_angle = self.smoothing_factor * raw_angle + \
                        (1 - self.smoothing_factor) * self.previous_angle
        
        # 步骤7：最大舵角限制
        current_angle = self._clamp(current_angle, -self.max_angle, self.max_angle)
        
        # 更新状态
        self.previous_angle = current_angle
        
        return current_angle


# ========== 测试代码（增量累积模式）==========
if __name__ == '__main__':
    print("=== 转向算法测试（增量累积模式）===")
    
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
    
    # 测试场景1：增量位移累积测试
    print("\n--- 测试场景1：增量位移累积 ---")
    sa.reset()
    delta_steps = [10, 10, 10, 10, 10, -5, -5]
    for delta in delta_steps:
        angle = sa.update(delta)
        print(f"增量位移={delta}, accumulated_x={sa.accumulated_x:.2f}, 角度={angle:.2f}")
    
    # 测试场景2：死区过滤测试
    print("\n--- 测试场景2：死区过滤 ---")
    sa.reset()
    small_deltas = [1, 2, 3, 4, -1, -2, -3, -4]
    for delta in small_deltas:
        angle = sa.update(delta)
        print(f"增量位移={delta}, accumulated_x={sa.accumulated_x:.2f}, 角度={angle:.2f}")
    
    # 测试场景3：最大角度限制
    print("\n--- 测试场景3：最大角度限制 ---")
    sa.reset()
    for i in range(0, 50):
        angle = sa.update(50)
        if abs(angle) >= sa.max_angle * 0.99:
            break
    print(f"累积位移={sa.accumulated_x:.2f}, 最终角度={angle:.2f}, 最大角度={sa.max_angle}")
    
    # 测试场景4：回正衰减测试
    print("\n--- 测试场景4：回正衰减 ---")
    sa.reset()
    # 累积到一定角度
    for _ in range(10):
        sa.update(20, is_moving=True)
    angle = sa.update(0, is_moving=True)
    print(f"累积后的角度: {angle:.2f}, accumulated_x={sa.accumulated_x:.2f}")
    
    # 停止移动，测试回正
    for i in range(15):
        angle = sa.update(0, is_moving=False)
        print(f"回正第{i+1}帧: 角度={angle:.2f}, accumulated_x={sa.accumulated_x:.2f}")
    
    # 测试场景5：四种曲线类型对比
    print("\n--- 测试场景5：曲线类型对比 ---")
    curves = ['linear', 'exponential', 'logarithmic', 's_curve']
    
    for curve in curves:
        sa_test = SteeringAlgorithm(
            sensitivity=0.5,
            max_angle=90,
            curve_type=curve,
            smoothing_factor=1.0
        )
        # 累积相同增量
        for _ in range(20):
            sa_test.update(10)
        angle = sa_test.update(0)
        print(f"曲线类型={curve}, accumulated_x={sa_test.accumulated_x:.2f}, 角度={angle:.2f}")
    
    # 测试场景6：平滑效果测试
    print("\n--- 测试场景6：平滑效果测试 ---")
    sa_smooth = SteeringAlgorithm(
        sensitivity=0.5,
        max_angle=90,
        curve_type='linear',
        smoothing_factor=0.1
    )
    
    # 模拟抖动输入
    for i, delta in enumerate([10, -2, 2, -1, 1, 0]):
        angle = sa_smooth.update(delta)
        print(f"第{i+1}帧: 增量={delta}, accumulated_x={sa_smooth.accumulated_x:.2f}, 角度={angle:.2f}")
    
    # 测试场景7：指数曲线幂次测试
    print("\n--- 测试场景7：指数曲线幂次测试 ---")
    for power in [1.0, 1.5, 2.0, 2.5, 3.0]:
        sa_exp = SteeringAlgorithm(
            sensitivity=0.5,
            max_angle=90,
            curve_type='exponential',
            exponential_power=power,
            smoothing_factor=1.0
        )
        for _ in range(20):
            sa_exp.update(10)
        angle = sa_exp.update(0)
        print(f"指数幂次={power}, accumulated_x={sa_exp.accumulated_x:.2f}, 角度={angle:.2f}")
    
    # 测试场景8：DPI联动换算测试
    print("\n--- 测试场景8：DPI联动换算测试 ---")
    print("基础灵敏度=1.0，基准DPI=800")
    print("换算公式：effective_sensitivity = base_sensitivity / (dpi / 800)")
    print("-" * 60)
    
    test_dpis = [400, 800, 1200, 1600, 3200, 6400]
    for dpi in test_dpis:
        sa_dpi = SteeringAlgorithm(
            sensitivity=1.0,
            dpi=dpi,
            max_angle=90,
            smoothing_factor=1.0
        )
        expected_sensitivity = 1.0 / (dpi / 800.0)
        print(f"DPI={dpi}, 基础灵敏度={sa_dpi.base_sensitivity:.2f}, 有效灵敏度={sa_dpi.sensitivity:.4f}, 理论值={expected_sensitivity:.4f}")
    
    # 测试场景9：不同DPI下手感一致性测试
    print("\n--- 测试场景9：不同DPI下手感一致性测试 ---")
    print("模拟相同物理移动距离（假设800DPI下移动100像素，灵敏度=1.0）")
    print("-" * 60)
    
    # 基准情况：800DPI，每次移动10像素，共10次
    sa_800 = SteeringAlgorithm(sensitivity=1.0, dpi=800, max_angle=90, smoothing_factor=1.0)
    for _ in range(10):
        sa_800.update(10)
    angle_800 = sa_800.update(0)
    print(f"DPI=800, 每次移动10像素x10次, 角度={angle_800:.2f}, accumulated_x={sa_800.accumulated_x:.2f}")
    
    # 高DPI情况：1600DPI，每次移动20像素（相同物理距离）
    sa_1600 = SteeringAlgorithm(sensitivity=1.0, dpi=1600, max_angle=90, smoothing_factor=1.0)
    for _ in range(10):
        sa_1600.update(20)
    angle_1600 = sa_1600.update(0)
    print(f"DPI=1600, 每次移动20像素x10次（相同物理距离）, 角度={angle_1600:.2f}, accumulated_x={sa_1600.accumulated_x:.2f}")
    
    # 低DPI情况：400DPI，每次移动5像素（相同物理距离）
    sa_400 = SteeringAlgorithm(sensitivity=1.0, dpi=400, max_angle=90, smoothing_factor=1.0)
    for _ in range(10):
        sa_400.update(5)
    angle_400 = sa_400.update(0)
    print(f"DPI=400, 每次移动5像素x10次（相同物理距离）, 角度={angle_400:.2f}, accumulated_x={sa_400.accumulated_x:.2f}")
    
    # 测试场景10：动态修改参数测试
    print("\n--- 测试场景10：动态修改参数测试 ---")
    sa_dynamic = SteeringAlgorithm(sensitivity=1.0, dpi=800, max_angle=90, smoothing_factor=1.0)
    
    print(f"初始DPI={sa_dynamic.dpi}, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('dpi', 1600)
    print(f"修改DPI=1600后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('dpi', 400)
    print(f"修改DPI=400后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    sa_dynamic.set_parameter('sensitivity', 2.0)
    print(f"修改基础灵敏度=2.0后, 有效灵敏度={sa_dynamic.sensitivity:.4f}")
    
    print("\n=== 测试完成 ===")
