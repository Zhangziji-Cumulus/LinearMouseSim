import time
import threading
from .mouse_capture import get_mouse_position, set_mouse_position, get_screen_center, ClipCursorManager, release_cursor_safety

class SteeringStateMachine:
    def __init__(self, vjoy_output):
        self.vjoy_output = vjoy_output
        self.state = 'OFF'
        self.base_x = 0
        self.base_y = 0
        self.current_angle = 0.0
        self.cursor_manager = ClipCursorManager()
        self.center_x, self.center_y = get_screen_center()
        self.lock_thread = None
        self.running = False
        self.mouse_moved = False
        self.last_mouse_x = 0
        self.mouse_delta_x = 0
        
    def start(self):
        self.running = True
        self.lock_thread = threading.Thread(target=self._cursor_lock_loop, daemon=True)
        self.lock_thread.start()
    
    def stop(self):
        self.running = False
        self.turn_off()
    
    def _cursor_lock_loop(self):
        while self.running:
            if self.state == 'ON':
                mouse_x, _ = get_mouse_position()
                delta = mouse_x - self.center_x
                if abs(delta) > 0:
                    self.mouse_delta_x += delta
                    self.mouse_moved = True
                set_mouse_position(self.center_x, self.center_y)
            time.sleep(0.01)
    
    def turn_on(self):
        if self.state == 'ON':
            return
        
        self.base_x = self.center_x
        self.base_y = self.center_y
        self.last_mouse_x = self.center_x
        self.current_angle = 0.0
        self.mouse_moved = False
        self.mouse_delta_x = 0
        
        try:
            self.cursor_manager.lock_to_center()
            set_mouse_position(self.center_x, self.center_y)
        except Exception as e:
            print(f"光标锁定失败: {e}")
        
        self.state = 'ON'
        self.vjoy_output.set_steering_angle(0)
        print("模拟已开启")
    
    def turn_off(self):
        if self.state == 'OFF':
            return
        
        try:
            self.cursor_manager.unlock()
        except Exception as e:
            print(f"光标解锁失败: {e}")
            release_cursor_safety()
        
        self.vjoy_output.reset()
        self.state = 'OFF'
        self.current_angle = 0.0
        self.mouse_moved = False
        print("模拟已关闭")
    
    def toggle(self):
        if self.state == 'OFF':
            self.turn_on()
        else:
            self.turn_off()
    
    def update(self, current_x):
        if self.state != 'ON':
            return 0.0
        
        delta_x = current_x - self.base_x
        self.current_angle = delta_x
        
        self.vjoy_output.set_steering_angle(self.current_angle)
        
        return self.current_angle
    
    def get_state(self):
        return self.state
    
    def get_current_angle(self):
        return self.current_angle
    
    def is_mouse_moved(self):
        return self.mouse_moved
    
    def reset_mouse_moved(self):
        self.mouse_moved = False
