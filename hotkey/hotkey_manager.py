import keyboard
import threading
import time

class HotkeyManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.callbacks = {}
        self.hotkeys = {}
        self.last_trigger_time = {}
        self.cooldown_ms = 200
        self.enabled = True
        
    def register_callback(self, action, callback):
        self.callbacks[action] = callback
    
    def _trigger_action(self, action):
        if not self.enabled:
            return
        
        now = time.time() * 1000
        if action in self.last_trigger_time:
            if now - self.last_trigger_time[action] < self.cooldown_ms:
                return
        
        self.last_trigger_time[action] = now
        
        if action in self.callbacks:
            try:
                self.callbacks[action]()
            except Exception as e:
                print(f"热键回调执行失败 {action}: {e}")
    
    def load_hotkeys(self):
        self.unregister_all()
        
        hotkey_config = self.config_manager.get('hotkeys', {})
        actions = ['toggle', 'increase_sensitivity', 'decrease_sensitivity', 'reset_steering']
        
        for action in actions:
            hotkey = hotkey_config.get(action, '')
            if hotkey:
                self.register_hotkey(action, hotkey)
    
    def register_hotkey(self, action, hotkey):
        try:
            keyboard.add_hotkey(hotkey, self._trigger_action, args=[action], suppress=False)
            self.hotkeys[action] = hotkey
            print(f"已注册热键 {action}: {hotkey}")
        except Exception as e:
            print(f"热键注册失败 {action} ({hotkey}): {e}")
    
    def unregister_all(self):
        for action, hotkey in self.hotkeys.items():
            try:
                keyboard.remove_hotkey(hotkey)
            except Exception:
                pass
        self.hotkeys = {}
    
    def set_hotkey(self, action, hotkey):
        if action in self.hotkeys:
            try:
                keyboard.remove_hotkey(self.hotkeys[action])
            except Exception:
                pass
        
        self.config_manager.set_hotkey(action, hotkey)
        
        if hotkey:
            try:
                keyboard.add_hotkey(hotkey, self._trigger_action, args=[action], suppress=False)
                self.hotkeys[action] = hotkey
                return True
            except Exception as e:
                print(f"热键设置失败 {action} ({hotkey}): {e}")
                return False
        else:
            self.hotkeys[action] = ''
            return True
    
    def get_hotkey(self, action):
        return self.hotkeys.get(action, '')
    
    def set_cooldown(self, ms):
        self.cooldown_ms = ms
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
    
    def start_listener(self):
        pass
    
    def stop_listener(self):
        self.unregister_all()

if __name__ == '__main__':
    from config.config_manager import ConfigManager
    
    config = ConfigManager()
    hotkey_manager = HotkeyManager(config)
    
    def on_toggle():
        print("切换模拟状态")
    
    def on_increase_sensitivity():
        print("增加灵敏度")
    
    def on_decrease_sensitivity():
        print("降低灵敏度")
    
    def on_reset_steering():
        print("重置方向盘")
    
    hotkey_manager.register_callback('toggle', on_toggle)
    hotkey_manager.register_callback('increase_sensitivity', on_increase_sensitivity)
    hotkey_manager.register_callback('decrease_sensitivity', on_decrease_sensitivity)
    hotkey_manager.register_callback('reset_steering', on_reset_steering)
    
    hotkey_manager.load_hotkeys()
    
    print("热键监听器已启动，按 = 切换状态，按 ESC 退出")
    
    try:
        keyboard.wait('esc')
    finally:
        hotkey_manager.stop_listener()
        print("热键监听器已停止")
