"""
CQApkTools 5.0 Web 应用入口
Flask + Bootstrap 5.3 浏览器界面
"""
import io
import os
import sys
import json
import time
import queue
import socket
import logging
import threading
import traceback
import subprocess
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify,
    Response, stream_with_context
)

# 导入后端模型
from models.CQAPKTools import NewConfigParser
from models.CQApkRename import rename_apk, batch_rename, extract_apk_info, build_filename
from models.ResetSystemApps import (
    scan_system_app_updates,
    reinstall_updated_apps,
    check_device_connected,
)
from models.CQAPKTools import (
    run_adb_command, uninstall_apk, install_apk,
    change_apk_enable, change_animation_speed,
    process_one_key_list, get_top_package_name,
    get_apk_package_name, organize_files_in_folder,
    process_apk_files_in_folder,
)

# ========== Flask 应用初始化 ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cqapktools-5.0-secret'

# 抑制 Flask/Werkzeug 请求日志
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.disable(logging.WARNING)


# ========== 日志系统 ==========
class LogCapture:
    """线程安全的日志捕获，通过 SSE 推送到前端"""
    def __init__(self):
        self._subscribers = []
        self._history = []
        self._max_history = 2000
        self._lock = threading.Lock()
        self._filter_patterns = [
            'GET /api/', 'POST /api/', 'GET /logs', 'GET /favicon',
        ]

    def _should_filter(self, msg):
        for p in self._filter_patterns:
            if p in msg:
                return True
        return False

    def write(self, msg):
        with self._lock:
            lines = str(msg).split('\n')
            for line in lines:
                line = line.rstrip('\r')
                if not line:
                    continue
                if self._should_filter(line):
                    continue
                self._history.append(line)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
                payload = json.dumps({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'msg': line,
                }, ensure_ascii=False)
                for sub in list(self._subscribers):
                    try:
                        sub.put(payload)
                    except Exception:
                        pass

    def subscribe(self):
        sub = queue.Queue(maxsize=200)
        with self._lock:
            self._subscribers.append(sub)
        return sub

    def unsubscribe(self, sub):
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def get_history(self, lines=500):
        with self._lock:
            return self._history[-lines:]


log_capture = LogCapture()

# 劫持 stdout/stderr，将所有 print 输出重定向到日志面板
# 打包为无控制台 exe 时 sys.stdout/stderr 可能为 None，需回退到 devnull
_stdout = sys.stdout if sys.stdout is not None else open(
    os.devnull, 'w', encoding='utf-8', errors='ignore'
)
_stderr = sys.stderr if sys.stderr is not None else open(
    os.devnull, 'w', encoding='utf-8', errors='ignore'
)

_app_log_file = None


def _get_app_log_file():
    """懒打开 app.log 文件，将日志同步落盘（无控制台时也能留痕）

    Returns:
        file | None: 已打开的日志文件句柄；打开失败返回 None 且不再重试
    """
    global _app_log_file
    if _app_log_file is None:
        try:
            if getattr(sys, 'frozen', False):
                log_dir = os.path.dirname(sys.executable)
            else:
                log_dir = os.path.dirname(os.path.realpath(__file__))
            _app_log_file = open(
                os.path.join(log_dir, 'app.log'), 'a',
                encoding='utf-8', errors='ignore'
            )
        except OSError:
            _app_log_file = False
    return _app_log_file or None


class _Redirector:
    def write(self, msg):
        if isinstance(msg, str) and msg.strip():
            log_capture.write(msg.rstrip('\n'))
            f = _get_app_log_file()
            if f:
                try:
                    f.write(msg)
                    f.flush()
                except OSError:
                    pass
        _stdout.write(msg)

    def flush(self):
        _stdout.flush()
        f = _get_app_log_file()
        if f:
            try:
                f.flush()
            except OSError:
                pass

    def fileno(self):
        return _stdout.fileno()


sys.stdout = _Redirector()
sys.stderr = _Redirector()


