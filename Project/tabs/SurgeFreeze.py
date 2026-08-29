"""澎湃冻结标签页 - MIUI 应用冻结/卸载管理"""
import PySimpleGUI as sg
from models.CQAPKTools import (
    change_apk_enable, uninstall_apk, process_one_key_list, get_top_package_name
)
from models.ResetSystemApps import check_device_connected, scan_system_app_updates, reinstall_updated_apps

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ====== 布局 ======
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

miui_icebox_list = [
    [sg.Text("导入一个CSV格式的列表，每行均为要冻结或者卸载的包名")],
    [sg.InputText(key='filelist'), sg.FileBrowse(button_text="...", key='filelist', file_types=(("CSV格式应用列表", "*.csv"),))],
    [sg.Button("一键冻结列表"), sg.Button("一键解冻列表"), sg.Button("一键卸载列表"), sg.Button("一键重装列表")],
]

miui_app_update = [
    [sg.Text("检测系统中已更新的应用，置顶重新安装后可在手机应用管理中手动「卸载更新」回退出厂版本（应用数据保留）")],
    [sg.Button("检测系统应用更新"), sg.Button("一键置顶并卸载更新"), sg.Text("install-existing 置顶法")]
]

layout = [
    [sg.Frame("列表冻结", miui_icebox_list, expand_x=True)],
    [sg.Frame("常用冻结", miui_icebox, expand_x=True)],
    [sg.Frame("系统应用更新", miui_app_update, expand_x=True)]
]


