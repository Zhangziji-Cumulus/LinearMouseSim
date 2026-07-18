import tkinter as tk
from tkinter import ttk
import math
from .theme import Theme
from .status_bar import StatusBar
from .parameter_panel import ParameterPanel
from .tray_manager import TrayManager
from core.state_machine import SimulationState

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
        cx = self._center_x
        cy = self._center_y

        # 1. Background glow: semi-transparent gradient circles
        for i in range(5):
            offset = i * 18
            r = wheel_radius + 40 - offset
            alpha_color = ['#e8f5e9', '#c8e6c9', '#a5d6a7', '#81c784', '#66bb6a'][i]
            self.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=alpha_color, outline='', tag='glow'
            )

        # 2. Outer ring: solid circle
        self.create_oval(
            cx - wheel_radius, cy - wheel_radius,
            cx + wheel_radius, cy + wheel_radius,
            fill=Theme.WHEEL_RING, outline=Theme.WHEEL_RING_EDGE, width=2, tag='outer_ring'
        )

        # 3. Spokes: 3 thick lines from radius 30 to 140 (rotate with angle)
        spoke_inner = 30
        spoke_outer = 140
        angle_rad = math.radians(self._angle)
        for i in range(3):
            base_angle = i * 120 + self._angle
            rad = math.radians(base_angle)
            x1 = cx + spoke_inner * math.sin(rad)
            y1 = cy - spoke_inner * math.cos(rad)
            x2 = cx + spoke_outer * math.sin(rad)
            y2 = cy - spoke_outer * math.cos(rad)
            self.create_line(x1, y1, x2, y2,
                             fill=Theme.WHEEL_SPOKE, width=8,
                             capstyle='round', tag='spoke')

        # 4. Center: 20px circle (static)
        center_r = 20
        self.create_oval(
            cx - center_r, cy - center_r,
            cx + center_r, cy + center_r,
            fill=Theme.WHEEL_CENTER, outline='', tag='center_plate'
        )

        # 5. 12 o'clock marker: vertical bar, 20x3px (rotates)
        marker_h = 20
        marker_w = 3
        marker_cx = cx
        marker_cy = cy - wheel_radius
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        # Rectangle vertices relative to marker center, then rotated around wheel center
        rect_pts = [
            (-marker_w / 2, -marker_h / 2),
            (marker_w / 2, -marker_h / 2),
            (marker_w / 2, marker_h / 2),
            (-marker_w / 2, marker_h / 2),
        ]
        rotated = []
        for px, py in rect_pts:
            rx = px * cos_a - py * sin_a + marker_cx
            ry = px * sin_a + py * cos_a + marker_cy
            rotated.extend([rx, ry])
        self.create_polygon(rotated, fill=Theme.WHEEL_MARKER, outline='', tag='12clock')

        # 6. Scale dial: tick marks, thicker and longer
        for angle_deg in range(-180, 181, 30):
            if angle_deg == 0:
                continue
            tick_outer_r = wheel_radius + 22
            tick_len = 18 if abs(angle_deg) % 60 == 0 else 12
            tick_inner_r = tick_outer_r - tick_len
            rad = math.radians(angle_deg)
            x1 = cx + tick_inner_r * math.sin(rad)
            y1 = cy - tick_inner_r * math.cos(rad)
            x2 = cx + tick_outer_r * math.sin(rad)
            y2 = cy - tick_outer_r * math.cos(rad)
            tick_width = 4 if abs(angle_deg) % 60 == 0 else 3
            self.create_line(x1, y1, x2, y2, fill='#000000', width=tick_width, tag='tick')

        # 7. Angle display: large number + direction text
        self.create_text(cx, cy + wheel_radius + 48,
                         text='0.0°', fill=Theme.ON_SURFACE,
                         font=(Theme.FONT_MONO, 28, 'bold'), tag='angle_text')
        self.create_text(cx, cy + wheel_radius + 74,
                         text='CENTER', fill=Theme.ON_SURFACE_VARIANT,
                         font=(Theme.FONT_FAMILY, 11), tag='rotation_text')

        self._initialized = True

    def _update_wheel(self):
        if not self._initialized:
            self._create_wheel_elements()
            return

        self.delete('all')

        cx = self._center_x
        cy = self._center_y
        wheel_radius = self._wheel_radius
        angle = self._angle
        angle_rad = math.radians(angle)

        # 1. Background glow
        for i in range(5):
            offset = i * 18
            r = wheel_radius + 40 - offset
            alpha_color = ['#e8f5e9', '#c8e6c9', '#a5d6a7', '#81c784', '#66bb6a'][i]
            self.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=alpha_color, outline='', tag='glow'
            )

        # 2. Outer ring (static)
        self.create_oval(
            cx - wheel_radius, cy - wheel_radius,
            cx + wheel_radius, cy + wheel_radius,
            fill=Theme.WHEEL_RING, outline=Theme.WHEEL_RING_EDGE, width=2, tag='outer_ring'
        )

        # 3. Spokes: 3 thick lines (rotate)
        spoke_inner = 30
        spoke_outer = 140
        for i in range(3):
            base_angle = i * 120 + angle
            rad = math.radians(base_angle)
            x1 = cx + spoke_inner * math.sin(rad)
            y1 = cy - spoke_inner * math.cos(rad)
            x2 = cx + spoke_outer * math.sin(rad)
            y2 = cy - spoke_outer * math.cos(rad)
            self.create_line(x1, y1, x2, y2,
                             fill=Theme.WHEEL_SPOKE, width=8,
                             capstyle='round', tag='spoke')

        # 4. Center (static)
        center_r = 20
        self.create_oval(
            cx - center_r, cy - center_r,
            cx + center_r, cy + center_r,
            fill=Theme.WHEEL_CENTER, outline='', tag='center_plate'
        )

        # 5. 12 o'clock marker (rotates)
        marker_h = 20
        marker_w = 3
        marker_cx = cx
        marker_cy = cy - wheel_radius
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rect_pts = [
            (-marker_w / 2, -marker_h / 2),
            (marker_w / 2, -marker_h / 2),
            (marker_w / 2, marker_h / 2),
            (-marker_w / 2, marker_h / 2),
        ]
        rotated = []
        for px, py in rect_pts:
            rx = px * cos_a - py * sin_a + marker_cx
            ry = px * sin_a + py * cos_a + marker_cy
            rotated.extend([rx, ry])
        self.create_polygon(rotated, fill=Theme.WHEEL_MARKER, outline='', tag='12clock')

        # 6. Scale dial: tick marks, thicker and longer
        for angle_deg in range(-180, 181, 30):
            if angle_deg == 0:
                continue
            tick_outer_r = wheel_radius + 22
            tick_len = 18 if abs(angle_deg) % 60 == 0 else 12
            tick_inner_r = tick_outer_r - tick_len
            rad = math.radians(angle_deg)
            x1 = cx + tick_inner_r * math.sin(rad)
            y1 = cy - tick_inner_r * math.cos(rad)
            x2 = cx + tick_outer_r * math.sin(rad)
            y2 = cy - tick_outer_r * math.cos(rad)
            tick_width = 4 if abs(angle_deg) % 60 == 0 else 3
            self.create_line(x1, y1, x2, y2, fill='#000000', width=tick_width, tag='tick')

        # 7. Direction arrows (static, color changes)
        arrow_size = 12
        left_ax = cx - wheel_radius - 40
        right_ax = cx + wheel_radius + 40
        left_color = Theme.TERTIARY if angle < -0.5 else Theme.OUTLINE
        right_color = Theme.TERTIARY if angle > 0.5 else Theme.OUTLINE
        self.create_polygon(
            left_ax + arrow_size, cy - arrow_size,
            left_ax, cy,
            left_ax + arrow_size, cy + arrow_size,
            fill=left_color, outline='', tag='left_arrow'
        )
        self.create_polygon(
            right_ax - arrow_size, cy - arrow_size,
            right_ax, cy,
            right_ax - arrow_size, cy + arrow_size,
            fill=right_color, outline='', tag='right_arrow'
        )

        # 8. Angle display
        self.create_text(cx, cy + wheel_radius + 48,
                         text=f'{angle:.1f}°', fill=Theme.ON_SURFACE,
                         font=(Theme.FONT_MONO, 28, 'bold'), tag='angle_text')
        if angle > 0.5:
            rot_text = 'RIGHT'
            rot_color = Theme.TERTIARY
        elif angle < -0.5:
            rot_text = 'LEFT'
            rot_color = Theme.TERTIARY
        else:
            rot_text = 'CENTER'
            rot_color = Theme.ON_SURFACE_VARIANT
        self.create_text(cx, cy + wheel_radius + 74,
                         text=rot_text, fill=rot_color,
                         font=(Theme.FONT_FAMILY, 11), tag='rotation_text')

    
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
    def __init__(self, app=None, presets=None):
        super().__init__()
        self.app = app
        self.presets = presets or {}
        self.title("LinearMouseSim")
        self.geometry("1200x750")
        self.minsize(900, 600)
        
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
                 background=[('active', Theme.PRIMARY_HOVER)])
        
        style.map('Secondary.TButton',
                 background=[('active', Theme.SURFACE_CONTAINER_HIGHEST)])
    
    def _create_layout(self):
        main_frame = ttk.Frame(self, style='Panel.TFrame', padding=0)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - parameter settings (fixed width)
        left_panel = ttk.Frame(main_frame, style='Panel.TFrame', width=360)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=8)
        left_panel.pack_propagate(False)
        
        self.param_panel = ParameterPanel(left_panel, self, presets=self.presets)
        self.param_panel.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - steering wheel
        wheel_frame = ttk.Frame(main_frame, style='Panel.TFrame')
        wheel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8)
        
        self.wheel_canvas = SteeringWheelCanvas(wheel_frame, bg=Theme.SURFACE)
        self.wheel_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar at bottom
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
        is_active = state == SimulationState.ON
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
                'center_enabled': self.app.config.get('steering.center_enabled', True),
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
