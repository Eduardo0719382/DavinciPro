<#
.SYNOPSIS
  Desinstala el Resolve Pro Pack usando el manifiesto creado por install.ps1.

.DESCRIPTION
  - Borra solo archivos cuyo hash sigue siendo el que se instalo.
  - Si modificaste un archivo instalado, lo conserva y avisa (usa -Force para borrarlo igualmente).
  - Si la instalacion hizo backup de un archivo previo, lo restaura.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -DryRun
  powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
#>
[CmdletBinding()]
param(
    [string]$StateDir = (Join-Path $env:LOCALAPPDATA 'ResolveProPack'),
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$Manifest = Join-Path $StateDir 'manifest.json'
function Say($msg, $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

Say "== Resolve Pro Pack: desinstalacion $(if ($DryRun) {'(SIMULACION, no se borra nada)'}) ==" Cyan
if (-not (Test-Path $Manifest)) { Say "No hay manifiesto en $Manifest. Nada que desinstalar." Yellow; exit 0 }

$files = @((Get-Content $Manifest -Raw | ConvertFrom-Json).files)
$kept = @(); $nDel = 0; $nRest = 0; $nMissing = 0

foreach ($f in $files) {
    $removed = $false
    if (Test-Path $f.dest) {
        $hash = (Get-FileHash $f.dest -Algorithm SHA256).Hash
        if ($hash -eq $f.sha256 -or $Force) {
            try {
                if (-not $DryRun) { Remove-Item $f.dest -Force }
                $removed = $true; $nDel++
                Say "  -  $($f.dest)" Green
            } catch {
                Say "  !  sin permiso para borrar $($f.dest) (LUT/DCTL: ejecuta como administrador)" Red
            }
        } else {
            Say "  ?  $($f.dest) fue modificado despues de instalar: se conserva (usa -Force para borrarlo)" Yellow
        }
    } else {
        $removed = $true; $nMissing++
    }

    if ($removed -and $f.backup -and (Test-Path $f.backup)) {
        if (-not $DryRun) { Copy-Item $f.backup $f.dest -Force }
        $nRest++
        Say "  R  restaurado tu archivo original: $($f.dest)" Cyan
    }
    if (-not $removed) { $kept += $f }
}

# carpetas propias del paquete (PRO Pack / PRO_Pack): quitarlas solo si quedaron vacias
$packDirs = @($files | ForEach-Object { Split-Path $_.dest } | Select-Object -Unique |
    Where-Object { (Split-Path $_ -Leaf) -in 'PRO Pack', 'PRO_Pack' })
foreach ($d in $packDirs) {
    if (-not $DryRun -and (Test-Path $d) -and -not (Get-ChildItem $d -Force)) {
        try { Remove-Item $d -Force } catch { Say "  !  no se pudo quitar la carpeta vacia $d" Yellow }
    }
}

if (-not $DryRun) {
    if ($kept.Count -eq 0) {
        Move-Item $Manifest (Join-Path $StateDir ("manifest.uninstalled-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))) -Force
    } else {
        $doc = [pscustomobject]@{ pack = 'Resolve Pro Pack'; installed = 'parcial'; files = $kept }
        $doc | ConvertTo-Json -Depth 4 | Set-Content $Manifest -Encoding UTF8
    }
}

Say ''
Say "Borrados: $nDel   Restaurados: $nRest   Ya no existian: $nMissing   Conservados: $($kept.Count)" Cyan
Say "Los backups se conservan en $StateDir\backups por si los necesitas." Gray
