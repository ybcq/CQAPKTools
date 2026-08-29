"""通用优化标签页 - 后台策略、一键降级、应用激活、动画设置"""
import PySimpleGUI as sg
from models.CQAPKTools import (
    run_adb_command, change_animation_speed,
    organize_files_in_folder, process_apk_files_in_folder
)

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ====== 布局 ======
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

layout = [
    [sg.Frame("后台策略", miui_better, expand_x=True)],
    [sg.Frame("一键降级", miui_exchange, expand_x=True)],
    [sg.Frame("应用激活", other_adb, expand_x=True)],
    [sg.Frame("动画设置", miui_catoon, expand_x=True)]
]


# ====== 事件处理 ======
def handle_event(window, event, values):
    """处理通用优化标签页的事件，返回 True 表示已处理"""
    # 动画设置
    if event == '无动画':
        r = change_animation_speed(window, "0", "0", "0")
        window['log'].print(r)
    elif event == '快速':
        r = change_animation_speed(window, "0.5", "0.5", "0.5")
        window['log'].print(r)
    elif event == '默认设置':
        r = change_animation_speed(window, "1", "1", "1")
        window['log'].print(r)
    elif event == '优雅':
        r = change_animation_speed(window, "1.5", "1.34", "1.17")
        window['log'].print(r)
    elif event == '自定义速度':
        r = change_animation_speed(window, values['speed1'], values['speed2'], values['speed3'])
        window['log'].print(r)

    # 后台策略
    elif event == '无后台':
        r = run_adb_command(window, 'shell settings put global activity_manager_constants max_cached_processes=0')
        window['log'].print(r)
    elif event == '激进':
        r = run_adb_command(window, 'shell settings put global activity_manager_constants max_cached_processes=1')
        window['log'].print(r)
    elif event == '轻快':
        r = run_adb_command(window, 'shell settings put global activity_manager_constants max_cached_processes=4')
        window['log'].print(r)
    elif event == '默认限制':
        r = run_adb_command(window, 'shell settings put global activity_manager_constants max_cached_processes=16')
        window['log'].print(r)
    elif event == '调整后台参数':
        level = values['level']
        r = run_adb_command(window, f'shell settings put global activity_manager_constants max_cached_processes={level}')
        window['log'].print(r)
    elif event == '开启墓碑进程':
        r = run_adb_command(window, 'shell device_config put activity_manager_native_boot use_freezer true && adb reboot')
        window['log'].print(r)
    elif event == '关闭墓碑进程':
        r = run_adb_command(window, 'shell device_config put activity_manager_native_boot use_freezer false && adb reboot')
        window['log'].print(r)

    # 一键降级
    elif event == '整理文件夹中的文件名':
        folder_path = values['apkfolder']
        if folder_path:
            organize_files_in_folder(window, folder_path)
    elif event == '卸载并安装文件夹中的应用':
        process_apk_files_in_folder(window, values['apkfolder'], "uninstall_install")
    elif event == '仅安装文件夹中的所有应用':
        process_apk_files_in_folder(window, values['apkfolder'], "install_only")
    elif event == '仅替换已安装的应用':
        process_apk_files_in_folder(window, values['apkfolder'], "replace")

    # 应用激活
    elif event == '激活女娲石':
        r1 = run_adb_command(window, 'shell setprop persist.log.tag.NotificationService DEBUGsetprop persist.log.tag.NotificationService DEBUG')
        window['log'].print(r1)
        r2 = run_adb_command(window, 'shell pm grant com.oasisfeng.nevo android.permission.READ_LOGS')
        window['log'].print(r2)
    elif event == '激活小黑屋':
        r = run_adb_command(window, 'shell sh /storage/emulated/0/Android/data/web1n.stopapp/files/starter.sh')
        window['log'].print(r)
    elif event == '激活Shizuku':
        r = run_adb_command(window, 'shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh')
        window['log'].print(r)
    elif event == '激活Scene':
        r = run_adb_command(window, 'shell sh /storage/emulated/0/Android/data/com.omarea.vtools/up.sh')
        window['log'].print(r)

    else:
        return False
    return True