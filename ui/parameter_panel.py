"""参数调节面板模块"""

import tkinter as tk
from tkinter import ttk
from config.presets import PRESETS


class ParameterSlider(tk.Frame):
    """参数滑块组件"""
    
    def __init__(self, parent, label_text, min_val, max_val, default_val, 
                 resolution=0.1, unit='', callback=None):
        super().__init__(parent)
        
        self._callback = callback
        self._unit = unit
        
        # 配置背景
        self.configure(bg='#1a1a2e')
        
        # 标签
        self.label = ttk.Label(self, text=label_text, foreground='#ffffff', background='#1a1a2e')
        self.label.pack(fill=tk.X, pady=(5, 2))
        
        # 滑块
        self.slider = ttk.Scale(
            self, from_=min_val, to=max_val, value=default_val,
            orient=tk.HORIZONTAL, command=self._on_slider_change
        )
        self.slider.pack(fill=tk.X, pady=(0, 2))
        
        # 数值显示
        value_frame = ttk.Frame(self)
        value_frame.pack(fill=tk.X)
        
        self.value_label = ttk.Label(
            value_frame, text=f'{default_val:.1f}{unit}', 
            foreground='#4a90d9', background='#1a1a2e', font=('Arial', 10, 'bold')
        )
        self.value_label.pack(side=tk.LEFT)
    
    def _on_slider_change(self, value):
        """滑块值变化事件"""
        float_val = float(value)
        self.value_label.config(text=f'{float_val:.1f}{self._unit}')
        if self._callback:
            self._callback(float_val)
    
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
        
        # 配置背景
        self.configure(bg='#1a1a2e')
        
        # 标题
        title_label = ttk.Label(
            self, text='参数设置', 
            foreground='#ffffff', background='#1a1a2e',
            font=('Arial', 14, 'bold')
        )
        title_label.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # 预设选择
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        preset_label = ttk.Label(
            preset_frame, text='游戏预设', 
            foreground='#ffffff', background='#1a1a2e'
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
        
        # 参数滑块列表
        self._sliders = {}
        
        # 预设应用回调
        self._on_preset_callback = None
        
        # 灵敏度滑块 (0.1 - 5.0)
        self._sliders['sensitivity'] = ParameterSlider(
            self, '灵敏度', 0.1, 5.0, 1.0, resolution=0.1, unit='x',
            callback=self._on_parameter_change
        )
        self._sliders['sensitivity'].pack(fill=tk.X, padx=10)
        
        # 平滑系数滑块 (0.0 - 0.99)
        self._sliders['smoothing_factor'] = ParameterSlider(
            self, '平滑系数', 0.0, 0.99, 0.3, resolution=0.01, unit='',
            callback=self._on_parameter_change
        )
        self._sliders['smoothing_factor'].pack(fill=tk.X, padx=10)
        
        # 死区滑块 (0 - 20)
        self._sliders['deadzone'] = ParameterSlider(
            self, '死区', 0, 20, 3, resolution=1, unit='px',
            callback=self._on_parameter_change
        )
        self._sliders['deadzone'].pack(fill=tk.X, padx=10)
        
        # 最大舵角滑块 (30 - 180)
        self._sliders['max_angle'] = ParameterSlider(
            self, '最大舵角', 30, 180, 90, resolution=1, unit='°',
            callback=self._on_parameter_change
        )
        self._sliders['max_angle'].pack(fill=tk.X, padx=10)
        
        # 回正速度滑块 (0 - 100)
        self._sliders['return_speed'] = ParameterSlider(
            self, '回正速度', 0, 100, 0, resolution=1, unit='%',
            callback=self._on_parameter_change
        )
        self._sliders['return_speed'].pack(fill=tk.X, padx=10)
        
        # 灵敏度曲线选择
        curve_frame = ttk.Frame(self)
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
        
        # 回调函数
        self._on_change_callback = None
    
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
            'return_speed': self._sliders['return_speed'].get_value() / 100.0,
            'curve_type': self._curve_var.get()
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
