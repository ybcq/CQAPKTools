"""
CQApkTools 核心模块
ADB 封装、APK 安装/卸载/冻结、动画设置、文件处理等
"""
import subprocess
import configparser
import os
import shutil
import shlex

# 外部工具统一放在 Tools 目录（源码模式为 Project/Tools，打包模式为 _internal/Tools）
MODELS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.dirname(MODELS_DIR)
TOOLS_DIR = os.path.join(PROJECT_DIR, 'Tools')
ADB_PATH = os.path.join(TOOLS_DIR, 'adb.exe')
AAPT_PATH = os.path.join(TOOLS_DIR, 'aapt.exe')


class NewConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def _execute(cmd, shell=True, use_privilege=False):
    """执行系统命令，返回 (success, output)"""
    display_cmd = cmd if isinstance(cmd, str) else ' '.join(cmd)
    _print(f">>> 执行命令: {display_cmd}")
    
    try:
        if isinstance(cmd, str) and shell:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=False)
        else:
            result = subprocess.run(cmd if isinstance(cmd, list) else shlex.split(cmd), capture_output=True, text=True, check=False)
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            output = f"{output}\n{err}".strip()
        success = result.returncode == 0
    except Exception as e:
        success = False
        output = str(e)
    
    result_preview = output.strip() if output.strip() else "(无输出)"
    _print(f"<<< 返回结果: {result_preview}")
    return success, output


def _print(msg):
    print(msg)


def run_adb_command(command):
    """执行 adb 命令，返回 stdout 文本；失败时返回 stderr"""
    _print(f">>> 执行命令: adb {command}")
    try:
        result = subprocess.run(
            [ADB_PATH] + shlex.split(command),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stdout.decode('utf-8', errors='ignore')
        err = result.stderr.decode('utf-8', errors='ignore')
        if result.returncode != 0:
            _print(f"<<< 返回结果: {output}{err}")
            return err
        else:
            _print(f"<<< 返回结果: {output}")
            return output
    except Exception as e:
        _print(f"<<< 返回结果: 执行ADB命令失败: {e}")
        return f"执行ADB命令失败: {e}"


def uninstall_apk(package_name, keep_data=False):
    command = f'shell pm uninstall {"-k " if keep_data else ""}{package_name}'
    r = run_adb_command(command)
    return r


def install_apk(apk_path):
    command = f'install -r -t -d "{apk_path}"'
    r = run_adb_command(command)
    return r


def check_app_exists(package_name):
    result = run_adb_command('shell pm list packages')
    return package_name in result


def change_apk_enable(state, name):
    action = "enable" if state else "disable-user"
    command = f'shell pm {action} {name}'
    r = run_adb_command(command)
    return r


def change_animation_speed(sulv1, sulv2, sulv3):
    commands = [
        f'shell settings put global window_animation_scale {sulv1}',
        f'shell settings put global transition_animation_scale {sulv2}',
        f'shell settings put global animator_duration_scale {sulv3}'
    ]
    for command in commands:
        run_adb_command(command)
    return True


def process_one_key_list(action, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                package_name = line.strip()
                if package_name:
                    if action == '冻结':
                        change_apk_enable(False, package_name)
                    elif action == '解冻':
                        change_apk_enable(True, package_name)
                    elif action == '卸载':
                        uninstall_apk(package_name, keep_data=False)
                    elif action == '重装':
                        uninstall_apk(package_name, keep_data=True)
                    _print(f"{action} {package_name}")
    except Exception as e:
        _print(f'读取文件时发生错误: {e}\n')
    _print(f'处理应用列表结束。\n')


def get_top_package_name():
    try:
        r = run_adb_command('shell dumpsys activity top | grep ACTIVITY')
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
            [AAPT_PATH, 'dump', 'badging', apk_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stdout.decode('utf-8', errors='ignore')

        package_name = None
        application_label = None

        for line in output.split('\n'):
            if line.startswith('package:'):
                package_info = line.strip()
                package_name = package_info.split('name=')[1].split(' ')[0].strip('"')
            if line.startswith('application-label:'):
                label_info = line.strip()
                application_label = label_info.split('application-label:')[1].strip('"')

        return package_name, application_label

    except Exception as e:
        _print(f"获取包名出错: {e}")
        return None, None


def uninstall_and_install_apk(apk_path):
    package_name, _ = get_apk_package_name(apk_path)
    if package_name:
        try:
            _print(f"正在卸载 {package_name}...")
            subprocess.run(
                ['adb', 'shell', 'pm', 'uninstall', package_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            _print(f"正在安装 {apk_path}...")
            install_result = subprocess.run(
                ['adb', 'install', '-r', '-d', apk_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if install_result.returncode == 0:
                _print(f"成功安装 {apk_path}")
                return True
            else:
                _print(f"安装失败: {install_result.stderr.decode('utf-8', errors='ignore')}")
                return False

        except Exception as e:
            _print(f"卸载和安装出错: {e}")
            return False
    else:
        _print(f"跳过 {apk_path}: 无法获取包名")
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
                _print(f"已重命名: {new_file_name}")
                processed_apps.append(new_file_path)
            else:
                _print(f"跳过重命名: {new_file_name} 已存在")
        else:
            try:
                shutil.move(apk_path, unrecognized_folder)
                _print(f"移动到无法识别的应用: {apk_file}")
                unrecognized_apps.append(apk_file)
            except Exception as e:
                _print(f"移动失败: {e}")

    _print("\n无法识别的应用列表:")
    for app in unrecognized_apps:
        _print(f"  - {app}")


def process_apk_files_in_folder(folder_path, mode):
    if not folder_path:
        _print("请选择APK文件所在的文件夹")
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
                        _print(f"卸载应用 {package_name} 失败")
                        continue
                else:
                    _print(f"应用 {package_name} 未安装，跳过卸载")
                file_processed = install_apk(apk_path)
            else:
                _print(f"跳过 {apk_file}: 无法获取包名")
                continue

        if not file_processed:
            _print(f"处理应用 {apk_file} 失败")
