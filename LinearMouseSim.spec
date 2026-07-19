# -*- mode: python ; coding: utf-8 -*-

import os
block_cipher = None

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[
        (os.path.join(project_root, '.venv', 'Lib', 'site-packages', 'pyvjoy', 'utils', 'x64', 'vJoyInterface.dll'), '.'),
        (os.path.join(project_root, '.venv', 'Lib', 'site-packages', 'vgamepad', 'win', 'vigem', 'client', 'x64', 'ViGEmClient.dll'), '.'),
    ],
    datas=[],
    hiddenimports=[
        'keyboard',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'pyvjoy',
        'vgamepad',
        'ctypes',
        'ctypes.wintypes',
        'core',
        'core.mouse_capture',
        'core.vjoy_output',
        'core.vgamepad_output',
        'core.state_machine',
        'core.steering_algorithm',
        'config',
        'config.config_manager',
        'config.presets',
        'ui',
        'ui.main_window',
        'ui.status_bar',
        'ui.parameter_panel',
        'ui.osd_manager',
        'ui.theme',
        'ui.tray_manager',
        'ui.widgets',
        'ui.widgets.custom_slider',
        'hotkey',
        'hotkey.hotkey_manager',
        'utils',
        'utils.os_utils',
    ],
    hookspath=[os.path.join(project_root, 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LinearMouseSim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'Logo', 'icon.ico'),
)
