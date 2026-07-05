"""参数调节面板模块"""

import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
from config.presets import PRESETS


class ParameterSlider(tk.Frame):
    """参数滑块组件"""
    
    def __init__(self, parent, label_text, min_val, max_val, default_val, 
                 resolution=0.1, unit='', callback=None, snap_points=None, snap_tolerance=15):
        super().__init__(parent)
        
        self._callback = callback
        self._unit = unit
        self._snap_points = snap_points or []
        self._snap_tolerance = snap_tolerance
        self._min_val = min_val
        self._max_val = max_val
        
        self.configure(bg='#16162a')
        
        self.label = ttk.Label(self, text=label_text, foreground='#8888aa', background='#16162a', font=('Segoe UI', 10))
        self.label.pack(fill=tk.X, pady=(8, 3))
        
        self.slider_container = tk.Frame(self, bg='#16162a')
        self.slider_container.pack(fill=tk.X, pady=(0, 2))
        
        self._snap_canvas = tk.Canvas(self.slider_container, bg='#16162a', highlightthickness=0, height=14)
        self._snap_canvas.pack(fill=tk.X, pady=(0, 0))
        
        self.slider = ttk.Scale(
            self.slider_container, from_=min_val, to=max_val, value=default_val,
            orient=tk.HORIZONTAL, command=self._on_slider_change
        )
        self.slider.pack(fill=tk.X, pady=(0, 2))
        
        self.slider.bind('<ButtonRelease-1>', self._on_slider_release)
        
        value_frame = ttk.Frame(self)
        value_frame.pack(fill=tk.X)
        
        self.value_label = ttk.Label(
            value_frame, text=f'{default_val:.1f}{unit}', 
            foreground='#4a90d9', background='#16162a', font=('Segoe UI', 11, 'bold')
        )
        self.value_label.pack(side=tk.LEFT)
        
        self.slider.after(100, self._draw_snap_markers)
    
    def _on_slider_change(self, value):
        """滑块值变化事件"""
        float_val = float(value)
        self.value_label.config(text=f'{float_val:.1f}{self._unit}')
        if self._callback:
            self._callback(float_val)
    
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
                # 绘制三角形标记
                self._snap_canvas.create_polygon(
                    x_pos, 0,
                    x_pos - 4, 8,
                    x_pos + 4, 8,
                    fill='#e94560', outline=''
                )
                # 绘制角度值标签
                self._snap_canvas.create_text(
                    x_pos, 10,
                    text=f'{int(point)}', fill='#e94560', font=('Arial', 7)
                )
    
    def get_value(self):
        """获取当前值"""
        return self.slider.get()
    
    def set_value(self, value):
        """设置值"""
        self.slider.set(value)
        self.value_label.config(text=f'{value:.1f}{self._unit}')


