"""状态栏模块，显示系统状态信息"""

import tkinter as tk
from tkinter import ttk
from .theme import Theme


class StatusBar(tk.Frame):
    """状态栏类"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.configure(bg=Theme.SURFACE)

        self._init_components()

    def _init_components(self):
        """初始化状态栏组件"""
        # Left: status LED + label
        left_frame = tk.Frame(self, bg=Theme.SURFACE)
        left_frame.pack(side=tk.LEFT, padx=16, pady=4)

        self.status_canvas = tk.Canvas(left_frame, width=12, height=12,
                                       bg=Theme.SURFACE, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 6))
        self._update_status_indicator(False)

        self.status_label = tk.Label(
            left_frame, text='未启动',
            fg=Theme.ON_SURFACE_VARIANT, bg=Theme.SURFACE,
            font=(Theme.FONT_FAMILY, 10)
        )
        self.status_label.pack(side=tk.LEFT)

        # Center: angle display
        center_frame = tk.Frame(self, bg=Theme.SURFACE)
        center_frame.pack(side=tk.LEFT, padx=30, pady=4)

        self.angle_label = tk.Label(
            center_frame, text='0.0°',
            fg=Theme.PRIMARY, bg=Theme.SURFACE,
            font=(Theme.FONT_MONO, 12, 'bold')
        )
        self.angle_label.pack(side=tk.LEFT)

        # Right: vJoy status
        right_frame = tk.Frame(self, bg=Theme.SURFACE)
        right_frame.pack(side=tk.RIGHT, padx=16, pady=4)

        self.gamepad_canvas = tk.Canvas(right_frame, width=10, height=10,
                                        bg=Theme.SURFACE, highlightthickness=0)
        self.gamepad_canvas.pack(side=tk.LEFT, padx=(0, 6))

        self.gamepad_status_text = tk.Label(
            right_frame, text='检测中',
            fg=Theme.ON_SURFACE_VARIANT, bg=Theme.SURFACE,
            font=(Theme.FONT_FAMILY, 10)
        )
        self.gamepad_status_text.pack(side=tk.LEFT)

    def _update_status_indicator(self, is_active):
        """更新状态指示灯"""
        self.status_canvas.delete('all')
        color = '#ffeb3b' if is_active else '#f44336'  # 黄色=开启，红色=关闭
        self.status_canvas.create_oval(1, 1, 11, 11, fill=color, outline='')

    def set_active(self, is_active):
        """设置激活状态"""
        self._update_status_indicator(is_active)
        self.status_label.config(text='运行中' if is_active else '未启动')
        self.status_label.config(foreground=Theme.PRIMARY if is_active else Theme.ON_SURFACE_VARIANT)

    def set_simulation_status(self, is_running):
        """设置模拟运行状态（兼容旧接口）"""
        self.set_active(is_running)

    def set_angle(self, angle):
        """设置角度显示"""
        self.angle_label.config(text=f'{angle:.1f}°')

    def set_sim_status(self, status_text, is_error=False):
        """设置模拟状态文本"""
        self.status_label.config(text=status_text)
        self.status_label.config(foreground=Theme.ERROR if is_error else Theme.ON_SURFACE)

    def set_vjoy_status(self, available, status_text):
        """设置手柄状态显示"""
        self.gamepad_canvas.delete('all')
        color = '#4caf50' if available else '#f44336'  # 绿色=已连接，红色=断开
        self.gamepad_canvas.create_oval(1, 1, 9, 9, fill=color, outline='')
        self.gamepad_status_text.config(text=status_text)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('状态栏测试')
    root.geometry('500x60')
    root.configure(bg=Theme.SURFACE)

    status_bar = StatusBar(root)
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def toggle_status():
        current = status_bar.status_label.cget('text') == '运行中'
        status_bar.set_active(not current)

    btn = ttk.Button(root, text='切换状态', command=toggle_status)
    btn.pack(pady=10)

    root.mainloop()
