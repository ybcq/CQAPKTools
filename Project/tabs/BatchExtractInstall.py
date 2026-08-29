import PySimpleGUI as sg
import os
import subprocess
from models.CQAPKTools import run_adb_command
from models.CQApkRename import extract_apk_info

sg.theme('DarkGray')
sg.set_options(font=("等线", 10))

# ====== 布局 ======
# 计算默认提取路径
_default_desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
if not os.path.exists(_default_desktop):
    _default_desktop = os.path.join(os.path.expanduser('~'), '桌面')
_default_extract_path = os.path.join(_default_desktop, '导出')

batch_extract_frame = [
    [sg.Text("提取目录"), sg.InputText(key='extract_path', default_text=_default_extract_path, expand_x=True), sg.FolderBrowse(button_text="...", key='extract_browse')],
    [sg.Button('开始提取')]
]

batch_install_frame = [
    [sg.Text("安装目录"), sg.InputText(key='install_path', expand_x=True), sg.FolderBrowse(button_text="...", key='install_browse')],
    [sg.Table(values=[], headings=['应用名', '是否已替换', '是否新安装'],
              key='extracted_list', auto_size_columns=False,
              col_widths=[40, 10, 10], num_rows=15, expand_x=True,
              justification='left')],
    [sg.Button('批量安装'), sg.Button('仅安装尚未安装的应用'),
     sg.Text("|", expand_x=True), sg.Button('用文件夹中的应用替换原应用'), sg.Checkbox('卸载时保留数据', key='keep_data'), sg.Checkbox('如果未安装则新安装', key='install_if_not_installed')],
]

layout = [
    [sg.Frame("批量提取", batch_extract_frame, expand_x=True)],
    [sg.Frame("批量安装", batch_install_frame, expand_x=True)]
]


