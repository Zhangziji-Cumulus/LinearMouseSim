import tkinter as tk
from tkinter import ttk
import math
from .status_bar import StatusBar
from .parameter_panel import ParameterPanel
from .tray_manager import TrayManager


class SteeringWheelCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._angle = 0.0
        self._max_angle = 90
        self._wheel_radius = 150
        self._center_x = 0
        self._center_y = 0
        self.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        self._draw_wheel()
    
    def _rotate_point(self, x, y, angle_rad):
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return x * cos_a - y * sin_a, x * sin_a + y * cos_a
    
    def _draw_wheel(self):
        self.delete('all')
        self._center_x = self.winfo_width() // 2
        self._center_y = self.winfo_height() // 2
        
        wheel_radius = self._wheel_radius
        center_x = self._center_x
        center_y = self._center_y
        angle_rad = math.radians(-self._angle)
        
        self.create_oval(
            center_x - wheel_radius, center_y - wheel_radius,
            center_x + wheel_radius, center_y + wheel_radius,
            fill='#1a1a2e', outline='#16213e', width=3
        )
        
        inner_radius = wheel_radius * 0.7
        self.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill='#0f0f1a', outline='#16213e', width=2
        )
        
        self._draw_ticks(wheel_radius, center_x, center_y, angle_rad)
        self._draw_spokes(wheel_radius, center_x, center_y, angle_rad)
        self._draw_center(wheel_radius, center_x, center_y)
        self._draw_angle_indicator(wheel_radius, center_x, center_y)
    
    def _draw_ticks(self, wheel_radius, center_x, center_y, angle_rad):
        for tick_angle in range(-180, 180, 15):
            rad = math.radians(tick_angle)
            if abs(tick_angle) % 45 == 0:
                inner = wheel_radius * 0.75
                outer = wheel_radius * 0.95
                width = 3
            else:
                inner = wheel_radius * 0.85
                outer = wheel_radius * 0.95
                width = 1
            
            x1 = inner * math.sin(rad)
            y1 = -inner * math.cos(rad)
            x2 = outer * math.sin(rad)
            y2 = -outer * math.cos(rad)
            
            rx1, ry1 = self._rotate_point(x1, y1, angle_rad)
            rx2, ry2 = self._rotate_point(x2, y2, angle_rad)
            
            color = '#e94560' if abs(tick_angle) >= self._max_angle else '#4a90d9'
            self.create_line(
                center_x + rx1, center_y + ry1,
                center_x + rx2, center_y + ry2,
                fill=color, width=width
            )
            
            if abs(tick_angle) % 45 == 0 and tick_angle != 0:
                text_radius = wheel_radius * 0.65
                tx = text_radius * math.sin(rad)
                ty = -text_radius * math.cos(rad)
                rtx, rty = self._rotate_point(tx, ty, angle_rad)
                
                text_angle = tick_angle + self._angle
                text_rad = math.radians(text_angle)
                
                label_x = center_x + rtx
                label_y = center_y + rty
                
                self.create_text(
                    label_x, label_y,
                    text=f'{tick_angle}°', fill='#ffffff', font=('Arial', 9)
                )
    
    def _draw_spokes(self, wheel_radius, center_x, center_y, angle_rad):
        spokes = 3
        for i in range(spokes):
            spoke_angle = i * 120
            rad = math.radians(spoke_angle)
            x = wheel_radius * 0.9 * math.sin(rad)
            y = -wheel_radius * 0.9 * math.cos(rad)
            
            rx, ry = self._rotate_point(x, y, angle_rad)
            
            self.create_line(
                center_x, center_y,
                center_x + rx, center_y + ry,
                fill='#4a90d9', width=8, capstyle='round'
            )
    
    def _draw_center(self, wheel_radius, center_x, center_y):
        center_radius = wheel_radius * 0.15
        self.create_oval(
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius,
            fill='#e94560', outline='#ffffff', width=2
        )
        self.create_text(center_x, center_y, text='L', fill='#ffffff', font=('Arial', 16, 'bold'))
    
    def _draw_angle_indicator(self, wheel_radius, center_x, center_y):
        line_length = wheel_radius * 1.2
        self.create_line(
            center_x - line_length, center_y,
            center_x + line_length, center_y,
            fill='#333333', width=1, dash=(4, 4)
        )
        
        angle_text = f'{self._angle:.1f}°'
        self.create_text(
            center_x, center_y + wheel_radius + 30,
            text=angle_text, fill='#ffffff', font=('Arial', 16, 'bold')
        )
        
        if self._angle > 1:
            self.create_text(
                center_x - wheel_radius - 50, center_y,
                text='← 左转', fill='#e94560', font=('Arial', 12)
            )
        elif self._angle < -1:
            self.create_text(
                center_x + wheel_radius + 50, center_y,
                text='右转 →', fill='#e94560', font=('Arial', 12)
            )
    
    def set_angle(self, angle):
        self._angle = max(-self._max_angle, min(self._max_angle, angle))
        self._draw_wheel()
    
    def get_angle(self):
        return self._angle
    
    def set_max_angle(self, max_angle):
        self._max_angle = max_angle


