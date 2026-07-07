"""参数调节面板模块"""

import tkinter as tk
from tkinter import ttk, messagebox
from .theme import Theme
from config.presets import PRESETS


class ParameterSlider(tk.Frame):
    """参数滑块组件，支持手动输入精确值"""
    
    def __init__(self, parent, label_text, min_val, max_val, default_val, 
                 resolution=0.1, unit='', callback=None, snap_points=None, snap_tolerance=15):
        super().__init__(parent)
        
        self._callback = callback
        self._unit = unit
        self._snap_points = snap_points or []
        self._snap_tolerance = snap_tolerance
        self._min_val = min_val
        self._max_val = max_val
        self._resolution = resolution
        self._setting_value = False
        
        self.configure(bg=Theme.SURFACE_CONTAINER)
        
        # 标题行：标签 + 输入框
        header_frame = tk.Frame(self, bg=Theme.SURFACE_CONTAINER)
        header_frame.pack(fill=tk.X, pady=(8, 3))
        
        self.label = ttk.Label(
            header_frame, text=label_text, 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER, 
            font=(Theme.FONT_FAMILY, 10, 'bold')
        )
        self.label.pack(side=tk.LEFT)
        
        # 手动输入框
        self._entry_var = tk.StringVar(value=f'{default_val:.1f}')
        self._entry = ttk.Entry(
            header_frame, textvariable=self._entry_var, width=8,
            font=(Theme.FONT_MONO, 10)
        )
        self._entry.pack(side=tk.RIGHT)
        self._entry.bind('<Return>', self._on_entry_return)
        self._entry.bind('<FocusOut>', self._on_entry_return)
        self._entry.bind('<Key>', self._validate_entry_input)
        
        unit_label = ttk.Label(
            header_frame, text=unit, width=4,
            foreground=Theme.ON_SURFACE_VARIANT,
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 9)
        )
        unit_label.pack(side=tk.RIGHT, padx=(0, 4))
        
        # 滑块区域
        self.slider_container = tk.Frame(self, bg=Theme.SURFACE_CONTAINER)
        self.slider_container.pack(fill=tk.X, pady=(0, 2))
        
        self._snap_canvas = tk.Canvas(self.slider_container, bg=Theme.SURFACE_CONTAINER, highlightthickness=0, height=14)
        self._snap_canvas.pack(fill=tk.X, pady=(0, 0))
        
        self.slider = ttk.Scale(
            self.slider_container, from_=min_val, to=max_val, value=default_val,
            orient=tk.HORIZONTAL, command=self._on_slider_change
        )
        self.slider.pack(fill=tk.X, pady=(0, 2))
        
        self.slider.bind('<ButtonRelease-1>', self._on_slider_release)
        
        # 值显示
        self.value_label = ttk.Label(
            self, text=f'{default_val:.1f}{unit}', 
            foreground=Theme.SECONDARY, 
            background=Theme.SURFACE_CONTAINER, 
            font=(Theme.FONT_MONO, 12, 'bold')
        )
        self.value_label.pack(fill=tk.X)
        
        self.slider.after(100, self._draw_snap_markers)
    
    def _on_slider_change(self, value):
        """滑块值变化事件"""
        if self._setting_value:
            return
        float_val = float(value)
        # 整数显示整数，浮点数保留两位小数
        if float_val == int(float_val):
            display_val = int(float_val)
        else:
            display_val = round(float_val, 2)
        self.value_label.config(text=f'{display_val}{self._unit}')
        self._entry_var.set(f'{display_val}')
        if self._callback:
            self._callback(float_val)
    
    def _on_entry_return(self, event):
        """手动输入确认，只允许数字和浮点数"""
        try:
            input_text = self._entry_var.get().strip()
            import re
            if not re.match(r'^-?\d*\.?\d*$', input_text):
                raise ValueError("无效输入")
            
            new_val = float(input_text) if input_text else self._min_val
            new_val = round(new_val, 2)
            new_val = max(self._min_val, min(self._max_val, new_val))
            self.slider.set(new_val)
            # ttk.Scale.set() 不触发 command 回调，必须手动调用
            self._on_slider_change(str(new_val))
        except ValueError:
            current = self.slider.get()
            display_val = int(current) if current == int(current) else round(current, 2)
            self._entry_var.set(f'{display_val}')
    
    def _validate_entry_input(self, event):
        """实时验证输入，只允许数字、小数点、负号"""
        # 允许控制键（退格、删除、方向键等）
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab'):
            return
        
        # 允许Ctrl+A/C/V/X
        if event.state & 0x4:  # Ctrl键
            return
        
        # 只允许数字、小数点、负号
        allowed_chars = set('0123456789.-')
        if event.char and event.char not in allowed_chars:
            return 'break'  # 阻止输入
    
    def _on_slider_release(self, event):
        """滑块释放事件，处理吸附逻辑"""
        if not self._snap_points:
            return
        
        current_val = self.slider.get()
        snapped_val = self._snap_to_nearest(current_val)
        
        if snapped_val is not None and abs(snapped_val - current_val) > 0.01:
            self.set_value(snapped_val)
    
    def _snap_to_nearest(self, value):
        """吸附到最近的吸附点"""
        nearest = None
        min_distance = float('inf')
        
        for point in self._snap_points:
            distance = abs(point - value)
            if distance <= self._snap_tolerance and distance < min_distance:
                min_distance = distance
                nearest = point
        
        return nearest
    
    def _draw_snap_markers(self):
        """在滑块下方绘制吸附点标记"""
        if not self._snap_points:
            return
        
        canvas_width = self._snap_canvas.winfo_width()
        if canvas_width < 10:
            self.slider.after(50, self._draw_snap_markers)
            return
        
        self._snap_canvas.delete('all')
        
        range_val = self._max_val - self._min_val
        if range_val <= 0:
            return
        
        for point in self._snap_points:
            if self._min_val <= point <= self._max_val:
                x_pos = ((point - self._min_val) / range_val) * canvas_width
                self._snap_canvas.create_polygon(
                    x_pos, 0,
                    x_pos - 4, 8,
                    x_pos + 4, 8,
                    fill=Theme.PRIMARY, outline=''
                )
                self._snap_canvas.create_text(
                    x_pos, 10,
                    text=f'{int(point)}', fill=Theme.PRIMARY, font=(Theme.FONT_MONO, 7)
                )
    
    def get_value(self):
        """获取当前值"""
        return self.slider.get()
    
    def set_value(self, value):
        """设置值"""
        self._setting_value = True
        self.slider.set(value)
        self._setting_value = False
        self._on_slider_change(str(value))


