# Prepara VenomScope para la defensa en esta notebook (Windows).
# Clona el repo FUERA de OneDrive, instala todo, genera los artefactos,
# precalienta la cache y corre los tests. Deja todo en preparar_demo.log.
# Correr con:  clic derecho > "Ejecutar con PowerShell"

$ErrorActionPreference = "Continue"
$Repo    = "https://github.com/camaleonica/VenomScope.git"
$Destino = Join-Path $env:USERPROFILE "VenomScope"
$Log     = Join-Path $PSScriptRoot "preparar_demo.log"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
"VenomScope - preparacion de la demo  $(Get-Date)" | Out-File -FilePath $Log

function Anotar($t) { $t | Tee-Object -FilePath $Log -Append }
function Paso($t)   { Anotar ""; Anotar "=== $t ===" }
function Correr([string]$desc, [scriptblock]$sb, [switch]$Seguir) {
    & $sb 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) {
        Anotar "FALLO: $desc (codigo $LASTEXITCODE)"
        if (-not $Seguir) { Anotar "RESULTADO: ERROR"; Read-Host "Fallo un paso. Enter para cerrar"; exit 1 }
    } else { Anotar "OK: $desc" }
}
function RefrescarPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}

Paso "1/6 Git y Python 3.12"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Anotar "No hay git: lo instalo con winget."
    Correr "instalar git" { winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements }
    RefrescarPath
}
Correr "git" { git --version }

$PyExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = (& py -3.12 -c "import sys;print(sys.executable)" 2>$null)
}
$Local312 = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
if (-not $PyExe -and (Test-Path $Local312)) { $PyExe = $Local312 }
if (-not $PyExe) {
    Anotar "No hay Python 3.12: lo instalo con winget (solo para este usuario)."
    Correr "instalar Python 3.12" { winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements }
    RefrescarPath
    if (Test-Path $Local312) { $PyExe = $Local312 }
}
if (-not $PyExe) { Anotar "RESULTADO: ERROR - no encuentro Python 3.12"; Read-Host "Enter para cerrar"; exit 1 }
Correr "python 3.12" { & $PyExe --version }

Paso "2/6 Repo en $Destino"
if (Test-Path (Join-Path $Destino ".git")) {
    Correr "git pull" { git -C $Destino pull --ff-only }
} else {
    Correr "git clone" { git clone $Repo $Destino }
}
Set-Location $Destino
Correr "commit actual" { git log -1 --oneline }

Paso "3/6 Entorno virtual y librerias (puede tardar 5-15 min)"
$VPy = Join-Path $Destino ".venv\Scripts\python.exe"
if (-not (Test-Path $VPy)) { Correr "crear .venv" { & $PyExe -m venv .venv } }
Correr "actualizar pip" { & $VPy -m pip install --upgrade pip --progress-bar off }
Correr "instalar requirements" { & $VPy -m pip install -r requirements.txt --progress-bar off }

Paso "4/6 Descargar ESM-2 y generar artefactos"
$env:HF_HUB_OFFLINE = "0"
Correr "construir_artefactos" { & $VPy scripts\construir_artefactos.py }

Paso "5/6 Precalentar la cache"
Correr "precalentar_cache" { & $VPy scripts\precalentar_cache.py }

Paso "6/6 Tests (sin internet)"
$env:HF_HUB_OFFLINE = "1"
Correr "pytest" { & $VPy -m pytest -q } -Seguir

Anotar ""
Anotar "RESULTADO: TERMINADO"
Anotar "Para abrir la app: doble clic en abrir_venomscope.bat (junto a este script)"
Read-Host "Listo. Enter para cerrar"
