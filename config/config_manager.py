import json
import os
import copy
import sys

DEFAULT_CONFIG = {
    'hotkeys': {
        'toggle': 'o',
        'increase_sensitivity': '+',
        'decrease_sensitivity': '-',
        'reset_steering': '0',
        'sensitivity_preset_1': 'f5',
        'sensitivity_preset_2': 'f6',
        'sensitivity_preset_3': 'f7',
        'cycle_curve': 'f8',
        'wheel_adjust': 'ctrl',
        'temp_sensitivity_half': 'shift'
    },
    'steering': {
        'sensitivity': 0.2,
        'smoothing_factor': 0.25,
        'deadzone': 0,
        'max_angle': 180,
        'return_speed': 0.0,
        'curve_type': 'linear',
        'exponential_power': 1.8,
        'reverse_direction': False,
        'assist_threshold': 30,
        'assist_return_rate': 0.15,
        'assist_rate_threshold': 50,
        'assist_rate_window': 0.02,
        'near_center_threshold': 50,
        'center_hold_ms': 100,
        'center_release_threshold': 200,
        'center_mode': 1,
        'center_speed_mode': 0,
        'center_speed': 0.05,
        'center_delay_ms': 200,
        'center_enabled': False
    },
    'three_zone': {
        'deadzone_start': 0,
        'deadzone_end': 3,
        'linear_start': 3,
        'linear_end': 500,
        'saturation_start': 500,
        'saturation_end': 1000
    },
    'mouse': {
        'dpi': 800,
        'enable_y_filter': True
    },
    'app': {
        'auto_start': False,
        'start_minimized': False,
        'tray_icon': True,
        'osd_enabled': True,
        'osd_duration': 2000,
        'sensitivity_presets': [1.0, 2.0, 3.0],
        'sensitivity_step': 0.1,
        'wheel_sensitivity_factor': 0.1,
        'main_loop_interval': 0.005,
        'hotkey_cooldown_ms': 200
    },
    'user_presets': {}
}

class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # 打包后使用 EXE 所在目录，开发时使用项目根目录
            if getattr(sys, 'frozen', False):
                # 打包后的 EXE
                self.config_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境
                self.config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_file = os.path.join(self.config_dir, 'config.json')
        else:
            self.config_file = config_file

        self.config = self._load_config()
    
    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return self._merge_config(DEFAULT_CONFIG, loaded)
            except Exception as e:
                print(f"配置文件加载失败: {e}")
                return copy.deepcopy(DEFAULT_CONFIG)
        else:
            self._save_config(DEFAULT_CONFIG)
            return copy.deepcopy(DEFAULT_CONFIG)
    
    def _merge_config(self, default, loaded):
        result = default.copy()
        for key in result:
            if key in loaded:
                if isinstance(result[key], dict) and isinstance(loaded[key], dict):
                    result[key] = self._merge_config(result[key], loaded[key])
                else:
                    result[key] = loaded[key]
        # 添加 loaded 中有但 default 中没有的键
        for key in loaded:
            if key not in result:
                result[key] = loaded[key]
        return result
    
    def _save_config(self, config):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def save(self):
        return self._save_config(self.config)
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        return self.save()
    
    def get_hotkey(self, action):
        return self.config['hotkeys'].get(action, '')
    
    def set_hotkey(self, action, hotkey):
        if action in self.config['hotkeys']:
            self.config['hotkeys'][action] = hotkey
            return self.save()
        return False
    
    def get_steering_params(self):
        return self.config['steering'].copy()
    
    def set_steering_params(self, params):
        for key, value in params.items():
            if key in self.config['steering']:
                self.config['steering'][key] = value
        return self.save()
    
    def get_three_zone_params(self):
        return self.config['three_zone'].copy()
    
    def get_mouse_dpi(self):
        return self.config['mouse'].get('dpi', 800)
    
    def set_mouse_dpi(self, dpi):
        self.config['mouse']['dpi'] = dpi
        return self.save()
    
    def get_app_settings(self):
        return self.config['app'].copy()
    
    def reset_to_default(self):
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        return self.save()
    
    def export_config(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                    self.config = self._merge_config(DEFAULT_CONFIG, imported)
                    return self.save()
            except Exception as e:
                print(f"导入配置失败: {e}")
                return False
        return False

if __name__ == '__main__':
    config = ConfigManager()
    print("当前配置:")
    print(json.dumps(config.config, indent=2, ensure_ascii=False))
    
    config.set('steering.sensitivity', 1.5)
    config.set('hotkeys.toggle', 'space')
    print("\n修改后的配置:")
    print(f"灵敏度: {config.get('steering.sensitivity')}")
    print(f"开关热键: {config.get('hotkeys.toggle')}")
