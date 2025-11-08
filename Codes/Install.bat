@ECHO OFF&PUSHD %~DP0 &TITLE 初琴APK安装器
mode con cols=30 lines=22
color 9E

::获取管理员权限
>NUL 2>&1 REG.exe query "HKU\S-1-5-19" || (
    ECHO SET UAC = CreateObject^("Shell.Application"^) > "%TEMP%\Getadmin.vbs"
    ECHO UAC.ShellExecute "%~f0", "%1", "", "runas", 1 >> "%TEMP%\Getadmin.vbs"
    "%TEMP%\Getadmin.vbs"
    DEL /f /q "%TEMP%\Getadmin.vbs" 2>NUL
    Exit /b
)

set "exe=InstallApk.exe"
set "lnk=拖拽到此安装APK"
mshta VBScript:Execute("Set a=CreateObject(""WScript.Shell""):Set b=a.CreateShortcut(a.SpecialFolders(""Desktop"") & ""\%lnk%.lnk""):b.TargetPath=""%~dp0%exe%"":b.WorkingDirectory=""%~dp0"":b.Save:close")

::目录
:Menu
Cls
@ echo. *************************** 
@ echo. *                         * 
@ echo. *　　   菜 单 选 项       * 
@ echo. *                         * 
@ echo. *   默认打开 → 请输入1   * 
@ echo. *                         * 
@ echo. *   右键菜单 → 请输入2   * 
@ echo. *                         * 
@ echo. *   删除右键 → 请输入3   * 
@ echo. *                         * 
@ echo. *   一键冰箱 → 请输入4   * 
@ echo. *                         * 
@ echo. *   一键黑域 → 请输入5   * 
@ echo. *                         * 
@ echo. *   FastBoot → 请输入6   * 
@ echo. *                         * 
@ echo. *   CPU 型号 → 请输入7   * 
@ echo. *                         * 
@ echo. *************************** 
@ echo.
set /p xj= 输入数字按回车：
if /i "%xj%"=="1" Goto InstallA
if /i "%xj%"=="2" Goto RightA
if /i "%xj%"=="3" Goto UnInstallA
if /i "%xj%"=="4" Goto IceBoxInstall
if /i "%xj%"=="5" Goto HeiYuInstall
if /i "%xj%"=="6" Goto Re2Fastboot
if /i "%xj%"=="7" Goto GetCpu 
@ echo.
echo      选择无效，请重新输入
ping -n 2 127.1>nul 
goto menu

:InstallA
@ echo.
ECHO 　　　正在设置中..请稍等..
assoc .apk=APKInstallFiles
ftype APKInstallFiles="%~dp0InstallApk.exe" %*
goto fanhui

:RightA
@ echo.
ECHO 　　　正在设置中..请稍等..
reg add "HKEY_CLASSES_ROOT\*\shell\用 ApkInstallLite 安装\command" /ve /t REG_SZ /d "\"%~dp0InstallApk.exe\" ""%%1""" /f
goto fanhui

:UnInstallA
@ echo.
ECHO 　　　正在删除中..请稍等..
reg delete "HKEY_CLASSES_ROOT\*\shell\用 ApkInstallLite 安装" /f
goto fanhui

:fanhui
@ echo.
ECHO 　　　修改完成..
pause
goto menu

::冰箱安装程序
:IceBoxInstall
cls
@ echo.
@ echo.     步骤1：
@ echo.     请确保安卓系统5.0以上
@ echo.     已连接好电脑
@ echo.     并完成第三方软件备份
@ echo.
pause

cls
@ echo.
@ echo.     步骤2：
@ echo.     请确保手机内所有账户已删除
@ echo.
pause

cls
@ echo.
@ echo.     步骤3：
@ echo.     正在安装IceBox...
@ echo.     请在手机上出现IceBox图标后
@ echo.     打开软件然后后退退出
@ echo.
adb install icebox.apk
pause

cls
@ echo.
@ echo.     步骤4：
@ echo.     正在获取管理员权限...
@ echo.     如果出现错误代码
@ echo.     尝试百度原因或者反馈代码
@ echo.     到作者的博客
@ echo.
adb shell dpm set-device-owner com.catchingnow.icebox/.receiver.DPMReceiver
pause

cls
@ echo.
@ echo.     步骤5：
@ echo.     打开IceBox查看是否可以使用
@ echo.
pause
goto Menu

::黑域安装
:HeiYuInstall
cls
@ echo.
@ echo.     步骤1：
@ echo.     请确保手机已使用
@ echo.     连接好电脑
@ echo.     并完成第三方软件备份
@ echo.
pause

cls
@ echo.
@ echo.     步骤2：
@ echo.     正在安装黑域...
@ echo.     请在手机上出现黑域图标后
@ echo.     打开软件，开始使用，后退退出
@ echo.
adb install heiyu.apk
pause

cls
@ echo.
@ echo.     步骤3：
@ echo.     正在获取权限...
@ echo.     如果出现错误代码
@ echo.     尝试百度原因或者反馈代码
@ echo.     到作者的博客
@ echo.
adb -d shell sh /data/data/me.piebridge.brevent/brevent.sh
adb shell dpm set-device-owner com.hld.apurikakusu/.receiver.DPMReceiver
pause

cls
@ echo.
@ echo.     步骤4：
@ echo.     打开黑域查看是否可以使用
@ echo.
pause
goto Menu

::重启到FastBoot
:Re2Fastboot
cls
@ echo.
@ echo.     正在重启到FastBoot...
@ echo.
adb reboot bootloader
pause
goto Menu

::CPU型号
:GetCpu
cls
@ echo.
@ echo.     正在获取CPU信息...
@ echo.
pause
goto Menu
adb shell cat /proc/cpuinfo
pause
goto Menu