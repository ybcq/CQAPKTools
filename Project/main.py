import PySimpleGUI as sg
import os
import sys
from models.CQAPKTools import NewConfigParser, run_adb_command
from models.CQApkRename import batch_rename

# Import tab modules
from tabs import SurgeFreeze, GeneralOptimize, HuaweiEngine, BatchRename, BatchExtractInstall

APP_NAME = "CQApkTools"
APP_VERSION = "4.0.0"

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

cfgpath = os.path.join(CURRENT_DIR, "Setup.ini")
batpath = os.path.join(CURRENT_DIR, "HuaweiSubstW.bat")
lnkpath = os.path.join(CURRENT_DIR, "HuaweiSubstW.lnk")
apkpath = os.path.join(CURRENT_DIR, "ApkInstaller.exe")

# 创建管理对象
conf = NewConfigParser()

# 读ini文件
conf.read(cfgpath, encoding="utf-8")
aaptPath = conf.get("Config", "aaptPath")
keytoolPath = conf.get("Config", "keytoolPath")
newFileNamePattern = conf.get("Config", "newFileNamePattern")

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ========== CLI 模式：右键菜单批量重命名 ==========
if '--rename' in sys.argv:
    # 收集所有 .apk 文件参数
    apk_files = []
    for arg in sys.argv[1:]:
        if arg == '--rename':
            continue
        arg = arg.strip('"').strip("'")
        if os.path.isfile(arg) and arg.lower().endswith('.apk'):
            apk_files.append(os.path.abspath(arg))

    if not apk_files:
        sg.Popup('未找到有效的 APK 文件', title='CQApkTools 重命名')
        sys.exit(0)

    _aapt = aaptPath if os.path.isabs(
        aaptPath) else os.path.join(CURRENT_DIR, aaptPath)
    _keytool = keytoolPath if os.path.isabs(
        keytoolPath) else os.path.join(CURRENT_DIR, keytoolPath)

    success, fail, results = batch_rename(
        apk_files, newFileNamePattern,
        aapt_path=_aapt, keytool_path=_keytool
    )

    msg_lines = [f'重命名完成：成功 {success}，失败 {fail}']
    for old, new, err in results:
        if err:
            msg_lines.append(f'  [失败] {os.path.basename(old)}: {err}')
        elif old != new:
            msg_lines.append(
                f'  {os.path.basename(old)} -> {os.path.basename(new)}')

    sg.Popup('\n'.join(msg_lines), title='CQApkTools 重命名结果')
    sys.exit(0)
# ========== CLI 模式结束 ==========

# 构建主窗口布局（组合各标签页的布局）
layout = [
    [sg.Text('设备ID'), sg.InputText(key='device_id', disabled=True, expand_x=True,
                                   text_color="Black"), sg.Text('状态', key='status'), sg.Button('连接设备'), sg.Button('断开连接')],
    [sg.TabGroup([[sg.Tab('通用优化', GeneralOptimize.layout), sg.Tab('澎湃冻结', SurgeFreeze.layout), sg.Tab(
        '华为引擎', HuaweiEngine.layout), sg.Tab('批量命名', BatchRename.layout), sg.Tab('批量提取安装', BatchExtractInstall.layout)]])],
    [sg.Multiline(key='log', disabled=True, size=(96, 10), expand_x=True)],
    [sg.Frame("关于", [[sg.Button('关于软件'), sg.Button('作者官网')]], expand_x=True)]
]

window = sg.Window(f'{APP_NAME} {APP_VERSION}', layout, finalize=True)

# 设置批量命名标签页中表达式的默认值
window['kind'].update(value=newFileNamePattern)

# 构建传递给各标签页的上下文
ctx = {
    'conf': conf,
    'cfgpath': cfgpath,
    'batpath': batpath,
    'lnkpath': lnkpath,
    'apkpath': apkpath,
    'aaptPath': aaptPath,
    'keytoolPath': keytoolPath,
    'newFileNamePattern': newFileNamePattern,
    'CURRENT_DIR': CURRENT_DIR,
}

# 事件循环
while True:
    event, values = window.read()

    if event in (None, 'Close'):
        break

    # 依次尝试各标签页的事件处理器
    handled = SurgeFreeze.handle_event(window, event, values)
    if not handled:
        handled = GeneralOptimize.handle_event(window, event, values)
    if not handled:
        handled = HuaweiEngine.handle_event(window, event, values, ctx)
    if not handled:
        handled = BatchRename.handle_event(window, event, values, ctx)
    if not handled:
        handled = BatchExtractInstall.handle_event(window, event, values, ctx)

    if handled:
        continue

    # 全局事件
    if event == '连接设备':
        r = run_adb_command(window, 'devices')
        window['log'].print(r)

        lines = r.strip().split('\n')
        device_id = '无设备'
        status = '未连接'

        for line in lines:
            if line and not line.startswith('List of devices attached'):
                parts = line.split('\t')
                if len(parts) > 1 and parts[1] == 'device':
                    device_id = parts[0]
                    status = '已连接'
                    break

        window['device_id'].update(value=device_id)
        window['status'].update(value=status)

    elif event == '断开连接':
        window['device_id'].update(value='')
        window['status'].update(value='未连接')

    elif event == '关于软件':
        changelog = (
            "=== 4.0.0 升级日志 ===\n"
            "\n"
            "【架构重构】\n"
            "  - 从单文件 CQAPKTools.py 重构为模块化架构\n"
            "  - main.py 入口 + models/ 业务逻辑 + tabs/ 界面\n"
            "  - 事件处理采用责任链模式，各标签页独立 handle_event()\n"
            "\n"
            "【新增功能】\n"
            "  - 批量提取安装标签页：从设备提取APK、批量安装、\n"
            "    智能替换（含实时状态表格和统计汇总）\n"
            "  - CLI 右键批量重命名：支持 --rename 参数从资源管理器\n"
            "    右键菜单静默批量重命名\n"
            "  - 应用激活：一键激活女娲石/小黑屋/Shizuku/Scene\n"
            "  - 内置 CQApkRename 模块，替代外部 CQApkRename.exe\n"
            "  - 新增证书占位符：{APP证书用户}、{APP证书序列号}\n"
            "  - 系统更新管理：冻结/解冻/卸载/还原 com.android.updater\n"
            "  - 自定义包名冻结：获取前台应用包名后自由操作\n"
            "  - 设备ID追踪：主界面显示当前连接设备ID\n"
            "  - 墓碑进程开关：开启/关闭 use_freezer\n"
            "  - 优雅动画预设：window=1.5, transition=1.34, animator=1.17\n"
            "  - 仅替换已安装应用模式\n"
            "\n"
            "【配置变更】\n"
            "  - 配置文件从 CQApkRename.ini 改为 Setup.ini\n"
            "  - NewConfigParser 保留配置键原始大小写\n"
            "\n"
            "CQApkTools不是一个原创工具，而是一个整合工具。\n"
            "其中 ApkRenamer 的作者是 AsionTang\n"
            "ApkInstaller 的汉化者是 御坂初琴\n"
            "\n"
            "御坂初琴软件屋\n"
            "https://ybcq.github.io/\n"
            "CopyRight By Misaka HatSune 2020-2025"
        )
        sg.Popup(changelog, title="关于")

    elif event == '作者官网':
        os.popen('explorer https://ybcq.github.io/')

window.close()
