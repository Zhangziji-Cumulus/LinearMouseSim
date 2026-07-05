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
        
        self._spokes = []
        self._ticks = []
        self._tick_labels = []
        
        self.bind('<Configure>', self._on_resize)
        self._initialized = False
    
    def _on_resize(self, event):
        self._initialized = False
        self._update_wheel()
    
    def _rotate_point(self, x, y, angle_rad):
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return x * cos_a - y * sin_a, x * sin_a + y * cos_a
    
    def _create_wheel_elements(self):
        self.delete('all')
        self._spokes = []
        self._ticks = []
        self._tick_labels = []
        
        self._center_x = self.winfo_width() // 2
        self._center_y = self.winfo_height() // 2
        
        wheel_radius = self._wheel_radius
        center_x = self._center_x
        center_y = self._center_y
        
        self.create_oval(
            center_x - wheel_radius, center_y - wheel_radius,
            center_x + wheel_radius, center_y + wheel_radius,
            fill='#1a1a2e', outline='#16213e', width=3, tag='outer_ring'
        )
        
        inner_radius = wheel_radius * 0.7
        self.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill='#0f0f1a', outline='#16213e', width=2, tag='inner_ring'
        )
        
        center_radius = wheel_radius * 0.15
        self.create_oval(
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius,
            fill='#e94560', outline='#ffffff', width=2, tag='center_cap'
        )
        self.create_text(center_x, center_y, text='L', fill='#ffffff', font=('Segoe UI', 16, 'bold'), tag='center_text')
        
        line_length = wheel_radius * 1.2
        self.create_line(
            center_x - line_length, center_y,
            center_x + line_length, center_y,
            fill='#333344', width=1, dash=(4, 4), tag='indicator_line'
        )
        
        self.create_text(
            center_x, center_y + wheel_radius + 35,
            text='0.0°', fill='#ffffff', font=('Segoe UI', 16, 'bold'), tag='angle_text'
        )
        
        self.create_text(
            center_x, center_y + wheel_radius + 60,
            text='', fill='#8888aa', font=('Segoe UI', 10), tag='rotation_text'
        )
        
        self.create_text(
            center_x - wheel_radius - 50, center_y,
            text='← 左转', fill='#e94560', font=('Segoe UI', 12), tag='left_label'
        )
        self.create_text(
            center_x + wheel_radius + 50, center_y,
            text='右转 →', fill='#e94560', font=('Segoe UI', 12), tag='right_label'
        )
        
        spokes = 3
        for i in range(spokes):
            spoke_angle = i * 120
            rad = math.radians(spoke_angle)
            x = wheel_radius * 0.9 * math.sin(rad)
            y = -wheel_radius * 0.9 * math.cos(rad)
            
            spoke_id = self.create_line(
                center_x, center_y,
                center_x + x, center_y + y,
                fill='#4a90d9', width=8, capstyle='round', tag='spoke'
            )
            self._spokes.append({'id': spoke_id, 'base_x': x, 'base_y': y})
        
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
            
            tick_id = self.create_line(
                center_x + x1, center_y + y1,
                center_x + x2, center_y + y2,
                fill='#4a90d9', width=width, tag='tick'
            )
            self._ticks.append({'id': tick_id, 'base_x1': x1, 'base_y1': y1, 
                               'base_x2': x2, 'base_y2': y2, 'width': width, 
                               'tick_angle': tick_angle})
            
            if abs(tick_angle) % 45 == 0 and tick_angle != 0:
                text_radius = wheel_radius * 0.65
                tx = text_radius * math.sin(rad)
                ty = -text_radius * math.cos(rad)
                
                label_id = self.create_text(
                    center_x + tx, center_y + ty,
                    text=f'{tick_angle}°', fill='#ffffff', font=('Arial', 9), tag='tick_label'
                )
                self._tick_labels.append({'id': label_id, 'base_tx': tx, 'base_ty': ty, 'tick_angle': tick_angle})
    
    def _update_wheel(self):
        if not self._initialized:
            self._create_wheel_elements()
            self._initialized = True
            return
        
        self._center_x = self.winfo_width() // 2
        self._center_y = self.winfo_height() // 2
        
        wheel_radius = self._wheel_radius
        center_x = self._center_x
        center_y = self._center_y
        angle_rad = math.radians(-self._angle)
        
        self.coords('outer_ring',
            center_x - wheel_radius, center_y - wheel_radius,
            center_x + wheel_radius, center_y + wheel_radius
        )
        
        inner_radius = wheel_radius * 0.7
        self.coords('inner_ring',
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius
        )
        
        center_radius = wheel_radius * 0.15
        self.coords('center_cap',
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius
        )
        self.coords('center_text', center_x, center_y)
        
        line_length = wheel_radius * 1.2
        self.coords('indicator_line',
            center_x - line_length, center_y,
            center_x + line_length, center_y
        )
        
        angle_text = f'{self._angle:.1f}°'
        self.itemconfig('angle_text', text=angle_text)
        self.coords('angle_text', center_x, center_y + wheel_radius + 35)
        
        if self._max_angle > 180:
            rotation_count = int(abs(self._angle) // 360)
            if rotation_count > 0:
                direction = '顺时针' if self._angle > 0 else '逆时针'
                rotation_text = f'已旋转 {rotation_count} 圈 ({direction})'
            else:
                rotation_text = ''
            self.itemconfig('rotation_text', text=rotation_text)
            self.coords('rotation_text', center_x, center_y + wheel_radius + 60)
        else:
            self.itemconfig('rotation_text', text='')
        
        self.coords('left_label', center_x - wheel_radius - 50, center_y)
        self.coords('right_label', center_x + wheel_radius + 50, center_y)
        
        if self._angle > 1:
            self.itemconfig('left_label', state='normal')
            self.itemconfig('right_label', state='hidden')
        elif self._angle < -1:
            self.itemconfig('left_label', state='hidden')
            self.itemconfig('right_label', state='normal')
        else:
            self.itemconfig('left_label', state='hidden')
            self.itemconfig('right_label', state='hidden')
        
        for spoke in self._spokes:
            rx, ry = self._rotate_point(spoke['base_x'], spoke['base_y'], angle_rad)
            self.coords(spoke['id'], center_x, center_y, center_x + rx, center_y + ry)
        
        for tick in self._ticks:
            rx1, ry1 = self._rotate_point(tick['base_x1'], tick['base_y1'], angle_rad)
            rx2, ry2 = self._rotate_point(tick['base_x2'], tick['base_y2'], angle_rad)
            
            self.coords(tick['id'],
                center_x + rx1, center_y + ry1,
                center_x + rx2, center_y + ry2
            )
            
            color = '#e94560' if abs(tick['tick_angle']) >= self._max_angle else '#4a90d9'
            self.itemconfig(tick['id'], fill=color)
        
        for label in self._tick_labels:
            rtx, rty = self._rotate_point(label['base_tx'], label['base_ty'], angle_rad)
            self.coords(label['id'], center_x + rtx, center_y + rty)
    
    def set_angle(self, angle):
        self._angle = max(-self._max_angle, min(self._max_angle, angle))
        self._update_wheel()
    
    def get_angle(self):
        return self._angle
    
    def set_max_angle(self, max_angle):
        self._max_angle = max_angle
        if self._initialized:
            self._update_wheel()


class MainWindow(tk.Tk):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.tray_manager = None
        
        self.title('LinearMouseSim - 方向盘模拟器')
        self.geometry('900x700')
        self.configure(bg='#0a0a14')
        
        self._setup_styles()
        
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.bind('<Unmap>', self._on_minimize)
        
        self._init_components()
        self._init_tray()
    
    def _setup_styles(self):
        style = ttk.Style()
        
        style.theme_use('clam')
        
        style.configure('Modern.TFrame', background='#0f0f1a')
        style.configure('Panel.TFrame', background='#16162a')
        
        style.configure('Modern.TLabel', 
            background='#0f0f1a', foreground='#ffffff',
            font=('Segoe UI', 10)
        )
        style.configure('Panel.TLabel', 
            background='#16162a', foreground='#ffffff',
            font=('Segoe UI', 10)
        )
        
        style.configure('Modern.TButton',
            background='#1a1a3e', foreground='#ffffff',
            bordercolor='#2a2a5e', borderwidth=1,
            focuscolor='#2a2a5e', focusthickness=0
        )
        style.map('Modern.TButton',
            background=[('active', '#2a2a5e')],
            foreground=[('active', '#ffffff')]
        )
        
        style.configure('Modern.TScale',
            background='#16162a', troughcolor='#2a2a4a',
            slidercolor='#4a90d9'
        )
        
        style.configure('Modern.TCombobox',
            fieldbackground='#1a1a3e', background='#1a1a3e',
            foreground='#ffffff', selectbackground='#2a2a5e',
            selectforeground='#ffffff'
        )
        
        style.configure('Modern.TCheckbutton',
            background='#16162a', foreground='#ffffff',
            focuscolor='#2a2a5e', focusthickness=0
        )
        
        style.configure('Modern.TRadiobutton',
            background='#16162a', foreground='#ffffff',
            focuscolor='#2a2a5e', focusthickness=0
        )
    
    def _init_components(self):
        bg_canvas = tk.Canvas(self, bg='#0a0a14', highlightthickness=0)
        bg_canvas.pack(fill=tk.BOTH, expand=True)
        
        bg_canvas.create_rectangle(
            0, 0, 900, 700,
            fill='#0a0a14', outline=''
        )
        
        gradient_id = bg_canvas.create_rectangle(
            0, 0, 900, 700,
            fill='', outline=''
        )
        bg_canvas.tag_lower(gradient_id)
        
        main_frame = ttk.Frame(bg_canvas, padding=10, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(main_frame, width=280, bg='#16162a', highlightbackground='#2a2a4a', highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        shadow_canvas = tk.Canvas(left_panel, bg='#0a0a14', highlightthickness=0, width=280, height=10)
        shadow_canvas.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.param_panel = ParameterPanel(left_panel)
        self.param_panel.pack(fill=tk.BOTH, expand=True)
        
        if self.app:
            self.param_panel.set_on_change_callback(self.app.update_steering_params)
            self.param_panel.set_on_preset_callback(self.app.apply_preset)
        
        right_area = ttk.Frame(main_frame, style='Modern.TFrame')
        right_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        wheel_container = tk.Frame(right_area, bg='#0f0f1a', highlightbackground='#2a2a4a', highlightthickness=1)
        wheel_container.pack(fill=tk.BOTH, expand=True, padx=(0, 0), pady=(0, 0))
        
        self.wheel_canvas = SteeringWheelCanvas(
            wheel_container, bg='#0f0f1a', highlightthickness=0
        )
        if self.app:
            self.wheel_canvas.set_max_angle(self.app.config.get('steering.max_angle', 90))
        self.wheel_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        """关闭窗口时退出程序"""
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "退出 LinearMouseSim",
            "确定要退出程序吗？\n\n退出后鼠标锁定将被释放。"
        )
        
        if result:
            if self.app:
                self.app.cleanup()
            self.quit()
            self.destroy()
    
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
