# push-to-github.ps1
# One-shot: initialize git in this folder and push to the
# avorial/MG-traveller-character-generator repo on GitHub.
#
# Run from this folder:
#   cd C:\Users\patricthomas\Documents\ND_Files\traveller-creator
#   .\push-to-github.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Traveller creator -> GitHub ===" -ForegroundColor Cyan
Write-Host ""

# 1. Clean up any broken .git folder from a previous attempt
if (Test-Path .git) {
    Write-Host "[1/5] Removing existing .git folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .git
} else {
    Write-Host "[1/5] No existing .git folder - skipping cleanup." -ForegroundColor DarkGray
}

# 2. Initialize a fresh repo on main
Write-Host "[2/5] Initializing new repo on branch 'main'..." -ForegroundColor Yellow
git init -b main | Out-Null
git config user.email "patricthomas@gmail.com"
git config user.name  "avorial"

# 3. Stage and show what's about to be committed
Write-Host "[3/5] Staging files..." -ForegroundColor Yellow
git add .
Write-Host ""
Write-Host "Files staged for first commit:" -ForegroundColor DarkGray
git status --short
Write-Host ""

# 4. Commit
Write-Host "[4/5] Creating initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit: Traveller (MgT 2e) character generation terminal" | Out-Null

# 5. Add remote and push
Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
git remote add origin https://github.com/avorial/MG-traveller-character-generator.git
git push -u origin main

Write-Host ""
Write-Host "Done. Repo is live at:" -ForegroundColor Green
Write-Host "  https://github.com/avorial/MG-traveller-character-generator" -ForegroundColor Green
Write-Host ""