# ========== 辅助函数 ==========
def _adb_success(output: str) -> bool:
    if not output:
        return True
    lower = output.lower()
    return not any(k in lower for k in [
        'error', '失败', 'exception', 'timeout', 'denied', 'permission', 'failed', 'failure', 'refused'
    ])


def is_port_in_use(port: int) -> bool:
    """检测本机端口是否已有服务监听

    Args:
        port (int): 待检测的 TCP 端口号

    Returns:
        bool: True 表示端口已被占用（后台已有服务在运行）
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


# ========== 常量 ==========
APP_NAME = 'CQApkTools'
APP_VERSION = '5.0.0'
SERVICE_PORT = 55500
SERVICE_URL = f'http://127.0.0.1:{SERVICE_PORT}'

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
cfgpath = os.path.join(CURRENT_DIR, 'Setup.ini')

# 读 ini 配置（相对路径锚定到 CURRENT_DIR，源码/exe 两种模式均有效）
conf = NewConfigParser()
conf.read(cfgpath, encoding="utf-8")
aapt_path = conf.get("Config", "aaptPath", fallback='Tools\\aapt.exe')
if not os.path.isabs(aapt_path):
    aapt_path = os.path.join(CURRENT_DIR, aapt_path)
keytool_path = conf.get("Config", "keytoolPath", fallback='Tools\\bin\\keytool.exe')
if not os.path.isabs(keytool_path):
    keytool_path = os.path.join(CURRENT_DIR, keytool_path)
new_file_name_pattern = conf.get("Config", "newFileNamePattern", fallback='{应用包名}_{版本名字}')


# ========== 路由 ==========
@app.route('/')
def index():
    return render_template('index.html', app_name=APP_NAME, app_version=APP_VERSION, pattern=new_file_name_pattern)


@app.route('/api/tabs')
def api_tabs():
    tabs = [
        {'id': 'surge-freeze', 'name': '澎湃冻结', 'icon': 'snow'},
        {'id': 'general-optimize', 'name': '通用优化', 'icon': 'speedometer2'},
        {'id': 'huawei-engine', 'name': '华为引擎', 'icon': 'hdd-network'},
        {'id': 'batch-rename', 'name': '批量命名', 'icon': 'file-earmark-text'},
        {'id': 'batch-extract-install', 'name': '批量提取安装', 'icon': 'phone'},
    ]
    return jsonify(tabs)


@app.route('/api/logs')
def api_logs():
    """SSE 日志流"""
    def stream():
        sub = log_capture.subscribe()
        try:
            # 先发送历史日志
            for line in log_capture.get_history(200):
                yield f"data: {json.dumps({'time': '', 'msg': line}, ensure_ascii=False)}\n\n"
            # 持续推送新日志
            while True:
                try:
                    payload = sub.get(timeout=30)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        except GeneratorExit:
            pass
        finally:
            log_capture.unsubscribe(sub)

    return Response(stream(), mimetype='text/event-stream')


@app.route('/api/action', methods=['POST'])
def api_action():
    """统一动作接口"""
    data = request.get_json(force=True)
    action = data.get('action', '')
    params = data.get('params', {})
    result = {'ok': True, 'msg': '操作成功', 'data': None}

    try:
        if action == 'connect_device':
            r = run_adb_command('devices')
            device_id = '无设备'
            status = '未连接'
            for line in r.splitlines():
                line = line.strip()
                if not line or line.startswith('List of devices attached'):
                    continue
                parts = [p.strip() for p in line.split('\t')]
                if len(parts) > 1 and parts[1] == 'device':
                    device_id = parts[0]
                    status = '已连接'
                    break
            result['data'] = {'device_id': device_id, 'status': status}

        elif action == 'disconnect_device':
            result['data'] = {'device_id': '', 'status': '未连接'}

        elif action == 'get_top_package':
            pkg = get_top_package_name()
            result['data'] = {'package': pkg}

        # ---------- 澎湃冻结 ----------
        elif action == 'freeze_app':
            r = change_apk_enable(False, params.get('package', ''))
            if _adb_success(r):
                result['msg'] = r.strip() or '已冻结'
            else:
                result['ok'] = False
                result['msg'] = r.strip() or '冻结失败'
        elif action == 'unfreeze_app':
            r = change_apk_enable(True, params.get('package', ''))
            if _adb_success(r):
                result['msg'] = r.strip() or '已解冻'
            else:
                result['ok'] = False
                result['msg'] = r.strip() or '解冻失败'
        elif action == 'uninstall_app':
            r = uninstall_apk(params.get('package', ''), keep_data=params.get('keep_data', False))
            if _adb_success(r):
                result['msg'] = r.strip() or '已卸载'
            else:
                result['ok'] = False
                result['msg'] = r.strip() or '卸载失败'
        elif action == 'one_key_list':
            action_type = params.get('type', '')
            file_path = params.get('file_path', '')
            process_one_key_list(action_type, file_path)
            result['msg'] = f'{action_type}列表完成'
        elif action == 'one_key_batch':
            action_type = params.get('type', '')
            packages = params.get('packages', [])
            fail_count = 0
            for pkg in packages:
                if action_type == '冻结':
                    r = change_apk_enable(False, pkg)
                elif action_type == '解冻':
                    r = change_apk_enable(True, pkg)
                elif action_type == '卸载':
                    r = uninstall_apk(pkg, keep_data=False)
                elif action_type == '重装':
                    r = uninstall_apk(pkg, keep_data=True)
                else:
                    continue
                if not _adb_success(r):
                    fail_count += 1
            if fail_count > 0:
                result['ok'] = False
                result['msg'] = f'{action_type}完成：成功 {len(packages) - fail_count}，失败 {fail_count}'
            else:
                result['msg'] = f'{action_type}完成：共 {len(packages)} 个'

        elif action == 'scan_system_updates':
            if not check_device_connected():
                result['ok'] = False
                result['msg'] = '设备未连接'
            else:
                updated = scan_system_app_updates(log=print)
                result['data'] = updated
                result['msg'] = f'检测完成：共 {len(updated)} 个系统应用，{sum(1 for x in updated if x["has_update"])} 个有更新'

        elif action == 'reinstall_system_updates':
            updated = params.get('updated', [])
            success, fail, fail_list = reinstall_updated_apps(updated, log=print)
            result['msg'] = f'置顶完成：成功 {success}，失败 {fail}'

        # ---------- 通用优化 ----------
        elif action == 'set_animation':
            speeds = [
                params.get('speed1', '1'),
                params.get('speed2', '1'),
                params.get('speed3', '1'),
            ]
            commands = [
                f'shell settings put global window_animation_scale {speeds[0]}',
                f'shell settings put global transition_animation_scale {speeds[1]}',
                f'shell settings put global animator_duration_scale {speeds[2]}',
            ]
            failed = False
            for cmd in commands:
                r = run_adb_command(cmd)
                if not _adb_success(r):
                    failed = True
                    break
            if failed:
                result['ok'] = False
                result['msg'] = '动画速度设置失败'
            else:
                result['msg'] = '动画速度已设置'
        elif action == 'set_background':
            r = run_adb_command(f'shell settings put global activity_manager_constants max_cached_processes={params.get("level", 16)}')
            if _adb_success(r):
                result['msg'] = '后台策略已设置'
            else:
                result['ok'] = False
                result['msg'] = '后台策略设置失败'
        elif action == 'set_freezer':
            state = 'true' if params.get('enable', True) else 'false'
            r1 = run_adb_command(f'shell device_config put activity_manager_native_boot use_freezer {state}')
            run_adb_command('reboot')
            if _adb_success(r1):
                result['msg'] = f'墓碑进程已{"开启" if params.get("enable", True) else "关闭"}，正在重启...'
            else:
                result['ok'] = False
                result['msg'] = '墓碑进程设置失败'
        elif action == 'organize_folder':
            organize_files_in_folder(params.get('folder_path', ''))
            result['msg'] = '文件夹整理完成'
        elif action == 'process_apk_folder':
            mode = params.get('mode', 'install_only')
            process_apk_files_in_folder(params.get('folder_path', ''), mode)
            result['msg'] = '批量处理完成'
        elif action == 'activate_app':
            app_name = params.get('app_name', '')
            failed = False
            if app_name == '女娲石':
                r1 = run_adb_command('shell setprop persist.log.tag.NotificationService DEBUG')
                r2 = run_adb_command('shell pm grant com.oasisfeng.nevo android.permission.READ_LOGS')
                if not _adb_success(r1) or not _adb_success(r2):
                    failed = True
            elif app_name == '小黑屋':
                r = run_adb_command('shell sh /storage/emulated/0/Android/data/web1n.stopapp/files/starter.sh')
                if not _adb_success(r):
                    failed = True
            elif app_name == 'Shizuku':
                r = run_adb_command('shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh')
                if not _adb_success(r):
                    failed = True
            elif app_name == 'Scene':
                r = run_adb_command('shell sh /storage/emulated/0/Android/data/com.omarea.vtools/up.sh')
                if not _adb_success(r):
                    failed = True
            if failed:
                result['ok'] = False
                result['msg'] = f'{app_name} 激活失败'
            else:
                result['msg'] = f'{app_name} 已激活'

        # ---------- 华为引擎 ----------
        elif action == 'map_shared_disk':
            r = subprocess.run(
                'subst w: %appdata%\\Huawei\\Emulator\\Share',
                shell=True, capture_output=True, text=True
            )
            if r.returncode == 0:
                result['msg'] = '已映射共享目录为 W 盘'
            else:
                result['ok'] = False
                result['msg'] = f"映射共享目录失败：{(r.stdout + r.stderr).strip()}"
        elif action == 'unmap_shared_disk':
            r = subprocess.run(
                'subst w: /d',
                shell=True, capture_output=True, text=True
            )
            if r.returncode == 0:
                result['msg'] = '已取消映射共享磁盘'
            else:
                result['ok'] = False
                result['msg'] = f"取消映射失败：{(r.stdout + r.stderr).strip()}"
        elif action == 'set_autorun_registry':
            # 直接把 subst 命令写入注册表，不再依赖外部 bat 文件
            r = subprocess.run(
                [
                    'reg', 'add',
                    r'HKEY_CLASSES_ROOT\SystemFileAssociations\.apk\shell\用 CQApkTools 重命名...\command',
                    '/ve', '/t', 'REG_SZ',
                    '/d', r'cmd /c subst w: %appdata%\Huawei\Emulator\Share',
                    '/f',
                ],
                capture_output=True, text=True
            )
            out = (r.stdout + r.stderr)
            if r.returncode != 0 or '拒绝' in out:
                result['ok'] = False
                result['msg'] = '权限不足，请使用管理员身份运行'
            else:
                result['msg'] = '已设置开机自动映射'
        elif action == 'create_network_icon':
            # 通过 PowerShell COM 动态生成快捷方式，不再依赖外部 lnk 文件
            dest_dir = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft', 'Windows', 'Network Shortcuts'
            )
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, '安卓磁盘 (W).lnk')
            target = os.path.join(
                os.environ.get('APPDATA', ''),
                'Huawei', 'Emulator', 'Share'
            )
            script = (
                "$s = New-Object -ComObject WScript.Shell; "
                f"$l = $s.CreateShortcut('{dest.replace(chr(39), chr(39) * 2)}'); "
                f"$l.TargetPath = '{target.replace(chr(39), chr(39) * 2)}'; "
                "$l.IconLocation = '%SystemRoot%\\system32\\imageres.dll,23'; "
                "$l.Save()"
            )
            r = subprocess.run(
                ['powershell', '-NoProfile', '-Command', script],
                capture_output=True, text=True
            )
            if r.returncode == 0 and os.path.exists(dest):
                result['msg'] = '已创建网络路径图标'
            else:
                result['ok'] = False
                result['msg'] = f"创建网络图标失败：{(r.stdout + r.stderr).strip()}"
        elif action == 'launch_apkinstaller':
            exe_path = os.path.join(CURRENT_DIR, 'Tools', 'ApkInstaller.exe')
            if not os.path.exists(exe_path):
                result['ok'] = False
                result['msg'] = f'未找到 ApkInstaller：{exe_path}'
            else:
                # ApkInstaller 的 manifest 要求管理员权限，startfile 走 ShellExecute 自动触发 UAC
                os.startfile(exe_path)
                result['msg'] = '已启动 ApkInstaller（请在 UAC 窗口确认）'

        # ---------- 批量命名 ----------
        elif action == 'start_rename':
            file_path = params.get('file_path', '')
            folder_path = params.get('folder_path', '')
            results = []
            if file_path and os.path.isfile(file_path):
                old, new, err = rename_apk(file_path, new_file_name_pattern, aapt_path, keytool_path)
                results.append({'old': os.path.basename(old), 'new': os.path.basename(new) if new else '', 'error': err})
            elif folder_path and os.path.isdir(folder_path):
                apk_paths = []
                for root, _, files in os.walk(folder_path):
                    for f in files:
                        if f.lower().endswith('.apk'):
                            apk_paths.append(os.path.join(root, f))
                success, fail, res = batch_rename(apk_paths, new_file_name_pattern, aapt_path, keytool_path)
                for old, new, err in res:
                    results.append({
                        'old': os.path.basename(old),
                        'new': os.path.basename(new) if new else '',
                        'error': err,
                    })
                result['msg'] = f'批量重命名完成：成功 {success}，失败 {fail}'
            else:
                result['ok'] = False
                result['msg'] = '请选择文件或文件夹'
            result['data'] = results

        elif action == 'save_pattern':
            pattern = params.get('pattern', '')
            conf.set('Config', 'newFileNamePattern', pattern)
            with open(cfgpath, 'w', encoding='utf-8') as f:
                conf.write(f)
            result['msg'] = f'已保存：{pattern}'

        # ---------- 批量提取安装 ----------
        elif action == 'start_extract':
            device_id = params.get('device_id', '')
            extract_path = params.get('extract_path', '')
            if not device_id:
                result['ok'] = False
                result['msg'] = '请先连接设备'
            else:
                result['data'] = []
                extract_path = os.path.join(extract_path, device_id)
                os.makedirs(extract_path, exist_ok=True)
                r = run_adb_command(f'-s {device_id} shell pm list packages -3')
                if not r or 'package:' not in r:
                    result['msg'] = '未找到第三方应用'
                else:
                    packages = [line.replace('package:', '').strip() for line in r.split('\n') if line.startswith('package:')]
                    extracted = []
                    for pkg in packages:
                        path_r = run_adb_command(f'-s {device_id} shell pm path {pkg}')
                        if not path_r or 'package:' not in path_r:
                            continue
                        apk_path = path_r.split(':', 1)[1].strip()
                        temp_path = os.path.join(extract_path, f'_temp_{pkg}.apk')
                        run_adb_command(f'-s {device_id} pull "{apk_path}" "{temp_path}"')
                        if os.path.exists(temp_path):
                            _, app_name, version, _, _ = extract_apk_info(temp_path, aapt_path, keytool_path)
                            new_name = f"{app_name}_{version}.apk"
                            final_path = os.path.join(extract_path, new_name)
                            if not os.path.exists(final_path):
                                os.rename(temp_path, final_path)
                            else:
                                final_path = temp_path
                            extracted.append({'name': app_name, 'version': version, 'path': final_path})
                        else:
                            extracted.append({'name': pkg, 'version': 'unknown', 'path': ''})
                    result['data'] = extracted
                    result['msg'] = f'提取完成：共 {len(extracted)} 个应用'

        elif action == 'batch_install':
            install_path = params.get('install_path', '')
            mode = params.get('mode', 'install_all')
            keep_data = params.get('keep_data', True)
            install_if_not = params.get('install_if_not_installed', False)
            if not install_path or not os.path.isdir(install_path):
                result['ok'] = False
                result['msg'] = '请选择有效的安装目录'
            else:
                apks = [f for f in os.listdir(install_path) if f.lower().endswith('.apk')]
                success = 0
                fail = 0
                details = []
                for apk in apks:
                    apk_path = os.path.join(install_path, apk)
                    pkg, _ = get_apk_package_name(apk_path)
                    if mode == 'install_not_installed':
                        exists = check_app_exists(pkg) if pkg else False
                        if exists:
                            details.append({'name': apk, 'installed': False, 'new': False})
                            continue
                    elif mode == 'replace':
                        if pkg and check_app_exists(pkg):
                            uninstall_apk(pkg, keep_data=keep_data)
                    r = install_apk(apk_path)
                    ok = 'Success' in r
                    details.append({'name': apk, 'installed': True, 'new': True})
                    if ok:
                        success += 1
                    else:
                        fail += 1
                result['data'] = details
                result['msg'] = f'安装完成：成功 {success}，失败 {fail}'

        else:
            result['ok'] = False
            result['msg'] = f'未知动作: {action}'

    except Exception as e:
        result['ok'] = False
        result['msg'] = f'操作失败: {traceback.format_exc()}'

    return jsonify(result)


@app.route('/api/pick-file')
def api_pick_file():
    """使用 easygui 选择本地文件，返回完整路径"""
    import easygui
    title = request.args.get('title', '选择文件')
    filt = request.args.get('filter', '')
    default = request.args.get('default', '*')

    if filt:
        exts = [e.strip().lower() for e in filt.split(',') if e.strip()]
        if exts:
            patterns = ';'.join(f'*{e}' for e in exts)
            filetypes = [patterns]
        else:
            filetypes = ['*.*']
    else:
        filetypes = ['*.*']

    path = easygui.fileopenbox(title=title, filetypes=filetypes, default=default)
    if not path:
        return jsonify({'ok': False, 'msg': '未选择文件', 'data': None})
    return jsonify({'ok': True, 'msg': '已选择', 'data': {'path': path}})


@app.route('/api/pick-folder')
def api_pick_folder():
    """使用 easygui 选择本地文件夹，返回完整路径"""
    import easygui
    title = request.args.get('title', '选择文件夹')
    default = request.args.get('default', os.path.expanduser('~'))

    path = easygui.diropenbox(title=title, default=default)
    if not path:
        return jsonify({'ok': False, 'msg': '未选择文件夹', 'data': None})
    return jsonify({'ok': True, 'msg': '已选择', 'data': {'path': path}})


def open_browser():
    # Windows 下用系统默认浏览器打开（os.startfile 为 Windows 专属 API）
    os.startfile(SERVICE_URL)


if __name__ == '__main__':
    # 打包为 exe 后（PyInstaller frozen 模式）禁用 debug 与 reloader
    is_frozen = getattr(sys, 'frozen', False)

    if is_port_in_use(SERVICE_PORT):
        # 后台已有服务在运行：打开浏览器后本进程直接退出
        print(f"检测到服务已在后台运行（端口 {SERVICE_PORT}），打开浏览器后退出")
        open_browser()
        sys.exit(0)

    # 后台无服务：启动服务，并在 3 秒后自动打开浏览器；
    # 本进程常驻后台提供服务（打包为无控制台 exe 即纯后台运行）
    print(f"CQApkTools {APP_VERSION} 已启动，端口号：{SERVICE_PORT}")

    threading.Timer(3.0, open_browser).start()

    app.run(
        debug=not is_frozen,
        host='0.0.0.0',
        port=SERVICE_PORT,
        threaded=True,
        use_reloader=not is_frozen,
    )
