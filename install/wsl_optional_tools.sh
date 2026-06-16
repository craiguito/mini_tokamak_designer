#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/install/INSTALL_LOG.md"

log() {
  printf -- '- [%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$LOG"
}

run_step() {
  log "COMMAND: $*"
  "$@" >>"$LOG" 2>&1
  status=$?
  log "EXIT_STATUS: $status"
  return 0
}

module_ok() {
  python - "$1" <<'PY' >/dev/null 2>&1
import importlib.util
import sys
raise SystemExit(0 if importlib.util.find_spec(sys.argv[1]) else 1)
PY
}

if [ -f "$HOME/miniforge/etc/profile.d/conda.sh" ]; then
  # shellcheck disable=SC1091
  source "$HOME/miniforge/etc/profile.d/conda.sh"
  conda activate mini-tokamak
fi

log "Starting WSL optional tool install helper."

for pkg in torch "jax[cpu]" freegs torax mlflow botorch; do
  module="${pkg%%[*}"
  if [ "$pkg" = "jax[cpu]" ]; then module="jax"; fi
  if module_ok "$module"; then
    log "SKIP: Python module $module already importable."
  elif [ "$pkg" = "torch" ]; then
    run_step python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
  else
    run_step python -m pip install "$pkg"
  fi
done

for pkg in cadquery openmc paramak; do
  if module_ok "$pkg"; then
    log "SKIP: Python module $pkg already importable."
  else
    run_step mamba install -y -c conda-forge "$pkg"
  fi
done

if command -v julia >/dev/null 2>&1; then
  log "SKIP: julia already on PATH."
elif [ -x "$HOME/.juliaup/bin/julia" ]; then
  export PATH="$HOME/.juliaup/bin:$PATH"
  log "SKIP: julia found through juliaup."
else
  run_step bash -lc 'curl -fsSL https://install.julialang.org | sh -s -- -y'
  export PATH="$HOME/.juliaup/bin:$PATH"
fi

if [ -x "$HOME/.juliaup/bin/julia" ]; then
  export PATH="$HOME/.juliaup/bin:$PATH"
fi

if command -v julia >/dev/null 2>&1; then
  run_step julia --version
  if julia -e 'using FUSE; using JSON' >/dev/null 2>&1; then
    log "SKIP: FUSE.jl and JSON already importable."
  else
    run_step env JULIA_PKG_USE_CLI_GIT=true \
      GIT_CONFIG_COUNT=1 \
      GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf \
      GIT_CONFIG_VALUE_0=git@github.com: \
      julia "$REPO_ROOT/install/install_julia_fuse.jl"
  fi
else
  log "SKIP: Julia unavailable, cannot attempt FUSE.jl."
fi

if command -v process >/dev/null 2>&1 || module_ok process; then
  log "SKIP: PROCESS appears available."
else
  mkdir -p "$HOME/src"
  if [ ! -d "$HOME/src/PROCESS/.git" ]; then
    run_step git clone --depth 1 https://github.com/ukaea/PROCESS "$HOME/src/PROCESS"
  fi
  if [ -d "$HOME/src/PROCESS" ]; then
    (cd "$HOME/src/PROCESS" && run_step python -m pip install .)
  fi
fi

if module_ok openfusiontoolkit || module_ok OpenFUSIONToolkit || module_ok oftpy; then
  log "SKIP: OpenFUSIONToolkit/TokaMaker appears importable."
else
  run_step python -m pip install openfusiontoolkit
fi

python "$REPO_ROOT/install/verify_stack.py" >>"$LOG" 2>&1
log "Completed WSL optional tool install helper."
