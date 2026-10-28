<#
Install cd-skills on Windows (links via junctions by default so `git pull` updates every install; use -Copy to copy).

  .\install.ps1 -Target claude                              # $HOME\.claude\skills
  .\install.ps1 -Target claude-project -Path C:\code\app    # <project>\.claude\skills
  .\install.ps1 -Target antigravity -Path C:\code\app       # <project>\.agents\skills
  .\install.ps1 -Target antigravity-global                  # $HOME\.gemini\antigravity\skills
  .\install.ps1 -Dest D:\any\skills\folder                  # any other skills folder
  .\install.ps1 -Target claude -Only cd-web-a11y-audit      # just some skills (comma-separated)
  .\install.ps1 -Target claude -Copy                        # copy files instead of linking via junction
#>
param(
  [ValidateSet('claude', 'claude-project', 'antigravity', 'antigravity-global')][string]$Target,
  [string]$Path,
  [string]$Dest,
  [string]$Only,
  [switch]$Copy
)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot

if (-not $Dest) {
  switch ($Target) {
    'claude'             { $Dest = Join-Path $HOME '.claude\skills' }
    'claude-project'     { if (-not $Path) { throw 'Use -Path <project folder>' }; $Dest = Join-Path $Path '.claude\skills' }
    'antigravity'        { if (-not $Path) { throw 'Use -Path <project folder>' }; $Dest = Join-Path $Path '.agents\skills' }
    'antigravity-global' { $Dest = Join-Path $HOME '.gemini\antigravity\skills' }
    default              { throw 'Use -Target claude|claude-project|antigravity|antigravity-global, or -Dest <folder>' }
  }
}

$wanted = if ($Only) { $Only.Split(',') | ForEach-Object { $_.Trim() } } else { $null }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$count = 0
Get-ChildItem -Directory (Join-Path $Repo 'skills') | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
  if ($wanted -and ($wanted -notcontains $_.Name)) { return }
  $t = Join-Path $Dest $_.Name
  if (Test-Path $t) {
    $item = Get-Item $t -Force
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
      cmd /c rmdir "$t"
    } else {
      Remove-Item -Recurse -Force $t
    }
  }

  if ($Copy) {
    Copy-Item -Recurse $_.FullName $t
    Write-Host "Installed $($_.Name) -> $t (copy)"
  } else {
    try {
      New-Item -ItemType Junction -Path $t -Target $_.FullName | Out-Null
      Write-Host "Installed $($_.Name) -> $t (junction)"
    } catch {
      Copy-Item -Recurse $_.FullName $t
      Write-Host "Installed $($_.Name) -> $t (copy, junction failed)"
    }
  }
  $count++
}
if ($count -eq 0) { throw 'No skills matched.' }
Write-Host "Done ($count skill(s)). Start a new agent session so they're picked up."