class MainWindow(tk.Tk):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.tray_manager = None
        
        self.title('LinearMouseSim - 方向盘模拟器')
        self.geometry('900x700')
        self.configure(bg='#0f0f1a')
        
        # 绑定最小化事件
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.bind('<Unmap>', self._on_minimize)
        
        self._init_components()
        self._init_tray()
    
    def _init_components(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(main_frame, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.param_panel = ParameterPanel(left_panel)
        self.param_panel.pack(fill=tk.BOTH, expand=True)
        
        if self.app:
            self.param_panel.set_on_change_callback(self.app.update_steering_params)
            self.param_panel.set_on_preset_callback(self.app.apply_preset)
        
        right_area = ttk.Frame(main_frame)
        right_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.wheel_canvas = SteeringWheelCanvas(
            right_area, bg='#0f0f1a', highlightthickness=0
        )
        if self.app:
            self.wheel_canvas.set_max_angle(self.app.config.get('steering.max_angle', 90))
        self.wheel_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def update_wheel_angle(self, angle):
        if self.app:
            self.wheel_canvas.set_max_angle(self.app.config.get('steering.max_angle', 90))
        self.wheel_canvas.set_angle(angle)
    
    def update_status_bar_angle(self, angle):
        self.status_bar.set_angle(angle)
    
    def update_status(self, state):
        self.status_bar.set_active(state == 'ON')
        # 更新托盘图标状态
        if self.tray_manager:
            self.tray_manager.update_status(state == 'ON')
    
    def _init_tray(self):
        """初始化系统托盘"""
        self.tray_manager = TrayManager(self, self.app)
    
    def _on_close(self):
        """关闭窗口时最小化到托盘"""
        self.hide_to_tray()
    
    def _on_minimize(self, event):
        """窗口最小化时隐藏到托盘"""
        # 检查是否是最小化操作（不是关闭或其他操作）
        if self.state() == 'iconic':
            self.hide_to_tray()
    
    def hide_to_tray(self):
        """隐藏窗口到托盘"""
        self.withdraw()
        if self.tray_manager:
            self.tray_manager.hide_window()
    
    def show_from_tray(self):
        """从托盘显示窗口"""
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def update_parameter_display(self):
        if self.app:
            params = self.app.config.get_steering_params()
            self.param_panel.set_parameters({
                'sensitivity': params.get('sensitivity', 1.0),
                'smoothing_factor': params.get('smoothing_factor', 0.3),
                'deadzone': params.get('deadzone', 3),
                'max_angle': params.get('max_angle', 90),
                'dpi': self.app.config.get('mouse.dpi', 800),
                'return_speed': params.get('return_speed', 0.0),
                'curve_type': params.get('curve_type', 'linear'),
                'reverse_direction': params.get('reverse_direction', False)
            })
            self.wheel_canvas.set_max_angle(params.get('max_angle', 90))
    
    def run(self):
        self.mainloop()


if __name__ == '__main__':
    app = MainWindow()
    app.run()
