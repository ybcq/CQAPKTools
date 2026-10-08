@echo off
setlocal

:: 清理旧的 build、dist 文件夹
echo 清理 build、dist 文件夹...
if exist build (
    rmdir /s /q build
)
if exist dist (
    rmdir /s /q dist
)

:: 使用 PyInstaller 按 CQAPKTools.spec 打包 app.py
:: （templates/static/Setup.ini 等运行时资源已配置在 spec 的 datas 中）
echo 正在使用 PyInstaller 打包 app.py...
pyinstaller --noconfirm CQAPKTools.spec

if %ERRORLEVEL% neq 0 (
    echo PyInstaller 打包失败。
    exit /b %ERRORLEVEL%
)

echo 打包完成：dist\CQAPKTools\CQAPKTools.exe
pause
endlocal
