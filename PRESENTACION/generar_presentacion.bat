@echo off
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generar_presentacion.ps1"
if errorlevel 1 pause
