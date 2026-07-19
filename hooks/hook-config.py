from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集 config 包的所有子模块
hiddenimports = collect_submodules('config')

# 收集 config 包的所有数据文件
datas = collect_data_files('config')
