@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
set "exit_code=%ERRORLEVEL%"

if not "%exit_code%"=="0" (
    echo.
    echo 运行失败，请查看上方错误信息。
    pause
)

exit /b %exit_code%
