@echo off
cd /d "%~dp0"
afkj-bot.exe --smoke
echo.
echo === smoke run done, press any key to close ===
pause >nul
