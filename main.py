import sys
import os
import time
import threading
import atexit
import signal
import ctypes
import ctypes.wintypes
import webbrowser

from core import (
    get_mouse_position,
    VGamepadOutput,
    SteeringStateMachine,
    SteeringAlgorithm,
    SimulationState,
    release_cursor_safety
)
from ui import MainWindow, StatusBar, ParameterPanel, OSDManager
from config import ConfigManager, PresetManager
from hotkey import HotkeyManager

MUTEX_NAME = "Global\\LinearMouseSim_Mutex"
_h_mutex = None

def check_single_instance():
    global _h_mutex
    kernel32 = ctypes.windll.kernel32
    h_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == 183:
        kernel32.CloseHandle(h_mutex)
        return False

    _h_mutex = h_mutex
    return True

def is_admin():
    """检查当前是否以管理员权限运行"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def request_admin():
    """请求以管理员权限重新启动程序，确保全局热键正常工作"""
    if not is_admin():
        try:
            script = sys.executable
            if getattr(sys, 'frozen', False):
                script = sys.executable
            else:
                script = os.path.abspath(sys.argv[0])
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}"', None, 1
            )
            if result > 32:
                # UAC 已接受，新进程已启动，退出当前进程
                sys.exit(0)
            # result <= 32: 用户拒绝提权或出错，继续运行（热键可能受限）
        except Exception:
            pass

def close_mutex():
    global _h_mutex
    if _h_mutex is not None:
        ctypes.windll.kernel32.CloseHandle(_h_mutex)
        _h_mutex = None

class LinearMouseSim:
    def __init__(self):
        self.config = ConfigManager()
        self.preset_manager = PresetManager(self.config)
        self.vjoy = VGamepadOutput()
        steering_params = self.config.get_steering_params()
        steering_params['dpi'] = self.config.get('mouse.dpi', 800)
        self.steering_algorithm = SteeringAlgorithm(**steering_params)
        self.state_machine = SteeringStateMachine(self.vjoy)
        
        three_zone_params = self.config.get_three_zone_params()
        for key, value in three_zone_params.items():
            self.steering_algorithm.set_parameter(key, value)
        
        self.hotkey_manager = HotkeyManager(self.config)
        self.hotkey_manager.set_cooldown(self.config.get('app.hotkey_cooldown_ms', 200))
        self.osd_manager = OSDManager(self.config)
        self.hotkey_manager.register_callback('toggle', self.on_toggle)
        self.hotkey_manager.register_callback('increase_sensitivity', self.on_increase_sensitivity)
        self.hotkey_manager.register_callback('decrease_sensitivity', self.on_decrease_sensitivity)
        self.hotkey_manager.register_callback('reset_steering', self.on_reset_steering)
        self.hotkey_manager.register_callback('sensitivity_preset_1', self.on_sensitivity_preset_1)
        self.hotkey_manager.register_callback('sensitivity_preset_2', self.on_sensitivity_preset_2)
        self.hotkey_manager.register_callback('sensitivity_preset_3', self.on_sensitivity_preset_3)
        self.hotkey_manager.register_callback('cycle_curve', self.on_cycle_curve)
        self.hotkey_manager.register_callback('wheel_increase_sensitivity', self.on_wheel_increase_sensitivity)
        self.hotkey_manager.register_callback('wheel_decrease_sensitivity', self.on_wheel_decrease_sensitivity)
        self.hotkey_manager.register_callback('temp_sensitivity_half_down', self.on_temp_sensitivity_half_down)
        self.hotkey_manager.register_callback('temp_sensitivity_half_up', self.on_temp_sensitivity_half_up)
        
        # 三档灵敏度预设值（从配置读取）
        self.sensitivity_presets = self.config.get('app.sensitivity_presets', [1.0, 2.0, 3.0])
        
        self.main_window = None
        self.running = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_moving = False

        # 鼠标按键常量
        self._VK_LBUTTON = 0x01
        self._VK_RBUTTON = 0x02
        self._user32 = ctypes.windll.user32
        
        atexit.register(self.cleanup)
        
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        def signal_handler(signum, frame):
            print(f"收到信号 {signum}，正在退出...")
            self.cleanup()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (OSError, ValueError):
            pass
    
    def on_toggle(self):
        self.state_machine.toggle()
        state = self.state_machine.get_state()
        if state == SimulationState.ON:
            self.steering_algorithm.reset()
        if self.main_window:
            self.main_window.after(0, lambda s=state: self.main_window.update_status(s))
            self.main_window.after(0, lambda s=state: self.osd_manager.show_toggle_state(s))
    
    def _apply_sensitivity(self, value):
        """统一灵敏度设置方法"""
        value = max(0.1, min(5.0, value))
        self.config.set('steering.sensitivity', value)
        self.steering_algorithm.set_parameter('sensitivity', value)
        if self.main_window:
            self.main_window.after(0, self.main_window.update_parameter_display)
            self.main_window.after(0, lambda v=value: self.osd_manager.show_sensitivity(v))

    def on_increase_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        step = self.config.get('app.sensitivity_step', 0.1)
        self._apply_sensitivity(current + step)

    def on_decrease_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        step = self.config.get('app.sensitivity_step', 0.1)
        self._apply_sensitivity(current - step)
    
    def on_reset_steering(self):
        self.steering_algorithm.reset()
        self.vjoy.reset()
    
    def on_sensitivity_preset_1(self):
        """切换到灵敏度预设1"""
        self._apply_sensitivity(self.sensitivity_presets[0])

    def on_sensitivity_preset_2(self):
        """切换到灵敏度预设2"""
        self._apply_sensitivity(self.sensitivity_presets[1])

    def on_sensitivity_preset_3(self):
        """切换到灵敏度预设3"""
        self._apply_sensitivity(self.sensitivity_presets[2])
    
    def on_cycle_curve(self):
        """曲线类型已固定为指数，此热键保留但不再切换曲线"""
    
    def on_wheel_increase_sensitivity(self):
        """滚轮增加灵敏度"""
        current = self.config.get('steering.sensitivity', 1.0)
        factor = self.config.get('app.wheel_sensitivity_factor', 0.1)
        self._apply_sensitivity(current * (1 + factor))

    def on_wheel_decrease_sensitivity(self):
        """滚轮降低灵敏度"""
        current = self.config.get('steering.sensitivity', 1.0)
        factor = self.config.get('app.wheel_sensitivity_factor', 0.1)
        self._apply_sensitivity(current * (1 - factor))
    
    def on_temp_sensitivity_half_down(self):
        """临时半灵敏度键按下"""
        self.steering_algorithm.set_temp_half_sensitivity(True)
    
    def on_temp_sensitivity_half_up(self):
        """临时半灵敏度键释放"""
        self.steering_algorithm.set_temp_half_sensitivity(False)
    
    def apply_preset(self, preset_id):
        self.preset_manager.apply_preset(preset_id, self.config)

        three_zone_params = self.config.get_three_zone_params()
        for key, value in three_zone_params.items():
            self.steering_algorithm.set_parameter(key, value)

        steering_params = self.config.get_steering_params()
        for key, value in steering_params.items():
            self.steering_algorithm.set_parameter(key, value)

        mouse_dpi = self.config.get('mouse.dpi', 800)
        self.steering_algorithm.set_parameter('dpi', mouse_dpi)

        if self.main_window:
            self.main_window.update_parameter_display()

    def save_preset(self, name):
        self.preset_manager.save_user_preset(name, self.config)
        self._refresh_presets()

    def rename_preset(self, preset_id, new_name):
        self.preset_manager.rename_user_preset(preset_id, new_name)
        self._refresh_presets()

    def delete_preset(self, preset_id):
        self.preset_manager.delete_user_preset(preset_id)
        self._refresh_presets()

    def _refresh_presets(self):
        presets = self.preset_manager.get_all_presets()
        if self.main_window and self.main_window.param_panel:
            self.main_window.param_panel.update_presets(presets)
    
    def _get_mouse_buttons(self):
        """读取鼠标按键状态，返回 (左键按下, 右键按下)"""
        left_down = bool(self._user32.GetAsyncKeyState(self._VK_LBUTTON) & 0x8000)
        right_down = bool(self._user32.GetAsyncKeyState(self._VK_RBUTTON) & 0x8000)
        return left_down, right_down

    def update_steering_params(self, params):
        # 保存 steering 参数
        for key, value in params.items():
            if key == 'dpi':
                self.config.set(f'mouse.{key}', value)
            elif key in ('deadzone', 'max_angle', 'smoothing_factor', 'return_speed',
                         'sensitivity', 'reverse_direction', 'exponential_power',
                         'assist_rate_threshold', 'assist_rate_window',
                         'assist_threshold', 'assist_return_rate', 'near_center_threshold',
                         'center_hold_ms', 'center_release_threshold',
                         'center_enabled', 'center_mode', 'center_speed_mode', 'center_speed', 'center_delay_ms'):
                self.config.set(f'steering.{key}', value)
            elif key == 'linear_end':
                self.config.set('three_zone.linear_end', value)
            self.steering_algorithm.set_parameter(key, value)
    
    def main_loop(self):
        self.running = True
        self.state_machine.start()
        self.hotkey_manager.load_hotkeys()
        
        while self.running:
            if self.state_machine.get_state() == SimulationState.ON:
                self.is_moving = self.state_machine.is_mouse_moved()
                self.state_machine.reset_mouse_moved()
                
                delta_x = self.state_machine.get_mouse_delta_x()
                
                angle = self.steering_algorithm.update(
                    delta_x=delta_x,
                    is_moving=self.is_moving
                )
                
                self.state_machine.current_angle = angle

                # 读取鼠标按键：左键=刹车，右键=油门
                left_down, right_down = self._get_mouse_buttons()
                brake = 1.0 if left_down else 0.0
                gas = 1.0 if right_down else 0.0

                # 同时发送方向盘角度 + 油门/刹车
                max_ang = self.steering_algorithm.max_angle
                normalized_angle = max(-1.0, min(1.0, angle / max_ang)) if max_ang > 0 else 0.0
                self.vjoy.set_axes(left_x=normalized_angle, right_trigger=gas, left_trigger=brake)

                if self.main_window:
                    self.main_window.after(0, lambda a=angle: self.main_window.update_wheel_angle(a))
                    self.main_window.after(0, lambda a=angle: self.main_window.update_status_bar_angle(a))
            
            interval = self.config.get('app.main_loop_interval', 0.005)
            time.sleep(interval)
    
    def run(self):
        # 检测 ViGEmBus 驱动
        from core.vgamepad_output import is_vigembus_installed, VIGEMBUS_DOWNLOAD_URL
        import tkinter as tk
        from tkinter import messagebox

        if not is_vigembus_installed():
            # ViGEmBus 驱动未安装，提示用户
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            result = messagebox.askyesno(
                "ViGEmBus 驱动未安装",
                "检测到 ViGEmBus 驱动未安装，虚拟手柄功能将不可用。\n\n"
                "是否打开浏览器下载驱动？\n"
                "（下载后需要安装驱动并重启程序）\n\n"
                "点击[否]将继续使用模拟模式（无虚拟手柄输出）"
            )

            if result:
                webbrowser.open(VIGEMBUS_DOWNLOAD_URL)
            root.destroy()

        self.vjoy.initialize()
        controller_available = self.vjoy.is_initialized()

        if not controller_available:
            status_text = self.vjoy.last_status
            print(f"虚拟手柄不可用，进入模拟模式; 当前状态: {status_text}")
        else:
            status_text = self.vjoy.last_status
            print(f"虚拟手柄可用，当前状态: {status_text}")
        
        presets = self.preset_manager.get_all_presets()
        self.main_window = MainWindow(self, presets=presets)
        self.osd_manager.set_root(self.main_window)
        self.main_window.set_vjoy_status(controller_available, status_text)
        self.main_window.update_status(self.state_machine.get_state())
        self.main_window.param_panel.set_hotkey_manager(self.hotkey_manager)
        self.main_window.param_panel.set_on_change_callback(self.update_steering_params)
        self.main_window.param_panel.set_on_preset_callback(self.apply_preset)
        self.main_window.param_panel.set_on_save_preset_callback(self.save_preset)
        self.main_window.param_panel.set_on_rename_preset_callback(self.rename_preset)
        self.main_window.param_panel.set_on_delete_preset_callback(self.delete_preset)
        self.main_window.update_parameter_display()
        
        # 强制显示窗口
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.attributes('-topmost', True)
        self.main_window.after(100, lambda: self.main_window.attributes('-topmost', False))
        
        loop_thread = threading.Thread(target=self.main_loop, daemon=True)
        loop_thread.start()
        
        self.main_window.run()
    
    def cleanup(self):
        self.running = False
        self.state_machine.stop()
        self.vjoy.close()
        self.hotkey_manager.stop_listener()
        self.osd_manager.close()
        release_cursor_safety()
        close_mutex()
        
        # 清理托盘资源
        if self.main_window and self.main_window.tray_manager:
            self.main_window.tray_manager.cleanup()

if __name__ == '__main__':
    request_admin()

    if not check_single_instance():
        print("程序已在运行中，同一时间只能启动一个实例。")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        from tkinter import messagebox
        messagebox.showwarning("LinearMouseSim", "程序已在运行中，同一时间只能启动一个实例。")
        root.destroy()
        sys.exit(0)
    
    try:
        app = LinearMouseSim()
        app.run()
    except KeyboardInterrupt:
        print("程序已中断")
    except Exception as e:
        print(f"程序出错: {e}")
        release_cursor_safety()
        close_mutex()
