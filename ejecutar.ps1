# Ejecuta Bomb Champions con el Python del entorno virtual del proyecto.
$Raiz = $PSScriptRoot
Set-Location $Raiz

$PythonVenv = Join-Path $Raiz ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonVenv)) {
    Write-Host "No se encontro .venv. Creando entorno e instalando pygame..."
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & py -3 -m venv (Join-Path $Raiz ".venv")
    } else {
        Write-Host "Instala Python 3.10+ o ejecuta ejecutar.bat tras crear el venv."
        exit 1
    }
    & $PythonVenv -m pip install -r requirements.txt
}

& $PythonVenv (Join-Path $Raiz "main.py")
