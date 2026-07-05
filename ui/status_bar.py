"""状态栏模块，显示系统状态信息"""

import tkinter as tk
from tkinter import ttk


class StatusBar(tk.Frame):
    """状态栏类"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 配置样式
        self.configure(bg='#1a1a2e')
        
        # 初始化组件
        self._init_components()
    
    def _init_components(self):
        """初始化状态栏组件"""
        # 左侧：开关状态指示灯
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, padx=15, pady=5)
        
        self.status_label = ttk.Label(left_frame, text='状态:', foreground='#ffffff', background='#1a1a2e')
        self.status_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态指示灯
        self.status_canvas = tk.Canvas(left_frame, width=16, height=16, bg='#1a1a2e', highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT)
        self._update_status_indicator(False)
        
        # 中间：角度显示
        center_frame = ttk.Frame(self)
        center_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.angle_label = ttk.Label(center_frame, text='角度:', foreground='#ffffff', background='#1a1a2e')
        self.angle_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.angle_value = ttk.Label(center_frame, text='0.0°', foreground='#4a90d9', background='#1a1a2e', font=('Arial', 12, 'bold'))
        self.angle_value.pack(side=tk.LEFT)
        
        # 右侧：模拟状态
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, padx=15, pady=5)
        
        self.sim_status_label = ttk.Label(right_frame, text='模拟状态:', foreground='#ffffff', background='#1a1a2e')
        self.sim_status_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.sim_status_value = ttk.Label(right_frame, text='未启动', foreground='#e94560', background='#1a1a2e')
        self.sim_status_value.pack(side=tk.LEFT)
    
    def _update_status_indicator(self, is_active):
        """更新状态指示灯"""
        self.status_canvas.delete('all')
        color = '#00ff00' if is_active else '#ff0000'
        # 绘制圆形指示灯
        self.status_canvas.create_oval(2, 2, 14, 14, fill=color, outline='#333333')
    
    def set_active(self, is_active):
        """设置激活状态"""
        self._update_status_indicator(is_active)
        self.sim_status_value.config(text='运行中' if is_active else '未启动')
        self.sim_status_value.config(foreground='#00ff00' if is_active else '#e94560')
    
    def set_angle(self, angle):
        """设置角度显示"""
        self.angle_value.config(text=f'{angle:.1f}°')
    
    def set_sim_status(self, status_text, is_error=False):
        """设置模拟状态文本"""
        self.sim_status_value.config(text=status_text)
        self.sim_status_value.config(foreground='#e94560' if is_error else '#ffffff')


if __name__ == '__main__':
    # 测试代码
    root = tk.Tk()
    root.title('状态栏测试')
    root.geometry('400x100')
    root.configure(bg='#0f0f1a')
    
    status_bar = StatusBar(root)
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    # 测试状态切换
    def toggle_status():
        current = status_bar.sim_status_value.cget('text') == '运行中'
        status_bar.set_active(not current)
    
    btn = ttk.Button(root, text='切换状态', command=toggle_status)
    btn.pack(pady=20)
    
    root.mainloop()