class ParameterPanel(tk.Frame):
    """参数调节面板类"""
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        
        self.configure(bg=Theme.SURFACE_CONTAINER)
        
        self._canvas = tk.Canvas(self, bg=Theme.SURFACE_CONTAINER, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._canvas.yview)
        self._inner_frame = ttk.Frame(self._canvas)
        
        self._inner_frame_id = self._canvas.create_window((0, 0), window=self._inner_frame, anchor='nw')
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._canvas.bind('<MouseWheel>', self._on_mouse_wheel)
        self._canvas.bind('<Configure>', self._on_canvas_configure)
        self._inner_frame.bind('<Configure>', self._on_inner_frame_configure)
        
        self._sliders = {}
        self._on_preset_callback = None
        self._hotkey_display = {}
        self._hotkey_buttons = {}
        self._hotkey_manager = None
        self._recording_action = None
        self._cancel_id = None
        
        self._build_content()
    
    def _on_inner_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self._canvas.itemconfig(self._inner_frame_id, width=canvas_width)
    
    def _on_mouse_wheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        return 'break'
    
    def _bind_mousewheel_recursive(self, widget):
        widget.bind('<MouseWheel>', self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)
    
    def _build_content(self):
        inner = self._inner_frame
        
        title_label = ttk.Label(
            inner, text='参数设置', 
            foreground=Theme.ON_SURFACE, 
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 16, 'bold')
        )
        title_label.pack(fill=tk.X, pady=(15, 15), padx=15)
        
        preset_frame = ttk.Frame(inner)
        preset_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        preset_label = ttk.Label(
            preset_frame, text='游戏预设', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 10, 'bold')
        )
        preset_label.pack(fill=tk.X, pady=(0, 5))
        
        self._preset_var = tk.StringVar(value='')
        self._preset_combo = ttk.Combobox(
            preset_frame, textvariable=self._preset_var,
            values=[preset['name'] for preset in PRESETS.values()],
            state='readonly'
        )
        self._preset_combo.pack(fill=tk.X)
        self._preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        self._sliders['sensitivity'] = ParameterSlider(
            inner, '灵敏度', 0.1, 5.0, 1.0, resolution=0.1, unit='x',
            callback=self._on_parameter_change
        )
        self._sliders['sensitivity'].pack(fill=tk.X, padx=15)
        
        self._sliders['smoothing_factor'] = ParameterSlider(
            inner, '平滑系数', 0.0, 0.99, 0.3, resolution=0.01, unit='',
            callback=self._on_parameter_change
        )
        self._sliders['smoothing_factor'].pack(fill=tk.X, padx=15)
        
        self._sliders['deadzone'] = ParameterSlider(
            inner, '死区', 0, 50, 3, resolution=1, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['deadzone'].pack(fill=tk.X, padx=15)
        
        self._sliders['max_angle'] = ParameterSlider(
            inner, '最大舵角', 10, 1800, 90, resolution=1, unit='°',
            callback=self._on_parameter_change,
            snap_points=[45, 90, 180, 360, 540, 720, 900],
            snap_tolerance=15
        )
        self._sliders['max_angle'].pack(fill=tk.X, padx=15)
        
        self._sliders['dpi'] = ParameterSlider(
            inner, '鼠标DPI', 50, 25600, 800, resolution=50, unit='',
            callback=self._on_parameter_change
        )
        self._sliders['dpi'].pack(fill=tk.X, padx=15)
        
        self._sliders['return_speed'] = ParameterSlider(
            inner, '回正速度', 0, 100, 0, resolution=1, unit='%',
            callback=self._on_parameter_change
        )
        self._sliders['return_speed'].pack(fill=tk.X, padx=15)

        # 辅助回中参数
        assist_label = ttk.Label(
            inner, text='辅助回中',
            foreground=Theme.ON_SURFACE_VARIANT,
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 10, 'bold')
        )
        assist_label.pack(fill=tk.X, padx=15, pady=(10, 3))

        self._sliders['assist_rate_window'] = ParameterSlider(
            inner, '回打检测时长', 0, 500, 100, resolution=10, unit='ms',
            callback=self._on_parameter_change
        )
        self._sliders['assist_rate_window'].pack(fill=tk.X, padx=15)

        self._sliders['assist_rate_threshold'] = ParameterSlider(
            inner, '回打位移阈值', 0, 2000, 100, resolution=10, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['assist_rate_threshold'].pack(fill=tk.X, padx=15)

        self._reverse_var = tk.BooleanVar(value=False)
        self._reverse_checkbox = ttk.Checkbutton(
            inner, text='反转方向盘方向',
            variable=self._reverse_var, command=self._on_parameter_change
        )
        self._reverse_checkbox.pack(fill=tk.X, padx=15, pady=(10, 15))

        # 三段式参数区
        three_zone_label = ttk.Label(
            inner, text='三段式映射',
            foreground=Theme.ON_SURFACE_VARIANT,
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 10, 'bold')
        )
        three_zone_label.pack(fill=tk.X, padx=15, pady=(10, 3))

        self._sliders['linear_end'] = ParameterSlider(
            inner, '像素→角度映射', 10, 5000, 500, resolution=10, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['linear_end'].pack(fill=tk.X, padx=15)

        # 辅助回中补充参数
        self._sliders['assist_threshold'] = ParameterSlider(
            inner, '辅助触发角度', 0, 900, 300, resolution=10, unit='°',
            callback=self._on_parameter_change
        )
        self._sliders['assist_threshold'].pack(fill=tk.X, padx=15)

        self._sliders['assist_return_rate'] = ParameterSlider(
            inner, '归中缩减比例', 0, 100, 20, resolution=1, unit='%',
            callback=self._on_parameter_change
        )
        self._sliders['assist_return_rate'].pack(fill=tk.X, padx=15)

        self._sliders['near_center_threshold'] = ParameterSlider(
            inner, '中心检测边界', 0, 500, 50, resolution=1, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['near_center_threshold'].pack(fill=tk.X, padx=15)

        # cm/360° 显示标签
        self._cm360_frame = tk.Frame(inner, bg=Theme.SURFACE_CONTAINER)
        self._cm360_frame.pack(fill=tk.X, padx=15, pady=(2, 8))
        self._cm360_label = ttk.Label(
            self._cm360_frame, text='当前 ≈ --.- cm/360°',
            foreground=Theme.SECONDARY,
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_MONO, 11, 'bold')
        )
        self._cm360_label.pack(side=tk.LEFT)

        hotkey_frame = ttk.Frame(inner)
        hotkey_frame.pack(fill=tk.X, padx=15, pady=(0, 20))
        
        hotkey_label = ttk.Label(
            hotkey_frame, text='快捷键配置', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER,
            font=(Theme.FONT_FAMILY, 10, 'bold')
        )
        hotkey_label.pack(fill=tk.X, pady=(0, 8))
        
        self._hotkey_actions = {
            'toggle': '切换模拟',
            'increase_sensitivity': '增加灵敏度',
            'decrease_sensitivity': '降低灵敏度',
            'reset_steering': '重置方向盘',
            'sensitivity_preset_1': '灵敏度预设1',
            'sensitivity_preset_2': '灵敏度预设2',
            'sensitivity_preset_3': '灵敏度预设3',
            'cycle_curve': '切换曲线',
            'wheel_adjust': '滚轮调节键',
            'temp_sensitivity_half': '临时降敏'
        }
        
        for action, label_text in self._hotkey_actions.items():
            hk_frame = ttk.Frame(hotkey_frame)
            hk_frame.pack(fill=tk.X, pady=(2, 2))
            
            hk_label = ttk.Label(
                hk_frame, text=label_text, width=12,
                foreground=Theme.ON_SURFACE, 
                background=Theme.SURFACE_CONTAINER, 
                font=(Theme.FONT_FAMILY, 9)
            )
            hk_label.pack(side=tk.LEFT)
            
            display_var = tk.StringVar(value='')
            display_label = ttk.Label(
                hk_frame, textvariable=display_var, width=8,
                foreground=Theme.SECONDARY, 
                background=Theme.SURFACE_CONTAINER, 
                font=(Theme.FONT_MONO, 10, 'bold')
            )
            display_label.pack(side=tk.LEFT, padx=(10, 5))
            
            change_btn = ttk.Button(
                hk_frame, text='修改', width=5,
                command=lambda a=action: self._start_hotkey_recording(a)
            )
            change_btn.pack(side=tk.RIGHT)
            
            self._hotkey_display[action] = display_var
            self._hotkey_buttons[action] = change_btn
        
        self._on_change_callback = None
        
        self._bind_mousewheel_recursive(self._inner_frame)
        self._canvas.after(100, self._update_scrollregion)
    
    def _update_scrollregion(self):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
    
    def _on_preset_selected(self, event):
        """预设选择回调"""
        preset_name = self._preset_var.get()
        for preset_id, preset in PRESETS.items():
            if preset['name'] == preset_name:
                if self._on_preset_callback:
                    self._on_preset_callback(preset_id)
                break
    
    def set_on_preset_callback(self, callback):
        """设置预设应用回调函数"""
        self._on_preset_callback = callback
    
    def select_preset(self, preset_id):
        """选中指定预设"""
        preset = PRESETS.get(preset_id)
        if preset:
            self._preset_var.set(preset['name'])
    
    def _on_parameter_change(self, value=None):
        """参数变化回调"""
        if self._on_change_callback:
            self._on_change_callback(self.get_parameters())
    
    def set_on_change_callback(self, callback):
        """设置参数变化回调函数"""
        self._on_change_callback = callback
    
    def get_parameters(self):
        """获取所有参数"""
        return {
            'sensitivity': self._sliders['sensitivity'].get_value(),
            'smoothing_factor': self._sliders['smoothing_factor'].get_value(),
            'deadzone': self._sliders['deadzone'].get_value(),
            'max_angle': self._sliders['max_angle'].get_value(),
            'dpi': self._sliders['dpi'].get_value(),
            'return_speed': self._sliders['return_speed'].get_value() / 100.0,
            'reverse_direction': self._reverse_var.get(),
            'assist_rate_window': self._sliders['assist_rate_window'].get_value() / 1000.0,
            'assist_rate_threshold': self._sliders['assist_rate_threshold'].get_value(),
            'linear_end': self._sliders['linear_end'].get_value(),
            'assist_threshold': self._sliders['assist_threshold'].get_value(),
            'assist_return_rate': self._sliders['assist_return_rate'].get_value() / 100.0,
            'near_center_threshold': self._sliders['near_center_threshold'].get_value(),
        }
    
    def set_parameters(self, params):
        """设置所有参数"""
        for key, value in params.items():
            if key == 'return_speed':
                value = value * 100.0
            elif key == 'assist_rate_window':
                value = value * 1000.0
            elif key == 'assist_return_rate':
                value = value * 100.0
            if key in self._sliders:
                self._sliders[key].set_value(value)
        if 'reverse_direction' in params:
            self._reverse_var.set(bool(params['reverse_direction']))
    
    def update_cm360_display(self, cm360_value: float):
        self._cm360_label.config(text=f'当前 ≈ {cm360_value:.1f} cm/360°')
    
    def set_hotkey_manager(self, hotkey_manager):
        """设置热键管理器"""
        self._hotkey_manager = hotkey_manager
        self.update_hotkey_display()
    
    def update_hotkey_display(self):
        """更新热键显示"""
        if self._hotkey_manager:
            for action in self._hotkey_actions:
                hotkey = self._hotkey_manager.get_hotkey(action)
                self._hotkey_display[action].set(hotkey)
    
    def _start_hotkey_recording(self, action):
        """开始录制热键"""
        if self._recording_action is not None:
            messagebox.showinfo('提示', '请先完成当前热键的录制')
            return
        
        self._recording_action = action
        self._hotkey_display[action].set('...')
        self._hotkey_buttons[action].config(text='取消', command=self._cancel_hotkey_recording)
        
        self.focus_set()
        self.bind('<Key>', self._on_key_press)
        self._cancel_id = self.after(10000, self._cancel_hotkey_recording)
    
    def _cancel_hotkey_recording(self):
        """取消热键录制"""
        if self._recording_action is not None:
            self.unbind('<Key>')
            if self._cancel_id:
                self.after_cancel(self._cancel_id)
            
            action = self._recording_action
            self._recording_action = None
            
            self._hotkey_buttons[action].config(text='修改', command=lambda a=action: self._start_hotkey_recording(a))
            self.update_hotkey_display()
    
    def _on_key_press(self, event):
        """处理按键录制"""
        if self._recording_action is None:
            return
        
        key = event.keysym
        
        if key in ['Escape']:
            self._cancel_hotkey_recording()
            return
        
        if len(key) > 1 and key not in ['space', 'Tab', 'Return', 'BackSpace', 'Delete', 'Insert', 'Home', 'End', 'Prior', 'Next']:
            key = key.lower()
        
        if self._hotkey_manager:
            success = self._hotkey_manager.set_hotkey(self._recording_action, key)
            if success:
                self._hotkey_display[self._recording_action].set(key)
                messagebox.showinfo('成功', f'快捷键已修改为: {key}')
            else:
                messagebox.showerror('错误', '设置快捷键失败')
        
        self._cancel_hotkey_recording()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('参数面板测试')
    root.geometry('320x600')
    root.configure(bg=Theme.SURFACE)
    
    panel = ParameterPanel(root)
    panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def on_params_change(params):
        print('参数变化:', params)
    
    panel.set_on_change_callback(on_params_change)
    
    root.mainloop()