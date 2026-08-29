# CQApkTools 开发指引

MIUI 设备管理 + APK 处理工具（Python 3.12 + PySimpleGUI，仅 Windows，UI/文案全中文）。

## 入口与结构

- 入口是 `main.py`（`python main.py` 启动 GUI）。`Project/CQAPKTools.py` 已重构为 `main.py`——旧文档、旧脚本里对它的引用一律过期。
- `models/` = 业务逻辑：`CQAPKTools.py`（`NewConfigParser`、`run_adb_command`、安装/卸载/冻结助手）、`CQApkRename.py`（aapt+keytool 重命名）、`ResetSystemApps.py`（系统应用更新管理；可按 `__main__` 独立 CLI 运行，也由 `tabs/SurgeFreeze.py` 调用，通过 `log=` 回调输出日志，勿依赖 `print`）。
- `tabs/` = PySimpleGUI 布局 + `handle_event()`。main.py:105 按责任链依次尝试：SurgeFreeze → GeneralOptimize → HuaweiEngine → BatchRename → BatchExtractInstall。SurgeFreeze/GeneralOptimize 签名是 `(window, event, values)`，其余三个带 `ctx`。
- 可复用逻辑放 `models/`，别在 `tabs/` 堆业务代码。版本号在 `main.py` 顶部 `APP_VERSION`（当前 4.0.0）。

## 运行与 CLI

- GUI：`python main.py`
- 右键菜单批量重命名 CLI：`python main.py --rename "a.apk" "b.apk"`（main.py:33）

## 配置（Project/Setup.ini）

- UTF-8，`main.py` 用 `encoding='utf-8'` 读取；键：`aaptPath`、`keytoolPath`、`newFileNamePattern`。
- 重命名占位符：`{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}`，默认 `{应用包名}_{版本名字}`。替换逻辑在 `models/CQApkRename.py` 的 `build_filename`。
- `NewConfigParser` 覆写 `optionxform` 保留键原始大小写（configparser 默认转小写，勿去掉）。

## 外部工具依赖

- `adb` 必须在系统 PATH（`run_adb_command` 直接 `['adb', ...]`）；`get_apk_package_name` 裸调 `aapt`（同样走 PATH）。`aapt.exe`/`fastboot.exe` 打包在 `Project/`。
- `keytool.exe` 在 `Project/bin/`（捆绑 JRE 的一部分），签名解析依赖它，别移动。

## 构建

- `Py2EXE.bat` 已过期：内部 `pyinstaller ... CQAPKTools.py` 指向不存在的文件。可靠构建：`pyinstaller CQAPKTools.spec`（spec 已指向 `main.py`，onedir 产物 `dist/CQAPKTools/`）。构建后需自行把 `aapt.exe`/`bin/` 等运行时资源拷进产物目录。
- 根目录 `CQApkTools.iss`（Inno Setup）同样过期（版本 2.0、路径指向不存在目录）。

## 注意事项

- 无测试、无 lint/typecheck、无 CI、无 requirements.txt（依赖仅 PySimpleGUI + PyInstaller）。手动验证：直接 `python main.py`。
- `.py`/`.ini` 为 UTF-8；`Py2EXE.bat`、`CQApkTools.iss` 为 GBK（UTF-8 下显示乱码）——改动这两个文件务必保持 GBK 编码。
- 部分功能需管理员权限（写注册表、映射盘符），设备需开启 ADB USB 调试。