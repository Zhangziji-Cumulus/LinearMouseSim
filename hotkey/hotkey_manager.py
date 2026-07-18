import keyboard
import time

class HotkeyManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.callbacks = {}
        self.hotkeys = {}
        self.last_trigger_time = {}
        self.cooldown_ms = 200
        self.enabled = True
        self.wheel_adjust_key = 'ctrl'
        self.wheel_adjust_active = False
        self._temp_sensitivity_key = None
        self._temp_sensitivity_hooks = []
        
    def register_callback(self, action, callback):
        self.callbacks[action] = callback
    
    def _trigger_action(self, action, *args):
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
        actions = [
            'toggle', 
            'increase_sensitivity', 
            'decrease_sensitivity', 
            'reset_steering',
            'sensitivity_preset_1',
            'sensitivity_preset_2',
            'sensitivity_preset_3',
            'cycle_curve'
        ]
        
        for action in actions:
            hotkey = hotkey_config.get(action, '')
            if hotkey:
                self.register_hotkey(action, hotkey)
        
        # 加载滚轮调节键配置
        self.wheel_adjust_key = hotkey_config.get('wheel_adjust', 'ctrl')
        
        # 注册滚轮事件监听（兼容不同版本的 keyboard 库）
        try:
            keyboard.on_scroll(self._on_scroll)
        except AttributeError:
            print("当前版本的 keyboard 库不支持 on_scroll，滚轮调节功能暂不可用")
        
        # 加载临时半灵敏度键配置
        temp_key = hotkey_config.get('temp_sensitivity_half', '')
        if temp_key:
            self._register_temp_sensitivity_key(temp_key)
    
    def _register_temp_sensitivity_key(self, key):
        """注册临时半灵敏度键的按下/释放监听"""
        # 清除之前的监听
        self._unregister_temp_sensitivity_key()
        self._temp_sensitivity_key = key
        
        try:
            hooks = keyboard.on_press_key(key, self._on_temp_sensitivity_down, suppress=False)
            self._temp_sensitivity_hooks.append(hooks)
            hooks = keyboard.on_release_key(key, self._on_temp_sensitivity_up, suppress=False)
            self._temp_sensitivity_hooks.append(hooks)
            print(f"已注册临时半灵敏度键: {key}")
        except Exception as e:
            print(f"临时半灵敏度键注册失败 ({key}): {e}")
    
    def _unregister_temp_sensitivity_key(self):
        """取消临时半灵敏度键的监听"""
        for hook in self._temp_sensitivity_hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._temp_sensitivity_hooks = []
        self._temp_sensitivity_key = None
    
    def _on_temp_sensitivity_down(self, event):
        """临时半灵敏度键按下回调"""
        self._trigger_action('temp_sensitivity_half_down')
    
    def _on_temp_sensitivity_up(self, event):
        """临时半灵敏度键释放回调"""
        self._trigger_action('temp_sensitivity_half_up')
    
    def _on_scroll(self, event):
        """处理滚轮滚动事件"""
        if not self.enabled:
            return
        
        # 检查是否按住调节键
        if not keyboard.is_pressed(self.wheel_adjust_key):
            return
        
        # 滚轮向上增加灵敏度，向下降低灵敏度
        if event.delta > 0:
            self._trigger_action('wheel_increase_sensitivity')
        elif event.delta < 0:
            self._trigger_action('wheel_decrease_sensitivity')
    
    def register_hotkey(self, action, hotkey):
        try:
            if hotkey.lower() == 'shift':
                def _on_shift_press(event):
                    self._trigger_action(action, True)
                def _on_shift_release(event):
                    self._trigger_action(action, False)
                keyboard.on_press_key('shift', _on_shift_press)
                keyboard.on_release_key('shift', _on_shift_release)
                self.hotkeys[action] = hotkey
            else:
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
        
        if action == 'wheel_adjust':
            self.wheel_adjust_key = hotkey
            return True
        
        if action == 'temp_sensitivity_half':
            if hotkey:
                self._register_temp_sensitivity_key(hotkey)
            else:
                self._unregister_temp_sensitivity_key()
            return True
        
        if hotkey:
            try:
                if hotkey.lower() == 'shift':
                    def _on_shift_press(event):
                        self._trigger_action(action, True)
                    def _on_shift_release(event):
                        self._trigger_action(action, False)
                    keyboard.on_press_key('shift', _on_shift_press)
                    keyboard.on_release_key('shift', _on_shift_release)
                else:
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
        if action == 'wheel_adjust':
            return self.wheel_adjust_key
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
    
    def on_preset_1():
        print("切换灵敏度预设1")
    
    def on_preset_2():
        print("切换灵敏度预设2")
    
    def on_preset_3():
        print("切换灵敏度预设3")
    
    def on_cycle_curve():
        print("切换灵敏度曲线")
    
    def on_wheel_increase():
        print("滚轮增加灵敏度")
    
    def on_wheel_decrease():
        print("滚轮降低灵敏度")
    
    hotkey_manager.register_callback('toggle', on_toggle)
    hotkey_manager.register_callback('increase_sensitivity', on_increase_sensitivity)
    hotkey_manager.register_callback('decrease_sensitivity', on_decrease_sensitivity)
    hotkey_manager.register_callback('reset_steering', on_reset_steering)
    hotkey_manager.register_callback('sensitivity_preset_1', on_preset_1)
    hotkey_manager.register_callback('sensitivity_preset_2', on_preset_2)
    hotkey_manager.register_callback('sensitivity_preset_3', on_preset_3)
    hotkey_manager.register_callback('cycle_curve', on_cycle_curve)
    hotkey_manager.register_callback('wheel_increase_sensitivity', on_wheel_increase)
    hotkey_manager.register_callback('wheel_decrease_sensitivity', on_wheel_decrease)
    
    hotkey_manager.load_hotkeys()
    
    print("热键监听器已启动，按 = 切换状态，按 ESC 退出")
    print("按住 Ctrl + 滚轮调节灵敏度")
    print("F5/F6/F7 切换灵敏度预设")
    print("F8 切换灵敏度曲线")
    
    try:
        keyboard.wait('esc')
    finally:
        hotkey_manager.stop_listener()
        print("热键监听器已停止")