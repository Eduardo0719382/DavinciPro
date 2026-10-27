<#
.SYNOPSIS
  Instala el Resolve Pro Pack en DaVinci Resolve (Windows).

.DESCRIPTION
  - Plantillas Fusion (.setting) -> carpeta de plantillas del usuario (no requiere administrador).
  - LUTs (.cube) y DCTL (.dctl)  -> carpeta LUT de Resolve, subcarpeta PRO_Pack (requiere administrador).
  - Antes de sobrescribir un archivo que no es de este paquete, lo copia a una carpeta de backup.
  - Guarda un manifiesto (rutas + hash) para que uninstall.ps1 quite solo lo que instalo.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
  powershell -ExecutionPolicy Bypass -File .\install.ps1
#>
[CmdletBinding()]
param(
    [string]$TemplatesRoot = (Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit'),
    [string]$FusesRoot     = (Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion\Fuses'),
    [string]$LutRoot       = (Join-Path $env:ProgramData 'Blackmagic Design\DaVinci Resolve\Support\LUT'),
    [string]$StateDir      = (Join-Path $env:LOCALAPPDATA 'ResolveProPack'),
    [string]$PackFolder    = 'PRO Pack',
    [switch]$SkipLUTs,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$PackDir   = $PSScriptRoot
$Stamp     = Get-Date -Format 'yyyyMMdd-HHmmss'
$Manifest  = Join-Path $StateDir 'manifest.json'
$BackupDir = Join-Path $StateDir "backups\$Stamp"
$LutDest   = [IO.Path]::Combine($LutRoot, 'PRO_Pack')

function Say($msg, $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

function Test-Writable($dir) {
    try {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null; $created = $true }
        $probe = Join-Path $dir ".proPack_probe_$Stamp"
        [IO.File]::WriteAllText($probe, 'x')
        Remove-Item $probe -Force
        if ($created) { Remove-Item $dir -Force }
        return $true
    } catch { return $false }
}

Say "== Resolve Pro Pack: instalacion $(if ($DryRun) {'(SIMULACION, no se escribe nada)'}) ==" Cyan
Say "Plantillas : $TemplatesRoot"
Say "LUT / DCTL : $LutDest"
Say "Estado     : $StateDir"

if (Get-Process -Name 'Resolve' -ErrorAction SilentlyContinue) {
    Say 'AVISO: DaVinci Resolve esta abierto. Reinicialo despues de instalar para ver las plantillas.' Yellow
}

# ---------------------------------------------------------------- plan de copia
$plan = @()
foreach ($cat in 'Transitions', 'Titles', 'Effects', 'Generators') {
    $src = Join-Path $PackDir $cat
    if (-not (Test-Path $src)) { continue }
    Get-ChildItem $src -File | Where-Object { $_.Extension -in '.setting', '.png' } | ForEach-Object {
        # subcarpeta propia: Resolve la muestra como grupo "PRO Pack" dentro de cada categoria
        $plan += [pscustomobject]@{ Src = $_.FullName; Dest = [IO.Path]::Combine($TemplatesRoot, $cat, $PackFolder, $_.Name); Kind = 'template' }
    }
}
$fuseSrc = Join-Path $PackDir 'Fuses'
if (Test-Path $fuseSrc) {
    Get-ChildItem $fuseSrc -File -Filter *.fuse | ForEach-Object {
        $plan += [pscustomobject]@{ Src = $_.FullName; Dest = (Join-Path $FusesRoot $_.Name); Kind = 'template' }
    }
}
if (-not $SkipLUTs) {
    foreach ($pair in @(@('LUTs', '*.cube'), @('DCTL', '*.dctl'))) {
        $src = Join-Path $PackDir $pair[0]
        if (-not (Test-Path $src)) { continue }
        Get-ChildItem $src -File -Filter $pair[1] | ForEach-Object {
            $plan += [pscustomobject]@{ Src = $_.FullName; Dest = [IO.Path]::Combine($LutDest, $_.Name); Kind = 'lut' }
        }
    }
    if (($plan | Where-Object Kind -eq 'lut') -and -not $DryRun -and -not (Test-Writable $LutRoot)) {
        Say 'AVISO: sin permiso de escritura en la carpeta LUT de Resolve.' Yellow
        Say '       Se instalan solo las plantillas. Para LUT/DCTL, vuelve a ejecutar en una PowerShell "Como administrador".' Yellow
        $plan = @($plan | Where-Object Kind -ne 'lut')
    }
}

foreach ($p in $plan) {
    if (-not ([IO.Path]::GetFileName($p.Dest)).StartsWith('PRO_')) { throw "Archivo sin prefijo PRO_: $($p.Src). Instalacion cancelada." }
}

# ---------------------------------------------------------------- manifiesto previo
$previous = @{}
if (Test-Path $Manifest) {
    foreach ($e in @((Get-Content $Manifest -Raw | ConvertFrom-Json).files)) { $previous[$e.dest] = $e }
}

# ---------------------------------------------------------------- ejecucion
$entries = @{}
foreach ($k in $previous.Keys) { $entries[$k] = $previous[$k] }
$nNew = 0; $nUpd = 0; $nSame = 0; $nBak = 0

foreach ($p in $plan) {
    $srcHash = (Get-FileHash $p.Src -Algorithm SHA256).Hash
    $backup = $null
    if ($previous.ContainsKey($p.Dest)) { $backup = $previous[$p.Dest].backup }

    if (Test-Path $p.Dest) {
        $destHash = (Get-FileHash $p.Dest -Algorithm SHA256).Hash
        if ($destHash -eq $srcHash) {
            $nSame++
            Say "  =  $($p.Dest) (ya instalado, sin cambios)" DarkGray
            $entries[$p.Dest] = [pscustomobject]@{ dest = $p.Dest; sha256 = $srcHash; backup = $backup; kind = $p.Kind }
            continue
        }
        $ours = $previous.ContainsKey($p.Dest) -and $previous[$p.Dest].sha256 -eq $destHash
        if (-not $ours) {
            # archivo ajeno (o tuyo modificado): backup antes de tocarlo
            $rel = $p.Dest -replace '^[A-Za-z]:\\', ''
            $backup = Join-Path $BackupDir $rel
            $nBak++
            Say "  B  backup de $($p.Dest)" Yellow
            if (-not $DryRun) {
                New-Item -ItemType Directory -Force (Split-Path $backup) | Out-Null
                Copy-Item $p.Dest $backup -Force
            }
        }
        $nUpd++
        Say "  ~  $($p.Dest) (actualizado)" Green
    } else {
        $nNew++
        Say "  +  $($p.Dest)" Green
    }
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force (Split-Path $p.Dest) | Out-Null
        Copy-Item $p.Src $p.Dest -Force
        if ((Get-FileHash $p.Dest -Algorithm SHA256).Hash -ne $srcHash) { throw "La copia de $($p.Dest) no coincide con el original." }
    }
    $entries[$p.Dest] = [pscustomobject]@{ dest = $p.Dest; sha256 = $srcHash; backup = $backup; kind = $p.Kind }
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Force $StateDir | Out-Null
    $doc = [pscustomobject]@{ pack = 'Resolve Pro Pack'; installed = $Stamp; files = @($entries.Values) }
    $doc | ConvertTo-Json -Depth 4 | Set-Content $Manifest -Encoding UTF8
}

Say ''
Say "Nuevos: $nNew   Actualizados: $nUpd   Sin cambios: $nSame   Backups: $nBak" Cyan
if ($nBak -gt 0 -and -not $DryRun) { Say "Backups en: $BackupDir" Yellow }
if ($DryRun) { Say 'Simulacion terminada. Ejecuta sin -DryRun para instalar.' Cyan }
else { Say 'Listo. Reinicia DaVinci Resolve. Busca "PRO_" en la Effects Library.' Cyan }
