import subprocess
import configparser
import os
import shutil
import shlex


class NewConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def run_adb_command(window, command):
    try:
        window['log'].print(f'执行命令: \r\n{command}')
        result = subprocess.run(
            ['adb'] + shlex.split(command),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"执行ADB命令失败: {e}"


def uninstall_apk(window, package_name, keep_data=False):
    command = f'shell pm uninstall {"-k " if keep_data else ""}{package_name}'
    r = run_adb_command(window, command)
    window['log'].print(r)
    return r


def install_apk(window, apk_path):
    command = f'install -r -t -d "{apk_path}"'
    r = run_adb_command(window, command)
    window['log'].print(r)
    return r


def check_app_exists(window, package_name):
    result = run_adb_command(window, 'shell pm list packages')
    return package_name in result


def change_apk_enable(window, state, name):
    action = "enable" if state else "disable-user"
    command = f'shell pm {action} {name}'
    r = run_adb_command(window, command)
    window['log'].print(r)
    return r


def change_animation_speed(window, sulv1, sulv2, sulv3):
    commands = [
        f'shell settings put global window_animation_scale {sulv1}',
        f'shell settings put global transition_animation_scale {sulv2}',
        f'shell settings put global animator_duration_scale {sulv3}'
    ]
    for command in commands:
        r = run_adb_command(window, command)
        window['log'].print(r)
    return r


def process_one_key_list(window, action, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                package_name = line.strip()
                if package_name:
                    if action == '冻结':
                        change_apk_enable(window, False, package_name)
                    elif action == '解冻':
                        change_apk_enable(window, True, package_name)
                    elif action == '卸载':
                        uninstall_apk(window, package_name, keep_data=False)
                    elif action == '重装':
                        uninstall_apk(window, package_name, keep_data=True)
                    window['log'].print(f"{action} {package_name}")
    except Exception as e:
        window['log'].print(f'读取文件时发生错误: {e}\n')
    window['log'].print(f'处理应用列表结束。\n')


def get_top_package_name(window):
    try:
        r = run_adb_command(window, 'shell dumpsys activity top | grep ACTIVITY')
        window['log'].update(r)
        lines = r.split('\n')
        if lines:
            last_line = lines[-2]
            package_name = last_line.replace("ACTIVITY ", "").split('/')[0].strip()
            return package_name
        else:
            return "无法获取前台应用包名"
    except Exception as e:
        return f"获取前台应用包名失败: {e}"


def get_apk_package_name(apk_path):
    try:
        result = subprocess.run(
            ['aapt', 'dump', 'badging', apk_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
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


def uninstall_and_install_apk(window, apk_path):
    package_name, _ = get_apk_package_name(apk_path)
    if package_name:
        try:
            window['log'].print(f"正在卸载 {package_name}...")
            subprocess.run(
                ['adb', 'shell', 'pm', 'uninstall', package_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            window['log'].print(f"正在安装 {apk_path}...")
            install_result = subprocess.run(
                ['adb', 'install', '-r', '-d', apk_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if install_result.returncode == 0:
                window['log'].print(f"成功安装 {apk_path}")
                return True
            else:
                window['log'].print(
                    f"安装失败: {install_result.stderr.decode('utf-8', errors='ignore')}")
                return False

        except Exception as e:
            window['log'].print(f"卸载和安装出错: {e}")
            return False
    else:
        window['log'].print(f"跳过 {apk_path}: 无法获取包名")
        return False


def organize_files_in_folder(window, folder_path):
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
                window['log'].print(f"已重命名: {new_file_name}")
                processed_apps.append(new_file_path)
            else:
                window['log'].print(f"跳过重命名: {new_file_name} 已存在")
        else:
            try:
                shutil.move(apk_path, unrecognized_folder)
                window['log'].print(f"移动到无法识别的应用: {apk_file}")
                unrecognized_apps.append(apk_file)
            except Exception as e:
                window['log'].print(f"移动失败: {e}")

    window['log'].print("\n无法识别的应用列表:")
    for app in unrecognized_apps:
        window['log'].print(f"  - {app}")


def process_apk_files_in_folder(window, folder_path, mode):
    if not folder_path:
        window['log'].print("请选择APK文件所在的文件夹")
        return

    apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
    for apk_file in apk_files:
        apk_path = os.path.join(folder_path, apk_file)
        package_name, _ = get_apk_package_name(apk_path)
        file_processed = False

        if mode == "uninstall_install":
            file_processed = uninstall_and_install_apk(window, apk_path)
        elif mode == "install_only":
            file_processed = install_apk(window, apk_path)
        elif mode == "replace":
            if package_name:
                if check_app_exists(window, package_name):
                    if not uninstall_apk(window, package_name):
                        window['log'].print(f"卸载应用 {package_name} 失败")
                        continue
                else:
                    window['log'].print(f"应用 {package_name} 未安装，跳过卸载")
                file_processed = install_apk(window, apk_path)
            else:
                window['log'].print(f"跳过 {apk_file}: 无法获取包名")
                continue

        if not file_processed:
            window['log'].print(f"处理应用 {apk_file} 失败")
