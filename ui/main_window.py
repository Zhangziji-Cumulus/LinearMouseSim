import tkinter as tk
from tkinter import ttk
import math
from .theme import Theme
from .status_bar import StatusBar
from .parameter_panel import ParameterPanel
from .tray_manager import TrayManager

class SteeringWheelCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._angle = 0.0
        self._target_angle = 0.0
        self._max_angle = 90
        self._wheel_radius = 160
        self._center_x = 0
        self._center_y = 0
        self._deadzone = 0.0
        self._smoothing_factor = 0.3
        self._animation_active = False
        
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
        
        self._center_x = self.winfo_width() // 2
        self._center_y = self.winfo_height() // 2
        
        wheel_radius = self._wheel_radius
        center_x = self._center_x
        center_y = self._center_y
        
        self.create_oval(
            center_x - wheel_radius - 12, center_y - wheel_radius - 12,
            center_x + wheel_radius + 12, center_y + wheel_radius + 12,
            fill='#000000', outline='', tag='shadow'
        )
        
        self.create_oval(
            center_x - wheel_radius, center_y - wheel_radius,
            center_x + wheel_radius, center_y + wheel_radius,
            fill=Theme.SURFACE_CONTAINER_LOWEST, outline=Theme.OUTLINE, width=2, tag='outer_ring'
        )
        
        grip_radius = wheel_radius * 0.88
        self.create_oval(
            center_x - grip_radius, center_y - grip_radius,
            center_x + grip_radius, center_y + grip_radius,
            fill=Theme.SURFACE_CONTAINER_HIGHEST, outline=Theme.OUTLINE, width=2, tag='grip_area'
        )
        
        for i in range(3):
            grip_angle = i * 120
            start_angle = grip_angle - 18
            end_angle = grip_angle + 18
            
            inner_grip = wheel_radius * 0.62
            outer_grip = wheel_radius * 0.96
            
            x1 = center_x + inner_grip * math.sin(math.radians(start_angle))
            y1 = center_y - inner_grip * math.cos(math.radians(start_angle))
            x2 = center_x + inner_grip * math.sin(math.radians(end_angle))
            y2 = center_y - inner_grip * math.cos(math.radians(end_angle))
            x3 = center_x + outer_grip * math.sin(math.radians(end_angle))
            y3 = center_y - outer_grip * math.cos(math.radians(end_angle))
            x4 = center_x + outer_grip * math.sin(math.radians(start_angle))
            y4 = center_y - outer_grip * math.cos(math.radians(start_angle))
            
            self.create_polygon(
                x1, y1, x2, y2, x3, y3, x4, y4,
                fill=Theme.SECONDARY, outline='#3a7bc8', width=1, tag='grip'
            )
        
        spoke_radius = wheel_radius * 0.45
        for i in range(3):
            angle = i * 120
            rad = math.radians(angle)
            x1 = center_x + spoke_radius * 0.3 * math.sin(rad)
            y1 = center_y - spoke_radius * 0.3 * math.cos(rad)
            x2 = center_x + spoke_radius * math.sin(rad)
            y2 = center_y - spoke_radius * math.cos(rad)
            self.create_line(x1, y1, x2, y2, fill=Theme.OUTLINE_VARIANT, width=4, tag='spoke')
        
        inner_radius = wheel_radius * 0.52
        self.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill=Theme.SURFACE_CONTAINER_LOW, outline=Theme.OUTLINE_VARIANT, width=1, tag='inner_ring'
        )
        
        center_radius = wheel_radius * 0.16
        self.create_oval(
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius,
            fill=Theme.PRIMARY, outline=Theme.ON_PRIMARY, width=2, tag='center_cap'
        )
        
        self.create_text(center_x, center_y, text='LMS', fill=Theme.ON_PRIMARY,
                        font=(Theme.FONT_FAMILY, 12, 'bold'), tag='center_text')
        
        line_length = wheel_radius * 1.2
        self.create_line(
            center_x - line_length, center_y,
            center_x + line_length, center_y,
            fill=Theme.OUTLINE_VARIANT, width=1, dash=(6, 4), tag='indicator_line'
        )
        
        self.create_line(
            center_x, center_y - line_length * 0.35,
            center_x, center_y + line_length * 0.35,
            fill=Theme.OUTLINE_VARIANT, width=1, dash=(6, 4), tag='indicator_line_vertical'
        )
        
        self.create_text(
            center_x, center_y + wheel_radius + 45,
            text='0.0°', fill=Theme.ON_SURFACE, font=(Theme.FONT_MONO, 28, 'bold'),
            tag='angle_text'
        )
        
        self.create_text(
            center_x, center_y + wheel_radius + 72,
            text='CENTER', fill=Theme.ON_SURFACE_VARIANT, font=(Theme.FONT_FAMILY, 11),
            tag='rotation_text'
        )
        
        left_arrow_x = center_x - wheel_radius - 75
        right_arrow_x = center_x + wheel_radius + 75
        
        self.create_polygon(
            left_arrow_x + 24, center_y - 20,
            left_arrow_x, center_y,
            left_arrow_x + 24, center_y + 20,
            fill=Theme.OUTLINE_VARIANT, outline='', tag='left_arrow'
        )
        self.create_text(left_arrow_x + 45, center_y, text='LEFT', fill=Theme.ON_SURFACE_VARIANT,
                        font=(Theme.FONT_FAMILY, 11, 'bold'), tag='left_label')
        
        self.create_polygon(
            right_arrow_x - 24, center_y - 20,
            right_arrow_x, center_y,
            right_arrow_x - 24, center_y + 20,
            fill=Theme.OUTLINE_VARIANT, outline='', tag='right_arrow'
        )
        self.create_text(right_arrow_x - 45, center_y, text='RIGHT', fill=Theme.ON_SURFACE_VARIANT,
                        font=(Theme.FONT_FAMILY, 11, 'bold'), tag='right_label')
        
        for angle in [-90, -60, -30, 30, 60, 90]:
            tick_radius = wheel_radius + 18
            tick_length = 14 if abs(angle) % 30 == 0 else 7
            
            rad = math.radians(angle)
            x1 = center_x + (tick_radius - tick_length) * math.sin(rad)
            y1 = center_y - (tick_radius - tick_length) * math.cos(rad)
            x2 = center_x + tick_radius * math.sin(rad)
            y2 = center_y - tick_radius * math.cos(rad)
            
            tick_color = Theme.TERTIARY if abs(angle) <= self._max_angle else Theme.OUTLINE_VARIANT
            self.create_line(x1, y1, x2, y2, fill=tick_color, width=2 if abs(angle) % 30 == 0 else 1,
                           tag='tick')
            
            label_radius = wheel_radius + 38
            lx = center_x + label_radius * math.sin(rad)
            ly = center_y - label_radius * math.cos(rad)
            
            label_color = Theme.ON_SURFACE if abs(angle) <= self._max_angle else Theme.ON_SURFACE_VARIANT
            self.create_text(lx, ly, text=f'{angle}°', fill=label_color,
                           font=(Theme.FONT_MONO, 10, 'bold'), tag='tick_label')
        
        deadzone_radius = wheel_radius * 0.25
        self.create_oval(
            center_x - deadzone_radius, center_y - deadzone_radius,
            center_x + deadzone_radius, center_y + deadzone_radius,
            fill=Theme.SURFACE_CONTAINER_LOW, outline=Theme.OUTLINE_VARIANT, width=1,
            tag='deadzone_indicator'
        )
        
        self.create_text(
            center_x, center_y + deadzone_radius + 20,
            text='DEADZONE', fill=Theme.WARNING, font=(Theme.FONT_FAMILY, 8, 'bold'),
            tag='deadzone_label'
        )
        
        self._initialized = True
    
    def _update_wheel(self):
        if not self._initialized:
            self._create_wheel_elements()
            return
        
        self.delete('all')
        
        center_x = self._center_x
        center_y = self._center_y
        wheel_radius = self._wheel_radius
        
        angle_rad = math.radians(self._angle)
        
        self.create_oval(
            center_x - wheel_radius - 12, center_y - wheel_radius - 12,
            center_x + wheel_radius + 12, center_y + wheel_radius + 12,
            fill='#000000', outline='', tag='shadow'
        )
        
        self.create_oval(
            center_x - wheel_radius, center_y - wheel_radius,
            center_x + wheel_radius, center_y + wheel_radius,
            fill=Theme.SURFACE_CONTAINER_LOWEST, outline=Theme.OUTLINE, width=2, tag='outer_ring'
        )
        
        grip_radius = wheel_radius * 0.88
        self.create_oval(
            center_x - grip_radius, center_y - grip_radius,
            center_x + grip_radius, center_y + grip_radius,
            fill=Theme.SURFACE_CONTAINER_HIGHEST, outline=Theme.OUTLINE, width=2, tag='grip_area'
        )
        
        for i in range(3):
            grip_angle = i * 120 + self._angle
            start_angle = grip_angle - 18
            end_angle = grip_angle + 18
            
            inner_grip = wheel_radius * 0.62
            outer_grip = wheel_radius * 0.96
            
            x1 = center_x + inner_grip * math.sin(math.radians(start_angle))
            y1 = center_y - inner_grip * math.cos(math.radians(start_angle))
            x2 = center_x + inner_grip * math.sin(math.radians(end_angle))
            y2 = center_y - inner_grip * math.cos(math.radians(end_angle))
            x3 = center_x + outer_grip * math.sin(math.radians(end_angle))
            y3 = center_y - outer_grip * math.cos(math.radians(end_angle))
            x4 = center_x + outer_grip * math.sin(math.radians(start_angle))
            y4 = center_y - outer_grip * math.cos(math.radians(start_angle))
            
            self.create_polygon(
                x1, y1, x2, y2, x3, y3, x4, y4,
                fill=Theme.SECONDARY, outline='#3a7bc8', width=1, tag='grip'
            )
        
        spoke_radius = wheel_radius * 0.45
        for i in range(3):
            angle = i * 120 + self._angle
            rad = math.radians(angle)
            x1 = center_x + spoke_radius * 0.3 * math.sin(rad)
            y1 = center_y - spoke_radius * 0.3 * math.cos(rad)
            x2 = center_x + spoke_radius * math.sin(rad)
            y2 = center_y - spoke_radius * math.cos(rad)
            self.create_line(x1, y1, x2, y2, fill=Theme.OUTLINE_VARIANT, width=4, tag='spoke')
        
        inner_radius = wheel_radius * 0.52
        self.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill=Theme.SURFACE_CONTAINER_LOW, outline=Theme.OUTLINE_VARIANT, width=1, tag='inner_ring'
        )
        
        center_radius = wheel_radius * 0.16
        self.create_oval(
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius,
            fill=Theme.PRIMARY, outline=Theme.ON_PRIMARY, width=2, tag='center_cap'
        )
        
        deadzone_radius = wheel_radius * (0.15 + self._deadzone / 50)
        is_in_deadzone = abs(self._angle) < (self._max_angle * self._deadzone / 100)
        deadzone_color = Theme.WARNING if is_in_deadzone else Theme.SURFACE_CONTAINER_LOW
        deadzone_outline = Theme.WARNING if is_in_deadzone else Theme.OUTLINE_VARIANT
        
        self.create_oval(
            center_x - deadzone_radius, center_y - deadzone_radius,
            center_x + deadzone_radius, center_y + deadzone_radius,
            fill=deadzone_color, outline=deadzone_outline, width=2, tag='deadzone_indicator'
        )
        
        for i in range(-self._max_angle, self._max_angle + 1, 30):
            if i == 0:
                continue
            
            tick_radius_inner = wheel_radius * 0.55
            tick_radius_outer = wheel_radius * 0.59
            
            angle_deg = i + self._angle
            rad = math.radians(angle_deg)
            
            x1 = center_x + tick_radius_inner * math.sin(rad)
            y1 = center_y - tick_radius_inner * math.cos(rad)
            x2 = center_x + tick_radius_outer * math.sin(rad)
            y2 = center_y - tick_radius_outer * math.cos(rad)
            
            color = Theme.TERTIARY if i % 60 == 0 else Theme.OUTLINE_VARIANT
            self.create_line(x1, y1, x2, y2, fill=color, width=2 if i % 60 == 0 else 1, tag='tick')
            
            if i % 30 == 0:
                label_radius = wheel_radius * 0.48
                label_x = center_x + label_radius * math.sin(rad)
                label_y = center_y - label_radius * math.cos(rad)
                
                label_text = f'{i}°'
                font_color = Theme.TERTIARY if i % 60 == 0 else Theme.ON_SURFACE_VARIANT
                self.create_text(label_x, label_y, text=label_text, fill=font_color,
                                font=(Theme.FONT_MONO, 8), tag='angle_label')
        
        center_line_length = wheel_radius * 0.35
        self.create_line(
            center_x, center_y - center_line_length,
            center_x, center_y + center_line_length,
            fill=Theme.PRIMARY, width=3, tag='center_line'
        )
        self.create_line(
            center_x - center_line_length, center_y,
            center_x + center_line_length, center_y,
            fill=Theme.PRIMARY, width=3, tag='center_line'
        )
        
        self.create_text(center_x, center_y, text='LM', fill=Theme.ON_PRIMARY,
                        font=(Theme.FONT_FAMILY, 12, 'bold'), tag='center_text')
        
        self.create_text(center_x, center_y + wheel_radius + 30,
                        text=f'{self._angle:.1f}°', fill=Theme.ON_SURFACE,
                        font=(Theme.FONT_MONO, 24, 'bold'), tag='angle_text')
        
        if self._angle > 0.5:
            rotation_text = 'RIGHT'
        elif self._angle < -0.5:
            rotation_text = 'LEFT'
        else:
            rotation_text = 'CENTER'
        
        self.create_text(center_x, center_y + wheel_radius + 55,
                        text=rotation_text, fill=Theme.SECONDARY,
                        font=(Theme.FONT_FAMILY, 10), tag='rotation_text')
        
        arrow_size = 12
        left_arrow_x = center_x - wheel_radius - 25
        right_arrow_x = center_x + wheel_radius + 25
        
        left_color = Theme.TERTIARY if self._angle < -0.5 else Theme.OUTLINE_VARIANT
        right_color = Theme.TERTIARY if self._angle > 0.5 else Theme.OUTLINE_VARIANT
        
        self.create_polygon(
            left_arrow_x + arrow_size, center_y - arrow_size,
            left_arrow_x, center_y,
            left_arrow_x + arrow_size, center_y + arrow_size,
            fill=left_color, outline=left_color, tag='left_arrow'
        )
        
        self.create_polygon(
            right_arrow_x - arrow_size, center_y - arrow_size,
            right_arrow_x, center_y,
            right_arrow_x - arrow_size, center_y + arrow_size,
            fill=right_color, outline=right_color, tag='right_arrow'
        )

    
    def _animate(self):
        if not self._animation_active:
            return
        
        diff = self._target_angle - self._angle
        if abs(diff) < 0.01:
            self._angle = self._target_angle
            self._animation_active = False
        else:
            self._angle += diff * (1 - self._smoothing_factor)
        
        self._update_wheel()
        
        if self._animation_active:
            self.after(16, self._animate)
    
    def set_angle(self, angle, smooth=True):
        if smooth:
            self._target_angle = angle
            if not self._animation_active:
                self._animation_active = True
                self._animate()
        else:
            self._angle = angle
            self._target_angle = angle
            self._animation_active = False
            self._update_wheel()
    
    def set_max_angle(self, max_angle):
        self._max_angle = max_angle
        self._initialized = False
        self._update_wheel()
    
    def set_deadzone(self, deadzone):
        self._deadzone = deadzone
        self._update_wheel()
    
    def set_smoothing_factor(self, factor):
        self._smoothing_factor = factor

