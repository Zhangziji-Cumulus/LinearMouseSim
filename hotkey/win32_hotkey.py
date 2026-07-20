"""
Win32 原生热键管理器
使用 RegisterHotKey API，能在全屏独占模式游戏中捕获按键

关键设计：窗口创建、热键注册、消息循环全部在同一个后台线程中执行。
RegisterHotKey 将 WM_HOTKEY 发送到创建窗口的线程，
所以这三件事必须在同一线程。
"""
import ctypes
import ctypes.wintypes
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID_BASE = 1


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
    ]


user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
user32.RegisterClassW.restype = ctypes.wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    ctypes.wintypes.DWORD, ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR,
    ctypes.wintypes.DWORD, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.wintypes.HWND,
    ctypes.wintypes.HMENU, ctypes.wintypes.HINSTANCE, ctypes.c_void_p,
]
user32.CreateWindowExW.restype = ctypes.wintypes.HWND
user32.RegisterHotKey.argtypes = [
    ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
]
user32.RegisterHotKey.restype = ctypes.wintypes.BOOL
user32.UnregisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = ctypes.wintypes.BOOL
user32.DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.DefWindowProcW.restype = ctypes.wintypes.LPARAM
user32.PostThreadMessageW.argtypes = [
    ctypes.wintypes.DWORD, ctypes.c_uint,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL

VK_MAP = {
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    '+': 0xBB, '=': 0xBB, '-': 0xBD, '_': 0xBD,
    '[': 0xDB, ']': 0xDD, '\\': 0xDC,
    ';': 0xBA, ':': 0xBA, "'": 0xDE, '"': 0xDE,
    ',': 0xBC, '.': 0xBE, '/': 0xBF, '?': 0xBF,
    '`': 0xC0, '~': 0xC0,
    'space': 0x20, 'enter': 0x0D, 'return': 0x0D,
    'tab': 0x09, 'escape': 0x1B, 'esc': 0x1B,
    'backspace': 0x08, 'delete': 0x2E, 'del': 0x2E,
    'insert': 0x2D, 'ins': 0x2D,
    'home': 0x24, 'end': 0x23,
    'pageup': 0x21, 'prior': 0x21,
    'pagedown': 0x22, 'next': 0x22,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'printscreen': 0x2C, 'prtsc': 0x2C,
    'ctrl': 0x11, 'ctrl_l': 0x11, 'ctrl_r': 0xA3,
    'alt': 0x12, 'alt_l': 0x12, 'alt_r': 0xA5,
    'shift': 0x10, 'shift_l': 0x10, 'shift_r': 0xA1,
    'win': 0x5B, 'win_l': 0x5B, 'win_r': 0x5C,
    'numlock': 0x90, 'scrolllock': 0x91, 'capslock': 0x14,
    'apps': 0x5D, 'numpad0': 0x60, 'numpad1': 0x61,
    'numpad2': 0x62, 'numpad3': 0x63, 'numpad4': 0x64,
    'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67,
    'numpad8': 0x68, 'numpad9': 0x69,
}


class Win32HotkeyManager:
    """基于 RegisterHotKey 的全局热键管理器"""

    def __init__(self):
        self._hwnd = None
        self._hotkey_map = {}
        self._id_counter = HOTKEY_ID_BASE
        self._registered = {}
        self._thread = None
        self._running = False
        self._wnd_proc_cb = None
        self._wnd_class_name = "LinearMouseSim_HotkeyWnd"
        # 线程安全的延迟注册
        self._pending = []
        self._lock = threading.Lock()
        self._ready = threading.Event()

    def _parse_hotkey(self, hotkey_str):
        parts = hotkey_str.lower().split('+')
        modifiers = 0
        vk = 0
        for part in parts:
            part = part.strip()
            if part in ('ctrl', 'ctrl_l', 'ctrl_r'):
                modifiers |= 0x0002
            elif part in ('alt', 'alt_l', 'alt_r'):
                modifiers |= 0x0001
            elif part in ('shift', 'shift_l', 'shift_r'):
                modifiers |= 0x0004
            elif part in ('win', 'win_l', 'win_r'):
                modifiers |= 0x0008
            else:
                vk = VK_MAP.get(part, 0)
        return modifiers, vk

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_HOTKEY:
            hotkey_id = wparam
            if hotkey_id in self._hotkey_map:
                action, callback = self._hotkey_map[hotkey_id]
                try:
                    callback()
                except Exception as e:
                    print(f"Win32 热键回调执行失败 {action}: {e}")
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _thread_main(self):
        """后台线程：创建窗口 → 注册热键 → 运行消息循环（全部同一线程）"""
        # 1. 创建窗口
        WndProcType = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.wintypes.HWND, ctypes.c_uint,
            ctypes.c_ulong, ctypes.c_long,
        )
        self._wnd_proc_cb = WndProcType(self._wnd_proc)

        wnd_class = WNDCLASS()
        wnd_class.style = 0
        wnd_class.lpfnWndProc = ctypes.cast(self._wnd_proc_cb, ctypes.c_void_p).value
        wnd_class.cbClsExtra = 0
        wnd_class.cbWndExtra = 0
        wnd_class.hInstance = kernel32.GetModuleHandleW(None)
        wnd_class.hIcon = 0
        wnd_class.hCursor = 0
        wnd_class.hbrBackground = 0
        wnd_class.lpszMenuName = None
        wnd_class.lpszClassName = self._wnd_class_name

        atom = user32.RegisterClassW(ctypes.byref(wnd_class))
        if atom == 0:
            print(f"RegisterClassW 失败: {ctypes.GetLastError()}")
            self._ready.set()
            return

        self._hwnd = user32.CreateWindowExW(
            0, self._wnd_class_name, "HotkeyReceiver",
            0, 0, 0, 0, 0,
            None, None, wnd_class.hInstance, None
        )
        if not self._hwnd:
            print(f"CreateWindowExW 失败: {ctypes.GetLastError()}")
            self._ready.set()
            return

        self._ready.set()

        # 2. 处理启动前的延迟注册
        self._process_pending()

        # 3. 消息循环
        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            # 处理新注册
            self._process_pending()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _process_pending(self):
        """处理延迟注册队列"""
        with self._lock:
            pending = self._pending[:]
            self._pending.clear()
        for action, hotkey_str, callback in pending:
            self._do_register(action, hotkey_str, callback)

    def _do_register(self, action, hotkey_str, callback):
        """在后台线程中执行注册"""
        if not hotkey_str or not self._hwnd:
            return False
        modifiers, vk = self._parse_hotkey(hotkey_str)
        if vk == 0:
            print(f"Win32 热键注册失败 {action}: 无法识别 '{hotkey_str}'")
            return False
        hotkey_id = self._id_counter
        self._id_counter += 1
        if not user32.RegisterHotKey(self._hwnd, hotkey_id, modifiers, vk):
            print(f"Win32 热键注册失败 {action}: {hotkey_str} (err={ctypes.GetLastError()})")
            return False
        self._hotkey_map[hotkey_id] = (action, callback)
        self._registered[action] = hotkey_id
        print(f"Win32 热键已注册 {action}: {hotkey_str}")
        return True

    def register(self, action, hotkey_str, callback):
        """线程安全的注册：加入队列，由后台线程执行"""
        if not hotkey_str:
            return False
        with self._lock:
            self._pending.append((action, hotkey_str, callback))
        return True

    def unregister(self, action):
        if action in self._registered:
            hotkey_id = self._registered.pop(action)
            if self._hwnd:
                user32.UnregisterHotKey(self._hwnd, hotkey_id)
            self._hotkey_map.pop(hotkey_id, None)

    def unregister_all(self):
        for action in list(self._registered.keys()):
            self.unregister(action)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3.0)

    def stop(self):
        self._running = False
        self.unregister_all()
        if self._thread and self._thread.is_alive():
            try:
                user32.PostThreadMessageW(self._thread.ident, WM_QUIT, 0, 0)
            except Exception:
                pass
            self._thread.join(timeout=2.0)
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        self._wnd_proc_cb = None

    def is_available(self):
        return self._hwnd is not None

    def set_hotkey(self, action, hotkey_str, callback):
        self.unregister(action)
        return self.register(action, hotkey_str, callback)
