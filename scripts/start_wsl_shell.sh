#!/usr/bin/env bash

set +e

echo "MiniTokamak Designer WSL startup"
echo "--------------------------------"

PROJECT_DIR="$HOME/projects/mini_tokamak_designer"
CONDA_SH="$HOME/miniforge/etc/profile.d/conda.sh"

if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR" || true
else
    echo "Project directory not found: $PROJECT_DIR"
fi

if [ -f "$CONDA_SH" ]; then
    # shellcheck disable=SC1090
    source "$CONDA_SH"
    conda activate mini-tokamak
    if [ "$?" -ne 0 ]; then
        echo "Could not activate conda env: mini-tokamak"
    fi
else
    echo "Conda startup script not found: $CONDA_SH"
fi

echo
echo "Current directory: $(pwd)"
echo "Python: $(command -v python || echo not found)"
echo "mini-tokamak: $(command -v mini-tokamak || echo not found)"
echo
echo "Try: mini-tokamak verify"
echo

if [ "${1:-}" = "--check" ]; then
    exit 0
fi

exec bash -i