# ====== 事件处理 ======
def handle_event(window, event, values, ctx):
    """处理批量提取安装标签页的事件，返回 True 表示已处理"""
    aaptPath = ctx['aaptPath']
    CURRENT_DIR = ctx['CURRENT_DIR']

    if event == '开始提取':
        extract_path = values['extract_path']
        if not extract_path:
            sg.Popup('请选择提取目录', title='提示')
            return True

        device_id = values['device_id']
        if device_id == '无设备' or device_id == '':
            sg.Popup('请先连接设备', title='提示')
            return True

        extract_path = os.path.join(extract_path, device_id)
        os.makedirs(extract_path, exist_ok=True)

        window['log'].print(f'开始提取设备 {device_id} 上的所有APK文件到 {extract_path}')
        window.refresh()

        # 获取第三方应用列表
        result = run_adb_command(window, f'-s {device_id} shell pm list packages -3')
        if not result or 'package:' not in result:
            window['log'].print('未找到第三方应用')
            window.refresh()
            return True

        packages = [line.replace('package:', '').strip() for line in result.split('\n') if line.startswith('package:')]
        window['log'].print(f'找到 {len(packages)} 个第三方应用')
        window.refresh()

        extracted_files = []
        for package_name in packages:
            path_result = run_adb_command(window, f'-s {device_id} shell pm path {package_name}')
            if not path_result or 'package:' not in path_result:
                window['log'].print(f'无法获取 {package_name} 的APK路径，跳过')
                window.refresh()
                continue

            apk_path = path_result.split(':', 1)[1].strip()

            temp_path = os.path.join(extract_path, f'_temp_{package_name}.apk')
            window['log'].print(f'正在提取: {package_name}')
            window.refresh()
            run_adb_command(window, f'-s {device_id} pull "{apk_path}" "{temp_path}"')

            if not os.path.exists(temp_path):
                window['log'].print(f'提取失败: {package_name}')
                window.refresh()
                continue

            app_name = package_name
            version_name = 'unknown'
            try:
                aapt_result = subprocess.run(
                    ['aapt', 'dump', 'badging', temp_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    encoding='utf-8', errors='ignore'
                )
                for line in aapt_result.stdout.splitlines():
                    if 'application-label:' in line:
                        app_name = line.split('application-label:')[1].strip().strip("'").strip('"')
                    if "versionName='" in line:
                        version_name = line.split("versionName='")[1].split("'")[0]
            except Exception as e:
                window['log'].print(f'aapt解析 {package_name} 失败: {e}')

            safe_name = ''.join(c for c in app_name if c.isalnum() or c in (' ', '.', '_', '-'))
            if not safe_name.strip():
                safe_name = package_name

            target_filename = f"{safe_name}_{version_name}.apk"
            target_path = os.path.join(extract_path, target_filename)

            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(temp_path, target_path)
            extracted_files.append([target_filename, '', ''])
            window['extracted_list'].update(values=extracted_files)
            window['log'].print(f'已提取: {target_filename}')
            window.refresh()

        window['install_path'].update(value=extract_path)
        window['log'].print(f'提取完成，共提取 {len(extracted_files)} 个APK文件')
        window.refresh()

    elif event == '批量安装':
        install_path = values['install_path']
        if not install_path:
            sg.Popup('请选择安装目录', title='提示')
            return True

        if not os.path.exists(install_path):
            sg.Popup('安装目录不存在', title='提示')
            return True

        device_id = values['device_id']
        if device_id == '无设备' or device_id == '':
            sg.Popup('请先连接设备', title='提示')
            return True

        apk_files = [os.path.join(install_path, f) for f in os.listdir(install_path) if f.endswith('.apk')]
        if not apk_files:
            sg.Popup('安装目录中没有APK文件', title='提示')
            return True

        window['log'].print(f'开始批量安装 {len(apk_files)} 个APK文件到设备 {device_id}')
        window.refresh()

        success_count = 0
        for apk_path in apk_files:
            apk_filename = os.path.basename(apk_path)
            window['log'].print(f'正在安装: {apk_filename}')
            window.refresh()
            install_result = run_adb_command(window, f'-s {device_id} install -r -d "{apk_path}"')
            if 'Success' in install_result:
                success_count += 1
                window['log'].print(f'安装成功: {apk_filename}')
            else:
                window['log'].print(f'安装失败: {apk_filename} - {install_result.strip()}')
            window.refresh()

        window['log'].print(f'批量安装完成，成功 {success_count}/{len(apk_files)}')
        window.refresh()

    elif event == '仅安装尚未安装的应用':
        install_path = values['install_path']
        if not install_path or not os.path.exists(install_path):
            sg.Popup('请选择有效的安装目录', title='提示')
            return True

        device_id = values['device_id']
        if device_id == '无设备' or device_id == '':
            sg.Popup('请先连接设备', title='提示')
            return True

        apk_files = [os.path.join(install_path, f) for f in os.listdir(install_path) if f.lower().endswith('.apk')]
        if not apk_files:
            sg.Popup('安装目录中没有APK文件', title='提示')
            return True

        window['log'].print(f'开始检查并安装 {len(apk_files)} 个APK文件到设备 {device_id}')
        window.refresh()

        _aapt = aaptPath if os.path.isabs(aaptPath) else os.path.join(CURRENT_DIR, aaptPath)
        installed_count = 0
        success_count = 0
        for apk_path in apk_files:
            apk_filename = os.path.basename(apk_path)
            try:
                info = extract_apk_info(apk_path, aapt_path=_aapt)
            except Exception as e:
                window['log'].print(f'解析失败: {apk_filename} - {e}')
                window.refresh()
                continue
            pkg = info['package_name']
            if not pkg:
                window['log'].print(f'无法获取包名: {apk_filename}')
                window.refresh()
                continue
            check_result = run_adb_command(window, f'-s {device_id} shell pm list packages {pkg}')
            if f'package:{pkg}' in check_result:
                installed_count += 1
                window['log'].print(f'已安装，跳过: {apk_filename}')
            else:
                window['log'].print(f'未安装，正在安装: {apk_filename}')
                window.refresh()
                install_result = run_adb_command(window, f'-s {device_id} install -r -d "{apk_path}"')
                if 'Success' in install_result:
                    success_count += 1
                    window['log'].print(f'安装成功: {apk_filename}')
                else:
                    window['log'].print(f'安装失败: {apk_filename} - {install_result.strip()}')
            window.refresh()

        window['log'].print(f'完成：已跳过 {installed_count} 个已安装应用，新安装成功 {success_count} 个')
        window.refresh()

    elif event == '用文件夹中的应用替换原应用':
        install_path = values['install_path']
        if not install_path or not os.path.exists(install_path):
            sg.Popup('请选择有效的安装目录', title='提示')
            return True

        device_id = values['device_id']
        if device_id == '无设备' or device_id == '':
            sg.Popup('请先连接设备', title='提示')
            return True

        apk_files = [os.path.join(install_path, f) for f in os.listdir(install_path) if f.lower().endswith('.apk')]
        if not apk_files:
            sg.Popup('安装目录中没有APK文件', title='提示')
            return True

        keep_data = values.get('keep_data', False)
        install_if_not_installed = values.get('install_if_not_installed', False)

        window['log'].print(f'开始替换安装 {len(apk_files)} 个APK文件到设备 {device_id}')
        if keep_data:
            window['log'].print('  选项：卸载时保留数据')
        if install_if_not_installed:
            window['log'].print('  选项：未安装则新安装')
        window.refresh()

        # 初始化表格：应用名列填入文件名，其余两列空白
        table_data = [[os.path.basename(f), '', ''] for f in apk_files]
        window['extracted_list'].update(values=table_data)
        window.refresh()

        _aapt = aaptPath if os.path.isabs(aaptPath) else os.path.join(CURRENT_DIR, aaptPath)
        replaced_count = 0
        new_installed_count = 0
        skipped_count = 0
        fail_count = 0
        for idx, apk_path in enumerate(apk_files):
            apk_filename = os.path.basename(apk_path)
            try:
                info = extract_apk_info(apk_path, aapt_path=_aapt)
            except Exception as e:
                window['log'].print(f'解析失败: {apk_filename} - {e}')
                window.refresh()
                fail_count += 1
                continue
            pkg = info['package_name']
            if not pkg:
                window['log'].print(f'无法获取包名: {apk_filename}')
                window.refresh()
                fail_count += 1
                continue
            check_result = run_adb_command(window, f'-s {device_id} shell pm list packages {pkg}')
            if f'package:{pkg}' in check_result:
                uninstall_flag = '-k' if keep_data else ''
                window['log'].print(f'已安装，正在卸载: {pkg}')
                window.refresh()
                run_adb_command(window, f'-s {device_id} uninstall {uninstall_flag} {pkg}')
                window['log'].print(f'正在安装新版本: {apk_filename}')
                window.refresh()
                install_result = run_adb_command(window, f'-s {device_id} install -r -d "{apk_path}"')
                if 'Success' in install_result:
                    replaced_count += 1
                    table_data[idx][1] = '√'
                    window['extracted_list'].update(values=table_data)
                    window['log'].print(f'替换成功: {apk_filename}')
                else:
                    fail_count += 1
                    window['log'].print(f'替换失败: {apk_filename} - {install_result.strip()}')
            elif install_if_not_installed:
                window['log'].print(f'未安装，正在新安装: {apk_filename}')
                window.refresh()
                install_result = run_adb_command(window, f'-s {device_id} install -r -d "{apk_path}"')
                if 'Success' in install_result:
                    new_installed_count += 1
                    table_data[idx][2] = '√'
                    window['extracted_list'].update(values=table_data)
                    window['log'].print(f'新安装成功: {apk_filename}')
                else:
                    fail_count += 1
                    window['log'].print(f'安装失败: {apk_filename} - {install_result.strip()}')
            else:
                skipped_count += 1
                window['log'].print(f'未安装，跳过: {apk_filename}')
            window.refresh()

        total = replaced_count + new_installed_count + skipped_count + fail_count
        window['log'].print(f'共{total}个应用，替换了{replaced_count}个应用，新安装{new_installed_count}个应用')
        window.refresh()

    else:
        return False
    return True
