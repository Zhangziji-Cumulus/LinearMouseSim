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
from ui import MainWindow, SteeringWheelCanvas, StatusBar, ParameterPanel
from config import ConfigManager, PresetManager
from hotkey import HotkeyManager
from utils import is_admin, check_vjoy_installed, show_message_box

class LinearMouseSim:
    def __init__(self):
        self.config = ConfigManager()
        self.vjoy = VJoyOutput()
        self.steering_algorithm = SteeringAlgorithm(**self.config.get_steering_params())
        self.state_machine = SteeringStateMachine(self.vjoy)
        
        three_zone_params = self.config.get_three_zone_params()
        for key, value in three_zone_params.items():
            self.steering_algorithm.set_parameter(key, value)
        
        self.hotkey_manager = HotkeyManager(self.config)
        self.hotkey_manager.register_callback('toggle', self.on_toggle)
        self.hotkey_manager.register_callback('increase_sensitivity', self.on_increase_sensitivity)
        self.hotkey_manager.register_callback('decrease_sensitivity', self.on_decrease_sensitivity)
        self.hotkey_manager.register_callback('reset_steering', self.on_reset_steering)
        
        self.main_window = None
        self.running = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_moving = False
        
        atexit.register(self.cleanup)
    
    def on_toggle(self):
        self.state_machine.toggle()
        if self.main_window:
            self.main_window.update_status(self.state_machine.get_state())
    
    def on_increase_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = min(5.0, current + 0.1)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
    
    def on_decrease_sensitivity(self):
        current = self.config.get('steering.sensitivity', 1.0)
        new_value = max(0.1, current - 0.1)
        self.config.set('steering.sensitivity', new_value)
        self.steering_algorithm.set_parameter('sensitivity', new_value)
        if self.main_window:
            self.main_window.update_parameter_display()
    
    def on_reset_steering(self):
        self.steering_algorithm.reset()
        self.vjoy.reset()
    
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
                mouse_x, mouse_y = get_mouse_position()
                
                self.is_moving = self.state_machine.is_mouse_moved()
                
                angle = self.steering_algorithm.update(
                    mouse_x=mouse_x,
                    base_x=self.state_machine.base_x,
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
        
        if not check_vjoy_installed():
            show_message_box('警告', '未检测到vJoy，请先安装vJoy驱动', 'error')
            return
        
        if not self.vjoy.initialize():
            show_message_box('错误', 'vJoy初始化失败，请确保vJoy已正确安装和配置', 'error')
            return
        
        self.main_window = MainWindow(self)
        self.main_window.update_status(self.state_machine.get_state())
        
        loop_thread = threading.Thread(target=self.main_loop, daemon=True)
        loop_thread.start()
        
        self.main_window.run()
    
    def cleanup(self):
        self.running = False
        self.state_machine.stop()
        self.vjoy.close()
        self.hotkey_manager.stop_listener()
        release_cursor_safety()

if __name__ == '__main__':
    try:
        app = LinearMouseSim()
        app.run()
    except KeyboardInterrupt:
        print("程序已中断")
    except Exception as e:
        print(f"程序出错: {e}")
        release_cursor_safety()
