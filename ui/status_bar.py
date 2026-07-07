"""状态栏模块，显示系统状态信息"""

import tkinter as tk
from tkinter import ttk
from .theme import Theme


class StatusBar(tk.Frame):
    """状态栏类"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(bg=Theme.SURFACE_CONTAINER_LOW)
        
        self._init_components()
    
    def _init_components(self):
        """初始化状态栏组件"""
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.status_label = ttk.Label(
            left_frame, text='状态:', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 10)
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_canvas = tk.Canvas(left_frame, width=24, height=24, bg=Theme.SURFACE_CONTAINER_LOW, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT)
        self._update_status_indicator(False)
        
        gamepad_frame = ttk.Frame(self)
        gamepad_frame.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        
        self.gamepad_label = ttk.Label(
            gamepad_frame, text='手柄:', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 10)
        )
        self.gamepad_label.pack(side=tk.LEFT, padx=(0, 4))
        
        self.gamepad_canvas = tk.Canvas(gamepad_frame, width=16, height=16, bg=Theme.SURFACE_CONTAINER_LOW, highlightthickness=0)
        self.gamepad_canvas.pack(side=tk.LEFT)
        
        self.gamepad_status_text = ttk.Label(
            gamepad_frame, text='检测中', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 10)
        )
        self.gamepad_status_text.pack(side=tk.LEFT, padx=(4, 0))
        
        center_frame = ttk.Frame(self)
        center_frame.pack(side=tk.LEFT, padx=30, pady=5)
        
        self.angle_label = ttk.Label(
            center_frame, text='当前角度:', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 10)
        )
        self.angle_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.angle_value = ttk.Label(
            center_frame, text='0.0°', 
            foreground=Theme.SECONDARY, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_MONO, 16, 'bold')
        )
        self.angle_value.pack(side=tk.LEFT)
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, padx=20, pady=5)
        
        self.sim_status_label = ttk.Label(
            right_frame, text='模拟:', 
            foreground=Theme.ON_SURFACE_VARIANT, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 10)
        )
        self.sim_status_label.pack(side=tk.LEFT, padx=(0, 8))
        
        self.sim_status_value = ttk.Label(
            right_frame, text='未启动', 
            foreground=Theme.ERROR, 
            background=Theme.SURFACE_CONTAINER_LOW, 
            font=(Theme.FONT_FAMILY, 11, 'bold')
        )
        self.sim_status_value.pack(side=tk.LEFT)
    
    def _update_status_indicator(self, is_active):
        """更新状态指示灯"""
        self.status_canvas.delete('all')
        
        if is_active:
            color = Theme.TERTIARY
            glow_color = '#00cc6a'
        else:
            color = Theme.ERROR
            glow_color = '#cc3333'
        
        self.status_canvas.create_oval(2, 2, 22, 22, fill=glow_color, outline='', stipple='gray50')
        self.status_canvas.create_oval(5, 5, 19, 19, fill=color, outline=Theme.OUTLINE_VARIANT, width=2)
    
    def set_active(self, is_active):
        """设置激活状态"""
        self._update_status_indicator(is_active)
        self.sim_status_value.config(text='运行中' if is_active else '未启动')
        self.sim_status_value.config(foreground=Theme.TERTIARY if is_active else Theme.ERROR)
    
    def set_angle(self, angle):
        """设置角度显示"""
        self.angle_value.config(text=f'{angle:.1f}°')
    
    def set_sim_status(self, status_text, is_error=False):
        """设置模拟状态文本"""
        self.sim_status_value.config(text=status_text)
        self.sim_status_value.config(foreground=Theme.ERROR if is_error else Theme.ON_SURFACE)
    
    def set_vjoy_status(self, available, status_text):
        """设置手柄状态显示"""
        self.gamepad_canvas.delete('all')
        if available:
            color = Theme.TERTIARY
            glow = '#00cc6a'
        else:
            color = Theme.ERROR
            glow = '#cc3333'
        
        self.gamepad_canvas.create_oval(1, 1, 15, 15, fill=glow, outline='', stipple='gray50')
        self.gamepad_canvas.create_oval(3, 3, 13, 13, fill=color, outline=Theme.OUTLINE_VARIANT, width=2)
        self.gamepad_status_text.config(text=status_text)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('状态栏测试')
    root.geometry('500x80')
    root.configure(bg=Theme.SURFACE)
    
    status_bar = StatusBar(root)
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def toggle_status():
        current = status_bar.sim_status_value.cget('text') == '运行中'
        status_bar.set_active(not current)
    
    btn = ttk.Button(root, text='切换状态', command=toggle_status)
    btn.pack(pady=20)
    
    root.mainloop()