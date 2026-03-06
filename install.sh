#!/bin/bash
# Flagged Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/MSanchezWorld/flagged/main/install.sh | bash

set -e

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD="\033[1m"
RESET="\033[0m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
CYAN="\033[96m"
GOLD="\033[33m"
DIM="\033[2m"

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}!${RESET} $1"; }
fail() { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
info() { echo -e "  ${DIM}·${RESET} $1"; }
step() { echo -e "\n${CYAN}── $1 ──────────────────────────────────────${RESET}\n"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GOLD}${BOLD}  ██╗  ██╗███████╗██████╗  █████╗ ██╗     ██████╗ ${RESET}"
echo -e "${GOLD}${BOLD}  ██║  ██║██╔════╝██╔══██╗██╔══██╗██║     ██╔══██╗${RESET}"
echo -e "${GOLD}${BOLD}  ███████║█████╗  ██████╔╝███████║██║     ██║  ██║${RESET}"
echo -e "${GOLD}${BOLD}  ██╔══██║██╔══╝  ██╔══██╗██╔══██║██║     ██║  ██║${RESET}"
echo -e "${GOLD}${BOLD}  ██║  ██║███████╗██║  ██║██║  ██║███████╗██████╔╝${RESET}"
echo -e "${GOLD}${BOLD}  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ${RESET}"
echo ""
echo -e "  ${BOLD}Local AI Email Monitor${RESET} — Installer"
echo -e "  ${DIM}github.com/MSanchezWorld/flagged${RESET}"
echo ""

# ── Check OS ──────────────────────────────────────────────────────────────────
step "System Check"

OS="$(uname -s)"
case "${OS}" in
  Darwin*)  PLATFORM="macOS" ;;
  Linux*)   PLATFORM="Linux" ;;
  *)        fail "Unsupported OS: ${OS}. Please install manually — see SETUP.md" ;;
esac
ok "Platform: ${PLATFORM}"

# ── Check Python ──────────────────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
  PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
  PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

  if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    fail "Python 3.9+ required. You have Python ${PYTHON_VERSION}."
  fi
  ok "Python ${PYTHON_VERSION}"
else
  fail "Python 3 not found. Install from https://python.org or: brew install python@3.11"
fi

# ── Check Git ─────────────────────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  if [ "$PLATFORM" = "macOS" ]; then
    warn "Git not found. Installing via Xcode Command Line Tools..."
    xcode-select --install 2>/dev/null || true
    fail "Please install git and re-run this script."
  else
    fail "Git not found. Install with: sudo apt install git"
  fi
fi
ok "git available"

# ── Install directory ─────────────────────────────────────────────────────────
step "Installation Location"

DEFAULT_DIR="$HOME/flagged"
read -p "  ${CYAN}?${RESET} Install Flagged to [$DEFAULT_DIR]: " INSTALL_DIR
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_DIR}"

if [ -d "$INSTALL_DIR/.git" ]; then
  warn "Flagged already installed at $INSTALL_DIR"
  echo ""
  read -p "  ${CYAN}?${RESET} Update existing installation? [Y/n]: " UPDATE
  UPDATE="${UPDATE:-Y}"
  if [[ "$UPDATE" =~ ^[Yy]$ ]]; then
    cd "$INSTALL_DIR"
    git pull origin main --quiet
    ok "Updated to latest version"
  fi
else
  # Clone the repo
  echo ""
  info "Cloning Flagged into $INSTALL_DIR..."
  git clone https://github.com/MSanchezWorld/flagged "$INSTALL_DIR" --quiet
  ok "Flagged cloned"
fi

cd "$INSTALL_DIR"

# ── Install Python dependencies ───────────────────────────────────────────────
step "Installing Dependencies"

python3 -m pip install -r requirements.txt -q
ok "Python packages installed"

# ── Run setup wizard ──────────────────────────────────────────────────────────
step "Configuration Wizard"

echo ""
echo -e "  The setup wizard will now walk you through:"
echo -e "  ${DIM}·${RESET} Connecting your Telegram bot"
echo -e "  ${DIM}·${RESET} Setting up Gmail API access"
echo -e "  ${DIM}·${RESET} Adding your email accounts"
echo -e "  ${DIM}·${RESET} Choosing your local AI model"
echo -e "  ${DIM}·${RESET} Installing the background service"
echo ""
read -p "  ${CYAN}?${RESET} Start the wizard now? [Y/n]: " START_WIZARD
START_WIZARD="${START_WIZARD:-Y}"

if [[ "$START_WIZARD" =~ ^[Yy]$ ]]; then
  python3 "$INSTALL_DIR/setup_wizard.py"
else
  echo ""
  ok "Installation complete. Run the wizard later:"
  info "  cd $INSTALL_DIR && python3 setup_wizard.py"
fi

echo ""
echo -e "  ${GREEN}${BOLD}Flagged installed at: $INSTALL_DIR${RESET}"
echo -e "  ${DIM}Docs: github.com/MSanchezWorld/flagged${RESET}"
echo ""
