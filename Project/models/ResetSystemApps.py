"""
系统应用更新管理工具 - install-existing 置顶法

原理：
    1. 检测所有已有更新的系统应用（apk 路径位于 /data/app/ 即说明被更新过）
    2. 使用 'cmd package install-existing' 重新安装这些应用
    3. 重新安装后应用会出现在应用列表（"最近安装"）顶部
    4. 然后可在手机设置里手动点击「卸载更新」，数据完全保留

既可独立运行（python models/ResetSystemApps.py），也可由 GUI 调用：
    scan_system_app_updates(log=None) -> 返回应用列表
    reinstall_updated_apps(updated, log=None) -> 执行置顶重装
"""

import subprocess
from typing import Callable, Dict, List, Optional, Tuple


def run_adb(command: str, timeout: int = 15) -> Tuple[str, str]:
    """执行adb命令，返回(stdout, stderr)"""
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "Timeout"
    except Exception as e:
        return "", str(e)


def check_device_connected() -> bool:
    """检查是否有设备在线"""
    stdout, _ = run_adb("adb devices")
    for line in stdout.splitlines():
        if line.endswith("device") and not line.startswith("List"):
            return True
    return False


def _log(log: Optional[Callable[[str], None]], msg: str) -> None:
    """输出到回调或控制台"""
    if log:
        log(msg)
    else:
        print(msg)


def scan_system_app_updates(log: Optional[Callable[[str], None]] = None) -> List[Dict]:
    """
    扫描所有系统应用，返回含全部系统应用的信息列表。
    每条包含 pkg / has_update / system_path / update_path / all_paths。
    apk 路径位于 /data/app/ 即认为该应用已更新。
    """
    _log(log, "🔍 检查设备连接...")
    if not check_device_connected():
        _log(log, "❌ 设备未就绪，请确认USB调试已授权")
        return []

    # 获取所有系统应用
    _log(log, "📊 正在扫描系统应用更新（应用较多时请耐心等待）...")
    stdout, _ = run_adb("adb shell pm list packages -s")

    if not stdout:
        _log(log, "❌ 获取系统应用列表失败，请检查设备连接")
        return []

    system_pkgs = [
        line.replace('package:', '').strip()
        for line in stdout.splitlines()
        if line.startswith('package:')
    ]

    _log(log, f"找到 {len(system_pkgs)} 个系统应用\n")

    results = []
    total = len(system_pkgs)

    for idx, pkg in enumerate(system_pkgs, 1):
        _log(log, f"  [{idx}/{total}] 检测: {pkg}")

        # 获取该应用的APK路径
        path_out, _ = run_adb(f"adb shell pm path {pkg}")

        # 判断是否有更新
        has_update = False
        update_path = None
        system_path = None

        for line in path_out.splitlines():
            if line.startswith('package:'):
                path = line.replace('package:', '').strip()
                if path.startswith('/data/app/'):
                    has_update = True
                    update_path = path
                elif path.startswith('/system/') or path.startswith('/vendor/') or path.startswith('/product/'):
                    system_path = path

        if has_update:
            _log(log, f"    ✅ 有更新! 更新包在: {update_path}")
        else:
            _log(log, "    ⏳ 无更新 (仅系统原始版本)")

        results.append({
            'pkg': pkg,
            'has_update': has_update,
            'system_path': system_path,
            'update_path': update_path,
            'all_paths': [
                line.replace('package:', '').strip()
                for line in path_out.splitlines()
                if line.startswith('package:')
            ]
        })

    return results


def reinstall_updated_apps(updated: List[Dict], log: Optional[Callable[[str], None]] = None) -> Tuple[int, int, List[str]]:
    """
    使用 install-existing 重新安装有更新的应用（置顶），数据保留。
    返回 (成功数, 失败数, 失败列表)。
    """
    success_count = 0
    fail_count = 0
    fail_list = []

    for idx, r in enumerate(updated, 1):
        pkg = r['pkg']
        _log(log, f"\n[{idx}/{len(updated)}] 处理: {pkg}")
        stdout, stderr = run_adb(f"adb shell cmd package install-existing {pkg}")

        if "Success" in stdout:
            _log(log, f"    ✅ 重新安装成功（已置顶）: {pkg}")
            success_count += 1
        else:
            _log(log, f"    ❌ 重新安装失败: {pkg}")
            if stderr:
                _log(log, f"       错误: {stderr}")
            if stdout:
                _log(log, f"       提示: {stdout}")
            fail_count += 1
            fail_list.append(pkg)

    return success_count, fail_count, fail_list


