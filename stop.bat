@echo off
echo Stopping Bandwidth Limiter...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Windows 11 Global Bandwidth Limiter*"
echo.
echo If the GUI was open, it should now be closed. You may need to verify if the python process is gone.
pause
