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
        # 保存原始光标位置，用于关闭模拟时恢复
        self.original_cursor_x = 0
        self.original_cursor_y = 0
        # 线程锁，确保状态切换的线程安全
        self.state_lock = threading.Lock()
        
    def start(self):
        self.running = True
        self.lock_thread = threading.Thread(target=self._cursor_lock_loop, daemon=True)
        self.lock_thread.start()
    
    def stop(self):
        self.running = False
        self.turn_off()
    
    def _cursor_lock_loop(self):
        while self.running:
            # 使用锁确保状态读取的线程安全
            with self.state_lock:
                current_state = self.state
            
            if current_state == 'ON':
                mouse_x, _ = get_mouse_position()
                delta = mouse_x - self.center_x
                if abs(delta) > 0:
                    self.mouse_delta_x += delta
                    self.mouse_moved = True
                set_mouse_position(self.center_x, self.center_y)
            time.sleep(0.01)
    
    def turn_on(self):
        with self.state_lock:
            if self.state == 'ON':
                return
            
            # 保存开启前的原始光标位置
            self.original_cursor_x, self.original_cursor_y = get_mouse_position()
            
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
        with self.state_lock:
            if self.state == 'OFF':
                return
            
            # 先将状态改为 OFF，防止 _cursor_lock_loop 线程继续重置鼠标位置
            self.state = 'OFF'
        
        # 等待一小段时间确保锁线程已退出锁定逻辑（使用更长时间确保线程安全）
        time.sleep(0.03)
        
        try:
            self.cursor_manager.unlock()
        except Exception as e:
            print(f"光标解锁失败: {e}")
            release_cursor_safety()
        
        # 恢复光标到开启前的原始位置
        set_mouse_position(self.original_cursor_x, self.original_cursor_y)
        
        self.vjoy_output.reset()
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
        with self.state_lock:
            return self.state
    
    def get_current_angle(self):
        return self.current_angle
    
    def is_mouse_moved(self):
        return self.mouse_moved
    
    def reset_mouse_moved(self):
        self.mouse_moved = False
