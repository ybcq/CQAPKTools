"""
CQApkRename - APK 批量重命名核心模块
替代原 CQApkRename.exe，使用 aapt + keytool 提取 APK 元数据并按模式重命名。

支持的占位符：
    {应用包名}       - package name
    {应用名字}       - application label
    {版本名字}       - version name
    {APP证书用户}    - certificate owner
    {APP证书序列号}  - certificate serial number
"""

import os
import re
import subprocess


def _run_aapt(aapt_path, apk_path):
    """运行 aapt dump badging 并返回输出文本"""
    result = subprocess.run(
        [aapt_path, 'dump', 'badging', apk_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', errors='ignore'
    )
    return result.stdout


def _run_keytool(keytool_path, apk_path):
    """运行 keytool -printcert -jarfile 并返回输出文本"""
    result = subprocess.run(
        [keytool_path, '-printcert', '-jarfile', apk_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', errors='ignore'
    )
    return result.stdout


def extract_apk_info(apk_path, aapt_path='aapt.exe', keytool_path='bin\\keytool.exe'):
    """
    从 APK 文件中提取元数据。

    返回 dict:
        package_name:  应用包名
        app_name:      应用名字
        version_name:  版本名字
        cert_owner:    APP证书用户
        cert_serial:   APP证书序列号
    """
    info = {
        'package_name': '',
        'app_name': '',
        'version_name': 'unknown',
        'cert_owner': 'unknown',
        'cert_serial': 'unknown',
    }

    # --- aapt 解析 ---
    aapt_output = _run_aapt(aapt_path, apk_path)

    for line in aapt_output.splitlines():
        # package: name='com.example.app' versionCode='1' versionName='1.0'
        if line.startswith('package:'):
            m = re.search(r"name='([^']*)'", line)
            if m:
                info['package_name'] = m.group(1)
            m = re.search(r"versionName='([^']*)'", line)
            if m:
                info['version_name'] = m.group(1)

        # application-label:'App Name'
        if line.startswith('application-label:'):
            label = line.split(':', 1)[1].strip().strip("'").strip('"')
            if label:
                info['app_name'] = label

        # application-label-zh_CN:'中文名' (优先使用中文名)
        if line.startswith('application-label-zh_CN:'):
            label = line.split(':', 1)[1].strip().strip("'").strip('"')
            if label:
                info['app_name'] = label

    # fallback: 如果没有应用名，使用包名
    if not info['app_name']:
        info['app_name'] = info['package_name']

    # --- keytool 解析 ---
    keytool_output = _run_keytool(keytool_path, apk_path)

    for line in keytool_output.splitlines():
        # Owner: CN=Taobao, OU=..., O=..., ...
        if line.strip().startswith('Owner:'):
            info['cert_owner'] = line.split(':', 1)[1].strip()

        # Serial number: 53ed542f
        if line.strip().startswith('Serial number:'):
            info['cert_serial'] = line.split(':', 1)[1].strip()

    return info


def build_filename(info, pattern):
    """
    根据元数据和命名模式生成新文件名（不含扩展名）。

    pattern 中的占位符会被替换：
        {应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}
    """
    filename = pattern
    filename = filename.replace('{应用包名}', info['package_name'])
    filename = filename.replace('{应用名字}', info['app_name'])
    filename = filename.replace('{版本名字}', info['version_name'])
    filename = filename.replace('{APP证书用户}', info['cert_owner'])
    filename = filename.replace('{APP证书序列号}', info['cert_serial'])

    # 清理文件名中的非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename.strip()


def rename_apk(apk_path, pattern, aapt_path='aapt.exe', keytool_path='bin\\keytool.exe'):
    """
    重命名单个 APK 文件。

    返回 (old_path, new_path, error_msg)。
    成功时 error_msg 为 None。
    """
    if not os.path.exists(apk_path):
        return (apk_path, None, f'文件不存在: {apk_path}')

    if not apk_path.lower().endswith('.apk'):
        return (apk_path, None, f'不是APK文件: {apk_path}')

    try:
        info = extract_apk_info(apk_path, aapt_path, keytool_path)
    except Exception as e:
        return (apk_path, None, f'解析失败: {e}')

    new_name = build_filename(info, pattern) + '.apk'
    new_path = os.path.join(os.path.dirname(apk_path), new_name)

    # 如果新旧路径相同，跳过
    if os.path.normcase(apk_path) == os.path.normcase(new_path):
        return (apk_path, new_path, None)

    # 如果目标已存在，添加序号
    counter = 1
    base_new_path = new_path
    while os.path.exists(new_path):
        name_part = build_filename(info, pattern)
        new_name = f'{name_part}_{counter}.apk'
        new_path = os.path.join(os.path.dirname(apk_path), new_name)
        counter += 1

    try:
        os.rename(apk_path, new_path)
        return (apk_path, new_path, None)
    except Exception as e:
        return (apk_path, None, f'重命名失败: {e}')


def batch_rename(apk_paths, pattern, aapt_path='aapt.exe', keytool_path='bin\\keytool.exe',
                 log_callback=None):
    """
    批量重命名 APK 文件。

    log_callback(msg) 可选，用于输出日志。

    返回 (success_count, fail_count, results)
        results: [(old_path, new_path, error_msg), ...]
    """
    results = []
    success_count = 0
    fail_count = 0

    for apk_path in apk_paths:
        if log_callback:
            log_callback(f'正在处理: {os.path.basename(apk_path)}')

        old_path, new_path, error = rename_apk(
            apk_path, pattern, aapt_path, keytool_path
        )

        if error:
            fail_count += 1
            if log_callback:
                log_callback(f'  失败: {error}')
        else:
            success_count += 1
            if log_callback:
                log_callback(f'  成功: {os.path.basename(new_path)}')

        results.append((old_path, new_path, error))

    return success_count, fail_count, results
