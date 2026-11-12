# Installs the Kiro GB Workflow kit into $env:USERPROFILE\.kiro (Windows / PowerShell).
# Usage: .\install.ps1 [-DryRun] [-Force]
# If scripts are blocked: powershell -ExecutionPolicy Bypass -File .\install.ps1
param([switch]$DryRun, [switch]$Force)
$ErrorActionPreference = 'Stop'

$Src = $PSScriptRoot
$Kiro = if ($env:KIRO_HOME) { $env:KIRO_HOME } else { Join-Path $env:USERPROFILE '.kiro' }
$Backup = Join-Path $Kiro (".gb-backup-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$script:Copied = 0
$script:Skipped = 0

# Copies a file or directory honoring -DryRun / -Force.
function Copy-Item-Safe([string]$From, [string]$To) {
    if ((Test-Path $To) -and -not $Force) {
        Write-Host "skip (exists): $To"; $script:Skipped++; return
    }
    if ($DryRun) { Write-Host "would copy: $To"; $script:Copied++; return }
    if (Test-Path $To) {
        $rel = $To.Substring($Kiro.Length).TrimStart('\', '/')
        $dest = Join-Path $Backup $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        Copy-Item -Recurse -Force $To $dest
        Remove-Item -Recurse -Force $To
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $To) | Out-Null
    Copy-Item -Recurse -Force $From $To
    $script:Copied++
}

foreach ($dir in Get-ChildItem -Directory (Join-Path $Src 'agents')) {
    if ($dir.Name -eq 'judgment-day') {
        foreach ($f in Get-ChildItem -File (Join-Path $dir.FullName '*.md')) {
            Copy-Item-Safe $f.FullName (Join-Path $Kiro "agents\$($f.Name)")
        }
        continue
    }
    Copy-Item-Safe (Join-Path $dir.FullName 'agent.json') (Join-Path $Kiro "agents\$($dir.Name).json")
    Copy-Item-Safe (Join-Path $dir.FullName 'prompt.md') (Join-Path $Kiro "crew\agents\$($dir.Name)\prompt.md")
}

$collab = @('chained-pr', 'cognitive-doc-design', 'comment-writer', 'judgment-day', 'rdd-defect-workflow',
            'skill-creator', 'skill-improver', 'systemic-issue-triage', 'work-unit-commits')
foreach ($dir in Get-ChildItem -Directory (Join-Path $Src 'skills')) {
    if ($dir.Name -eq 'learnings') {
        foreach ($l in Get-ChildItem -Directory $dir.FullName) {
            Copy-Item-Safe $l.FullName (Join-Path $Kiro "crew\skills\auto\$($l.Name)")
        }
    } elseif ($collab -contains $dir.Name) {
        Copy-Item-Safe $dir.FullName (Join-Path $Kiro "skills\$($dir.Name)")
    } else {
        Copy-Item-Safe $dir.FullName (Join-Path $Kiro "crew\skills\$($dir.Name)")
    }
}

Copy-Item-Safe (Join-Path $Src 'steering\dev-flows') (Join-Path $Kiro 'steering\dev-flows')
Copy-Item-Safe (Join-Path $Src 'steering\dev-flow-router.md') (Join-Path $Kiro 'steering\dev-flow-router.md')
foreach ($part in 'scripts', 'templates', 'workflows') {
    Copy-Item-Safe (Join-Path $Src "dev-flows\$part") (Join-Path $Kiro "crew\dev-flows\$part")
}

Write-Host "Done. copied=$script:Copied skipped=$script:Skipped dry_run=$DryRun"
if ($script:Skipped -gt 0) { Write-Host "Use -Force to overwrite (backup goes to $Backup)." }
Write-Host "Next: configure your local secrets, see docs\06-windows.md"
