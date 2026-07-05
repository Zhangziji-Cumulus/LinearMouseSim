# LinearMouseSim - 快捷键冲突与角度映射修复验证清单

- [ ] Checkpoint 1: 默认 toggle 快捷键已修改为 `}`，与 `+`/`-` 参数调节无冲突
- [ ] Checkpoint 2: 开启模拟时，SteeringAlgorithm.previous_angle 为 0
- [ ] Checkpoint 3: 开启模拟后，UI 显示角度为 0°
- [ ] Checkpoint 4: 开启模拟后移动鼠标，角度随移动正常变化
- [ ] Checkpoint 5: 关闭模拟后移动鼠标到边缘，再开启时角度从零开始，无突变
- [ ] Checkpoint 6: 参数面板中显示热键配置区域，包含四个热键（toggle、increase_sensitivity、decrease_sensitivity、reset_steering）
- [ ] Checkpoint 7: 点击热键修改按钮后，提示用户按下新按键
- [ ] Checkpoint 8: 按下新按键后，热键立即更新并生效
- [ ] Checkpoint 9: 关闭程序后重启，热键配置保持不变（持久化）
- [ ] Checkpoint 10: 所有功能正常工作，无明显延迟或性能问题