class MainWindow(tk.Tk):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.title("LinearMouseSim")
        self.geometry("900x650")
        self.minsize(700, 500)
        
        self.configure(bg=Theme.SURFACE)
        
        self._setup_styles()
        
        self._create_layout()
        
        self._current_angle = 0.0
        
        self.tray_manager = TrayManager(self)
    
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Panel.TFrame', background=Theme.SURFACE_CONTAINER)
        style.configure('Card.TFrame', background=Theme.SURFACE_CONTAINER_HIGH)
        
        style.configure('Heading.TLabel',
                       background=Theme.SURFACE_CONTAINER,
                       foreground=Theme.ON_SURFACE,
                       font=(Theme.FONT_FAMILY, 14, 'bold'))
        
        style.configure('Label.TLabel',
                       background=Theme.SURFACE_CONTAINER_HIGH,
                       foreground=Theme.ON_SURFACE_VARIANT,
                       font=(Theme.FONT_FAMILY, 11))
        
        style.configure('Value.TLabel',
                       background=Theme.SURFACE_CONTAINER_HIGH,
                       foreground=Theme.ON_SURFACE,
                       font=(Theme.FONT_MONO, 14, 'bold'))
        
        style.configure('Primary.TButton',
                       background=Theme.PRIMARY,
                       foreground=Theme.ON_PRIMARY,
                       font=(Theme.FONT_FAMILY, 11, 'bold'),
                       padding=8,
                       borderwidth=0)
        
        style.configure('Secondary.TButton',
                       background=Theme.SURFACE_CONTAINER_HIGH,
                       foreground=Theme.ON_SURFACE,
                       font=(Theme.FONT_FAMILY, 11),
                       padding=8,
                       borderwidth=1,
                       bordercolor=Theme.OUTLINE)
        
        style.configure('TScale',
                       background=Theme.SURFACE_CONTAINER_HIGH,
                       troughcolor=Theme.SURFACE_CONTAINER_LOW,
                       sliderrelief='flat')
        
        style.map('Primary.TButton',
                 background=[('active', '#ff6b85')])
        
        style.map('Secondary.TButton',
                 background=[('active', Theme.SURFACE_CONTAINER_HIGHEST)])
    
    def _create_layout(self):
        main_frame = ttk.Frame(self, style='Panel.TFrame', padding=0)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(main_frame, style='Panel.TFrame', width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=8)
        left_panel.pack_propagate(False)
        
        wheel_frame = ttk.Frame(main_frame, style='Panel.TFrame')
        wheel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8)
        
        self.wheel_canvas = SteeringWheelCanvas(wheel_frame, bg=Theme.SURFACE_CONTAINER_LOW)
        self.wheel_canvas.pack(fill=tk.BOTH, expand=True, padx=8)
        
        self.param_panel = ParameterPanel(left_panel, self)
        self.param_panel.pack(fill=tk.BOTH, expand=True)
        
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_wheel_angle(self, angle):
        self.wheel_canvas.set_angle(angle)
    
    def update_status_bar_angle(self, angle):
        self.status_bar.set_angle(angle)
    
    def update_angle(self, angle):
        self._current_angle = angle
        self.wheel_canvas.set_angle(angle)
        self.status_bar.set_angle(angle)
    
    def set_simulation_status(self, is_running):
        self.status_bar.set_simulation_status(is_running)
    
    def set_vjoy_status(self, available, status_text):
        self.status_bar.set_vjoy_status(available, status_text)
    
    def update_status(self, state):
        is_active = state == 'ON'
        self.status_bar.set_active(is_active)
    
    def update_parameter_display(self):
        if self.app and self.app.config:
            params = {
                'sensitivity': self.app.config.get('steering.sensitivity', 1.0),
                'smoothing_factor': self.app.config.get('steering.smoothing_factor', 0.3),
                'deadzone': self.app.config.get('steering.deadzone', 3),
                'max_angle': self.app.config.get('steering.max_angle', 90),
                'dpi': self.app.config.get('mouse.dpi', 800),
                'return_speed': self.app.config.get('steering.return_speed', 0),
                'reverse_direction': self.app.config.get('steering.reverse_direction', False),
                'assist_rate_window': self.app.config.get('steering.assist_rate_window', 0.05),
                'assist_rate_threshold': self.app.config.get('steering.assist_rate_threshold', 100),
                'center_hold_ms': self.app.config.get('steering.center_hold_ms', 500),
                'center_release_threshold': self.app.config.get('steering.center_release_threshold', 200),
                'linear_end': self.app.config.get('three_zone.linear_end', 500),
                'saturation_end': self.app.config.get('three_zone.saturation_end', 1000),
                'assist_threshold': self.app.config.get('steering.assist_threshold', 300),
                'assist_return_rate': self.app.config.get('steering.assist_return_rate', 0.20),
                'near_center_threshold': self.app.config.get('steering.near_center_threshold', 50),
            }
            self.param_panel.set_parameters(params)
    
    def show_osd(self, message, duration=2000):
        osd_window = tk.Toplevel(self)
        osd_window.attributes('-topmost', True)
        osd_window.attributes('-transparentcolor', '#000000')
        osd_window.overrideredirect(True)
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        osd_width = 350
        osd_height = 90
        
        x = (screen_width - osd_width) // 2
        y = screen_height // 4
        
        osd_window.geometry(f'{osd_width}x{osd_height}+{x}+{y}')
        
        frame = ttk.Frame(osd_window, style='Panel.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        label = ttk.Label(frame, text=message,
                         font=(Theme.FONT_MONO, 22, 'bold'),
                         foreground=Theme.ON_SURFACE,
                         background=Theme.SURFACE_CONTAINER,
                         justify=tk.CENTER)
        label.pack(fill=tk.BOTH, expand=True)
        
        def hide_osd():
            osd_window.destroy()
        
        self.after(duration, hide_osd)
    
    def run(self):
        self.mainloop()