"""系统托盘管理器"""
import tkinter as tk
from PIL import Image, ImageDraw


class TrayManager:
    """系统托盘管理器"""
    
    def __init__(self, root, app=None):
        """
        初始化托盘管理器
        
        Args:
            root: Tkinter主窗口
            app: 应用程序实例
        """
        self.root = root
        self.app = app
        self.tray_icon = None
        self.is_active = False
        self._use_pystray = False
        
        # 创建图标
        self._create_icons()
        
        # 初始化托盘
        self._init_tray()
    
    def _create_icons(self):
        """创建绿色（开启）和红色（关闭）图标"""
        # 创建32x32像素的图标
        size = (32, 32)
        
        # 绿色图标（开启状态）
        green_image = Image.new('RGB', size, (0, 0, 0))
        green_draw = ImageDraw.Draw(green_image)
        green_draw.ellipse((2, 2, 30, 30), fill=(0, 200, 0), outline=(0, 255, 0), width=2)
        self.green_icon = green_image
        
        # 红色图标（关闭状态）
        red_image = Image.new('RGB', size, (0, 0, 0))
        red_draw = ImageDraw.Draw(red_image)
        red_draw.ellipse((2, 2, 30, 30), fill=(200, 0, 0), outline=(255, 0, 0), width=2)
        self.red_icon = red_image
    
    def _init_tray(self):
        """初始化系统托盘"""
        try:
            # 尝试使用pystray库
            self._init_with_pystray()
        except ImportError:
            # 如果没有pystray，使用tkinter方案
            self._init_with_tkinter()
    
    def _init_with_pystray(self):
        """使用pystray库初始化托盘"""
        import pystray
        from pystray import MenuItem as item
        
        def on_double_click(icon, item):
            """双击托盘图标事件"""
            self.show_window()
        
        def on_show_window(icon, item):
            """打开主窗口"""
            self.show_window()
        
        def on_toggle(icon, item):
            """切换模拟状态"""
            if self.app:
                self.app.on_toggle()
        
        def on_exit(icon, item):
            """退出程序"""
            if self.app:
                self.app.cleanup()
            icon.stop()
            self.root.quit()
            self.root.destroy()
        
        # 创建菜单
        menu = pystray.Menu(
            item('打开主窗口', on_show_window),
            item('切换模拟状态', on_toggle),
            item('退出程序', on_exit)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            'LinearMouseSim',
            self.red_icon,
            'LinearMouseSim - 方向盘模拟器',
            menu
        )
        
        # 设置双击事件
        self.tray_icon.icon = self.red_icon
        
        # 在后台线程中运行托盘
        import threading
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        self._use_pystray = True
    
    def _init_with_tkinter(self):
        """使用tkinter方案初始化托盘（Windows）"""
        # 创建一个隐藏的顶层窗口用于托盘消息
        self._tray_window = tk.Toplevel(self.root)
        self._tray_window.withdraw()
        
        # 使用ctypes实现Windows托盘
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            
            # 托盘数据结构
            class NOTIFYICONDATA(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.DWORD),
                    ('hWnd', wintypes.HWND),
                    ('uID', wintypes.UINT),
                    ('uFlags', wintypes.UINT),
                    ('uCallbackMessage', wintypes.UINT),
                    ('hIcon', wintypes.HICON),
                    ('szTip', ctypes.c_wchar * 128),
                    ('dwState', wintypes.DWORD),
                    ('dwStateMask', wintypes.DWORD),
                    ('szInfo', ctypes.c_wchar * 256),
                    ('uVersion', wintypes.UINT),
                    ('szInfoTitle', ctypes.c_wchar * 64),
                    ('dwInfoFlags', wintypes.DWORD),
                    ('guidItem', wintypes.GUID),
                    ('hBalloonIcon', wintypes.HICON)
                ]
            
            # 获取窗口句柄
            hwnd = int(self._tray_window.frame(), 16)
            
            # 创建HICON
            hicon = self._image_to_hicon(self.red_icon)
            
            # 设置托盘数据
            nid = NOTIFYICONDATA()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
            nid.hWnd = hwnd
            nid.uID = 1
            nid.uFlags = 0x00000001 | 0x00000002 | 0x00000004  # NIF_ICON | NIF_MESSAGE | NIF_TIP
            nid.uCallbackMessage = 0x0400 + 100  # WM_USER + 100
            nid.hIcon = hicon
            nid.szTip = 'LinearMouseSim - 方向盘模拟器'
            
            # 添加托盘图标
            user32.Shell_NotifyIconW(0, ctypes.byref(nid))
            
            # 保存数据
            self._tray_nid = nid
            self._tray_hicon = hicon
            
            # 绑定消息处理
            self._tray_window.bind('<Message>', self._on_tray_message)
            
        except Exception:
            # 如果失败，不使用托盘
            pass
    
    def _image_to_hicon(self, image):
        """将PIL图像转换为Windows HICON"""
        import ctypes
        import tempfile
        import os
        
        # 将图像保存为临时BMP文件
        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as f:
            temp_path = f.name
        
        try:
            image.save(temp_path)
            
            # 加载图标
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # 获取模块句柄
            hmodule = kernel32.GetModuleHandleW(None)
            
            # 加载图标（使用LoadImage）
            hicon = user32.LoadImageW(
                hmodule,
                temp_path,
                1,  # IMAGE_ICON
                32, 32,
                0x00000010  # LR_LOADFROMFILE
            )
            
            return hicon
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _on_tray_message(self, event):
        """处理托盘消息"""
        lparam = event.lparam
        
        # WM_LBUTTONDBLCLK = 0x0203
        if lparam == 0x0203:
            self.show_window()
        # WM_RBUTTONUP = 0x0205
        elif lparam == 0x0205:
            self._show_context_menu()
    
    def _show_context_menu(self):
        """显示右键菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label='打开主窗口', command=self.show_window)
        
        state_text = '关闭模拟' if self.is_active else '开启模拟'
        menu.add_command(label=state_text, command=self._on_toggle)
        
        menu.add_separator()
        menu.add_command(label='退出程序', command=self._on_exit)
        
        # 获取鼠标位置显示菜单
        try:
            import ctypes
            cursor_pos = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
            menu.tk_popup(cursor_pos.x, cursor_pos.y)
        except Exception:
            menu.tk_popup(0, 0)
    
    def _on_toggle(self):
        """切换模拟状态"""
        if self.app:
            self.app.on_toggle()
    
    def _on_exit(self):
        """退出程序"""
        if self.app:
            self.app.cleanup()
        self.cleanup()
        self.root.quit()
        self.root.destroy()
    
    def update_status(self, is_active):
        """更新托盘图标状态"""
        self.is_active = is_active
        
        if self._use_pystray and self.tray_icon:
            # 使用pystray更新图标
            icon = self.green_icon if is_active else self.red_icon
            self.tray_icon.icon = icon
        else:
            # 更新Windows托盘图标（ctypes方式）
            try:
                import ctypes
                user32 = ctypes.windll.user32
                
                # 创建新图标
                new_hicon = self._image_to_hicon(self.green_icon if is_active else self.red_icon)
                
                if new_hicon:
                    # 更新图标
                    self._tray_nid.hIcon = new_hicon
                    user32.Shell_NotifyIconW(1, ctypes.byref(self._tray_nid))  # NIM_MODIFY
                    
                    # 销毁旧图标
                    if self._tray_hicon:
                        user32.DestroyIcon(self._tray_hicon)
                    self._tray_hicon = new_hicon
            except Exception:
                pass
    
    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self):
        """隐藏主窗口到托盘"""
        self.root.withdraw()
    
    def cleanup(self):
        """清理托盘资源"""
        if self._use_pystray and self.tray_icon:
            self.tray_icon.stop()
        else:
            # 删除Windows托盘图标
            try:
                import ctypes
                user32 = ctypes.windll.user32
                user32.Shell_NotifyIconW(2, ctypes.byref(self._tray_nid))  # NIM_DELETE
                if self._tray_hicon:
                    user32.DestroyIcon(self._tray_hicon)
            except Exception:
                pass
