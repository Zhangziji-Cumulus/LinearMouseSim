import wx
import threading
import time

class OSDManager:
    """
    OSD (On-Screen Display) 屏幕显示管理器
    
    功能：
    1. 灵敏度变化时屏幕中央显示当前灵敏度值
    2. 曲线切换时显示当前曲线类型
    3. 模拟开关状态变化时显示状态提示
    4. 配置可控制OSD显示时长和是否启用
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.osd_enabled = self.config_manager.get('app.osd_enabled', True)
        self.osd_duration = self.config_manager.get('app.osd_duration', 2000)
        self._window = None
        self._timer = None
        self._lock = threading.Lock()
        self._app = None
        
        # 曲线类型中文映射
        self.curve_type_map = {
            'linear': '线性',
            'exponential': '指数',
            'logarithmic': '对数',
            's_curve': 'S型'
        }
    
    def _ensure_app(self):
        """确保wxPython应用存在"""
        if self._app is None:
            self._app = wx.App(False)
        return self._app
    
    def _create_window(self):
        """创建OSD显示窗口"""
        if self._window is not None:
            return
        
        app = self._ensure_app()
        
        # 获取屏幕尺寸
        screen = wx.GetDisplaySize()
        screen_width, screen_height = screen
        
        # 计算窗口位置（屏幕中央）
        window_width = 300
        window_height = 80
        pos_x = (screen_width - window_width) // 2
        pos_y = screen_height // 3
        
        # 创建无边框顶层窗口
        self._window = wx.Frame(
            None,
            title='OSD',
            pos=(pos_x, pos_y),
            size=(window_width, window_height),
            style=wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.FRAME_SHAPED
        )
        
        # 设置窗口透明背景
        self._window.SetTransparent(230)
        
        # 创建面板
        panel = wx.Panel(self._window)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0, 180))
        
        # 创建文本控件
        self._text_label = wx.StaticText(
            panel,
            label='',
            style=wx.ALIGN_CENTER
        )
        
        # 设置字体和颜色
        font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self._text_label.SetFont(font)
        self._text_label.SetForegroundColour(wx.Colour(255, 255, 255))
        
        # 创建布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._text_label, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(sizer)
        
        # 设置窗口形状为圆角矩形
        self._set_window_shape()
    
    def _set_window_shape(self):
        """设置窗口为圆角矩形形状"""
        if self._window is None:
            return
        
        width, height = self._window.GetSize()
        bitmap = wx.Bitmap(width, height)
        dc = wx.MemoryDC(bitmap)
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
        
        # 绘制圆角矩形
        radius = 10
        dc.DrawRoundedRectangle(0, 0, width, height, radius)
        
        self._window.SetShape(wx.Region(bitmap))
    
    def _show_text(self, text, duration=None):
        """显示OSD文本"""
        if not self.osd_enabled:
            return
        
        with self._lock:
            self._create_window()
            
            if self._timer is not None:
                self._timer.Stop()
            
            self._text_label.SetLabel(text)
            self._window.Layout()
            self._window.Show(True)
            self._window.Raise()
            
            # 设置自动隐藏定时器
            show_duration = duration if duration is not None else self.osd_duration
            self._timer = wx.Timer(self._window)
            self._window.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
            self._timer.Start(show_duration, oneShot=True)
    
    def _on_timer(self, event):
        """定时器触发，隐藏窗口"""
        with self._lock:
            if self._window is not None:
                self._window.Show(False)
            if self._timer is not None:
                self._timer.Stop()
    
    def show_sensitivity(self, sensitivity):
        """显示灵敏度变化提示"""
        text = f'灵敏度: {sensitivity:.2f}'
        self._show_text(text)
    
    def show_curve_type(self, curve_type):
        """显示曲线类型变化提示"""
        curve_name = self.curve_type_map.get(curve_type, curve_type)
        text = f'曲线: {curve_name}'
        self._show_text(text)
    
    def show_toggle_state(self, state):
        """显示模拟开关状态提示"""
        if state == 'ON':
            text = '模拟已开启'
        else:
            text = '模拟已关闭'
        self._show_text(text)
    
    def update_config(self):
        """更新配置"""
        self.osd_enabled = self.config_manager.get('app.osd_enabled', True)
        self.osd_duration = self.config_manager.get('app.osd_duration', 2000)
    
    def close(self):
        """关闭OSD窗口"""
        with self._lock:
            if self._timer is not None:
                self._timer.Stop()
                self._timer = None
            if self._window is not None:
                self._window.Destroy()
                self._window = None

if __name__ == '__main__':
    # 测试代码
    from config.config_manager import ConfigManager
    
    config = ConfigManager()
    osd = OSDManager(config)
    
    # 显示灵敏度
    osd.show_sensitivity(2.0)
    time.sleep(2)
    
    # 显示曲线类型
    osd.show_curve_type('exponential')
    time.sleep(2)
    
    # 显示开关状态
    osd.show_toggle_state('ON')
    time.sleep(2)
    
    # 显示关闭状态
    osd.show_toggle_state('OFF')
    time.sleep(2)
    
    osd.close()
