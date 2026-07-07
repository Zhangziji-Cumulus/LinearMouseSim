"""测试OSD功能"""
import sys
sys.path.insert(0, '.')

from config.config_manager import ConfigManager
from ui.osd_manager import OSDManager
import time

def test_osd():
    print("=== 测试OSD管理器 ===")
    
    # 创建配置管理器
    config = ConfigManager()
    print(f"配置加载成功")
    print(f"OSD启用: {config.get('app.osd_enabled')}")
    print(f"OSD时长: {config.get('app.osd_duration')}")
    
    # 创建OSD管理器
    osd = OSDManager(config)
    print("OSD管理器初始化成功")
    
    # 测试显示灵敏度
    print("\n测试显示灵敏度...")
    osd.show_sensitivity(2.0)
    time.sleep(1.5)
    
    # 测试显示临时降敏
    print("\n测试显示临时降敏...")
    osd.show_temp_sensitivity(True)
    time.sleep(1.5)
    
    # 测试显示开关状态
    print("\n测试显示开启状态...")
    osd.show_toggle_state('ON')
    time.sleep(1.5)
    
    # 测试显示关闭状态
    print("\n测试显示关闭状态...")
    osd.show_toggle_state('OFF')
    time.sleep(1.5)
    
    # 关闭OSD
    osd.close()
    print("\n测试完成")

if __name__ == '__main__':
    test_osd()
