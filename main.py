import sys
import time
import threading
import atexit

from core import (
    get_mouse_position,
    VJoyOutput,
    SteeringStateMachine,
    SteeringAlgorithm,
    release_cursor_safety
)
from ui import MainWindow, SteeringWheelCanvas, StatusBar, ParameterPanel, OSDManager
from config import ConfigManager, PresetManager
from hotkey import HotkeyManager
from utils import is_admin, check_vjoy_installed, show_message_box

class LinearMouseSim:
    def __init__(self):
        self.config = ConfigManager()
        self.vjoy = VJoyOutput()
        steering_params = self.config.get_steering_params()
        steering_params['dpi'] = self.config.get('mouse.dpi', 800)
        self.steering_algorithm = SteeringAlgorithm(**steering_params)
        self.state_machine = SteeringStateMachine(self.vjoy)
        
        three_zone_params = self.config.get_three_zone_params()
        for key, value in three_zone_params.items():
            self.steering_algorithm.set_parameter(key, value)
        
        self.hotkey_manager = HotkeyManager(self.config)
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
        
        # 三档灵敏度预设值
        self.sensitivity_presets = [1.0, 2.0, 3.0]
        
        self.main_window = None
        self.running = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_moving = False
        
        atexit.register(self.cleanup)
    
    def on_toggle(self):
        self.state_machine.toggle()
        if self.state_machine.get_state() == 'ON':
            self.steering_algorithm.reset()
        if self.main_window:
            self.main_window.update_status(self.state_machine.get_state())
        self.osd_manager.show_toggle_state(self.state_machine.get_state())
    
    def on_increase_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = min(5.0, current + 0.1)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(new_value)
    
    def on_decrease_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = max(0.1, current - 0.1)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(new_value)
    
    def on_reset_steering(self):
        self.steering_algorithm.reset()
        self.vjoy.reset()
    
    def on_sensitivity_preset_1(self):
        """切换到灵敏度预设1"""
        preset_value = self.sensitivity_presets[0]
        self.config.set('steering.sensitivity', preset_value)
        self.steering_algorithm.set_parameter('sensitivity', preset_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(preset_value)
    
    def on_sensitivity_preset_2(self):
        """切换到灵敏度预设2"""
        preset_value = self.sensitivity_presets[1]
        self.config.set('steering.sensitivity', preset_value)
        self.steering_algorithm.set_parameter('sensitivity', preset_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(preset_value)
    
    def on_sensitivity_preset_3(self):
        """切换到灵敏度预设3"""
        preset_value = self.sensitivity_presets[2]
        self.config.set('steering.sensitivity', preset_value)
        self.steering_algorithm.set_parameter('sensitivity', preset_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(preset_value)
    
    def on_cycle_curve(self):
        """循环切换灵敏度曲线"""
        curve_types = ['linear', 'exponential', 'logarithmic', 's_curve']
        current_curve = self.config.get('steering.curve_type', 'linear')
        current_index = curve_types.index(current_curve) if current_curve in curve_types else 0
        next_index = (current_index + 1) % len(curve_types)
        new_curve = curve_types[next_index]
        
        self.config.set('steering.curve_type', new_curve)
        self.steering_algorithm.set_parameter('curve_type', new_curve)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_curve_type(new_curve)
    
    def on_wheel_increase_sensitivity(self):
        """滚轮增加灵敏度（+10%）"""
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = min(5.0, current * 1.1)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(new_value)
    
    def on_wheel_decrease_sensitivity(self):
        """滚轮降低灵敏度（-10%）"""
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = max(0.1, current * 0.9)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
        self.osd_manager.show_sensitivity(new_value)
    
    def apply_preset(self, preset_id):
        preset_manager = PresetManager()
        preset_manager.apply_preset(preset_id, self.config)
        
        three_zone_params = self.config.get_three_zone_params()
        for key, value in three_zone_params.items():
            self.steering_algorithm.set_parameter(key, value)
        
        steering_params = self.config.get_steering_params()
        for key, value in steering_params.items():
            self.steering_algorithm.set_parameter(key, value)
        
        if self.main_window:
            self.main_window.update_parameter_display()
    
    def update_steering_params(self, params):
        for key, value in params.items():
            if key == 'dpi':
                self.config.set(f'mouse.{key}', value)
            else:
                self.config.set(f'steering.{key}', value)
            self.steering_algorithm.set_parameter(key, value)
        
        three_zone = {
            'deadzone_start': 0,
            'deadzone_end': params.get('deadzone', 3),
            'linear_start': params.get('deadzone', 3),
            'linear_end': 500,
            'saturation_start': 500,
            'saturation_end': 1000
        }
        for key, value in three_zone.items():
            self.config.set(f'three_zone.{key}', value)
            self.steering_algorithm.set_parameter(key, value)
    
    def main_loop(self):
        self.running = True
        self.state_machine.start()
        self.hotkey_manager.load_hotkeys()
        
        while self.running:
            if self.state_machine.get_state() == 'ON':
                self.is_moving = self.state_machine.is_mouse_moved()
                self.state_machine.reset_mouse_moved()
                
                delta_x = self.state_machine.get_mouse_delta_x()
                
                angle = self.steering_algorithm.update(
                    delta_x=delta_x,
                    is_moving=self.is_moving
                )
                
                self.state_machine.current_angle = angle
                self.vjoy.set_steering_angle(angle, self.config.get('steering.max_angle', 90))
                
                if self.main_window:
                    self.main_window.update_wheel_angle(angle)
                    self.main_window.update_status_bar_angle(angle)
            
            time.sleep(0.005)
    
    def run(self):
        if not is_admin():
            show_message_box('提示', '建议以管理员身份运行以获得更好的兼容性', 'warning')
        
        vjoy_available = check_vjoy_installed() and self.vjoy.initialize()
        
        if not vjoy_available:
            print("vJoy不可用，进入模拟模式（仅测试UI和算法）")
        
        self.main_window = MainWindow(self)
        self.main_window.update_status(self.state_machine.get_state())
        self.main_window.param_panel.set_hotkey_manager(self.hotkey_manager)
        
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
        
        # 清理托盘资源
        if self.main_window and self.main_window.tray_manager:
            self.main_window.tray_manager.cleanup()

if __name__ == '__main__':
    try:
        app = LinearMouseSim()
        app.run()
    except KeyboardInterrupt:
        print("程序已中断")
    except Exception as e:
        print(f"程序出错: {e}")
        release_cursor_safety()
