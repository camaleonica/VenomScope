@echo off
rem Doble clic aca. Corre preparar_demo.ps1 sin depender de la politica de scripts
rem y deja la ventana abierta al final para ver si hubo algun error.
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0preparar_demo.ps1"
echo.
echo (codigo de salida: %ERRORLEVEL%)
pause
