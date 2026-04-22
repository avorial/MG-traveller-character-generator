# push-to-github.ps1
# Stage, commit, tag, and push to the
# avorial/MG-traveller-character-generator repo on GitHub.
#
# Version policy: every push bumps the minor digit and creates an
# annotated git tag (v1.0 -> v1.1 -> v1.2 -> ...). Major bumps are
# explicit. The current version lives in the VERSION file.
#
# Usage:
#   .\push-to-github.ps1
#       -> bump minor (default), commit, tag, push
#
#   .\push-to-github.ps1 -Message "Added Zhodani species"
#       -> same, but sets the commit message
#
#   .\push-to-github.ps1 -Major
#       -> bump major, reset minor to 0 (v1.7 -> v2.0)
#
#   .\push-to-github.ps1 -NoBump
#       -> commit + push without creating a new version/tag
#          (for README tweaks, typo fixes, etc.)
#
#   .\push-to-github.ps1 -Reinit
#       -> blow away .git and re-initialize. Only use if the repo
#          is in a broken state. Will re-push as v1.0 unless you
#          also change the VERSION file.

param(
    [string]$Message = "",
    [switch]$Major,
    [switch]$NoBump,
    [switch]$Reinit
)

$ErrorActionPreference = "Stop"

$RepoUrl   = "https://github.com/avorial/MG-traveller-character-generator.git"
$UserEmail = "patricthomas@gmail.com"
$UserName  = "avorial"
$VersionFile = "VERSION"

Write-Host ""
Write-Host "=== Traveller creator -> GitHub ===" -ForegroundColor Cyan
Write-Host ""

# ----- Version bookkeeping -------------------------------------------------

if (-not (Test-Path $VersionFile)) {
    "1.0" | Set-Content -Path $VersionFile -NoNewline
    Write-Host "VERSION file created at v1.0" -ForegroundColor DarkGray
}

$currentRaw = (Get-Content $VersionFile -Raw).Trim()
if ($currentRaw -notmatch '^\s*v?(\d+)\.(\d+)\s*$') {
    throw "VERSION file is malformed: '$currentRaw'. Expected something like '1.3'."
}
$curMajor = [int]$matches[1]
$curMinor = [int]$matches[2]
$current  = "v$curMajor.$curMinor"

if ($NoBump) {
    $next = $current
    $bumpNote = "no version bump"
} elseif ($Major) {
    $next = "v$($curMajor + 1).0"
    $bumpNote = "major bump"
} else {
    $next = "v$curMajor.$($curMinor + 1)"
    $bumpNote = "minor bump"
}

Write-Host "Current version: $current" -ForegroundColor DarkGray
Write-Host "Next version:    $next   ($bumpNote)" -ForegroundColor Cyan
Write-Host ""

# ----- Reinit path (rare) --------------------------------------------------

if ($Reinit) {
    if (Test-Path .git) {
        Write-Host "[reinit] Removing existing .git folder..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .git
    }
    git init -b main | Out-Null
    git config user.email $UserEmail
    git config user.name  $UserName
    git remote add origin $RepoUrl 2>$null | Out-Null
    Write-Host "[reinit] Fresh repo initialized." -ForegroundColor Yellow
}

# ----- First-time init -----------------------------------------------------

if (-not (Test-Path .git)) {
    Write-Host "[init] No .git folder found - initializing..." -ForegroundColor Yellow
    git init -b main | Out-Null
    git config user.email $UserEmail
    git config user.name  $UserName
    git remote add origin $RepoUrl 2>$null | Out-Null
}

# Make sure identity is set (idempotent)
git config user.email $UserEmail | Out-Null
git config user.name  $UserName  | Out-Null

# Make sure the remote exists and points where we want
$existingRemote = git remote get-url origin 2>$null
if (-not $existingRemote) {
    git remote add origin $RepoUrl | Out-Null
} elseif ($existingRemote -ne $RepoUrl) {
    Write-Host "[remote] Updating origin -> $RepoUrl" -ForegroundColor Yellow
    git remote set-url origin $RepoUrl
}

# ----- Write the bumped version, stage, commit -----------------------------

if (-not $NoBump) {
    $versionWithoutV = $next.Substring(1)  # "v1.2" -> "1.2"
    $versionWithoutV | Set-Content -Path $VersionFile -NoNewline
}

Write-Host "[stage] Staging all changes..." -ForegroundColor Yellow
git add .

# Show what's about to go out
Write-Host ""
Write-Host "Files staged:" -ForegroundColor DarkGray
git status --short
Write-Host ""

# If nothing to commit AND we're not bumping, bail gracefully
$pending = git status --porcelain
if (-not $pending) {
    if ($NoBump) {
        Write-Host "Nothing to commit and -NoBump set. Exiting." -ForegroundColor Yellow
        exit 0
    } else {
        # We bumped the VERSION file — that should itself be a change. If it's
        # not (e.g. VERSION was already at $next somehow), allow empty commit
        # so the tag still lands.
        Write-Host "No file changes detected; creating empty version commit." -ForegroundColor DarkGray
    }
}

# Build the commit message
if (-not $Message) {
    if ($NoBump) {
        $Message = "Misc updates"
    } else {
        $Message = "Release $next"
    }
}
$commitSubject = if ($NoBump) { $Message } else { "${next}: $Message" }

Write-Host "[commit] $commitSubject" -ForegroundColor Yellow
git commit --allow-empty -m "$commitSubject" | Out-Null

# Tag only when bumping
if (-not $NoBump) {
    # If the tag already exists locally (e.g. re-running after a push that
    # died mid-way), delete it first so we can retag cleanly.
    $existingTag = git tag -l $next
    if ($existingTag) {
        Write-Host "[tag] Removing existing local tag $next to recreate..." -ForegroundColor DarkGray
        git tag -d $next | Out-Null
    }
    Write-Host "[tag] Creating annotated tag $next" -ForegroundColor Yellow
    git tag -a $next -m "$commitSubject"
}

# ----- Push ----------------------------------------------------------------

Write-Host "[push] Pushing main..." -ForegroundColor Yellow
git push -u origin main

if (-not $NoBump) {
    Write-Host "[push] Pushing tag $next..." -ForegroundColor Yellow
    git push origin $next
}

Write-Host ""
Write-Host "Done. Released as $next" -ForegroundColor Green
Write-Host "  Repo:     https://github.com/avorial/MG-traveller-character-generator" -ForegroundColor Green
if (-not $NoBump) {
    Write-Host "  Release:  https://github.com/avorial/MG-traveller-character-generator/releases/tag/$next" -ForegroundColor Green
}
Write-Host ""
