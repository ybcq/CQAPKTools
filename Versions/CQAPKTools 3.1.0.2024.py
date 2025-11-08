# from operator import length_hint
# from tkinter.tix import Tree
# import subprocess
# import pyperclip
import PySimpleGUI as sg
import os
import configparser
import codecs

curpath = os.path.dirname(os.path.realpath(__file__))
cfgpath = os.path.join(curpath, "CQApkRename.ini")
exepath = os.path.join(curpath, "CQApkRename.exe")
batpath = os.path.join(curpath, "HuaweiSubstW.bat")
lnkpath = os.path.join(curpath, "HuaweiSubstW.lnk")
apkpath = os.path.join(curpath, "ApkInstaller.exe")


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

# MIUI优化窗口布局F
miui_icebox = [
    [sg.Text("以下冻结的应用是在尽可能保留系统正常功能的情况下释放内存占用的列表，不是激进冻结列表")],
    # [sg.Text("如果需要自由冻结应用，请自行使用 adb shell pm disable-user + 包名 或 搞机工具箱",)],
    # [sg.Text("")],
    [sg.Button('冻结Analytics'),
     sg.Button('解冻Analytics'),
     sg.Button('卸载Analytics'),
     sg.Button('重装Analytics'),
     sg.Text("分析服务，通常无用")],
    [sg.Button("冻结Adsolution"),
     sg.Button("解冻Adsolution"),
     sg.Button("卸载Adsolution"),
     sg.Button("重装Adsolution"),
     sg.Text("广告服务，冻结可减少广告")],
    [sg.Button("冻结Joyose"),
     sg.Button("解冻Joyose"),
     sg.Button("卸载Joyose"),
     sg.Button("重装Joyose"),
     sg.Text("温控服务，冻结可能影响计步")],
    [sg.Button("冻结SIM STK"),
     sg.Button("解冻SIM STK"),
     sg.Button("卸载SIM STK"),
     sg.Button("重装SIM STK"),
     sg.Text("SIM卡服务，通常无用")],
    [sg.Button("冻结内容中心"), sg.Button("解冻内容中心"), sg.Button("卸载内容中心"),
     sg.Button("重装内容中心"), sg.Text("桌面上滑的新闻，通常无用")],
    [sg.Button("冻结快应用"), sg.Button("解冻快应用"), sg.Button("卸载快应用"),
     sg.Button("重装快应用"), sg.Text("快应用服务框架，通常无用")],
    [sg.Button("冻结电量与性能"),
     sg.Button("解冻电量与性能"),
     sg.Button("卸载电量与性能"),
     sg.Button("重装电量与性能"),
     sg.Text("冻结可开启全局高刷，会导致耗电更快")],
    [sg.Button("冻结系统更新"), sg.Button("解冻系统更新"), sg.Button(
        "卸载系统更新"), sg.Button("还原系统更新"), sg.Text("解锁ID机专用")],
    [sg.Text("")],
    [sg.Button("一键冻结"), sg.Button("一键解冻"), sg.Button("一键卸载"),
     sg.Button("一键重装"), sg.Text("冻结、解冻、卸载和重装除了电量与性能以外的所有项")],
    [sg.InputText(key='pname', size=(30, 5)), sg.Button("获取前台应用包名"), sg.Button("冻结该包"), sg.Button("解冻该包"), sg.Button("卸载该包"), sg.Button("重装该包")]
]

miui_icebox_list = [[sg.Text("导入一个CSV格式的列表，每行均为要冻结或者卸载的包名")],
                     [sg.InputText(key='filelist'),
                     sg.FileBrowse(button_text="...",
                                   key='filelist',
                                   file_types=(("CSV格式应用列表", "*.csv"),)
                                   )],
                    [sg.Button("一键冻结列表"),
                     sg.Button("一键解冻列表"),
                     sg.Button("一键卸载列表"),
                     sg.Button("一键重装列表")],
                     # sg.Text("冻结、解冻、卸载和重装导入的列表的所有项"),
                    ]