def _explain(log: Optional[Callable[[str], None]] = None) -> None:
    """输出工作原理说明"""
    _log(log, "=" * 60)
    _log(log, "系统应用更新管理工具 - install-existing 置顶法")
    _log(log, "=" * 60)
    _log(log, "\n📌 原理说明:")
    _log(log, "   1. 检测所有已有更新的系统应用")
    _log(log, "   2. 使用 'cmd package install-existing' 重新安装这些应用")
    _log(log, "   3. 重新安装后，应用会出现在应用列表的顶部")
    _log(log, "   4. 然后你可以在设置里手动点击「卸载更新」")
    _log(log, "   5. ✅ 数据完全保留，不会丢失")
    _log(log, "=" * 60)


def main():
    _explain()

    # 检查设备连接
    print("\n🔍 检查设备连接...")
    if not check_device_connected():
        print("❌ 设备未就绪，请确认USB调试已授权")
        return
    print("✅ 设备已连接\n")

    # 执行检测
    results = scan_system_app_updates()
    if not results:
        print("❌ 扫描失败或未获取到系统应用列表")
        return

    # 统计
    updated = [r for r in results if r['has_update']]
    not_updated = [r for r in results if not r['has_update']]

    print("\n" + "=" * 60)
    print("📊 扫描结果")
    print("=" * 60)
    print(f"总系统应用: {len(results)} 个")
    print(f"有更新的:   {len(updated)} 个")
    print(f"无更新的:   {len(not_updated)} 个")

    if not updated:
        print("\n✅ 没有发现任何系统应用有更新，无需操作。")
        return

    # 显示有更新的应用列表
    print(f"\n📦 找到 {len(updated)} 个有更新的系统应用:")
    for idx, r in enumerate(updated, 1):
        print(f"  {idx}. {r['pkg']}")

    # 确认操作
    print("\n" + "⚠️ " * 20)
    print("下一步操作说明:")
    print(f"  1. 脚本将使用 'install-existing' 重新安装这 {len(updated)} 个应用")
    print("  2. 重新安装后，打开手机 设置 → 应用设置 → 应用管理")
    print("  3. 在应用列表顶部找到「最近安装」的应用")
    print("  4. 逐个点击应用，选择「卸载更新」")
    print("")
    print("✅ 优势:")
    print("  - 使用 install-existing，数据完全保留")
    print("  - 不会导致应用异常")
    print("  - 可以精确控制哪些应用回退到出厂版本")
    print("  - 不需要从设备拉取APK，速度快")
    print("⚠️ " * 20)

    confirm = input("\n确认继续重新安装这些应用? (输入 YES 继续, 其他键取消): ")
    if confirm != "YES":
        print("❌ 操作已取消")
        return

    # 执行重新安装
    print("\n" + "=" * 60)
    print("🚀 开始使用 install-existing 重新安装应用...")
    print("=" * 60)

    success_count, fail_count, fail_list = reinstall_updated_apps(updated)

    # 最终报告
    print("\n" + "=" * 60)
    print("📊 操作完成")
    print("=" * 60)
    print(f"✅ 成功重新安装: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")

    if fail_list:
        print("\n失败的应用列表:")
        for pkg in fail_list:
            print(f"  - {pkg}")
        print("\n💡 失败的应用可能是核心组件，需要手动在设置中操作")

    print("\n" + "=" * 60)
    print("📌 下一步操作（重要）:")
    print("=" * 60)
    print("1. 打开手机: 设置 → 应用设置 → 应用管理")
    print("2. 点击右上角排序按钮，选择「按安装时间排序」")
    print("3. 找到刚刚重新安装的应用（在列表顶部）")
    print("4. 逐个点击，选择「卸载更新」")
    print("")
    print("💡 提示:")
    print("  - 只卸载你确定不需要更新的应用（如广告、分析组件等）")
    print("  - 桌面、电话、短信等核心应用建议保留更新")
    print("  - 如果不小心卸载了重要应用，去应用商店更新即可恢复")


if __name__ == "__main__":
    main()