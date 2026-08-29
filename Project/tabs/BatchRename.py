"""批量命名标签页 - APK 文件批量重命名"""
import PySimpleGUI as sg
import os
import sys
import codecs
from models.CQApkRename import rename_apk
from models.CQAPKTools import run_adb_command

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ====== 布局 ======
rename_path = [
    [sg.Text("选择单文件"), sg.InputText(key='file', expand_x=True), sg.FileBrowse(button_text="...", key='file', file_types=(("安卓应用安装包", "*.apk"),))],
    [sg.Text("选择文件夹"), sg.InputText(key='path', expand_x=True), sg.FolderBrowse(button_text="...", key='path')]
]

rename_set = [
    [sg.Text("表达式：{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}")],
    [sg.InputText(key='kind', expand_x=True)],
    [sg.Button('应用设置'), sg.Button("关联到右键菜单"), sg.Button("删除右键菜单")]
]

rename_result = [
    [sg.Table(values=[], headings=['重命名前', '重命名后'], key='rename_result_table',
              auto_size_columns=False, col_widths=[35, 35],
              display_row_numbers=True, num_rows=12, expand_x=True)]
]

layout = [
    [sg.Frame("重命名操作", rename_path, expand_x=True), sg.Button('开始重命名')],
    [sg.Frame("重命名设置", rename_set, expand_x=True)],
    [sg.Frame("重命名结果", rename_result, expand_x=True)]
]


# ====== 事件处理 ======
def handle_event(window, event, values, ctx):
    """处理批量命名标签页的事件，返回 True 表示已处理"""
    conf = ctx['conf']
    cfgpath = ctx['cfgpath']
    aaptPath = ctx['aaptPath']
    keytoolPath = ctx['keytoolPath']
    newFileNamePattern = ctx['newFileNamePattern']
    CURRENT_DIR = ctx['CURRENT_DIR']

    if event == '开始重命名':
        _aapt = aaptPath if os.path.isabs(aaptPath) else os.path.join(CURRENT_DIR, aaptPath)
        _keytool = keytoolPath if os.path.isabs(keytoolPath) else os.path.join(CURRENT_DIR, keytoolPath)

        window['rename_result_table'].update(values=[])

        # 单文件
        file_path = values['file']
        if file_path is not None and os.path.isfile(file_path):
            old, new, err = rename_apk(file_path, newFileNamePattern,
                                       aapt_path=_aapt, keytool_path=_keytool)
            old_name = os.path.basename(old)
            new_name = os.path.basename(new) if new else (err or '失败')
            window['rename_result_table'].update(values=[[old_name, new_name]])
            window.refresh()
            if err:
                sg.Popup(f'重命名失败：{err}', title='重命名失败')
            elif old != new:
                sg.Popup(f'{old_name} -> {new_name}', title='重命名成功')
            else:
                sg.Popup('文件名无需修改', title='重命名')

        # 多文件
        pathpath = values['path']
        if pathpath is not None and os.path.isdir(pathpath):
            apk_paths = []
            for root, dirs, files in os.walk(pathpath):
                for file in files:
                    if file.lower().endswith('.apk'):
                        apk_paths.append(os.path.join(root, file))
            if apk_paths:
                success = 0
                fail = 0
                table_data = []
                for apk_path in apk_paths:
                    old, new, err = rename_apk(apk_path, newFileNamePattern,
                                               aapt_path=_aapt, keytool_path=_keytool)
                    old_name = os.path.basename(old)
                    new_name = os.path.basename(new) if new else (err or '失败')
                    table_data.append([old_name, new_name])
                    window['rename_result_table'].update(values=table_data)
                    window.refresh()
                    if err:
                        fail += 1
                    else:
                        success += 1
                sg.Popup(f'批量重命名完成：成功 {success}，失败 {fail}', title='重命名结果')
            else:
                sg.Popup('未找到 APK 文件', title='重命名')

    elif event == '应用设置':
        setpath = values['kind']
        conf.set("Config", "newFileNamePattern", setpath)
        conf.write(codecs.open(cfgpath, "w", "utf-8"))
        sg.Popup('已成功修改设置为：', setpath, title='成功')

    elif event == '关联到右键菜单':
        try:
            exe_path = os.path.abspath(sys.argv[0])
            r = run_adb_command(window, f'reg add "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名...\\command" /ve /t REG_SZ /d "{exe_path}" --rename "%1" /f')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功加入安装包的右键菜单', title='成功')
        except BaseException:
            pass

    elif event == '删除右键菜单':
        try:
            r = run_adb_command(window, 'reg delete "HKEY_CLASSES_ROOT\\SystemFileAssociations\\.apk\\shell\\用 CQApkTools 重命名..." /f')
            if r.find("拒绝"):
                sg.Popup('权限不足，请使用管理员身份运行该软件', title='权限不足')
            else:
                sg.Popup('已成功删除安装包的右键菜单', title='成功')
        except BaseException:
            pass

    else:
        return False
    return True