miui_catoon = [
    [
        sg.Button('无动画'), sg.Button('快速'), sg.Button('默认设置'), sg.Button("优雅")], [
            sg.InputText(
                key='speed1', default_text="1.5", size=(
                    5, 5)), sg.InputText(
                        key='speed2', default_text="1.5", size=(
                            5, 5)), sg.InputText(
                                key='speed3', default_text="1.5", size=(
                                    5, 5)), sg.Button("自定义速度"), sg.Text("该设置会影响所有系统动画")]]

miui_better = [
    [sg.Text("该设置可能会引起微信后台不稳定，推荐在备用机上使用。该设置重启后保留")],
    [sg.Button('无后台'), sg.Button('激进'), sg.Button('轻快'), sg.Button("默认限制")],
    [sg.InputText(key='level', size=(5, 5), default_text="16"), sg.Text("数字范围0-16，0表示无后台，16表示默认值")],
    [sg.Button('调整后台参数'), sg.Button('开启墓碑进程'), sg.Button('关闭墓碑进程')]
]

miui_exchange = [
    [sg.Text("可用于一键替换手机上的应用为定制版。该操作可能会删除被降级的应用的数据(比如聊天记录)，请谨慎操作")],
    [sg.Text("选择文件夹"), sg.InputText(key='apkfolder'), sg.FolderBrowse(button_text="...", key='path')],
    [sg.Button("整理文件夹中的文件名"), sg.Button("卸载并安装文件夹中的应用"), sg.Button("仅安装文件夹中的所有应用"), sg.Button('仅替换已安装的应用')],
]

def uninstallappk(package_name):
    try:
        r = os.popen('adb shell pm uninstall -k ' + package_name).read()
        window_main['log'].print(r)
        # window_main['log'].print(f"卸载应用 {package_name}\n")
        return r
    except Exception as e:
        window_main['log'].print(f"卸载应用 {package_name} 失败: {e}\n")

def uninstallapp(package_name):
    try:
        r = os.popen('adb shell pm uninstall ' + package_name).read()
        window_main['log'].print(r)
        # window_main['log'].print(f"卸载应用 {package_name}\n")
        return r
    except Exception as e:
        window_main['log'].print(f"卸载应用 {package_name} 失败: {e}\n")
        
def installapk(apk_path):
    try:
        r = os.popen('adb install -r -t -d "' + apk_path + '"').read()
        window_main['log'].print(r)
        # window_main['log'].print(f"安装应用 {apk_path}\n")
        return r
    except Exception as e:
        window_main['log'].print(f"安装应用 {apk_path} 失败: {e}\n")

def checkappexists(package_name):
    result = os.popen('adb shell pm list packages').read()
    return package_name in result

def processapps(action):
    path = values['path']
    if path:
        for apk_file in os.listdir(path):
            if apk_file.endswith(".apk"):
                package_name = apk_file[:-4]
                apk_path = os.path.join(path, apk_file)
                window_main['log'].print(f"处理应用 {package_name}\n")
                if action == '仅替换':
                    if checkappexists(package_name):
                        uninstallapp(package_name)
                        installapk(apk_path)
                elif action == '卸载并安装':
                    uninstallapp(package_name)
                    installapk(apk_path)
                elif action == '仅安装':
                    installapk(apk_path)
    window_main['log'].print(f'处理应用文件夹结束。\n')


other_adb = [
    [sg.Button("激活女娲石"), sg.Text("同步移除")],
    [sg.Button("激活小黑屋"), sg.Text("麦克斯韦妖模式")],
    [sg.Button("激活Shizuku"), sg.Text("比无线调试更稳定")],
    [sg.Button("激活Scene"), sg.Text("手机管理工具")],
    # [sg.Button("激活爱玩机工具箱"),sg.Text("尚未实现")],
]

# 定义标签页内容
tab1_layout = [
    [sg.Frame("列表冻结", miui_icebox_list, expand_x=True)],
    [sg.Frame("常用冻结", miui_icebox)],
]

