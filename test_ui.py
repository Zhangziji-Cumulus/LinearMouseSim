"""UI测试脚本"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def test_wheel_rotation(app):
    """测试方向盘旋转动画"""
    angle = 0
    direction = 1
    speed = 2
    
    def animate():
        nonlocal angle, direction
        angle += speed * direction
        
        if abs(angle) >= 90:
            direction *= -1
        
        app.update_wheel_angle(angle)
        app.update_status_bar_angle(angle)
        app.after(50, animate)
    
    animate()

if __name__ == '__main__':
    app = MainWindow()
    test_wheel_rotation(app)
    app.run()
