import time
import uuid
from copy import deepcopy

# 默认预设配置（使用 DEFAULT_CONFIG 的值）
DEFAULT_PRESET_CONFIG = {
    'steering': {
        'sensitivity': 1.0,
        'smoothing_factor': 0.3,
        'deadzone': 3,
        'max_angle': 90,
        'return_speed': 0.0,
        'curve_type': 'linear',
        'exponential_power': 1.5,
        'reverse_direction': False,
        'assist_threshold': 300,
        'assist_return_rate': 0.20,
        'assist_rate_threshold': 50,
        'assist_rate_window': 0.10,
        'near_center_threshold': 50,
        'center_hold_ms': 100,
        'center_release_threshold': 200
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
    }
}


class PresetManager:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def _get_user_presets(self):
        if self.config_manager:
            return self.config_manager.get('user_presets', {})
        return {}

    def _set_user_presets(self, presets):
        if self.config_manager:
            self.config_manager.set('user_presets', presets)

    def get_all_presets(self):
        result = {'default': {'name': '默认', 'description': '默认配置'}}
        user_presets = self._get_user_presets()
        for preset_id, preset in user_presets.items():
            result[preset_id] = {
                'name': preset.get('name', '未命名预设'),
                'description': preset.get('description', '')
            }
        return result

    def get_preset(self, preset_id):
        if preset_id == 'default':
            return deepcopy(DEFAULT_PRESET_CONFIG)
        user_presets = self._get_user_presets()
        preset = user_presets.get(preset_id)
        if preset:
            return deepcopy(preset.get('config', {}))
        return None

    def get_preset_info(self, preset_id):
        presets = self.get_all_presets()
        return presets.get(preset_id)

    def apply_preset(self, preset_id, config_manager):
        config = self.get_preset(preset_id)
        if config is None:
            return False

        if 'steering' in config:
            config_manager.set_steering_params(config['steering'])
        if 'three_zone' in config:
            for key, value in config['three_zone'].items():
                config_manager.set(f'three_zone.{key}', value)
        if 'mouse' in config:
            for key, value in config['mouse'].items():
                config_manager.set(f'mouse.{key}', value)
        return True

    def save_user_preset(self, name, config_manager, description=''):
        preset_id = f"preset_{int(time.time() * 1000)}"
        config = {
            'name': name or f'用户预设{len(self._get_user_presets()) + 1}',
            'description': description,
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'config': {
                'steering': config_manager.get_steering_params(),
                'three_zone': config_manager.get('three_zone', {}),
                'mouse': {
                    'dpi': config_manager.get('mouse.dpi', 800),
                    'enable_y_filter': config_manager.get('mouse.enable_y_filter', True)
                }
            }
        }

        user_presets = self._get_user_presets()
        user_presets[preset_id] = config
        self._set_user_presets(user_presets)
        return preset_id

    def delete_user_preset(self, preset_id):
        if preset_id == 'default':
            return False
        user_presets = self._get_user_presets()
        if preset_id in user_presets:
            del user_presets[preset_id]
            self._set_user_presets(user_presets)
            return True
        return False

    def rename_user_preset(self, preset_id, new_name):
        if preset_id == 'default':
            return False
        user_presets = self._get_user_presets()
        if preset_id in user_presets:
            user_presets[preset_id]['name'] = new_name
            self._set_user_presets(user_presets)
            return True
        return False


PRESETS = {
    'default': {
        'name': '默认',
        'description': '默认配置'
    }
}


if __name__ == '__main__':
    from config_manager import ConfigManager
    cm = ConfigManager()
    pm = PresetManager(cm)
    print("可用预设:")
    for preset_id, info in pm.get_all_presets().items():
        print(f"- {info['name']} ({preset_id}): {info.get('description', '')}")