# 定义标签页内容
tab5_layout = [
    [sg.Frame("后台策略", miui_better, expand_x=True)],
    [sg.Frame("一键降级", miui_exchange, expand_x=True)],
    [sg.Frame("应用激活", other_adb, expand_x=True)],
    [sg.Frame("动画设置", miui_catoon, expand_x=True)],
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
    [sg.Button('为华为移动引擎安装软件'), sg.Text("打开汉化版的ApkInstaller")],
]

tab2_layout = [
    [sg.Frame("共享磁盘", huawei_disk, expand_x=True)],
    [sg.Frame("其他功能", huawei_other, expand_x=True)],
]

# 批量重命名窗口布局
rename_path = [
    [
        sg.Text("选择单文件"), sg.InputText(
            key='file', expand_x=True), sg.FileBrowse(
                button_text="...", key='file', file_types=(("安卓应用安装包", "*.apk"),))], [
                    sg.Text("选择文件夹"), sg.InputText(
                        key='path', expand_x=True), sg.FolderBrowse(
                            button_text="...", key='path')]]

rename_set = [
    [sg.Text("表达式：{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}")],
    [sg.InputText(key='kind', default_text=newFileNamePattern, expand_x=True)],
    [sg.Button('应用设置'), sg.Button("关联到右键菜单"), sg.Button("删除右键菜单")]
]

tab3_layout = [
    [sg.Frame("重命名操作", rename_path, expand_x=True), sg.Button('开始重命名')],
    [sg.Frame("重命名设置", rename_set, expand_x=True)],
]

'''
tab4_layout = [
    [sg.Frame("ADB激活",other_adb,expand_x=True)]
]
'''

layout_about = [
    [sg.Button('关于软件'), sg.Button('作者官网')]
]

# 主窗口布局，包含四个标签页
layout = [
    [sg.Text('设备ID'),
     sg.InputText(key='device_id',
                  disabled=True,
                  expand_x=True,
                  text_color="Black"),
     sg.Text('状态',
             key='status'),
     sg.Button('连接设备'),
     sg.Button('断开连接')],
    [sg.TabGroup([[ 
        sg.Tab('通用优化', tab5_layout),
        sg.Tab('澎湃冻结', tab1_layout),
        sg.Tab('华为引擎', tab2_layout),
        sg.Tab('批量命名', tab3_layout),
        # sg.Tab('其他功能', tab4_layout)
    ]])],
    [sg.Multiline(key='log', disabled=True, size=(96, 10), expand_x=True)],
    [sg.Frame("关于", layout_about, expand_x=True)],
]

window_main = sg.Window('CQADBTools 3.1.0.2024', layout)

# 存储日志的列表
log_buffer = []

# 冻结子函数，True为解冻，False为冻结
def apkchange(state, name):
    if state:
        st = "enable"
    else:
        st = "disable-user"

    r = os.popen('adb shell pm ' + st + " " + name).read()
    # log_buffer.append(r)
    window_main['log'].print(r)

# 卸载子函数


def apkuninstall(state, name):
    if not state:
        r = os.popen('adb shell pm uninstall -k --user 0 ' + name).read()
        # log_buffer.append(r)
        window_main['log'].print(r)
    else:
        r = os.popen('adb shell pm install-existing --user 0 ' + name).read()
        # log_buffer.append(r)
        window_main['log'].print(r)

# 调整动画子函数


def dhchange(sulv1, sulv2, sulv3):
    r = os.popen(
        'adb shell settings put global window_animation_scale ' +
        sulv1).read()
    # log_buffer.append(r)
    window_main['log'].print(r)
    r = os.popen(
        'adb shell settings put global transition_animation_scale ' +
        sulv2).read()
    # log_buffer.append(r)
    window_main['log'].print(r)
    r = os.popen(
        'adb shell settings put global animator_duration_scale ' +
        sulv3).read()
    # log_buffer.append(r)
    window_main['log'].print(r)

# CSV列表函数


