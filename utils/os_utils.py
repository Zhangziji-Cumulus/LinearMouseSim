import ctypes
import os
import sys
import platform

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    
    script = sys.argv[0]
    params = ' '.join(sys.argv[1:])
    
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1
        )
        return True
    except Exception as e:
        print(f"提升权限失败: {e}")
        return False

def set_auto_start(enable=True):
    if platform.system() != 'Windows':
        return False
    
    import winreg
    
    app_name = 'LinearMouseSim'
    key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if enable:
            exe_path = os.path.abspath(sys.argv[0])
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            print(f"已设置开机自启: {exe_path}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                print("已取消开机自启")
            except FileNotFoundError:
                pass
        
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"设置开机自启失败: {e}")
        return False

def check_vjoy_installed():
    import winreg
    
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', 0, winreg.KEY_READ)
        
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                
                if 'vJoy' in display_name:
                    winreg.CloseKey(subkey)
                    winreg.CloseKey(key)
                    return True
                    
                winreg.CloseKey(subkey)
            except Exception:
                continue
        
        winreg.CloseKey(key)
        return False
    except Exception:
        return False

def get_vjoy_version():
    import winreg
    
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', 0, winreg.KEY_READ)
        
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                
                if 'vJoy' in display_name:
                    version, _ = winreg.QueryValueEx(subkey, 'DisplayVersion')
                    winreg.CloseKey(subkey)
                    winreg.CloseKey(key)
                    return version
                    
                winreg.CloseKey(subkey)
            except Exception:
                continue
        
        winreg.CloseKey(key)
        return None
    except Exception:
        return None

def show_message_box(title, message, icon='info'):
    icons = {
        'info': 0x40,
        'warning': 0x30,
        'error': 0x10,
        'question': 0x20
    }
    
    ctypes.windll.user32.MessageBoxW(None, message, title, icons.get(icon, 0x40))

if __name__ == '__main__':
    print(f"管理员权限: {is_admin()}")
    print(f"vJoy已安装: {check_vjoy_installed()}")
    print(f"vJoy版本: {get_vjoy_version()}")
