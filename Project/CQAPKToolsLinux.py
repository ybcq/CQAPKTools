import subprocess
import PySimpleGUI as sg
import os
import configparser
import codecs
import shutil

APP_NAME = "CQApkTools"
APP_VERSION = "3.2.0.2025"

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

cfgpath = os.path.join(CURRENT_DIR, "CQApkRename.ini")
exepath = os.path.join(CURRENT_DIR, "CQApkRename.exe")
batpath = os.path.join(CURRENT_DIR, "HuaweiSubstW.bat")
lnkpath = os.path.join(CURRENT_DIR, "HuaweiSubstW.lnk")
apkpath = os.path.join(CURRENT_DIR, "ApkInstaller.exe")

class NewConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

# 创建管理对象
conf = NewConfigParser()

# 读ini文件
conf.read(cfgpath, encoding="utf-8")  # python3
aaptPath = conf.get("Config", "aaptPath")
keytoolPath = conf.get("Config", "keytoolPath")
newFileNamePattern = conf.get("Config", "newFileNamePattern")

# sg.theme_previewer()
sg.theme('DarkGray')  # Add a little color to your windows
sg.set_options(font=("等线", 10))

# 存储日志的列表
log_buffer = []

def run_adb_command(command):
    try:
        window_main['log'].print(f'执行命令: \r\n{command}')
        result = subprocess.run(['adb'] + command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"执行ADB命令失败: {e}"

def uninstall_apk(package_name, keep_data=False):
    command = f'shell pm uninstall {"-k " if keep_data else ""}{package_name}'
    r = run_adb_command(command)
    window_main['log'].print(r)
    return r

def install_apk(apk_path):
    command = f'install -r -t -d "{apk_path}"'
    r = run_adb_command(command)
    window_main['log'].print(r)
    return r

def check_app_exists(package_name):
    result = run_adb_command('shell pm list packages')
    return package_name in result

def change_apk_enable(state, name):
    action = "enable" if state else "disable-user"
    command = f'shell pm {action} {name}'
    r = run_adb_command(command)
    window_main['log'].print(r)
    return r

def change_animation_speed(sulv1, sulv2, sulv3):
    commands = [
        f'shell settings put global window_animation_scale {sulv1}',
        f'shell settings put global transition_animation_scale {sulv2}',
        f'shell settings put global animator_duration_scale {sulv3}'
    ]
    for command in commands:
        r = run_adb_command(command)
        window_main['log'].print(r)
    return r

def process_one_key_list(action, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                package_name = line.strip()  # 去除可能的空白字符
                if package_name:  # 如果行不为空
                    if action == '冻结':
                        change_apk_enable(False, package_name)  # 冻结应用
                    elif action == '解冻':
                        change_apk_enable(True, package_name)  # 解冻应用
                    elif action == '卸载':
                        uninstall_apk(package_name, keep_data=False)  # 卸载应用
                    elif action == '重装':
                        uninstall_apk(package_name, keep_data=True)  # 重装应用
                    window_main['log'].print(f"{action} {package_name}")
    except Exception as e:
        window_main['log'].print(f'读取文件时发生错误: {e}\n')
    window_main['log'].print(f'处理应用列表结束。\n')

def get_top_package_name():
    try:
        r = run_adb_command('shell dumpsys activity top | grep ACTIVITY')
        window_main['log'].update(r)
        lines = r.split('\n')
        if lines:  # 确保列表不为空
            # 获取最后一行，去除 "ACTIVITY " 前缀并提取包名
            last_line = lines[-2]
            package_name = last_line.replace("ACTIVITY ", "").split('/')[0].strip()
            return package_name
        else:
            return "无法获取前台应用包名"
    except Exception as e:
        return f"获取前台应用包名失败: {e}"

def get_apk_package_name(apk_path):
    try:
        result = subprocess.run(['aapt', 'dump', 'badging', apk_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8', errors='ignore')

        package_name = None
        application_label = None

        for line in output.split('\n'):
            if 'package:' in line:
                package_info = line.strip()
                package_name = package_info.split('name=')[1].split(' ')[0].strip('"')
            if 'application-label:' in line:
                label_info = line.strip()
                application_label = label_info.split('application-label:')[1].strip('"')

        return package_name, application_label

    except Exception as e:
        print(f"获取包名出错: {e}")
        return None, None

def uninstall_and_install_apk(apk_path):
    package_name, _ = get_apk_package_name(apk_path)
    if package_name:
        try:
            # 卸载应用
            window_main['log'].print(f"正在卸载 {package_name}...")
            uninstall_result = subprocess.run(
                ['adb', 'shell', 'pm', 'uninstall', package_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # 安装APK
            window_main['log'].print(f"正在安装 {apk_path}...")
            install_result = subprocess.run(
                ['adb', 'install', '-r', '-d', apk_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if install_result.returncode == 0:
                window_main['log'].print(f"成功安装 {apk_path}")
                return True
            else:
                window_main['log'].print(
                    f"安装失败: {install_result.stderr.decode('utf-8', errors='ignore')}")
                return False

        except Exception as e:
            window_main['log'].print(f"卸载和安装出错: {e}")
            return False
    else:
        window_main['log'].print(f"跳过 {apk_path}: 无法获取包名")
        return False

def organize_files_in_folder(folder_path):
    unrecognized_folder = os.path.join(folder_path, "无法识别的应用")
    os.makedirs(unrecognized_folder, exist_ok=True)

    apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
    unrecognized_apps = []
    processed_apps = []

    for apk_file in apk_files:
        apk_path = os.path.join(folder_path, apk_file)
        package_name, application_label = get_apk_package_name(apk_path)

        if package_name and application_label:
            sanitized_label = ''.join(
                e for e in application_label if e.isalnum() or e in (' ', '.', '_'))
            new_file_name = f"{sanitized_label} {package_name}.apk"
            new_file_path = os.path.join(folder_path, new_file_name)

            if not os.path.exists(new_file_path):
                os.rename(apk_path, new_file_path)
                window_main['log'].print(f"已重命名: {new_file_name}")
                processed_apps.append(new_file_path)
            else:
                window_main['log'].print(f"跳过重命名: {new_file_name} 已存在")
        else:
            try:
                shutil.move(apk_path, unrecognized_folder)
                window_main['log'].print(f"移动到无法识别的应用: {apk_file}")
                unrecognized_apps.append(apk_file)
            except Exception as e:
                window_main['log'].print(f"移动失败: {e}")

    # 输出无法识别的应用列表
    window_main['log'].print("\n无法识别的应用列表:")
    for app in unrecognized_apps:
        window_main['log'].print(f"  - {app}")

def process_apk_files_in_folder(folder_path, mode):
    if not folder_path:
        window_main['log'].print("请选择APK文件所在的文件夹")
        return

    apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
    for apk_file in apk_files:
        apk_path = os.path.join(folder_path, apk_file)
        package_name, _ = get_apk_package_name(apk_path)
        file_processed = False

        if mode == "uninstall_install":
            file_processed = uninstall_and_install_apk(apk_path)
        elif mode == "install_only":
            file_processed = install_apk(apk_path)
        elif mode == "replace":
            if package_name:
                if check_app_exists(package_name):
                    if not uninstall_apk(package_name):
                        window_main['log'].print(f"卸载应用 {package_name} 失败")
                        continue
                else:
                    window_main['log'].print(f"应用 {package_name} 未安装，跳过卸载")
                file_processed = install_apk(apk_path)
            else:
                window_main['log'].print(f"跳过 {apk_file}: 无法获取包名")
                continue

        if not file_processed:
            window_main['log'].print(f"处理应用 {apk_file} 失败")

# =========================界面布局==========================
# MIUI优化窗口布局F
miui_icebox = [
    [sg.Text("以下冻结的应用是在尽可能保留系统正常功能的情况下释放内存占用的列表，不是激进冻结列表")],
    [sg.Button('冻结Analytics'), sg.Button('解冻Analytics'), sg.Button('卸载Analytics'), sg.Button('重装Analytics'), sg.Text("分析服务，通常无用")],
    [sg.Button("冻结Adsolution"), sg.Button("解冻Adsolution"), sg.Button("卸载Adsolution"), sg.Button("重装Adsolution"), sg.Text("广告服务，冻结可减少广告")],
    [sg.Button("冻结Joyose"), sg.Button("解冻Joyose"), sg.Button("卸载Joyose"), sg.Button("重装Joyose"), sg.Text("温控服务，冻结可能影响计步")],
    [sg.Button("冻结SIM STK"), sg.Button("解冻SIM STK"), sg.Button("卸载SIM STK"), sg.Button("重装SIM STK"), sg.Text("SIM卡服务，通常无用")],
    [sg.Button("冻结内容中心"), sg.Button("解冻内容中心"), sg.Button("卸载内容中心"), sg.Button("重装内容中心"), sg.Text("桌面上滑的新闻，通常无用")],
    [sg.Button("冻结快应用"), sg.Button("解冻快应用"), sg.Button("卸载快应用"), sg.Button("重装快应用"), sg.Text("快应用服务框架，通常无用")],
    [sg.Button("冻结电量与性能"), sg.Button("解冻电量与性能"), sg.Button("卸载电量与性能"), sg.Button("重装电量与性能"), sg.Text("冻结可开启全局高刷，会导致耗电更快")],
    [sg.Button("冻结系统更新"), sg.Button("解冻系统更新"), sg.Button("卸载系统更新"), sg.Button("还原系统更新"), sg.Text("解锁ID机专用")],
    [sg.Text("")],
    [sg.Button("一键冻结"), sg.Button("一键解冻"), sg.Button("一键卸载"), sg.Button("一键重装"), sg.Text("冻结、解冻、卸载和重装除了电量与性能以外的所有项")],
    [sg.InputText(key='pname', size=(30, 5)), sg.Button("获取前台应用包名"), sg.Button("冻结该包"), sg.Button("解冻该包"), sg.Button("卸载该包"), sg.Button("重装该包")]
]

miui_icebox_list = [[sg.Text("导入一个CSV格式的列表，每行均为要冻结或者卸载的包名")],
                    [sg.InputText(key='filelist'), sg.FileBrowse(button_text="...", key='filelist', file_types=(("CSV格式应用列表", "*.csv"),))],
                    [sg.Button("一键冻结列表"), sg.Button("一键解冻列表"), sg.Button("一键卸载列表"), sg.Button("一键重装列表")],
                    ]

miui_catoon = [
    [sg.Button('无动画'), sg.Button('快速'), sg.Button('默认设置'), sg.Button("优雅")],
    [sg.InputText(key='speed1', default_text="1.5", size=(5, 5)), sg.InputText(key='speed2', default_text="1.5", size=(5, 5)), sg.InputText(key='speed3', default_text="1.5", size=(5, 5)), sg.Button("自定义速度"), sg.Text("该设置会影响所有系统动画")]
]

miui_better = [
    [sg.Text("该设置可能会引起微信后台不稳定，推荐在备用机上使用。该设置重启后保留")],
    [sg.Button('无后台'), sg.Button('激进'), sg.Button('轻快'), sg.Button("默认限制")],
    [sg.InputText(key='level', size=(5, 5), default_text="16")],
    [sg.Button('调整后台参数'), sg.Button('开启墓碑进程'), sg.Button('关闭墓碑进程')]
]

miui_exchange = [
    [sg.Text("可用于一键替换手机上的应用为定制版。该操作可能会删除被降级的应用的数据(比如聊天记录)，请谨慎操作")],
    [sg.Text("选择文件夹"), sg.InputText(key='apkfolder'), sg.FolderBrowse(button_text="...", key='path')],
    [sg.Button("整理文件夹中的文件名"), sg.Button("卸载并安装文件夹中的应用"), sg.Button("仅安装文件夹中的所有应用"), sg.Button('仅替换已安装的应用')]
]

other_adb = [
    [sg.Button("激活女娲石"), sg.Text("同步移除")],
    [sg.Button("激活小黑屋"), sg.Text("麦克斯韦妖模式")],
    [sg.Button("激活Shizuku"), sg.Text("比无线调试更稳定")],
    [sg.Button("激活Scene"), sg.Text("手机管理工具")],
]

# 定义标签页内容
icobox_layout = [
    [sg.Frame("列表冻结", miui_icebox_list, expand_x=True)],
    [sg.Frame("常用冻结", miui_icebox)]
]

# 定义标签页内容
optimization_layout = [
    [sg.Frame("后台策略", miui_better, expand_x=True)],
    [sg.Frame("一键降级", miui_exchange, expand_x=True)],
    [sg.Frame("应用激活", other_adb, expand_x=True)],
    [sg.Frame("动画设置", miui_catoon, expand_x=True)]
]

# 华为引擎窗口布局
huawei_disk = [
    [sg.Text("用于把华为移动应用引擎的共享目录映射为盘符，方便传入传出文件")],
    [sg.Text("方法1：")],
    [sg.Button('映射共享目录为W盘'), sg.Button('取消映射共享磁盘'), sg.Button("设置开机自动映射共享目录")],
    [sg.Text("方法2：")],
    [sg.Button("使用网络路径方式创建共享目录图标")]
]

huawei_other = [
    [sg.Button('安装华为移动引擎'), sg.Text("跳转到心某人的网站")],
    [sg.Button('杀死华为移动引擎'), sg.Text("用于华为移动应用引擎卡死后或不再使用时释放内存")],
    [sg.Button('为华为移动引擎安装软件'), sg.Text("打开汉化版的ApkInstaller")]
]

huawei_layout = [
    [sg.Frame("共享磁盘", huawei_disk, expand_x=True)],
    [sg.Frame("其他功能", huawei_other, expand_x=True)]
]

# 批量重命名窗口布局
rename_path = [
    [sg.Text("选择单文件"), sg.InputText(key='file', expand_x=True), sg.FileBrowse(button_text="...", key='file', file_types=(("安卓应用安装包", "*.apk"),))],
    [sg.Text("选择文件夹"), sg.InputText(key='path', expand_x=True), sg.FolderBrowse(button_text="...", key='path')]
]

rename_set = [
    [sg.Text("表达式：{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}")],
    [sg.InputText(key='kind', default_text=newFileNamePattern, expand_x=True)],
    [sg.Button('应用设置'), sg.Button("关联到右键菜单"), sg.Button("删除右键菜单")]
]

rename_layout = [
    [sg.Frame("重命名操作", rename_path, expand_x=True), sg.Button('开始重命名')],
    [sg.Frame("重命名设置", rename_set, expand_x=True)]
]

layout_about = [
    [sg.Button('关于软件'), sg.Button('作者官网')]
]

# 主窗口布局，包含四个标签页
layout = [
    [sg.Text('设备ID'), sg.InputText(key='device_id', disabled=True, expand_x=True, text_color="Black"), sg.Text('状态', key='status'), sg.Button('连接设备'), sg.Button('断开连接')],
    [sg.TabGroup([[sg.Tab('通用优化', optimization_layout), sg.Tab('澎湃冻结', icobox_layout), sg.Tab('华为引擎', huawei_layout), sg.Tab('批量命名', rename_layout)]])],
    [sg.Multiline(key='log', disabled=True, size=(96, 4), expand_x=True)],
    [sg.Frame("关于", layout_about, expand_x=True)]
]

window_main = sg.Window(f'{APP_NAME} {APP_VERSION}', layout)

# Create the event loop
while True:
    event, values = window_main.read()

    if event in (None, 'Close'):
        break

    # tab1的事件
    elif event in (None, '冻结Analytics'):
        change_apk_enable(False, "com.miui.analytics")

    elif event in (None, '解冻Analytics'):
        change_apk_enable(True, "com.miui.analytics")

    elif event in (None, '冻结Joyose'):
        change_apk_enable(False, "com.xiaomi.joyose")

    elif event in (None, '解冻Joyose'):
        change_apk_enable(True, "com.xiaomi.joyose")

    elif event in (None, '冻结Adsolution'):
        change_apk_enable(False, "com.miui.systemAdSolution")

    elif event in (None, '解冻Adsolution'):
        change_apk_enable(True, "com.miui.systemAdSolution")
                          
    elif event in (None, '冻结SIM STK'):
        change_apk_enable(False, "com.android.stk")

    elif event in (None, '解冻SIM STK'):
        change_apk_enable(True, "com.android.stk")

    elif event in (None, '冻结快应用'):
        change_apk_enable(False, "com.miui.hybrid")

    elif event in (None, '解冻快应用'):
        change_apk_enable(True, "com.miui.hybrid")

    elif event in (None, '冻结内容中心'):
        change_apk_enable(False, "com.miui.newhome")

    elif event in (None, '解冻内容中心'):
        change_apk_enable(True, "com.miui.newhome")

    elif event in (None, '冻结电量与性能'):
        change_apk_enable(False, "com.miui.powerkeeper")

    elif event in (None, '解冻电量与性能'):
        change_apk_enable(False, "com.miui.powerkeeper")

    elif event in (None, '冻结系统更新'):
        change_apk_enable(True, "com.android.updater")

    elif event in (None, '解冻系统更新'):
        change_apk_enable(False, "com.android.updater")

    elif event in (None, '卸载Analytics'):
        uninstall_apk("com.miui.analytics", keep_data=False)

    elif event in (None, '重装Analytics'):
        uninstall_apk("com.miui.analytics", keep_data=True)

    elif event in (None, '卸载Joyose'):
        uninstall_apk("com.xiaomi.joyose", keep_data=False)

    elif event in (None, '重装Joyose'):
        uninstall_apk("com.xiaomi.joyose", keep_data=True)

    elif event in (None, '卸载Adsolution'):
        uninstall_apk("com.miui.systemAdSolution", keep_data=False)

    elif event in (None, '重装Adsolution'):
        uninstall_apk("com.miui.systemAdSolution", keep_data=True)

    elif event in (None, '卸载SIM STK'):
        uninstall_apk("com.android.stk", keep_data=False)

    elif event in (None, '重装SIM STK'):
        uninstall_apk("com.android.stk", keep_data=True)

    elif event in (None, '卸载快应用'):
        uninstall_apk("com.miui.hybrid", keep_data=False)

    elif event in (None, '重装快应用'):
        uninstall_apk("com.miui.hybrid", keep_data=True)

    elif event in (None, '卸载内容中心'):
        uninstall_apk("com.miui.newhome", keep_data=False)

    elif event in (None, '重装内容中心'):
        uninstall_apk("com.miui.newhome", keep_data=True)

    elif event in (None, '卸载电量与性能'):
        uninstall_apk("com.miui.powerkeeper", keep_data=False)

    elif event in (None, '重装电量与性能'):
        uninstall_apk("com.miui.powerkeeper", keep_data=True)

    elif event in (None, '卸载系统更新'):
        uninstall_apk("com.android.updater", keep_data=False)

    elif event in (None, '重装系统更新'):
        uninstall_apk("com.android.updater", keep_data=True)

    elif event in (None, '一键冻结'):
        change_apk_enable(True, "com.miui.analytics")
        change_apk_enable(True, "com.xiaomi.joyose")
        change_apk_enable(True, "com.miui.systemAdSolution")
        change_apk_enable(True, "com.android.stk")
        change_apk_enable(True, "com.miui.hybrid")
        change_apk_enable(True, "com.miui.newhome")

    elif event in (None, '一键解冻'):
        uninstall_apk("com.miui.analytics", keep_data=False)
        uninstall_apk("com.xiaomi.joyose", keep_data=False)
        uninstall_apk("com.miui.systemAdSolution", keep_data=False)
        uninstall_apk("com.android.stk", keep_data=False)
        uninstall_apk("com.miui.hybrid", keep_data=False)
        uninstall_apk("com.miui.newhome", keep_data=False)

    elif event in (None, '一键卸载'):
        uninstall_apk("com.miui.analytics", keep_data=False)
        uninstall_apk("com.xiaomi.joyose", keep_data=False)
        uninstall_apk("com.miui.systemAdSolution", keep_data=False)
        uninstall_apk("com.android.stk", keep_data=False)
        uninstall_apk("com.miui.hybrid", keep_data=False)
        uninstall_apk("com.miui.newhome", keep_data=False)

    elif event in (None, '一键重装'):
        uninstall_apk("com.miui.analytics", keep_data=True)
        uninstall_apk("com.xiaomi.joyose", keep_data=True)
        uninstall_apk("com.miui.systemAdSolution", keep_data=True)
        uninstall_apk("com.android.stk", keep_data=True)
        uninstall_apk("com.miui.hybrid", keep_data=True)
        uninstall_apk("com.miui.newhome", keep_data=True)

    elif event == '一键冻结列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list('冻结', file_path)

    elif event == '一键解冻列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list('解冻', file_path)

    elif event == '一键卸载列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list('卸载', file_path)

    elif event == '一键重装列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list('重装', file_path)

    elif event == '整理文件夹中的文件名':
        folder_path = values['apkfolder']
        if folder_path:
            organize_files_in_folder(folder_path)

    elif event == '卸载并安装文件夹中的应用':
        process_apk_files_in_folder(values['apkfolder'], "uninstall_install")

    elif event == '仅安装文件夹中的所有应用':
        process_apk_files_in_folder(values['apkfolder'], "install_only")

    elif event == '仅替换已安装的应用':
        process_apk_files_in_folder(values['apkfolder'], "replace")

    # tab5的事件
    elif event in (None, '无动画'):
        r = change_animation_speed("0", "0", "0")
        window_main['log'].print(r)

    elif event in (None, '快速'):
        r = change_animation_speed("0.5", "0.5", "0.5")
        window_main['log'].print(r)

    elif event in (None, '默认设置'):
        r = change_animation_speed("1", "1", "1")
        window_main['log'].print(r)

    elif event in (None, '优雅'):
        r = change_animation_speed("1.5", "1.34", "1.17")
        window_main['log'].print(r)

    elif event in (None, '自定义速度'):
        r = change_animation_speed(values['speed1'], values['speed2'], values['speed3'])
        window_main['log'].print(r)

    elif event in (None, '无后台'):
        r = run_adb_command('shell settings put global activity_manager_constants max_cached_processes=0')
        window_main['log'].print(r)

    elif event in (None, '激进'):
        r = run_adb_command('shell settings put global activity_manager_constants max_cached_processes=1')
        window_main['log'].print(r)

    elif event in (None, '轻快'):
        r = run_adb_command('shell settings put global activity_manager_constants max_cached_processes=4')
        window_main['log'].print(r)

    elif event in (None, '默认限制'):
        r = run_adb_command('shell settings put global activity_manager_constants max_cached_processes=16')
        window_main['log'].print(r)

    elif event in (None, '调整后台参数'):
        level = values['level']
        r = run_adb_command(f'shell settings put global activity_manager_constants max_cached_processes={level}')
        window_main['log'].print(r)

    elif event in (None, '开启墓碑进程'):
        r = run_adb_command('shell device_config put activity_manager_native_boot use_freezer true && adb reboot')
        window_main['log'].print(r)

    elif event in (None, '关闭墓碑进程'):
        r = run_adb_command('shell device_config put activity_manager_native_boot use_freezer false && adb reboot')
        window_main['log'].print(r)

    # tab2的事件
    elif event in (None, '映射共享目录为W盘'):
        r = run_adb_command('shell subst w: %appdata%\\Huawei\\Emulator\\Share')
        sg.Popup('已成功映射共享目录为W盘，如果不显示就多刷新几下。', title='成功')
        os.popen('explorer')

    elif event in (None, '取消映射共享磁盘'):
        r = run_adb_command('shell subst w: /d')
        sg.Popup('已取消映射华为移动应用引擎到W盘！', title='成功')

    elif event in (None, '设置开机自动映射共享目录'):
        r = run_adb_command(f'reg add "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名...\\command" /ve /t REG_SZ /d "{batpath}" "%1" /f')
        if r.find("拒绝"):
            sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
        else:
            sg.Popup('已成功设置开机自动映射共享目录。', title='成功')

    elif event in (None, '使用网络路径方式创建共享目录图标'):
        r = run_adb_command(f'copy "{lnkpath}" "%appdata%\\Microsoft\\Windows\\Network Shortcuts\\安卓磁盘 (W).lnk"')
        sg.Popup('已成功使用网络路径方式创建共享目录图标。', title='成功')
        os.popen('explorer')

    elif event in (None, '安装华为移动引擎'):
        os.popen('explorer https://space.bilibili.com/28516198')

    elif event in (None, '杀死华为移动引擎'):
        r = run_adb_command('taskkill /f /im MobileAppEngine.exe')
        sg.Popup('已关闭华为应用引擎', title="成功")

    elif event in (None, '为华为移动引擎安装软件'):
        try:
            r = run_adb_command(f'call "{apkpath}"')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
        except BaseException:
            sg.Popup('请使用管理员身份运行该软件', title='权限不足')

    elif event in (None, '开始重命名'):
        # 单文件
        file_path = values['file']
        if file_path is not None:
            if os.path.exists(file_path):
                r = run_adb_command(f'"{exepath}"' + ' "' + file_path + '"')

        # 多文件
        pathpath = values['path']
        s = ""  # 路径整合
        if pathpath is not None:
            if os.path.exists(pathpath):
                for root, dirs, files in os.walk(pathpath):
                    for file in files:
                        apkpath = os.path.join(root, file)
                        if apkpath.endswith("apk"):
                            apkpath = apkpath.replace('/', '\\')
                            s = s + '"' + apkpath + '" '
                r = run_adb_command(f'"{exepath}"' + ' ' + s)

    elif event in (None, '应用设置'):
        setpath = values['kind']
        conf.set("Config", "newFileNamePattern", setpath)
        conf.write(codecs.open(cfgpath, "w", "utf-8"))
        sg.Popup('已成功修改设置为：', setpath, title='成功')

    elif event in (None, '关联到右键菜单'):
        try:
            r = run_adb_command(f'reg add "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名...\\command" /ve /t REG_SZ /d "{exepath}" "%1" /f')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功加入安装包的右键菜单', title='成功')
        except BaseException:
            pass

    elif event in (None, '删除右键菜单'):
        try:
            r = run_adb_command('reg delete "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名..." /f')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功删除安装包的右键菜单', title='成功')
        except BaseException:
            pass

    # tab4的事件
    if event in (None, '激活女娲石'):
        r1 = run_adb_command('shell setprop persist.log.tag.NotificationService DEBUGsetprop persist.log.tag.NotificationService DEBUG')
        window_main['log'].print(r1)
        r2 = run_adb_command('shell pm grant com.oasisfeng.nevo android.permission.READ_LOGS')
        window_main['log'].print(r2)

    if event in (None, '激活小黑屋'):
        r = run_adb_command('shell sh /storage/emulated/0/Android/data/web1n.stopapp/files/starter.sh')
        window_main['log'].print(r)

    if event in (None, '激活Shizuku'):
        r = run_adb_command('shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh')
        window_main['log'].print(r)

    if event in (None, '激活Scene'):
        r = run_adb_command('shell sh /storage/emulated/0/Android/data/com.omarea.vtools/up.sh')
        window_main['log'].print(r)

    elif event in (None, '关于软件'):
        sg.Popup(
            f"{APP_NAME} V{APP_VERSION}",
            "CQApkTools不是一个原创工具，而是一个整合工具。",
            "其中",
            "ApkRenamer 的作者是 AsionTang",
            "ApkInstaller 的汉化者是 御坂初琴",
            "",
            '御坂初琴软件屋',
            "https://ybcq.github.io/",
            "CopyRight By Misaka HatSune 2020-2025",
            title="关于")

    elif event in (None, '作者官网'):
        os.popen('explorer https://ybcq.github.io/')

    # V3.0 新增代码
    if event == '连接设备':
        r = run_adb_command('devices')
        window_main['log'].print(r)

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

        window_main['device_id'].update(value=device_id)
        window_main['status'].update(value=status)
    elif event == '断开连接':
        window_main['device_id'].update(value='')
        window_main['status'].update(value='未连接')

    elif event == '获取前台应用包名':
        package_name = get_top_package_name()
        window_main['pname'].update(value=package_name)

    elif event == '冻结该包':
        package_name = values['pname']
        if package_name:
            change_apk_enable(False, package_name)

    elif event == '解冻该包':
        package_name = values['pname']
        if package_name:
            change_apk_enable(True, package_name)

    elif event == '卸载该包':
        package_name = values['pname']
        if package_name:
            uninstall_apk(package_name, keep_data=False)

    elif event == '重装该包':
        package_name = values['pname']
        if package_name:
            uninstall_apk(package_name, keep_data=True)

window_main.close()