def processlist(action, filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                package_name = line.strip()  # 去除可能的空白字符
                if package_name:  # 如果行不为空
                    if action == '冻结':
                        apkchange(False, package_name)  # 冻结应用
                    elif action == '解冻':
                        apkchange(True, package_name)  # 解冻应用
                    elif action == '卸载':
                        apkuninstall(False, package_name)  # 卸载应用
                    elif action == '重装':
                        apkuninstall(True, package_name)  # 重装应用
                    window_main['log'].print(f"{action} {package_name}")
    except Exception as e:
        window_main['log'].print(f'读取文件时发生错误: {e}\n')
    window_main['log'].print(f'处理应用列表结束。\n')

# 修改文件名
def gettoppackagename():
    try:
        r = os.popen('adb shell dumpsys activity top | grep ACTIVITY').read()
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

def changenames(apkfolder):    
    conf.set("Config", "newFileNamePattern", r"{应用包名}")
    conf.write(codecs.open(cfgpath, "w", "utf-8"))
    
    s = ""  # 路径整合
    if apkfolder is not None:
        if os.path.exists(apkfolder):
            for root, dirs, files in os.walk(apkfolder):
                for file in files:
                    apkpath = os.path.join(root, file)
                    # print (apkpath)
                    if apkpath.endswith("apk"):
                        apkpath = apkpath.replace('/', '\\')
                        s = s + '"' + apkpath + '" '
            print(f'"{exepath}"' + ' ' + s)
            os.popen(f'"{exepath}"' + ' ' + s)
    
    setpath = values['kind']
    conf.set("Config", "newFileNamePattern", setpath)
    conf.write(codecs.open(cfgpath, "w", "utf-8"))


# Create the event loop
while True:
    event, values = window_main.read()

    if event in (None, 'Close'):
        break

    # tab1的事件
    elif event in (None, '冻结Analytics'):
        apkchange(False, "com.miui.analytics")

    elif event in (None, '解冻Analytics'):
        apkchange(True, "com.miui.analytics")

    elif event in (None, '冻结Joyose'):
        apkchange(False, "com.xiaomi.joyose")

    elif event in (None, '解冻Joyose'):
        apkchange(True, "com.xiaomi.joyose")

    elif event in (None, '冻结Adsolution'):
        apkchange(False, "com.miui.systemAdSolution")

    elif event in (None, '解冻Adsolution'):
        apkchange(True, "com.miui.systemAdSolution")

    elif event in (None, '冻结SIM STK'):
        apkchange(False, "com.android.stk")

    elif event in (None, '解冻SIM STK'):
        apkchange(True, "com.android.stk")

    elif event in (None, '冻结快应用'):
        apkchange(False, "com.miui.hybrid")

    elif event in (None, '解冻快应用'):
        apkchange(True, "com.miui.hybrid")

    elif event in (None, '冻结内容中心'):
        apkchange(False, "com.miui.newhome")

    elif event in (None, '解冻内容中心'):
        apkchange(True, "com.miui.newhome")

    elif event in (None, '冻结电量与性能'):
        apkchange(False, "com.miui.powerkeeper")

    elif event in (None, '解冻电量与性能'):
        apkchange(False, "com.miui.powerkeeper")

    elif event in (None, '冻结系统更新'):
        apkchange(True, "com.android.updater")

    elif event in (None, '解冻系统更新'):
        apkchange(False, "com.android.updater")

    elif event in (None, '卸载Analytics'):
        apkuninstall(False, "com.miui.analytics")

    elif event in (None, '重装Analytics'):
        apkuninstall(True, "com.miui.analytics")

    elif event in (None, '卸载Joyose'):
        apkuninstall(False, "com.xiaomi.joyose")

    elif event in (None, '重装Joyose'):
        apkuninstall(True, "com.xiaomi.joyose")

    elif event in (None, '卸载Adsolution'):
        apkuninstall(False, "com.miui.systemAdSolution")

    elif event in (None, '重装Adsolution'):
        apkuninstall(True, "com.miui.systemAdSolution")

    elif event in (None, '卸载SIM STK'):
        apkuninstall(False, "com.android.stk")

    elif event in (None, '重装SIM STK'):
        apkuninstall(True, "com.android.stk")

    elif event in (None, '卸载快应用'):
        apkuninstall(False, "com.miui.hybrid")

    elif event in (None, '重装快应用'):
        apkuninstall(True, "com.miui.hybrid")

    elif event in (None, '卸载内容中心'):
        apkuninstall(False, "com.miui.newhome")

    elif event in (None, '重装内容中心'):
        apkuninstall(True, "com.miui.newhome")

    elif event in (None, '卸载电量与性能'):
        apkuninstall(False, "com.miui.powerkeeper")

    elif event in (None, '重装电量与性能'):
        apkuninstall(True, "com.miui.powerkeeper")

    elif event in (None, '卸载系统更新'):
        apkuninstall(False, "com.android.updater")

    elif event in (None, '重装系统更新'):
        apkuninstall(True, "com.android.updater")

    elif event in (None, '一键冻结'):
        apkchange(True, "com.miui.analytics")
        apkchange(True, "com.xiaomi.joyose")
        apkchange(True, "com.miui.systemAdSolution")
        apkchange(True, "com.android.stk")
        apkchange(True, "com.miui.hybrid")
        apkchange(True, "com.miui.newhome")

    elif event in (None, '一键解冻'):
        apkuninstall(False, "com.miui.analytics")
        apkuninstall(False, "com.xiaomi.joyose")
        apkuninstall(False, "com.miui.systemAdSolution")
        apkuninstall(False, "com.android.stk")
        apkuninstall(False, "com.miui.hybrid")
        apkuninstall(False, "com.miui.newhome")

    elif event in (None, '一键卸载'):
        apkuninstall(False, "com.miui.analytics")
        apkuninstall(False, "com.xiaomi.joyose")
        apkuninstall(False, "com.miui.systemAdSolution")
        apkuninstall(False, "com.android.stk")
        apkuninstall(False, "com.miui.hybrid")
        apkuninstall(False, "com.miui.newhome")

    elif event in (None, '一键重装'):
        apkuninstall(True, "com.miui.analytics")
        apkuninstall(True, "com.xiaomi.joyose")
        apkuninstall(True, "com.miui.systemAdSolution")
        apkuninstall(True, "com.android.stk")
        apkuninstall(True, "com.miui.hybrid")
        apkuninstall(True, "com.miui.newhome")

    elif event == '一键冻结列表':
        filepath = values['filelist']
        if filepath:
            processlist('冻结', filepath)

    elif event == '一键解冻列表':
        filepath = values['filelist']
        if filepath:
            processlist('解冻', filepath)

    elif event == '一键卸载列表':
        filepath = values['filelist']
        if filepath:
            processlist('卸载', filepath)

    elif event == '一键重装列表':
        filepath = values['filelist']
        if filepath:
            processlist('重装', filepath)

    elif event == '整理文件夹中的文件名':
        changenames(values['apkfolder'])

    elif event == '卸载并安装文件夹中的应用':
        # print('卸载并重装')
        processapps('卸载并重装')

    elif event == '仅安装文件夹中的所有应用':
        # print('仅安装')
        processapps('仅安装')
    
    elif event == '仅替换已安装的应用':
        # print('仅替换')
        processapps('仅替换')

    # tab5的事件
    elif event in (None, '无动画'):
        r = dhchange("0", "0", "0")
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '快速'):
        r = dhchange("0.5", "0.5", "0.5")
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '默认设置'):
        r = dhchange("1", "1", "1")
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '优雅'):
        r = dhchange("1.5", "1.34", "1.17")
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '自定义速度'):
        r = dhchange(values['speed1'], values['speed2'], values['speed3'])
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '无后台'):
        os.popen(
            'adb shell settings put global activity_manager_constants max_cached_processes=0')
        r = os.popen(
            'adb shell get settings put global activity_manager_constants').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '激进'):
        os.popen(
            'adb shell settings put global activity_manager_constants max_cached_processes=1')
        r = os.popen(
            'adb shell get settings put global activity_manager_constants').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '轻快'):
        os.popen(
            'adb shell settings put global activity_manager_constants max_cached_processes=4')
        r = os.popen(
            'adb shell get settings put global activity_manager_constants').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '默认限制'):
        os.popen(
            'adb shell settings put global activity_manager_constants max_cached_processes=16')
        r = os.popen(
            'adb shell get settings put global activity_manager_constants').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '调整后台参数'):
        level = values['level']
        os.popen(
            'adb shell settings put global activity_manager_constants max_cached_processes=' +
            level)
        r = os.popen(
            'adb shell get settings put global activity_manager_constants').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '开启墓碑进程'):
        r = os.popen(
            'adb shell device_config put activity_manager_native_boot use_freezer true && adb reboot').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    elif event in (None, '关闭墓碑进程'):
        r = os.popen(
            'adb shell device_config put activity_manager_native_boot use_freezer false && adb reboot').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    # tab2的事件
    elif event in (None, '映射共享目录为W盘'):
        os.popen('subst w: %appdata%\\Huawei\\Emulator\\Share')
        sg.Popup('已成功映射共享目录为W盘，如果不显示就多刷新几下。', title='成功')
        os.popen('explorer')

    elif event in (None, '取消映射共享磁盘'):
        os.popen('subst w: /d')
        sg.Popup('已取消映射华为移动应用引擎到W盘！', title='成功')

    elif event in (None, '设置开机自动映射共享目录'):
        os.popen(
            r'xcopy "' +
            batpath +
            r'" "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup"')
        sg.Popup('已成功设置开机自动映射共享目录。', title='成功')

    elif event in (None, '使用网络路径方式创建共享目录图标'):
        os.popen(
            r'copy "' +
            lnkpath +
            r'" "%appdata%\Microsoft\Windows\Network Shortcuts\安卓磁盘 (W).lnk"')
        sg.Popup('已成功使用网络路径方式创建共享目录图标。', title='成功')
        os.popen('explorer')

    elif event in (None, '安装华为移动引擎'):
        os.popen('explorer https://space.bilibili.com/28516198')

    elif event in (None, '杀死华为移动引擎'):
        os.popen('taskkill /f /im MobileAppEngine.exe')
        sg.Popup('已关闭华为应用引擎', title="成功")

    elif event in (None, '为华为移动引擎安装软件'):
        try:
            os.popen('call "' + apkpath + '"')
            # r=os.popen('start ' + apkpath).read()
            # if r.find("拒绝"):
            # sg.Popup('权限不足，请使用管理员身份运行该软件',title='权限不足')
        except BaseException:
            sg.Popup('请使用管理员身份运行该软件', title='权限不足')

    elif event in (None, '开始重命名'):
        # User closed the Window or hit the Cancel button
        # 单文件
        print(values['file'])
        try:
            filepath = values['file']
        except BaseException:
            break
        # print(filepath)
        if filepath is not None:
            if os.path.exists(filepath):
                os.popen(f'"{exepath}"' + ' "' + filepath + '"')

        # 多文件
        pathpath = values['path']
        s = ""  # 路径整合
        if pathpath is not None:
            if os.path.exists(pathpath):
                for root, dirs, files in os.walk(pathpath):
                    for file in files:
                        apkpath = os.path.join(root, file)
                        # print (apkpath)
                        if apkpath.endswith("apk"):
                            apkpath = apkpath.replace('/', '\\')
                            s = s + '"' + apkpath + '" '
                print(f'"{exepath}"' + ' ' + s)
                os.popen(f'"{exepath}"' + ' ' + s)

    elif event in (None, '应用设置'):
        setpath = values['kind']
        conf.set("Config", "newFileNamePattern", setpath)
        conf.write(codecs.open(cfgpath, "w", "utf-8"))
        sg.Popup('已成功修改设置为：', setpath, title='成功')

    elif event in (None, '关联到右键菜单'):
        # 使用RegOpenKey打开注册表项
        try:
            r = os.popen(
                f'reg add "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名...\\command" /ve /t REG_SZ /d "\\"{exepath}\\" \\"%1\\"" /f').read()
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功加入安装包的右键菜单', title='成功')
        except BaseException:
            break

    elif event in (None, '删除右键菜单'):
        # 使用RegOpenKey打开注册表项
        try:
            r = os.popen(
                'reg delete "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名..." /f').read()
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功删除安装包的右键菜单', title='成功')
        except BaseException:
            break

    # tab4的事件
    if event in (None, '激活女娲石'):
        r1 = os.popen(
            'adb shell setprop persist.log.tag.NotificationService DEBUGsetprop persist.log.tag.NotificationService DEBUG').read()
        log_buffer.append(r1)
        window_main['log'].print(r1)
        r2 = os.popen(
            'adb shell pm grant com.oasisfeng.nevo android.permission.READ_LOGS').read()
        log_buffer.append(r2)
        window_main['log'].print(r2)

    if event in (None, '激活小黑屋'):
        r = os.popen(
            'adb shell sh /storage/emulated/0/Android/data/web1n.stopapp/files/starter.sh').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

    if event in (None, '激活Shizuku'):
        r = os.popen(
            'adb shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

        # sg.Popup('已尝试激活，返回值为：',r,title="成功")

    if event in (None, '激活Scene'):
        r = os.popen(
            'adb shell sh /data/user/0/com.omarea.vtools/files/up.sh').read()
        # log_buffer.append(r)
        window_main['log'].print(r)

        # sg.Popup('已尝试激活，返回值为：',r,title="成功")

    # if event in (None,'激活爱玩机工具箱'):
        # r=os.popen('adb shell settings put global activity_manager_constants max_cached_processes=16').read()
        # sg.Popup('已尝试激活，返回值为：',r,title="成功")

    elif event in (None, '关于软件'):
        sg.Popup(
            "CQApkTools Ver 3.1.0.2024",
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
        # 执行 adb devices 命令
        r = os.popen('adb devices').read()
        # 更新日志
        log_buffer.append(r)
        window_main['log'].print(r)

        # 解析设备列表
        lines = r.strip().split('\n')
        # 初始化设备ID和状态
        device_id = '无设备'
        status = '未连接'

        # 遍历每一行，找到设备信息
        for line in lines:
            if line and not line.startswith('List of devices attached'):
                parts = line.split('\t')
                if len(parts) > 1 and parts[1] == 'device':
                    device_id = parts[0]
                    status = '已连接'
                    break

        # 更新设备ID和状态
        window_main['device_id'].update(value=device_id)
        window_main['status'].update(value=status)
    elif event == '断开连接':
        # 清空设备ID和状态
        window_main['device_id'].update(value='')
        window_main['status'].update(value='未连接')
        # 可以在这里添加断开连接的代码

    # 获取前台应用包名
    elif event == '获取前台应用包名':
        package_name = gettoppackagename()
        window_main['pname'].update(value=package_name)
        if package_name != "无法获取前台应用包名":
            # window_main['log'].print(f"前台应用包名: {package_name}\n")
            continue
        else:
            # window_main['log'].print(package_name + "\n")
            continue

    # 冻结前台应用
    elif event == '冻结该包':
        package_name = values['pname']
        if package_name:
            apkchange(False, package_name)

    # 解冻前台应用
    elif event == '解冻该包':
        package_name = values['pname']
        if package_name:
            apkchange(True, package_name)

    # 卸载前台应用
    elif event == '卸载该包':
        package_name = values['pname']
        if package_name:
            apkuninstall(False, package_name)

    # 重装前台应用
    elif event == '重装该包':
        package_name = values['pname']
        if package_name:
            apkuninstall(True, package_name)
        
window_main.close()
