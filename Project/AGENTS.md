# CQApkTools 开发指引

MIUI 设备管理 + APK 处理工具（Flask Web 应用，Python 3.12，UI/文案全中文，仅 Windows）。

## 入口与结构

- 入口是 `Project/app.py`。版本号 `APP_VERSION = '5.0.0'`，端口 `SERVICE_PORT = 55500`。
- `app.py` 启动即双模式判断（`is_port_in_use`）：端口 55500 已有服务监听 → 打开浏览器后进程退出；否则启动 Flask 服务并在 3 秒后打开浏览器，进程常驻后台。原 `CQApkTools.py` 包装脚本的功能已全部合并进 `app.py`。
- `models/` = 业务逻辑：`CQAPKTools.py`（`NewConfigParser`、`run_adb_command`、安装/卸载/冻结助手）、`CQApkRename.py`（aapt+keytool 重命名）、`ResetSystemApps.py`（系统应用更新管理）。
- 前端：`templates/index.html`（单页 Bootstrap 5.3 界面）、`static/js/app.js`、`static/css/style.css`。
- 路由：`/` 首页、`/api/tabs` 标签页列表、`/api/logs` SSE 日志流、`/api/action` 后端动作接口、`/api/pick-file` 文件选择、`/api/pick-folder` 文件夹选择。
- 日志：`LogCapture` 类（app.py）线程安全，通过 SSE 推送到前端 `appendLog()`；同时 `_Redirector` 将 print 输出落盘到 exe 旁/项目目录的 `app.log`（无控制台的打包版也能留痕）。

## 运行与打包

- Web：`python Project/app.py` → 浏览器访问 `http://localhost:55500`
- 依赖：`pip install -r requirements.txt`（**项目根目录**，flask + easygui；本机当前实测 Flask 2.1.3 亦可运行）
- 打包：`pyinstaller --noconfirm CQAPKTools.spec`（入口 `app.py`，`console=False` 无窗口后台运行），产物 `dist/CQAPKTools/CQAPKTools.exe`。templates/static/Setup.ini/ico/Tools 等已在 spec 的 datas 中（Tools 含 adb/aapt/ApkInstaller 及捆绑 JRE 的 `Tools/bin`+`Tools/lib`，打包后位于 `_internal/Tools/`）。
- 打包环境要求：PyInstaller ≥ 6.10（本机 6.22.3）、setuptools 75.x（`pkg_resources` 必须完整——setuptools 81+ 已移除 `pkg_resources`，会导致 exe 启动即报 `NullProvider` 错误）。
- frozen（exe）模式下自动禁用 Flask debug 与 reloader。
- 前端静态资源：Bootstrap 5.3/Bootstrap Icons 已本地化在 `static/vendor/`，离线可用，无需 CDN。

## 配置（Project/Setup.ini）

- UTF-8，键：`aaptPath`、`keytoolPath`、`newFileNamePattern`。
- 重命名占位符：`{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}`，默认 `{应用包名}_{版本名字}`。替换逻辑在 `models/CQApkRename.py` 的 `build_filename`。
- `NewConfigParser` 覆写 `optionxform` 保留键原始大小写（configparser 默认转小写，勿去掉）。

## 外部工具依赖

- 外部工具统一放 `Project/Tools/`：`adb.exe` + `AdbWinApi.dll` + `AdbWinUsbApi.dll`（三件套必须同版本）、`aapt.exe`、`ApkInstaller.exe`。`run_adb_command`/`get_apk_package_name` 通过 `models/CQAPKTools.py` 的 `ADB_PATH`/`AAPT_PATH` 常量调用，**不依赖系统 PATH**；`Setup.ini` 的 `aaptPath`/`keytoolPath` 相对路径由 `app.py` 锚定 `CURRENT_DIR`。`Tools/fastboot.exe` 与 `Tools/7za.exe` 当前代码零引用（遗留文件）。
- `keytool.exe` 在 `Project/Tools/bin/`，与平级的 `Project/Tools/lib/` 合起来才是捆绑 JRE（JRE home = `Tools/`）——**bin 与 lib 必须成对、必须平级**，移动需一起。它只被 `models/CQApkRename.py` 的 `_run_keytool` 使用（`keytool -printcert -jarfile` 提取证书信息供 `{APP证书用户}`/`{APP证书序列号}` 占位符），是"没装 Java 的机器"上该功能的唯一依赖，别删。注意 aapt **不**依赖 Java（原生程序）。
- `easygui`：用于文件/文件夹选择对话框（`/api/pick-file`、`/api/pick-folder`）。

## 前端动作接口规范

- 所有前端按钮通过 `data-action` 调用 `/api/action`，返回 `jsonify({'ok': bool, 'msg': str, 'data': ...})`。
- 日志通过 `EventSource('/api/logs')` 实时推送到右侧日志面板。
- 文件/文件夹选择使用 easygui 系统原生对话框，返回真实路径。

## 功能模块

- **通用优化**：后台策略、墓碑进程、动画速度、一键降级（APK 批量替换安装）、应用激活（女娲石/小黑屋/Shizuku/Scene）。
- **澎湃冻结**：常用系统服务冻结/解冻/卸载/重装、CSV 列表批量操作、一键批量、前台应用获取。
- **华为引擎**：共享目录映射、华为移动应用引擎管理、为引擎安装软件。
- **批量命名**：APK 文件/文件夹批量重命名、自定义命名规则。右键菜单集成：前端 `register_context_menu`/`unregister_context_menu` 入口保留，但**后端 action 缺失**（5.0 迁移遗留，待实现）。
- **批量提取安装**：APK 批量提取到目录、批量安装、保留数据卸载。

## 更新日志

### V5.0.0
- 全面重构为 Flask Web 应用，浏览器访问本地服务
- 左侧标签栏 + 右侧内容页布局
- 右侧实时日志流（SSE）
- 全功能迁移：通用优化、澎湃冻结、华为引擎、批量命名、批量提取安装
- 使用 easygui 进行文件/文件夹选择，返回真实路径

### V4.0.0
- 重构为 PySimpleGUI 多标签页界面
- 标签页：澎湃冻结、通用优化、华为引擎、批量命名、批量提取安装
- 支持右键菜单批量重命名 CLI 模式
- 模块化 models/ 与 tabs/ 分离

### V3.2.0.2025
- 新增设备连接状态显示
- 支持获取前台应用包名
- 支持应用冻结/解冻/卸载/重装（保留数据）
- 新增动画速度三档独立调节
- 优化日志输出

### V1.0-V1.1
- 首批 PySimpleGUI 图形界面
- 基础 MIUI 优化（冻结 Analytics/Adsolution/Joyose 等）
- 华为引擎共享目录映射
- APK 拖拽安装与重命名

### V0.9
- 初始版本，以批处理脚本为主
- 集成 IceBox/黑域等工具
- 基础 APK 安装与重命名

## 注意事项

- 无测试、无 lint/typecheck、无 CI。手动验证：启动服务后浏览器访问各功能标签页。
- `.py`/`.ini` 为 UTF-8。
- 部分功能需管理员权限（写注册表、映射盘符），设备需开启 ADB USB 调试。
- 旧版 `main.py` 和 `tabs/` 目录已删除（5.0 重写为 Web 应用）。
- 仅支持 Windows 系统。
