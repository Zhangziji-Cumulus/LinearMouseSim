import time
import threading
from enum import Enum
from .mouse_capture import get_mouse_position, set_mouse_position, get_screen_center, ClipCursorManager, release_cursor_safety


class SimulationState(Enum):
    ON = 'ON'
    OFF = 'OFF'


class SteeringStateMachine:
    def __init__(self, vjoy_output):
        self.vjoy_output = vjoy_output
        self.state = SimulationState.OFF
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
        # 关闭标志，用于立即停止光标锁定
        self._turning_off = False
        
    def start(self):
        self.running = True
        self.lock_thread = threading.Thread(target=self._cursor_lock_loop, daemon=True)
        self.lock_thread.start()
    
    def stop(self):
        self.running = False
        with self.state_lock:
            self._turning_off = True
        self.cursor_manager.unlock()
        release_cursor_safety()
        self.turn_off()
    
    def _cursor_lock_loop(self):
        while self.running:
            with self.state_lock:
                current_state = self.state
            
            if current_state == SimulationState.ON and not self._turning_off:
                mouse_x, _ = get_mouse_position()
                delta = mouse_x - self.last_mouse_x
                if abs(delta) > 0:
                    self.mouse_delta_x += delta
                    self.mouse_moved = True
                set_mouse_position(self.center_x, self.center_y)
                self.last_mouse_x = self.center_x
            time.sleep(0.01)
    
    def turn_on(self):
        with self.state_lock:
            if self.state == SimulationState.ON:
                return

            self.original_cursor_x, self.original_cursor_y = get_mouse_position()

            self.base_x = self.center_x
            self.base_y = self.center_y
            self.last_mouse_x = self.center_x
            self.current_angle = 0.0
            self.mouse_moved = False
            self.mouse_delta_x = 0
            self._turning_off = False

            set_mouse_position(self.center_x, self.center_y)

            self.state = SimulationState.ON
            self.vjoy_output.set_steering_angle(0)
            print("模拟已开启")
    
    def turn_off(self):
        with self.state_lock:
            if self.state == SimulationState.OFF:
                return

            self.state = SimulationState.OFF
            self._turning_off = True
        
        self.cursor_manager.unlock()
        release_cursor_safety()
        
        time.sleep(0.02)
        
        set_mouse_position(self.original_cursor_x, self.original_cursor_y)
        
        self.vjoy_output.reset()
        self.current_angle = 0.0
        self.mouse_moved = False
        self._turning_off = False
        print("模拟已关闭")
    
    def toggle(self):
        if self.state == SimulationState.OFF:
            self.turn_on()
        else:
            self.turn_off()
    
    def get_mouse_delta_x(self):
        """
        获取累积的鼠标增量位移并清零
        
        返回：
            累积的鼠标X轴增量位移
        """
        delta = self.mouse_delta_x
        self.mouse_delta_x = 0
        return delta
    
    def get_state(self):
        with self.state_lock:
            return self.state
    
    def get_current_angle(self):
        return self.current_angle
    
    def is_mouse_moved(self):
        return self.mouse_moved
    
    def reset_mouse_moved(self):
        self.mouse_moved = False
