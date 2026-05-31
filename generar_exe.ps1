# Genera dist\BombChampions.exe (incluye Python y pygame; no requiere instalación previa).
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Pip = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"

if (-not (Test-Path $Python)) {
    Write-Error "No se encontró .venv. Ejecuta primero ejecutar.bat o crea el entorno virtual."
    exit 1
}

& $Pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m PyInstaller --noconfirm --clean BombChampions.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Listo: dist\BombChampions.exe"
Write-Host "Copia ese archivo a otro PC con Windows y ejecútalo con doble clic."
