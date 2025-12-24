@echo off
setlocal

:: 定义要排除的文件夹和文件
set EXCLUDE=build\ dist\ Py2EXE.bat

:: 1. 删除当前文件夹下的build和dist文件夹
echo 删除build和dist文件夹...
if exist build (
    rmdir /s /q build
)
if exist dist (
    rmdir /s /q dist
)

:: 2. 使用PyInstaller打包CQAPKTools.py
echo 正在使用PyInstaller打包CQAPKTools.py...
pyinstaller -w -i CQAPKTools.ico CQAPKTools.py

:: 检查PyInstaller是否成功执行
if %ERRORLEVEL% neq 0 (
    echo PyInstaller执行失败。
    exit /b %ERRORLEVEL%
)

:: 3. 复制当前文件夹下的除了build文件夹、dist文件夹、Py2EXE.bat之外的所有文件和文件夹到dist\CQAPKTools\_internal\
echo 正在复制文件到dist\CQAPKTools\_internal\...
for /d %%i in (*) do (
    if "%%i" NEQ "build" if "%%i" NEQ "dist" (
        xcopy "%%i" "dist\CQAPKTools\_internal\%%i\" /s /i /q
    )
)
for %%i in (*.*) do (
    if "%%i" NEQ "Py2EXE.bat" (
        copy "%%i" "dist\CQAPKTools\_internal\%%i"
    )
)

echo 所有操作完成。
pause
endlocal