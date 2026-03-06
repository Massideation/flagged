# Flagged Installer for Windows
# Usage: irm https://raw.githubusercontent.com/MSanchezWorld/flagged/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Write-Ok($msg)   { Write-Host "  " -NoNewline; Write-Host "✓" -ForegroundColor Green -NoNewline; Write-Host " $msg" }
function Write-Warn($msg) { Write-Host "  " -NoNewline; Write-Host "!" -ForegroundColor Yellow -NoNewline; Write-Host " $msg" }
function Write-Fail($msg) { Write-Host "  " -NoNewline; Write-Host "✗" -ForegroundColor Red -NoNewline; Write-Host " $msg"; exit 1 }
function Write-Info($msg) { Write-Host "  · $msg" -ForegroundColor DarkGray }
function Write-Step($msg) { Write-Host "`n── $msg ────────────────────────────────────────" -ForegroundColor Cyan; Write-Host "" }

# Banner
Write-Host ""
Write-Host "  FLAGGED — Local AI Email Monitor" -ForegroundColor Yellow
Write-Host "  github.com/MSanchezWorld/flagged" -ForegroundColor DarkGray
Write-Host ""

# Check Python
Write-Step "System Check"
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
            Write-Fail "Python 3.9+ required. You have $pyVersion"
        }
        Write-Ok "$pyVersion"
    }
} catch {
    Write-Fail "Python not found. Install from https://python.org"
}

# Check Git
try {
    git --version | Out-Null
    Write-Ok "git available"
} catch {
    Write-Fail "Git not found. Install from https://git-scm.com"
}

# Install location
Write-Step "Installation Location"
$defaultDir = "$HOME\flagged"
$installDir = Read-Host "  Install Flagged to [$defaultDir]"
if (-not $installDir) { $installDir = $defaultDir }

if (Test-Path "$installDir\.git") {
    Write-Warn "Flagged already installed at $installDir"
    $update = Read-Host "  Update existing installation? [Y/n]"
    if (-not $update -or $update -match "^[Yy]") {
        Set-Location $installDir
        git pull origin main --quiet
        Write-Ok "Updated to latest version"
    }
} else {
    Write-Info "Cloning Flagged into $installDir..."
    git clone https://github.com/MSanchezWorld/flagged $installDir --quiet
    Write-Ok "Flagged cloned"
}

Set-Location $installDir

# Install dependencies
Write-Step "Installing Dependencies"
python -m pip install -r requirements.txt -q
Write-Ok "Python packages installed"

# Launch wizard
Write-Step "Configuration Wizard"
Write-Host ""
Write-Info "The setup wizard will walk you through connecting Telegram,"
Write-Info "setting up Gmail API access, and configuring your accounts."
Write-Host ""
$startWizard = Read-Host "  Start the wizard now? [Y/n]"
if (-not $startWizard -or $startWizard -match "^[Yy]") {
    python "$installDir\setup_wizard.py"
} else {
    Write-Ok "Run the wizard later: python setup_wizard.py"
}

Write-Host ""
Write-Ok "Flagged installed at: $installDir" 
Write-Host "  Docs: github.com/MSanchezWorld/flagged" -ForegroundColor DarkGray
Write-Host ""