# ====== 事件处理 ======
def handle_event(window, event, values):
    """处理澎湃冻结标签页的事件，返回 True 表示已处理"""
    if event == '冻结Analytics':
        change_apk_enable(window, False, "com.miui.analytics")
    elif event == '解冻Analytics':
        change_apk_enable(window, True, "com.miui.analytics")
    elif event == '冻结Joyose':
        change_apk_enable(window, False, "com.xiaomi.joyose")
    elif event == '解冻Joyose':
        change_apk_enable(window, True, "com.xiaomi.joyose")
    elif event == '冻结Adsolution':
        change_apk_enable(window, False, "com.miui.systemAdSolution")
    elif event == '解冻Adsolution':
        change_apk_enable(window, True, "com.miui.systemAdSolution")
    elif event == '冻结SIM STK':
        change_apk_enable(window, False, "com.android.stk")
    elif event == '解冻SIM STK':
        change_apk_enable(window, True, "com.android.stk")
    elif event == '冻结快应用':
        change_apk_enable(window, False, "com.miui.hybrid")
    elif event == '解冻快应用':
        change_apk_enable(window, True, "com.miui.hybrid")
    elif event == '冻结内容中心':
        change_apk_enable(window, False, "com.miui.newhome")
    elif event == '解冻内容中心':
        change_apk_enable(window, True, "com.miui.newhome")
    elif event == '冻结电量与性能':
        change_apk_enable(window, False, "com.miui.powerkeeper")
    elif event == '解冻电量与性能':
        change_apk_enable(window, False, "com.miui.powerkeeper")
    elif event == '冻结系统更新':
        change_apk_enable(window, True, "com.android.updater")
    elif event == '解冻系统更新':
        change_apk_enable(window, False, "com.android.updater")
    elif event == '卸载Analytics':
        uninstall_apk(window, "com.miui.analytics", keep_data=False)
    elif event == '重装Analytics':
        uninstall_apk(window, "com.miui.analytics", keep_data=True)
    elif event == '卸载Joyose':
        uninstall_apk(window, "com.xiaomi.joyose", keep_data=False)
    elif event == '重装Joyose':
        uninstall_apk(window, "com.xiaomi.joyose", keep_data=True)
    elif event == '卸载Adsolution':
        uninstall_apk(window, "com.miui.systemAdSolution", keep_data=False)
    elif event == '重装Adsolution':
        uninstall_apk(window, "com.miui.systemAdSolution", keep_data=True)
    elif event == '卸载SIM STK':
        uninstall_apk(window, "com.android.stk", keep_data=False)
    elif event == '重装SIM STK':
        uninstall_apk(window, "com.android.stk", keep_data=True)
    elif event == '卸载快应用':
        uninstall_apk(window, "com.miui.hybrid", keep_data=False)
    elif event == '重装快应用':
        uninstall_apk(window, "com.miui.hybrid", keep_data=True)
    elif event == '卸载内容中心':
        uninstall_apk(window, "com.miui.newhome", keep_data=False)
    elif event == '重装内容中心':
        uninstall_apk(window, "com.miui.newhome", keep_data=True)
    elif event == '卸载电量与性能':
        uninstall_apk(window, "com.miui.powerkeeper", keep_data=False)
    elif event == '重装电量与性能':
        uninstall_apk(window, "com.miui.powerkeeper", keep_data=True)
    elif event == '卸载系统更新':
        uninstall_apk(window, "com.android.updater", keep_data=False)
    elif event == '重装系统更新':
        uninstall_apk(window, "com.android.updater", keep_data=True)
    elif event == '一键冻结':
        change_apk_enable(window, True, "com.miui.analytics")
        change_apk_enable(window, True, "com.xiaomi.joyose")
        change_apk_enable(window, True, "com.miui.systemAdSolution")
        change_apk_enable(window, True, "com.android.stk")
        change_apk_enable(window, True, "com.miui.hybrid")
        change_apk_enable(window, True, "com.miui.newhome")
    elif event == '一键解冻':
        uninstall_apk(window, "com.miui.analytics", keep_data=False)
        uninstall_apk(window, "com.xiaomi.joyose", keep_data=False)
        uninstall_apk(window, "com.miui.systemAdSolution", keep_data=False)
        uninstall_apk(window, "com.android.stk", keep_data=False)
        uninstall_apk(window, "com.miui.hybrid", keep_data=False)
        uninstall_apk(window, "com.miui.newhome", keep_data=False)
    elif event == '一键卸载':
        uninstall_apk(window, "com.miui.analytics", keep_data=False)
        uninstall_apk(window, "com.xiaomi.joyose", keep_data=False)
        uninstall_apk(window, "com.miui.systemAdSolution", keep_data=False)
        uninstall_apk(window, "com.android.stk", keep_data=False)
        uninstall_apk(window, "com.miui.hybrid", keep_data=False)
        uninstall_apk(window, "com.miui.newhome", keep_data=False)
    elif event == '一键重装':
        uninstall_apk(window, "com.miui.analytics", keep_data=True)
        uninstall_apk(window, "com.xiaomi.joyose", keep_data=True)
        uninstall_apk(window, "com.miui.systemAdSolution", keep_data=True)
        uninstall_apk(window, "com.android.stk", keep_data=True)
        uninstall_apk(window, "com.miui.hybrid", keep_data=True)
        uninstall_apk(window, "com.miui.newhome", keep_data=True)
    elif event == '一键冻结列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list(window, '冻结', file_path)
    elif event == '一键解冻列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list(window, '解冻', file_path)
    elif event == '一键卸载列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list(window, '卸载', file_path)
    elif event == '一键重装列表':
        file_path = values['filelist']
        if file_path:
            process_one_key_list(window, '重装', file_path)
    elif event == '获取前台应用包名':
        package_name = get_top_package_name(window)
        window['pname'].update(value=package_name)
    elif event == '冻结该包':
        package_name = values['pname']
        if package_name:
            change_apk_enable(window, False, package_name)
    elif event == '解冻该包':
        package_name = values['pname']
        if package_name:
            change_apk_enable(window, True, package_name)
    elif event == '卸载该包':
        package_name = values['pname']
        if package_name:
            uninstall_apk(window, package_name, keep_data=False)
    elif event == '重装该包':
        package_name = values['pname']
        if package_name:
            uninstall_apk(window, package_name, keep_data=True)
    elif event == '检测系统应用更新':
        results = scan_system_app_updates(log=lambda msg: window['log'].print(msg))
        updated = [r for r in results if r['has_update']]
        window['log'].print(f"检测完成：系统应用 {len(results)} 个，有更新 {len(updated)} 个")
        if updated:
            pkgs = '\n'.join(f"  {r['pkg']}" for r in updated)
            sg.Popup(f"发现 {len(updated)} 个已更新的系统应用：\n{pkgs}", title='检测结果')
        else:
            sg.Popup('未发现已更新的系统应用', title='检测结果')
    elif event == '一键置顶并卸载更新':
        if not check_device_connected():
            sg.Popup('设备未连接，请先连接设备并开启USB调试', title='错误')
        else:
            results = scan_system_app_updates(log=lambda msg: window['log'].print(msg))
            updated = [r for r in results if r['has_update']]
            if not updated:
                sg.Popup('未发现已更新的系统应用', title='检测结果')
            else:
                pkgs = '\n'.join(f"  {r['pkg']}" for r in updated)
                confirm = sg.PopupYesNo(
                    f"将使用 install-existing 重新安装以下 {len(updated)} 个应用并置顶：\n"
                    f"{pkgs}\n\n"
                    f"之后请在手机「设置 → 应用管理」中点击「卸载更新」回退到出厂版本（数据保留）。\n\n"
                    f"是否继续？", title='确认操作')
                if confirm != 'Yes':
                    window['log'].print('操作已取消')
                else:
                    success, fail, fail_list = reinstall_updated_apps(
                        updated, log=lambda msg: window['log'].print(msg))
                    msg = f"操作完成：成功 {success}，失败 {fail}"
                    if fail_list:
                        msg += '\n失败应用：' + ', '.join(fail_list)
                    sg.Popup(msg, title='操作结果')
    else:
        return False
    return True