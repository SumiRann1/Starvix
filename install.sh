#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[38;5;51m'
PURPLE='\033[38;5;141m'
GREEN='\033[38;5;84m'
YELLOW='\033[38;5;221m'
RED='\033[38;5;203m'
RESET='\033[0m'

info()    { echo -e "${CYAN}❯${RESET} $1"; }
success() { echo -e "${GREEN}✔${RESET} $1"; }
warn()    { echo -e "${YELLOW}▲${RESET} $1"; }
error()   { echo -e "${RED}✖${RESET} $1" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
VENV_DIR="${STARVIX_VENV_DIR:-$HOME/.local/share/starvix/venv}"
VENV_PYTHON="$VENV_DIR/bin/python"

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
    info "Setting up Virtual Environment at $VENV_DIR..."
    if ! command -v uv &> /dev/null; then
        info "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | bash
        success "uv installed."
    else
        info "uv is already installed."
    fi

    mkdir -p "$(dirname "$VENV_DIR")"

    if [ ! -d "$VENV_DIR" ]; then
        uv venv --python "$PYTHON" "$VENV_DIR"
        success "Virtual environment created at $VENV_DIR."
    else
        info "Virtual environment $VENV_DIR already exists."
    fi

    VIR_ENV="$VENV_DIR/bin/activate"
    source "$VIR_ENV"
    success "Activated virtual environment."

    # Maintain a symlink in the project directory for IDE discovery
    if [ -d ".venv" ] && [ ! -L ".venv" ]; then
        rm -rf .venv
    fi
    ln -sfn "$VENV_DIR" .venv
    info "Linked .venv -> $VENV_DIR for IDE discovery."
}

install_requirements() {
    info "Installing dependencies..."
    if command -v uv &>/dev/null; then
        uv pip install --python "$VENV_PYTHON" -e ".[dev,providers]"
    else
        "$VENV_PYTHON" -m pip install -e ".[dev,providers]"
    fi
    success "Dependencies installed."
}

setup_dotenv() {
    info "Checking configuration (.env)..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            success "Created .env from .env.example"
            warn "Please edit .env to insert your API keys (GROQ_API_KEY, GOOGLE_API_KEY, etc.)"
        fi
    else
        success ".env file already exists."
    fi
}

setup_launcher() {
    info "Setting up global 'starvix' launcher..."
    LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"

    cat << EOF > "$LOCAL_BIN/starvix"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/starvix" "\$@"
EOF

    chmod +x "$LOCAL_BIN/starvix"
    success "Global launcher created at $LOCAL_BIN/starvix"
}

print_banner
check_python
setup_virenv
install_requirements
setup_dotenv
setup_launcher

echo -e "\n${GREEN}${BOLD}🎉 Installation Complete!${RESET}"
echo -e "${DIM}----------------------------------------------------${RESET}"
echo -e "Virtual environment location:"
echo -e "  ${CYAN}$VENV_DIR${RESET}"
echo -e "\nTo activate your virtual environment:"
echo -e "  Linux / macOS   : ${CYAN}source $VENV_DIR/bin/activate${RESET}"
echo -e "  (or locally)    : ${CYAN}source .venv/bin/activate${RESET}"
echo -e "\nTo launch the Starvix chat:"
echo -e "  ${CYAN}${BOLD}starvix chat${RESET}\n"