@ECHO OFF&PUSHD %~DP0 &TITLE 绿化和选项
mode con cols=30 lines=16
color 9E

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
@ echo. *************************** 
@ echo.
set /p xj= 输入数字按回车：
if /i "%xj%"=="1" Goto InstallA
if /i "%xj%"=="2" Goto RightA
if /i "%xj%"=="3" Goto UnInstallA
@ echo.
echo      选择无效，请重新输入
ping -n 2 127.1>nul 
goto menu

:InstallA
@ echo.
ECHO 　　　正在设置中..请稍等..
assoc .apk=CQApkRenameFiles
ftype CQApkRenameFiles="%~dp0CQApkRename.exe" %*
goto fanhui

:RightA
@ echo.
ECHO 　　　正在设置中..请稍等..
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.apk\shell\重命名APK\command" /ve /t REG_SZ /d "\"%~dp0CQApkRename.exe\" ""%*""" /f
goto fanhui

:UnInstallA
@ echo.
ECHO 　　　正在删除中..请稍等..
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.apk\shell\重命名APK" /f
goto fanhui

:fanhui
@ echo.
ECHO 　　　修改完成..
pause
goto menu