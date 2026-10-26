#!/usr/bin/env bash
# ==============================================================================
# Starvix Installer Script
# Automated environment setup, dependency installation, and CLI configuration
# ==============================================================================

set -euo pipefail

# --- Color Palette (ANSI) ---
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[38;5;51m'
PURPLE='\033[38;5;141m'
GREEN='\033[38;5;84m'
YELLOW='\033[38;5;221m'
RED='\033[38;5;203m'
RESET='\033[0m'

# --- Output Helpers ---
info()    { echo -e "${CYAN}❯${RESET} $1"; }
success() { echo -e "${GREEN}✔${RESET} $1"; }
warn()    { echo -e "${YELLOW}▲${RESET} $1"; }
error()   { echo -e "${RED}✖${RESET} $1" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Starvix ASCII Banner ---
print_banner() {
    echo -e "${PURPLE}${BOLD}"
    cat << "EOF"
  ███████╗████████╗ █████╗ ██████╗ ██╗   ██╗██╗██╗  ██╗
  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║   ██║██║╚██╗██╔╝
  ███████╗   ██║   ███████║██████╔╝██║   ██║██║ ╚███╔╝ 
  ╚════██║   ██║   ██╔══██║██╔══██╗╚██╗ ██╔╝██║ ██╔██╗ 
  ███████║   ██║   ██║  ██║██║  ██║ ╚████╔╝ ██║██╔╝ ██╗
  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝
EOF
    echo -e "${CYAN}        Local-First LangGraph Agent Runtime${RESET}"
    echo -e "${DIM}====================================================${RESET}\n"
}

check_python() {
    info "Checking Python Version..."

    PYTHON=""
    if command -v python &> /dev/null; then
        PYTHON="python"
        info "Python found: $($PYTHON --version)"
    elif command -v python3 &> /dev/null; then
        PYTHON="python3"
        info "Python found: $($PYTHON --version)"
    else
        error "Python is not installed. Please install Python >= 3.11."
        exit 1
    fi
        
    MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
    MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")

    if [[ "$MAJOR" -lt 3 ]] || { [[ "$MAJOR" -eq 3 ]] && [[ "$MINOR" -lt 11 ]]; }; then
        error "Python >= 3.11 is required. Found: Python ${MAJOR}.${MINOR}"
    fi
    success "Python version is valid (${MAJOR}.${MINOR})."
}

setup_virenv(){
    info "Setting up Virtual Environment..."
    if [ ! -d ".venv" ]; then
        $PYTHON -m venv .venv
        success "Virtual environment created."
    else
        warn "Virtual environment already exists."
    fi

    source .venv/bin/activate
    success "Activated virtual environment."
}

install_requirements(){
    info "Installing dependencies..."
    $PYTHON -m pip install -e .[dev][providers]
    success "Dependencies installed."
}



print_banner
check_python
setup_virenv