import time
import ctypes

try:
    import pyvjoy
    PYVJOY_AVAILABLE = True
except ImportError:
    pyvjoy = None
    PYVJOY_AVAILABLE = False

class VJoyOutput:
    def __init__(self, device_id=1):
        self.device_id = device_id
        self.joy = None
        self.min_value = 0
        self.max_value = 32767
        self.center_value = (self.max_value - self.min_value) // 2
        self.deadzone = 0.02
        self.last_status = '未初始化'
    
    def _force_release_device(self):
        if not PYVJOY_AVAILABLE:
            return False
        try:
            import pyvjoy._sdk as sdk
            status = sdk.GetVJDStatus(self.device_id)
            if status != 0:
                sdk.RelinquishVJD(self.device_id)
                time.sleep(0.1)
            return True
        except Exception:
            return False
    
    def initialize(self):
        if not PYVJOY_AVAILABLE:
            self.last_status = 'pyvjoy库未安装'
            print("pyvjoy库未安装，vJoy功能不可用")
            return False

        self._force_release_device()

        for attempt in range(3):
            try:
                self.joy = pyvjoy.VJoyDevice(self.device_id)
                self.last_status = '初始化成功'
                print(f"vJoy初始化成功，设备ID={self.device_id}")
                return True
            except Exception as e:
                self.last_status = f'初始化失败: {e}'
                print(f"vJoy初始化尝试 {attempt+1}/3 失败: {e}")
                self._force_release_device()
                time.sleep(0.2)

        self.last_status = 'vJoy驱动未就绪或设备不可用'
        print("vJoy初始化失败，请确保vJoy已正确安装")
        return False
    
    def is_initialized(self):
        return self.joy is not None
    
    def set_axis_value(self, axis, value):
        if not self.joy:
            return
        value = max(self.min_value, min(self.max_value, int(value)))
        if axis == 'x':
            self.joy.set_axis(pyvjoy.HID_USAGE_X, value)
        elif axis == 'y':
            self.joy.set_axis(pyvjoy.HID_USAGE_Y, value)
    
    def set_steering_angle(self, angle, max_angle=90):
        if not self.joy:
            return

        if abs(angle) <= max_angle * self.deadzone:
            axis_value = self.center_value
        else:
            normalized = max(-1.0, min(1.0, angle / max_angle))
            axis_value = ((normalized + 1.0) / 2.0) * (self.max_value - self.min_value) + self.min_value

        self.set_axis_value('x', axis_value)
    
    def reset(self):
        if self.joy:
            self.set_axis_value('x', self.center_value)
            self.set_axis_value('y', self.center_value)
    
    def close(self):
        if self.joy:
            self.reset()
            self.joy = None
        self.last_status = '已关闭'

def test_vjoy_output():
    vjoy = VJoyOutput()
    if vjoy.initialize():
        print("vJoy初始化成功")
        for i in range(3):
            vjoy.set_steering_angle(0)
            time.sleep(0.5)
            vjoy.set_steering_angle(45)
            time.sleep(0.5)
            vjoy.set_steering_angle(-45)
            time.sleep(0.5)
        vjoy.reset()
        vjoy.close()
        print("vJoy测试完成")
    else:
        print("vJoy未安装或未配置")

if __name__ == "__main__":
    test_vjoy_output()
