PRESETS = {
    'arcade': {
        'name': '街机娱乐',
        'description': '地平线、极品飞车、狂野飙车',
        'steering': {
            'sensitivity': 1.5,
            'smoothing_factor': 0.2,
            'deadzone': 2,
            'max_angle': 45,
            'return_speed': 0.02,
            'curve_type': 'linear',
            'exponential_power': 2.0
        },
        'three_zone': {
            'deadzone_start': 0,
            'deadzone_end': 2,
            'linear_start': 2,
            'linear_end': 200,
            'saturation_start': 200,
            'saturation_end': 500
        }
    },
    'racing': {
        'name': '标准竞速',
        'description': 'GT赛车、Forza、神力科莎',
        'steering': {
            'sensitivity': 1.0,
            'smoothing_factor': 0.3,
            'deadzone': 3,
            'max_angle': 90,
            'return_speed': 0.0,
            'curve_type': 'linear',
            'exponential_power': 1.5
        },
        'three_zone': {
            'deadzone_start': 0,
            'deadzone_end': 3,
            'linear_start': 3,
            'linear_end': 500,
            'saturation_start': 500,
            'saturation_end': 1000
        }
    },
    'simulation': {
        'name': '专业模拟',
        'description': 'iRacing、rFactor、神力科莎竞技版',
        'steering': {
            'sensitivity': 0.5,
            'smoothing_factor': 0.4,
            'deadzone': 1,
            'max_angle': 180,
            'return_speed': 0.0,
            'curve_type': 'linear',
            'exponential_power': 1.0
        },
        'three_zone': {
            'deadzone_start': 0,
            'deadzone_end': 1,
            'linear_start': 1,
            'linear_end': 1000,
            'saturation_start': 1000,
            'saturation_end': 2000
        }
    },
    'rally': {
        'name': '拉力越野',
        'description': '尘埃、WRC、理查德伯恩斯拉力',
        'steering': {
            'sensitivity': 1.2,
            'smoothing_factor': 0.25,
            'deadzone': 5,
            'max_angle': 120,
            'return_speed': 0.01,
            'curve_type': 'linear',
            'exponential_power': 1.8
        },
        'three_zone': {
            'deadzone_start': 0,
            'deadzone_end': 5,
            'linear_start': 5,
            'linear_end': 400,
            'saturation_start': 400,
            'saturation_end': 800
        }
    },
    'truck': {
        'name': '卡车模拟',
        'description': '欧洲卡车模拟、美国卡车模拟',
        'steering': {
            'sensitivity': 0.8,
            'smoothing_factor': 0.5,
            'deadzone': 4,
            'max_angle': 90,
            'return_speed': 0.03,
            'curve_type': 'linear',
            'exponential_power': 1.0
        },
        'three_zone': {
            'deadzone_start': 0,
            'deadzone_end': 4,
            'linear_start': 4,
            'linear_end': 600,
            'saturation_start': 600,
            'saturation_end': 1200
        }
    }
}

class PresetManager:
    def __init__(self):
        self.presets = PRESETS
    
    def get_preset(self, preset_id):
        return self.presets.get(preset_id)
    
    def get_all_presets(self):
        return list(self.presets.keys())
    
    def get_preset_info(self, preset_id):
        preset = self.get_preset(preset_id)
        if preset:
            return {
                'id': preset_id,
                'name': preset['name'],
                'description': preset['description']
            }
        return None
    
    def apply_preset(self, preset_id, config_manager):
        preset = self.get_preset(preset_id)
        if preset:
            config_manager.set_steering_params(preset['steering'])
            three_zone = preset.get('three_zone', {})
            for key, value in three_zone.items():
                config_manager.set(f'three_zone.{key}', value)
            return True
        return False
    
    def get_preset_names(self):
        return {key: preset['name'] for key, preset in self.presets.items()}

if __name__ == '__main__':
    pm = PresetManager()
    print("可用预设:")
    for preset_id in pm.get_all_presets():
        info = pm.get_preset_info(preset_id)
        print(f"- {info['name']} ({preset_id}): {info['description']}")
