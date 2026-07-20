import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position():
    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def set_mouse_position(x, y):
    user32.SetCursorPos(x, y)

def get_screen_center():
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    return screen_width // 2, screen_height // 2

class ClipCursorManager:
    def __init__(self):
        self.original_rect = ctypes.wintypes.RECT()

    def lock_to_center(self):
        center_x, center_y = get_screen_center()
        rect = ctypes.wintypes.RECT()
        rect.left = center_x - 1
        rect.top = center_y - 1
        rect.right = center_x + 1
        rect.bottom = center_y + 1
        user32.GetClipCursor(ctypes.byref(self.original_rect))
        user32.ClipCursor(ctypes.byref(rect))

    def unlock(self):
        user32.ClipCursor(ctypes.byref(self.original_rect))

def show_cursor():
    """显示鼠标光标"""
    user32.ShowCursor(True)

def hide_cursor():
    """隐藏鼠标光标"""
    user32.ShowCursor(False)

def release_cursor_safety():
    user32.ShowCursor(True)
    user32.ClipCursor(None)
