#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/install/INSTALL_LOG.md"

log() {
  printf -- '- [%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$LOG"
}

log "wsl_bootstrap.sh started from $REPO_ROOT"
log "Updating Ubuntu packages and installing build tools."
sudo apt-get update
sudo apt-get install -y git curl wget ca-certificates build-essential gfortran cmake ninja-build pkg-config openmpi-bin libopenmpi-dev python3-tk

if ! command -v mamba >/dev/null 2>&1 && [ ! -x "$HOME/miniforge/bin/mamba" ]; then
  log "Installing Miniforge to $HOME/miniforge."
  curl -L -o /tmp/miniforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
  bash /tmp/miniforge.sh -b -p "$HOME/miniforge"
fi

export PATH="$HOME/miniforge/bin:$PATH"
ENV_FILE="$REPO_ROOT/environment-core.yml"
log "Creating/updating conda environment mini-tokamak from environment-core.yml."
mamba env update -n mini-tokamak -f "$ENV_FILE" || mamba env create -f "$ENV_FILE"

log "Installing project editable package in mini-tokamak."
source "$HOME/miniforge/etc/profile.d/conda.sh"
conda activate mini-tokamak
python -m pip install -e "$REPO_ROOT[dev]"
python "$REPO_ROOT/install/verify_stack.py"
