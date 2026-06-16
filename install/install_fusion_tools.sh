#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/install/INSTALL_LOG.md"

log() {
  printf -- '- [%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$LOG"
}

run_step() {
  log "COMMAND: $*"
  "$@" 2>&1 | tee -a "$LOG"
  status=${PIPESTATUS[0]}
  log "EXIT_STATUS: $status"
  return 0
}

log "Fusion tool install attempts started. Commands are based on official docs checked 2026-06-15."
log "PROCESS docs: https://ukaea.github.io/PROCESS/installation/installation/"
log "FUSE docs: https://fuse.help/dev/install.html"
log "FreeGS README: https://github.com/freegs-plasma/freegs"
log "TORAX docs: https://torax.readthedocs.io/en/v1.4.0/installation.html"
log "OpenFUSIONToolkit README: https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit"
log "OpenMC docs: https://docs.openmc.org/en/stable/quickinstall.html"
log "Paramak docs: https://fusion-energy.github.io/paramak/stable/install.html"

if command -v mamba >/dev/null 2>&1; then
  run_step mamba install -y -c conda-forge cadquery openmc paramak openmdao optuna
else
  log "mamba not found; skipping conda-forge CAD/OpenMC/Paramak install."
fi

if command -v python >/dev/null 2>&1; then
  run_step python -m pip install freegs
  run_step python -m pip install torax
  run_step python -m pip install openfusiontoolkit
else
  log "python not found; skipping pip fusion installs."
fi

if command -v git >/dev/null 2>&1 && command -v python >/dev/null 2>&1; then
  log "PROCESS official docs recommend WSL/Linux. Cloning/installing only on Linux-like environment."
  if [ "$(uname -s)" = "Linux" ]; then
    mkdir -p "$HOME/src"
    if [ ! -d "$HOME/src/PROCESS" ]; then
      run_step git clone https://github.com/ukaea/PROCESS "$HOME/src/PROCESS"
    fi
    if [ -d "$HOME/src/PROCESS" ]; then
      (cd "$HOME/src/PROCESS" && run_step python -m pip install .)
    fi
  fi
fi

if command -v julia >/dev/null 2>&1; then
  run_step julia "$REPO_ROOT/install/install_julia_fuse.jl"
else
  log "julia not found; skipping FUSE.jl install."
fi

python "$REPO_ROOT/install/verify_stack.py" 2>&1 | tee -a "$LOG"

