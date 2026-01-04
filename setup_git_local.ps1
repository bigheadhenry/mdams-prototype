# Check if Git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Git for Windows first: https://git-scm.com/download/win"
    exit
}

Write-Host "Initializing Local Git Repository..."
git init

Write-Host "Adding files..."
git add .

Write-Host "Committing initial version..."
git commit -m "Initial commit: MEAM Prototype"

# Check if remote exists
$remoteExists = git remote | Select-String "production"
if (-not $remoteExists) {
    Write-Host "Adding remote 'production'..."
    git remote add production ssh://bigheadhenry@192.168.5.13/home/bigheadhenry/repos/meam.git
}

Write-Host "---------------------------------------------------"
Write-Host "Setup Complete!"
Write-Host "To deploy code, run:"
Write-Host "  git push production master"
Write-Host "---------------------------------------------------"
