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
import time


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
            curve_type: 曲线类型，固定为 exponential
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
        self.deadzone = self._clamp(kwargs.get('deadzone', 3), 0, 50)
        self.linear_end = max(1, kwargs.get('linear_end', 500))  # 多少像素 = max_angle

        # DPI参数（用于灵敏度自动换算）
        # 基准DPI为800，不同DPI会自动调整有效灵敏度
        self.dpi = self._clamp(kwargs.get('dpi', 800), 100, 25600)

        # 角度限制参数
        self.max_angle = self._clamp(kwargs.get('max_angle', 90), 10, 1800)

        # 回正惯性参数
        self.return_speed = self._clamp(kwargs.get('return_speed', 0.0), 0.0, 1.0)

        # 曲线类型参数（默认线性曲线）
        self.curve_type = kwargs.get('curve_type', 'linear')
        self.exponential_power = self._clamp(kwargs.get('exponential_power', 1.5), 1.0, 3.0)

        # 方向反转参数
        self.reverse_direction = kwargs.get('reverse_direction', False)

        # 辅助回中参数
        # 当用户从大角度向中心回打时，按比例快速缩减累积位移，让回中更跟手
        self.assist_threshold = kwargs.get('assist_threshold', 300.0)    # 角度超过此值(度)才启用辅助
        self.assist_rate_threshold = kwargs.get('assist_rate_threshold', 30.0)  # 检测期内角度变化超过此值才触发
        self.assist_rate_window = kwargs.get('assist_rate_window', 0.10)       # 检测窗口（秒），默认100ms
        self.assist_return_rate = kwargs.get('assist_return_rate', 0.20)    # 每次回打缩减比例 (0~1)
        self.near_center_threshold = kwargs.get('near_center_threshold', 50.0)  # 进入中心检测的边界
        self.center_hold_ms = kwargs.get('center_hold_ms', 100)            # 中心检测保持时长（ms）
        self.center_release_threshold = kwargs.get('center_release_threshold', 200)  # 释放位移阈值

        # 临时半灵敏度模式
        self._temp_sensitivity_half = False
        
        # 状态变量
        self.previous_angle = 0.0
        self.accumulated_x = 0.0
        # 辅助回中状态机
        self._assist_active = False        # 是否在辅助归中
        self._assist_from_direction = 0    # 进入辅助时的 delta_x 方向
        self._hold_delta_sum = 0           # 中心检测态累计位移
        self._hold_start_time = 0          # 中心检测态开始时间

        # 预计算 accumulated_x 的有效上限
        # 超过此值后 _apply_mapping 已返回 max_angle，再多累积也没用
        # 需要确保用户回打时能立即响应，不用先"消化"多余累积
        self._max_useful_acc = self._compute_max_useful_acc()
        # 连续回打累计：从回打开始持续累加位移，直到用户换向或停止
        self._reversal_sum = 0.0          # 本次回打累计位移
        self._reversal_start_time = 0     # 回打开始时间
        self._reversal_direction = 0      # 回打方向（1=右，-1=左）
    
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
        effective = self.base_sensitivity / (self.dpi / 800.0)
        if self._temp_sensitivity_half:
            effective /= 2.0
        return effective
    
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
        self._assist_active = False
        self._assist_from_direction = 0
        self._hold_delta_sum = 0
        self._hold_start_time = 0
        self._reversal_sum = 0
        self._reversal_start_time = 0
        self._reversal_direction = 0

    def set_temp_half_sensitivity(self, enabled: bool):
        """设置临时半灵敏度模式（按住键时灵敏度减半）"""
        self._temp_sensitivity_half = enabled

    def _compute_max_useful_acc(self):
        """
        找出 _apply_mapping 首次达到 max_angle 时的 accumulated_x
        超过此值后角度不再增加，回打时需要先"消化"多余累积，造成手感卡顿
        """
        # 简化映射：angle = accumulated_x * (max_angle / linear_end)
        # 当 accumulated_x >= linear_end 时，angle = max_angle
        return self.linear_end
    
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
            self.deadzone = self._clamp(value, 0, 50)
        elif param_name == 'max_angle':
            self.max_angle = self._clamp(value, 10, 1800)
            self._max_useful_acc = self._compute_max_useful_acc()
        elif param_name == 'return_speed':
            self.return_speed = self._clamp(value, 0.0, 1.0)
        elif param_name == 'exponential_power':
            self.exponential_power = self._clamp(value, 1.0, 3.0)
        elif param_name == 'reverse_direction':
            self.reverse_direction = bool(value)
        elif param_name == 'assist_threshold':
            self.assist_threshold = max(0.0, value)
        elif param_name == 'assist_rate_threshold':
            self.assist_rate_threshold = max(0.0, value)
        elif param_name == 'assist_rate_window':
            self.assist_rate_window = max(0.01, value)
        elif param_name == 'near_center_threshold':
            self.near_center_threshold = max(0.0, value)
        elif param_name == 'assist_return_rate':
            self.assist_return_rate = max(0.0, min(1.0, value))
        elif param_name == 'center_hold_ms':
            self.center_hold_ms = max(0, value)
        elif param_name == 'center_release_threshold':
            self.center_release_threshold = max(0.0, value)
        elif param_name == 'linear_end':
            self.linear_end = max(1, value)
            self._max_useful_acc = self._compute_max_useful_acc()
    
    def get_cm360(self) -> float:
        """返回当前灵敏度对应的 cm/360° 值"""
        if self.dpi <= 0 or self.max_angle <= 0:
            return 0.0
        total_pixels = self._max_useful_acc * (360.0 / self.max_angle)
        return total_pixels * 2.54 / self.dpi

    def calculate_sensitivity_for_cm360(self, cm_per_360: float) -> float:
        """根据目标 cm/360° 计算所需的基础灵敏度"""
        if cm_per_360 <= 0 or self.dpi <= 0 or self.max_angle <= 0:
            return self.base_sensitivity
        target_total_pixels = cm_per_360 * self.dpi / 2.54
        target_max_useful = target_total_pixels * self.max_angle / 360.0
        if self._max_useful_acc > 0:
            ratio = target_max_useful / self._max_useful_acc
            return self._clamp(self.base_sensitivity * ratio, 0.1, 5.0)
        return self.base_sensitivity

    def _apply_curve(self, normalized_input: float) -> float:
        """
        应用灵敏度曲线
        
        参数：
            normalized_input: 归一化输入值 (-1.0 到 1.0)
            
        返回：
            应用曲线后的归一化输出值 (-1.0 到 1.0)
            
        支持曲线类型：
        - linear: 线性曲线 y = x，鼠标移多少方向盘转多少
        - exponential: 指数曲线 y = sign(x) * |x|^n，小幅慢大幅快
        """
        if normalized_input == 0:
            return 0.0
            
        if self.curve_type == 'linear':
            return normalized_input
        
        # 指数曲线
        abs_input = abs(normalized_input)
        sign = 1 if normalized_input >= 0 else -1
        return sign * math.pow(abs_input, self.exponential_power)
    
    def _apply_mapping(self, accumulated_x: float) -> float:
        """
        简化的角度映射：accumulated_x → 角度
        
        参数：
            accumulated_x: 累积的鼠标位移（像素）
            
        返回：
            方向盘角度（-max_angle 到 +max_angle）
            
        映射逻辑：
        1. 死区：|accumulated_x| < deadzone 时输出0
        2. 线性映射：angle = accumulated_x * (max_angle / linear_end)
        3. 钳位：限制在 [-max_angle, +max_angle]
        """
        abs_acc = abs(accumulated_x)
        sign = 1 if accumulated_x >= 0 else -1
        
        # 死区
        if abs_acc < self.deadzone:
            return 0.0
        
        # 线性映射：accumulated_x / linear_end * max_angle
        if self.linear_end > 0:
            angle = sign * min(abs_acc, self.linear_end) * (self.max_angle / self.linear_end)
        else:
            angle = sign * abs_acc
        
        return self._clamp(angle, -self.max_angle, self.max_angle)
    
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

        # 记录回打方向位移到滑动窗口（只计与 accumulated_x 相反的位移）
        # 不受灵敏度、曲线、三段式影响，只反映用户的回打意图
        # 连续回打累计：一旦检测到回打，持续累加位移直到用户换向或停止
        # 不受灵敏度、曲线、三段式、角度位置影响
        now = time.monotonic()
        if self._reversal_start_time > 0:
            # 已跟踪回打：只要 delta_x 方向不变就继续累加
            same_direction = (self._reversal_direction > 0 and delta_x > 0) or \
                             (self._reversal_direction < 0 and delta_x < 0)
            if same_direction:
                self._reversal_sum += abs_delta
            else:
                self._reversal_sum = 0
                self._reversal_start_time = 0
        else:
            # 未跟踪：检测新回打开始（基于角度方向）
            moving_toward_center = (delta_x < 0 and self.previous_angle > 0) or \
                                   (delta_x > 0 and self.previous_angle < 0)
            if moving_toward_center:
                self._reversal_start_time = now
                self._reversal_direction = 1 if delta_x > 0 else -1
                self._reversal_sum = abs_delta
        
        # 步骤1：死区过滤
        # 如果|delta_x| < deadzone，不累积增量，保持当前状态
        if abs_delta < self.deadzone:
            # 辅助回中期间，即使小位移也继续按比例缩减
            if self._assist_active:
                self.accumulated_x *= (1.0 - self.assist_return_rate)
                if abs(self.accumulated_x) < self.near_center_threshold:
                    self.accumulated_x = 0.0
                    self._assist_active = False
            elif not is_moving and self.return_speed > 0:
                self.accumulated_x *= (1 - self.return_speed)
                if abs(self.accumulated_x) < 0.01:
                    self.accumulated_x = 0.0

            # 限制 accumulated_x 不超过有效上限
            # 避免超出后角度不再增大，但回打时仍需消化多余累积位移导致手感卡顿
            self.accumulated_x = self._clamp(self.accumulated_x, -self._max_useful_acc, self._max_useful_acc)
            
            raw_angle = self._apply_mapping(self.accumulated_x)
            if self.max_angle > 0:
                normalized_angle = raw_angle / self.max_angle
                normalized_angle = self._apply_curve(normalized_angle)
                raw_angle = normalized_angle * self.max_angle
            current_angle = self.smoothing_factor * raw_angle + \
                            (1 - self.smoothing_factor) * self.previous_angle
            current_angle = self._clamp(current_angle, -self.max_angle, self.max_angle)
            self.previous_angle = current_angle
            return current_angle

        # ===== 辅助回中三状态机 =====
        # 状态 A（普通态）：正常累积，检测到大角度回打则进入 B
        # 状态 B（归中态）：比例缩减 accumulated_x，到达近中心则进入 C
        # 状态 C（检测态）：锁定 0，等待一段时间后退出辅助模式

        if self._assist_active and self._hold_start_time > 0:
            # ── 状态 C：中心检测态 ──
            # accumulated_x 已经接近 0，保持为 0
            self.accumulated_x = 0.0
            elapsed_ms = (time.monotonic() - self._hold_start_time) * 1000
            if elapsed_ms >= self.center_hold_ms:
                # 检测态结束，直接退出辅助模式
                # 不释放累积的位移，因为 accumulated_x 已经接近 0
                # 用户想要继续转向会在普通态中累积新位移
                self._assist_active = False
                self._hold_start_time = 0
                self._hold_delta_sum = 0.0
            
            # 状态C期间直接计算角度并返回，不执行后续逻辑
            raw_angle = self._apply_mapping(self.accumulated_x)
            if self.max_angle > 0:
                normalized_angle = raw_angle / self.max_angle
                normalized_angle = self._apply_curve(normalized_angle)
                raw_angle = normalized_angle * self.max_angle
            current_angle = self.smoothing_factor * raw_angle + \
                            (1 - self.smoothing_factor) * self.previous_angle
            current_angle = self._clamp(current_angle, -self.max_angle, self.max_angle)
            self.previous_angle = current_angle
            return current_angle
        elif self._assist_active:
            # ── 状态 B：辅助归中态 ──
            if abs(self.accumulated_x) > self.near_center_threshold:
                self.accumulated_x *= (1.0 - self.assist_return_rate)
            else:
                # 进入状态 C：中心检测态
                self.accumulated_x = 0.0
                self._hold_delta_sum = 0.0
                self._hold_start_time = time.monotonic()
        else:
            # ── 状态 A：普通态 ──
            rough_angle = self._apply_mapping(self.accumulated_x)

            still_reversing = (self._reversal_start_time > 0)
            fast_reversal = self._reversal_sum >= self.assist_rate_threshold

            # 在触发辅助前检查角度阈值
            if abs(rough_angle) >= self.assist_threshold and fast_reversal and still_reversing:
                self._assist_active = True
                self._assist_from_direction = 1 if delta_x > 0 else -1
                self.accumulated_x *= (1.0 - self.assist_return_rate)
                self._reversal_sum = 0
                self._reversal_start_time = 0
            else:
                self.accumulated_x += delta_x * self.sensitivity
                if not still_reversing and self._reversal_sum > 0:
                    self._reversal_sum = 0
                    self._reversal_start_time = 0
        
        # 步骤3：回正衰减（如果鼠标停止移动）
        if not is_moving and self.return_speed > 0:
            self.accumulated_x *= (1 - self.return_speed)
        
        # 限制 accumulated_x 不超过有效上限
        # 避免超出后角度不再增大，但回打时仍需消化多余累积位移导致手感卡顿
        self.accumulated_x = self._clamp(self.accumulated_x, -self._max_useful_acc, self._max_useful_acc)
        
        # 步骤4：三段式灵敏度分区计算原始角度
        # 使用累积位移 accumulated_x 而非原始 delta_x
        raw_angle = self._apply_mapping(self.accumulated_x)
        
        # 步骤5：归一化并应用灵敏度曲线
        if self.max_angle > 0:
            normalized_angle = raw_angle / self.max_angle
            normalized_angle = self._apply_curve(normalized_angle)
            raw_angle = normalized_angle * self.max_angle
        
        # 步骤6：线性插值平滑
        # current_angle = alpha * raw_angle + (1-alpha) * previous_angle
        current_angle = self.smoothing_factor * raw_angle + \
                        (1 - self.smoothing_factor) * self.previous_angle
        
        # 角度追上逻辑：当角度在增大方向时，允许追上 raw_angle
        # 解决低 smoothing_factor 导致角度永远达不到 max_angle 的问题
        if abs(raw_angle) > abs(self.previous_angle):
            # 角度在增大，确保不小于上一帧
            if abs(current_angle) < abs(self.previous_angle):
                current_angle = self.previous_angle
            # 也不能小于 raw_angle 与 previous_angle 的中间值
            min_abs = (abs(raw_angle) + abs(self.previous_angle)) / 2
            if abs(current_angle) < min_abs:
                current_angle = min_abs * (1 if raw_angle >= 0 else -1)
        
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
