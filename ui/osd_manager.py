import tkinter as tk
import threading
import time

class OSDManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.osd_enabled = self.config_manager.get('app.osd_enabled', False)
        self.osd_duration = self.config_manager.get('app.osd_duration', 2000)
        self._window = None
        self._timer = None
        self._lock = threading.Lock()
        self._root = None
    
    def set_root(self, root):
        """设置主窗口的 Tk 根实例，避免创建第二个根窗口"""
        self._root = root
    
    def _ensure_root(self):
        if self._root is None:
            self._root = tk.Tk()
            self._root.withdraw()
        return self._root
    
    def _create_window(self):
        if self._window is not None:
            return
        
        root = self._ensure_root()
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        window_width = 300
        window_height = 80
        pos_x = (screen_width - window_width) // 2
        pos_y = screen_height // 3
        
        self._window = tk.Toplevel(root)
        self._window.title('OSD')
        self._window.geometry(f'{window_width}x{window_height}+{pos_x}+{pos_y}')
        self._window.overrideredirect(True)
        self._window.attributes('-topmost', True)
        self._window.attributes('-alpha', 0.85)
        self._window.config(bg='#000000')
        
        self._text_label = tk.Label(
            self._window,
            text='',
            bg='#000000',
            fg='#ffffff',
            font=('Arial', 24, 'bold')
        )
        self._text_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _show_text(self, text, duration=None):
        if not self.osd_enabled:
            return
        
        with self._lock:
            self._create_window()
            
            if self._timer is not None:
                self._window.after_cancel(self._timer)
            
            self._text_label.config(text=text)
            self._window.deiconify()
            self._window.lift()
            
            show_duration = duration if duration is not None else self.osd_duration
            self._timer = self._window.after(show_duration, self._hide_window)
    
    def _hide_window(self):
        with self._lock:
            if self._window is not None:
                self._window.withdraw()
            self._timer = None
    
    def show_sensitivity(self, sensitivity):
        text = f'灵敏度: {sensitivity:.2f}'
        self._show_text(text)
    
    def show_temp_sensitivity(self, enabled: bool):
        text = '临时降敏: 开' if enabled else '临时降敏: 关'
        self._show_text(text)
    
    def show_toggle_state(self, state):
        if state.value == 'ON':
            text = '模拟已开启'
        else:
            text = '模拟已关闭'
        self._show_text(text)
    
    def update_config(self):
        self.osd_enabled = self.config_manager.get('app.osd_enabled', False)
        self.osd_duration = self.config_manager.get('app.osd_duration', 2000)
    
    def close(self):
        with self._lock:
            if self._timer is not None:
                try:
                    self._window.after_cancel(self._timer)
                except Exception:
                    pass
                self._timer = None
            if self._window is not None:
                self._window.destroy()
                self._window = None
            if self._root is not None:
                self._root.destroy()
                self._root = None