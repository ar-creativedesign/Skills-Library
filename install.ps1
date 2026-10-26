<#
Install cd-skills on Windows (copies the folders; re-run after `git pull` to update).

  .\install.ps1 -Target claude                              # $HOME\.claude\skills
  .\install.ps1 -Target claude-project -Path C:\code\app    # <project>\.claude\skills
  .\install.ps1 -Target antigravity -Path C:\code\app       # <project>\.agents\skills
  .\install.ps1 -Dest D:\any\skills\folder                  # any other skills folder (e.g. Antigravity global)
  .\install.ps1 -Target claude -Only cd-web-a11y-audit      # just some skills (comma-separated)
#>
param(
  [ValidateSet('claude', 'claude-project', 'antigravity')][string]$Target,
  [string]$Path,
  [string]$Dest,
  [string]$Only
)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot

if (-not $Dest) {
  switch ($Target) {
    'claude'         { $Dest = Join-Path $HOME '.claude\skills' }
    'claude-project' { if (-not $Path) { throw 'Use -Path <project folder>' }; $Dest = Join-Path $Path '.claude\skills' }
    'antigravity'    { if (-not $Path) { throw 'Use -Path <project folder>' }; $Dest = Join-Path $Path '.agents\skills' }
    default          { throw 'Use -Target claude|claude-project|antigravity, or -Dest <folder>' }
  }
}

$wanted = if ($Only) { $Only.Split(',') | ForEach-Object { $_.Trim() } } else { $null }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$count = 0
Get-ChildItem -Directory (Join-Path $Repo 'skills') | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
  if ($wanted -and ($wanted -notcontains $_.Name)) { return }
  $t = Join-Path $Dest $_.Name
  if (Test-Path $t) { Remove-Item -Recurse -Force $t }
  Copy-Item -Recurse $_.FullName $t
  Write-Host "Installed $($_.Name) -> $t"
  $count++
}
if ($count -eq 0) { throw 'No skills matched.' }
Write-Host "Done ($count skill(s)). Start a new agent session so they're picked up."