class ParameterPanel(tk.Frame):
    """参数调节面板类"""
    
    CURVE_TYPES = [
        ('线性', 'linear'),
        ('指数', 'exponential'),
        ('对数', 'logarithmic'),
        ('S型', 's_curve')
    ]
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(bg='#16162a')
        
        self._canvas = tk.Canvas(self, bg='#16162a', highlightthickness=0)
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
            foreground='#ffffff', background='#16162a',
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(fill=tk.X, pady=(15, 15), padx=10)
        
        preset_frame = ttk.Frame(inner)
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        preset_label = ttk.Label(
            preset_frame, text='游戏预设', 
            foreground='#8888aa', background='#16162a',
            font=('Segoe UI', 10)
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
        self._sliders['sensitivity'].pack(fill=tk.X, padx=10)
        
        self._sliders['smoothing_factor'] = ParameterSlider(
            inner, '平滑系数', 0.0, 0.99, 0.3, resolution=0.01, unit='',
            callback=self._on_parameter_change
        )
        self._sliders['smoothing_factor'].pack(fill=tk.X, padx=10)
        
        self._sliders['deadzone'] = ParameterSlider(
            inner, '死区', 0, 20, 3, resolution=1, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['deadzone'].pack(fill=tk.X, padx=10)
        
        self._sliders['max_angle'] = ParameterSlider(
            inner, '最大舵角', 30, 720, 90, resolution=1, unit='°',
            callback=self._on_parameter_change,
            snap_points=[180, 360, 540, 720],
            snap_tolerance=15
        )
        self._sliders['max_angle'].pack(fill=tk.X, padx=10)
        
        self._sliders['dpi'] = ParameterSlider(
            inner, '鼠标DPI', 100, 25600, 800, resolution=100, unit='',
            callback=self._on_parameter_change
        )
        self._sliders['dpi'].pack(fill=tk.X, padx=10)
        
        self._sliders['return_speed'] = ParameterSlider(
            inner, '回正速度', 0, 100, 0, resolution=1, unit='%',
            callback=self._on_parameter_change
        )
        self._sliders['return_speed'].pack(fill=tk.X, padx=10)
        
        self._reverse_var = tk.BooleanVar(value=False)
        self._reverse_checkbox = ttk.Checkbutton(
            inner, text='反转方向盘方向（鼠标左移=顺时针，右移=逆时针）',
            variable=self._reverse_var, command=self._on_parameter_change
        )
        self._reverse_checkbox.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        curve_frame = ttk.Frame(inner)
        curve_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        curve_label = ttk.Label(
            curve_frame, text='灵敏度曲线', 
            foreground='#ffffff', background='#1a1a2e'
        )
        curve_label.pack(fill=tk.X, pady=(5, 5))
        
        self._curve_var = tk.StringVar(value='linear')
        self._curve_frame = ttk.Frame(curve_frame)
        self._curve_frame.pack(fill=tk.X)
        
        for text, value in self.CURVE_TYPES:
            rb = ttk.Radiobutton(
                self._curve_frame, text=text, variable=self._curve_var, 
                value=value, command=self._on_parameter_change
            )
            rb.pack(side=tk.LEFT, padx=(0, 10))
        
        self._hotkey_frame = ttk.Frame(inner)
        self._hotkey_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        hotkey_label = ttk.Label(
            self._hotkey_frame, text='快捷键配置', 
            foreground='#8888aa', background='#16162a',
            font=('Segoe UI', 10)
        )
        hotkey_label.pack(fill=tk.X, pady=(5, 5))
        
        self._hotkey_actions = {
            'toggle': '切换模拟',
            'increase_sensitivity': '增加灵敏度',
            'decrease_sensitivity': '降低灵敏度',
            'reset_steering': '重置方向盘',
            'sensitivity_preset_1': '灵敏度预设1',
            'sensitivity_preset_2': '灵敏度预设2',
            'sensitivity_preset_3': '灵敏度预设3',
            'cycle_curve': '切换曲线',
            'wheel_adjust': '滚轮调节键'
        }
        
        for action, label_text in self._hotkey_actions.items():
            hk_frame = ttk.Frame(self._hotkey_frame)
            hk_frame.pack(fill=tk.X, pady=(2, 2))
            
            hk_label = ttk.Label(
                hk_frame, text=label_text, width=12,
                foreground='#cccccc', background='#16162a', font=('Segoe UI', 9)
            )
            hk_label.pack(side=tk.LEFT)
            
            display_var = tk.StringVar(value='')
            display_label = ttk.Label(
                hk_frame, textvariable=display_var, width=6,
                foreground='#4a90d9', background='#16162a', font=('Segoe UI', 10, 'bold')
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
            'curve_type': self._curve_var.get(),
            'reverse_direction': self._reverse_var.get()
        }
    
    def set_parameters(self, params):
        """设置所有参数"""
        for key, value in params.items():
            if key == 'return_speed':
                value = value * 100.0
            if key in self._sliders:
                self._sliders[key].set_value(value)
        if 'curve_type' in params:
            self._curve_var.set(params['curve_type'])
        if 'reverse_direction' in params:
            self._reverse_var.set(bool(params['reverse_direction']))
    
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
    # 测试代码
    root = tk.Tk()
    root.title('参数面板测试')
    root.geometry('300x500')
    root.configure(bg='#0f0f1a')
    
    panel = ParameterPanel(root)
    panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 测试回调
    def on_params_change(params):
        print('参数变化:', params)
    
    panel.set_on_change_callback(on_params_change)
    
    root.mainloop()
