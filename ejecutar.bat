@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual. Creando e instalando dependencias...
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3 -m venv .venv
    ) else (
        echo Instala Python 3.10+ desde https://www.python.org/downloads/
        echo O crea el venv manualmente y vuelve a ejecutar este archivo.
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
