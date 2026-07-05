"""
ViGEmBus 虚拟手柄输出模块（基于 vgamepad）

将方向盘角度映射为 Xbox 360 手柄左摇杆 X 轴输入，
使游戏原生识别为手柄操作，无需额外配置。
"""

import time

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except ImportError:
    vg = None
    VGAMEPAD_AVAILABLE = False


class VGamepadOutput:
    """
    虚拟手柄输出类

    将鼠标水平位移映射为 Xbox 360 手柄左摇杆 X 轴，
    模拟方向盘操作。后续可扩展右摇杆（油门/刹车）和扳机键。
    """

    def __init__(self):
        self.gamepad = None
        self.last_status = "未初始化"
        self.deadzone = 0.02  # 死区比例
        self.steering_axis = 'left_x'  # 方向盘使用的轴

    def initialize(self):
        """初始化虚拟手柄"""
        if not VGAMEPAD_AVAILABLE:
            self.last_status = "vgamepad库未安装"
            print("vgamepad库未安装，虚拟手柄功能不可用")
            return False

        try:
            self.gamepad = vg.VX360Gamepad()
            # 发送一次初始状态（全部回中）
            self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.gamepad.update()
            self.last_status = "初始化成功"
            print(f"虚拟Xbox 360手柄初始化成功")
            return True
        except Exception as e:
            self.last_status = f"初始化失败: {e}"
            print(f"虚拟手柄初始化失败: {e}")
            return False

    def is_initialized(self):
        """检查手柄是否已初始化"""
        return self.gamepad is not None

    def set_steering_angle(self, angle, max_angle=90):
        """
        将方向盘角度写入左摇杆 X 轴

        参数：
            angle: 当前方向盘角度（度），负值=左转，正值=右转
            max_angle: 最大舵角（度）

        映射逻辑：
            angle=0    → X轴中心 (0.0)
            angle>0    → X轴正半轴 (右)
            angle<0    → X轴负半轴 (左)

        Xbox 360 左摇杆 X 轴范围：-1.0 (左) ~ 0.0 (中心) ~ 1.0 (右)
        """
        if not self.gamepad:
            return

        # 死区处理：小角度直接回中
        if abs(angle) <= max_angle * self.deadzone:
            x_value = 0.0
        else:
            # 归一化到 [-1.0, 1.0]
            x_value = max(-1.0, min(1.0, angle / max_angle))

        self.gamepad.left_joystick_float(x_value_float=x_value, y_value_float=0.0)
        self.gamepad.update()

    def set_axes(self, left_x=0.0, left_y=0.0, right_x=0.0, right_y=0.0,
                 left_trigger=0.0, right_trigger=0.0):
        """
        设置所有手柄轴（扩展用）

        参数范围：
            摇杆: -1.0 ~ 1.0
            扳机: 0.0 ~ 1.0
        """
        if not self.gamepad:
            return

        self.gamepad.left_joystick_float(
            x_value_float=max(-1.0, min(1.0, left_x)),
            y_value_float=max(-1.0, min(1.0, left_y))
        )
        self.gamepad.right_joystick_float(
            x_value_float=max(-1.0, min(1.0, right_x)),
            y_value_float=max(-1.0, min(1.0, right_y))
        )
        self.gamepad.left_trigger_float(value_float=max(0.0, min(1.0, left_trigger)))
        self.gamepad.right_trigger_float(value_float=max(0.0, min(1.0, right_trigger)))
        self.gamepad.update()

    def press_button(self, button):
        """
        按下手柄按钮（扩展用）

        参数：
            button: vgamepad.XUSB_BUTTON 枚举值
        """
        if not self.gamepad:
            return
        self.gamepad.press_button(button=button)
        self.gamepad.update()

    def release_button(self, button):
        """释放手柄按钮"""
        if not self.gamepad:
            return
        self.gamepad.release_button(button=button)
        self.gamepad.update()

    def reset(self):
        """重置所有输入到中心/释放状态"""
        if self.gamepad:
            self.gamepad.reset()
            self.gamepad.update()

    def close(self):
        """释放手柄资源"""
        if self.gamepad:
            try:
                self.reset()
            except Exception:
                pass
            self.gamepad = None
        self.last_status = "已关闭"
