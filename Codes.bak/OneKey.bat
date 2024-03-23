::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCuDJFiA9n4fJh5/SR2rP26YCa1S4ev0jw==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCuDJFiA9n4fJh5/SR2rP26YCa1S7fD+jw==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
::题目与颜色
@echo OFF&PUSHD %~DP0 &TITLE 枫云海韵一键ICEBOX小程序
mode con cols=32 lines=20
color 3F

::请求管理员权限
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
echo 请求管理员权限...
goto UACPrompt 
) else ( goto gotAdmin )

:UACPrompt
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
exit /B

:gotAdmin
::显示文本
cls
@ echo.
@ echo. ****************************** 
@ echo. *                            *
@ echo. *　　　 菜 单 选 项          *
@ echo. *                            *
@ echo. *    一键冰箱 → 请输入1     *
@ echo. *                            *
@ echo. *    一键黑域 → 请输入2     *
@ echo. *                            *
@ echo. *  启动 FastBoot → 请输入3  *
@ echo. *                            *
@ echo. *   获取CPU型号 → 请输入4   *
@ echo. *                            *
@ echo. ******************************

set /p xj=输入数字按回车：
if /i "%xj%"=="1" Goto IceBoxInstall
if /i "%xj%"=="2" Goto HeiYuInstall
if /i "%xj%"=="3" Goto Re2Fastboot
if /i "%xj%"=="4" Goto GetCpu 
@ echo.
echo      选择无效，请重新输入
ping -n 2 127.1>nul 
goto gotAdmin

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
goto gotAdmin

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
goto gotAdmin

::重启到FastBoot
:Re2Fastboot
cls
@ echo.
@ echo.     正在重启到FastBoot...
@ echo.
adb reboot bootloader
pause
goto gotAdmin

::重启到FastBoot
:GetCpu
cls
@ echo.
@ echo.     正在获取CPU信息...
@ echo.
pause
goto gotAdmin
adb shell cat /proc/cpuinfo
pause
goto gotAdmin
