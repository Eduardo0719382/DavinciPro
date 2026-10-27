<#
.SYNOPSIS
  Descarga la ultima version del Resolve Pro Pack desde GitHub e instala los cambios.

.DESCRIPTION
  1. git pull (trae los cambios del repositorio).
  2. Ejecuta install.ps1: copia solo lo nuevo o modificado, con backup de cualquier archivo ajeno.
  Si editaste archivos del paquete en esta carpeta, git pull se detiene y avisa en lugar de pisarlos.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\actualizar.ps1
#>
[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host '== Resolve Pro Pack: actualizacion ==' -ForegroundColor Cyan
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'No se encontro git. Instalalo desde https://git-scm.com/download/win y vuelve a ejecutar este script.'
}

$before = (git rev-parse HEAD).Trim()
git pull --ff-only
if ($LASTEXITCODE -ne 0) {
    throw 'git pull no pudo actualizar (quizas cambiaste archivos aqui). No se instalo nada.'
}
$after = (git rev-parse HEAD).Trim()

if ($before -eq $after) {
    Write-Host 'Ya tenias la ultima version. Verificando instalacion igualmente...' -ForegroundColor Gray
} else {
    Write-Host 'Cambios descargados:' -ForegroundColor Green
    git log --oneline "$before..$after"
}

& (Join-Path $PSScriptRoot 'install.ps1') -DryRun:$DryRun
