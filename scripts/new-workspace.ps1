# Creates (or completes) a Kiro Crew workspace folder for the project repositories (Windows / PowerShell).
# Usage: .\scripts\new-workspace.ps1 -Path <workspace-path> [-Clone] [-DryRun] [-Force]
#   -Clone   git clone every repository listed in <workspace>\repos.txt that is not there yet
#   -DryRun  print what would be done
#   -Force   regenerate the steering and .code-workspace files (repos.txt is never overwritten)
# If scripts are blocked: powershell -ExecutionPolicy Bypass -File .\scripts\new-workspace.ps1 -Path <path>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [switch]$Clone, [switch]$DryRun, [switch]$Force
)
$ErrorActionPreference = 'Stop'

$Src = Split-Path -Parent $PSScriptRoot
$Template = Join-Path $Src 'workspace-template'
$Target = [Environment]::ExpandEnvironmentVariables($Path)
if ($Target.StartsWith('~')) { $Target = Join-Path $HOME $Target.Substring(1).TrimStart('\', '/') }
$Name = Split-Path -Leaf $Target
$Utf8 = New-Object System.Text.UTF8Encoding($false)

# Writes a UTF-8 file (no BOM) when it is missing or -Force is set.
function Write-IfAbsent([string]$FilePath, [string]$Content) {
    if ((Test-Path $FilePath) -and -not $Force) { Write-Host "skip (exists): $FilePath"; return }
    if ($DryRun) { Write-Host "would write: $FilePath"; return }
    [IO.File]::WriteAllText($FilePath, $Content + "`n", $Utf8)
    Write-Host "wrote: $FilePath"
}

# Returns the repository entries of a repos file as objects with Url and Folder.
function Get-Repos([string]$ReposFile) {
    foreach ($line in Get-Content $ReposFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $trimmed -split '\s+'
        $folder = if ($parts.Count -gt 1) { $parts[1] } else { [IO.Path]::GetFileNameWithoutExtension($parts[0].TrimEnd('/')) }
        [pscustomobject]@{ Url = $parts[0]; Folder = $folder }
    }
}

if ($DryRun) { Write-Host "would: create $Target\.kiro\steering" }
else { New-Item -ItemType Directory -Force -Path (Join-Path $Target '.kiro\steering') | Out-Null }

# repos.txt is user data: never overwritten, not even with -Force.
$ReposPath = Join-Path $Target 'repos.txt'
if (Test-Path $ReposPath) { Write-Host "keep: $ReposPath" }
else { Write-IfAbsent $ReposPath ((Get-Content -Raw (Join-Path $Template 'repos.txt')).TrimEnd()) }

$steering = (Get-Content -Raw (Join-Path $Template '.kiro\steering\gb-workspace.md')).Replace('__WORKSPACE_NAME__', $Name).TrimEnd()
Write-IfAbsent (Join-Path $Target '.kiro\steering\gb-workspace.md') $steering

$reposSource = if (Test-Path $ReposPath) { $ReposPath } else { Join-Path $Template 'repos.txt' }
$folders = @([ordered]@{ path = '.'; name = "$Name (root)" })
foreach ($repo in Get-Repos $reposSource) { $folders += [ordered]@{ path = $repo.Folder } }
$codeWorkspace = ([ordered]@{ folders = $folders } | ConvertTo-Json -Depth 4)
Write-IfAbsent (Join-Path $Target "$Name.code-workspace") $codeWorkspace

if ($Clone) {
    foreach ($repo in Get-Repos $reposSource) {
        $dest = Join-Path $Target $repo.Folder
        if (Test-Path $dest) { Write-Host "skip (exists): $($repo.Folder)"; continue }
        if ($DryRun) { Write-Host "would: git clone $($repo.Url) $dest"; continue }
        git clone $repo.Url $dest
        if ($LASTEXITCODE -ne 0) { throw "git clone failed for $($repo.Url)" }
    }
}

Write-Host "Workspace ready: $Target"
Write-Host 'Next: open a Kiro Crew chat with this folder as its project directory (see docs\07-workspace.md).'
