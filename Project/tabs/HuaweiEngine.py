"""华为引擎标签页 - 共享磁盘映射、引擎管理"""
import PySimpleGUI as sg
import os
from models.CQAPKTools import run_adb_command

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ====== 布局 ======
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

layout = [
    [sg.Frame("共享磁盘", huawei_disk, expand_x=True)],
    [sg.Frame("其他功能", huawei_other, expand_x=True)]
]


# ====== 事件处理 ======
def handle_event(window, event, values, ctx):
    """处理华为引擎标签页的事件，返回 True 表示已处理"""
    batpath = ctx['batpath']
    lnkpath = ctx['lnkpath']
    apkpath = ctx['apkpath']

    if event == '映射共享目录为W盘':
        r = run_adb_command(window, 'shell subst w: %appdata%\\Huawei\\Emulator\\Share')
        sg.Popup('已成功映射共享目录为W盘，如果不显示就多刷新几下。', title='成功')
        os.popen('explorer')

    elif event == '取消映射共享磁盘':
        r = run_adb_command(window, 'shell subst w: /d')
        sg.Popup('已取消映射华为移动应用引擎到W盘！', title='成功')

    elif event == '设置开机自动映射共享目录':
        r = run_adb_command(window, f'reg add "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名...\\command" /ve /t REG_SZ /d "{batpath}" "%1" /f')
        if r.find("拒绝"):
            sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
        else:
            sg.Popup('已成功设置开机自动映射共享目录。', title='成功')

    elif event == '使用网络路径方式创建共享目录图标':
        r = run_adb_command(window, f'copy "{lnkpath}" "%appdata%\\Microsoft\\Windows\\Network Shortcuts\\安卓磁盘 (W).lnk"')
        sg.Popup('已成功使用网络路径方式创建共享目录图标。', title='成功')
        os.popen('explorer')

    elif event == '安装华为移动引擎':
        os.popen('explorer https://space.bilibili.com/28516198')

    elif event == '杀死华为移动引擎':
        r = run_adb_command(window, 'taskkill /f /im MobileAppEngine.exe')
        sg.Popup('已关闭华为应用引擎', title="成功")

    elif event == '为华为移动引擎安装软件':
        try:
            r = run_adb_command(window, f'call "{apkpath}"')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
        except BaseException:
            sg.Popup('请使用管理员身份运行该软件', title='权限不足')

    else:
        return False
    return True