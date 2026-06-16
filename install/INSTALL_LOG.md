# MiniTokamak Designer Install Log

This log records install sources, commands, errors, and workarounds. It intentionally separates MVP Python verification from heavyweight fusion tools.

## Official docs checked on 2026-06-15

- PROCESS: https://ukaea.github.io/PROCESS/installation/installation/
  - Relevant command from docs: `wsl --install`
  - Relevant install path from docs: `git clone https://github.com/ukaea/PROCESS`, `python3 -m venv .venv`, `pip install .`
- FUSE.jl: https://fuse.help/dev/install.html
  - Relevant commands from docs: add `https://github.com/ProjectTorreyPines/FuseRegistry.jl.git`, `Pkg.add("FUSE")`, `using FUSE`
- FreeGS: https://github.com/freegs-plasma/freegs
  - Relevant command from README: `pip install --user freegs`
- TORAX: https://torax.readthedocs.io/en/v1.4.0/installation.html
  - Relevant command from docs: `pip install torax`
- OpenFUSIONToolkit/TokaMaker: https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit
  - Relevant command from README: `pip install openfusiontoolkit`
- OpenMC: https://docs.openmc.org/en/stable/quickinstall.html
  - Relevant conda commands from docs: `conda config --add channels conda-forge`, `conda create --name openmc-env openmc`
  - Relevant Docker command from docs: `docker run openmc/openmc:latest`
- CadQuery: https://cadquery.readthedocs.io/en/latest/installation.html
  - Relevant guidance: conda is the better tested installation method; pip is available.
- Paramak: https://fusion-energy.github.io/paramak/stable/install.html
  - Relevant commands from docs: `python -m pip install paramak`, `mamba install -c conda-forge paramak`

## Session attempts on 2026-06-15

- Checked `wsl.exe --status` and `wsl.exe --list --verbose`.
  - Result: WSL command exists, but Windows Subsystem for Linux is not installed.
- Checked Windows optional feature state with `Get-WindowsOptionalFeature -Online`.
  - Result: command requires elevation in this shell.
- Attempted Microsoft-supported WSL install commands:
  - `wsl.exe --install -d Ubuntu --no-launch`
  - `wsl.exe --install`
  - Result: both returned the same "Windows Subsystem for Linux is not installed" message and did not start installation from this context.
- Workaround: created a Windows Python 3.12 MVP environment path so the research framework can be verified without WSL. WSL/Ubuntu remains the preferred target for PROCESS/OpenMC/CadQuery/Paramak.

## Windows MVP environment completed on 2026-06-15

- Created environment:
  - `py -3.12 -m venv .venv`
  - `.venv\Scripts\python.exe -m pip install --upgrade pip`
  - `.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- Installed optional Python packages:
  - `.venv\Scripts\python.exe -m pip install optuna`
  - `.venv\Scripts\python.exe -m pip install openmdao`
  - `.venv\Scripts\python.exe -m pip install freegs`
  - `.venv\Scripts\python.exe -m pip install torax`
  - `.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu`
  - `.venv\Scripts\python.exe -m pip install botorch`
  - `.venv\Scripts\python.exe -m pip install mlflow`
- Attempted optional OpenFUSIONToolkit install:
  - `.venv\Scripts\python.exe -m pip install openfusiontoolkit`
  - Result: failed on Windows/Python 3.12 with `ERROR: Could not find a version that satisfies the requirement openfusiontoolkit`.
- Dependency note:
  - TORAX initially installed `h5py 3.14.0`, `jax 0.10.1`, `jaxlib 0.10.1`, and `protobuf 7.35.1`.
  - MLflow then downgraded `pandas` to `2.3.3` and `protobuf` to `6.33.6`. The MVP tests and CLI verification still pass.

## Verified versions after install

- `numpy==2.4.6`
- `scipy==1.17.1`
- `pandas==2.3.3`
- `xarray==2026.4.0`
- `pydantic==2.13.4`
- `matplotlib==3.11.0`
- `plotly==6.8.0`
- `rich==15.0.0`
- `typer==0.26.7`
- `duckdb==1.5.3`
- `h5py==3.14.0`
- `zarr==3.2.1`
- `pytest==9.1.0`
- `ruff==0.15.17`
- `black==26.5.1`
- `mypy==2.1.0`
- `optuna==4.9.0`
- `openmdao==3.44.0`
- `FreeGS==0.8.2`
- `torax==1.4.0`
- `jax==0.10.1`
- `jaxlib==0.10.1`
- `torch==2.12.0+cpu`
- `botorch==0.18.1`
- `mlflow==3.13.0`

## Verification commands completed

- `.venv\Scripts\mini-tokamak.exe verify`
  - Result: PASS for core Python stack, Optuna, PyTorch CPU, JAX CPU, OpenMDAO, MLflow, FreeGS, and TORAX.
  - Result: PROCESS, FUSE.jl, TokaMaker, OpenMC, CadQuery, and Paramak are missing/stubbed in the current Windows environment.
- `.venv\Scripts\python.exe -m pytest`
  - Result: `6 passed`.
- `.venv\Scripts\mini-tokamak.exe run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Result: run `20260615T211508Z-221e9c1e`, 100 candidate rows in DuckDB, Markdown/HTML reports, plots, CSV, and PNG/SVG CAD cross-section fallback.

## Elevated WSL setup attempt on 2026-06-15

- Confirmed elevated PowerShell:
  - `whoami /groups`
  - Result included `BUILTIN\Administrators` and `High Mandatory Level`.
- Checked WSL feature state:
  - `Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux`
  - `Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform`
  - Initial result: both disabled.
- Attempted official WSL command:
  - `wsl.exe --install -d Ubuntu --no-launch`
  - Result: returned the "Windows Subsystem for Linux is not installed" message before feature enablement.
- Enabled Windows features without reboot:
  - `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart`
  - `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`
  - Result: DISM text reported "The operation completed successfully" for both.
- Verified feature state after DISM:
  - `Microsoft-Windows-Subsystem-Linux`: `Enabled`
  - `VirtualMachinePlatform`: `Enabled`
- Installed WSL app package:
  - `winget install -e --id Microsoft.WSL --accept-source-agreements --accept-package-agreements --silent`
  - Result: installed `Microsoft.WSL` / `MicrosoftCorporationII.WindowsSubsystemForLinux` version `2.7.8`.
- Checked WSL status:
  - `wsl.exe --status`
  - Result: default version is 2, but WSL2 cannot start because virtualization/hypervisor is not active yet.
  - `Get-ComputerInfo -Property CsHypervisorPresent,HyperVisorPresent`
  - Result: both `False`.
- Attempted Ubuntu no-launch install:
- `wsl.exe --install Ubuntu --no-launch`
  - Result: Windows reported VirtualMachinePlatform changes will not be effective until the system is rebooted.
- Final state before reboot:
  - WSL features are enabled.
  - WSL app package 2.7.8 is installed.
  - No Linux distributions are installed yet.
  - Reboot is required before Ubuntu/WSL2 can be initialized.

## WSL bootstrap after reboot on 2026-06-15

- Confirmed elevated shell remained active.
- Confirmed `CsHypervisorPresent` and `HyperVisorPresent` were both `True`.
- Installed Ubuntu:
  - `wsl.exe --install Ubuntu --no-launch`
  - Result: distribution successfully installed.
- Initialized Ubuntu non-interactively as root:
  - `wsl.exe -d Ubuntu -u root -- bash -lc "id; uname -a; cat /etc/os-release | head -n 5"`
  - Result: Ubuntu WSL2 initialized successfully.
- Created WSL user:
  - `useradd -m -s /bin/bash craig`
  - `usermod -aG sudo craig`
  - `/etc/wsl.conf` set default user to `craig`.
- Mirrored repo into Linux home:
  - Source: `/mnt/c/Users/Craig/projects/mini_tokamak_designer/`
  - Target: `/home/craig/projects/mini_tokamak_designer/`
  - Excluded `.venv`, `.git`, and Python cache directories.
- Started original WSL bootstrap:
  - `bash install/wsl_bootstrap.sh`
  - Result: Miniforge installed successfully, but the all-in-one `mamba env create -f environment.yml` solve was still CPU-bound after about 18 minutes.
  - Workaround: stopped the solve and split environment files into `environment-core.yml` for reliable MVP bootstrap and `environment-full.yml` for heavy optional CAD/neutronics/fusion attempts.

## Final WSL verification on 2026-06-15

- WSL repo path: `/home/craig/projects/mini_tokamak_designer`
- Windows mirror path: `C:\Users\Craig\projects\mini_tokamak_designer`
- Ubuntu default user: `craig`
- Conda environment: `mini-tokamak`
- Final WSL commands completed:
  - `mini-tokamak verify`
  - `python -m pytest`
  - `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
- Latest WSL run:
  - Run ID: `20260615T233904Z-867f4ead`
  - Run directory: `/home/craig/projects/mini_tokamak_designer/data/runs/20260615T233904Z-867f4ead`
  - Report directory: `/home/craig/projects/mini_tokamak_designer/data/reports/20260615T233904Z-867f4ead`
  - CAD directory: `/home/craig/projects/mini_tokamak_designer/data/cad/20260615T233904Z-867f4ead`
  - CAD outputs: PNG, SVG, and STEP were generated.
- WSL tools verified as importable or available:
  - Core stack: NumPy, SciPy, pandas, xarray, pydantic, matplotlib, plotly, rich, Typer, DuckDB, h5py, zarr
  - Dev/test: pytest, ruff, black, mypy
  - Optimization/ML: Optuna, PyTorch CPU, JAX CPU, BoTorch, MLflow
  - Fusion/systems/CAD/neutronics: PROCESS, FreeGS, TORAX, CadQuery, OpenMC, Paramak, OpenFUSIONToolkit
  - Julia: `julia version 1.12.6`
- WSL stubbed/failing:
  - FUSE.jl: attempted via `julia install/install_julia_fuse.jl`; it installed many dependencies but failed because Julia attempted to clone `git@github.com:ProjectTorreyPines/ALPHA.jl.git` and requested SSH credentials.
  - Lowercase Python module name `openfusiontoolkit` is not importable, but installed package `OpenFUSIONToolkit==26.6` is importable and the TokaMaker adapter probe passes.
- [2026-06-15T19:08:37-04:00] Starting WSL optional Python package install attempts.
- [2026-06-15T19:08:37-04:00] COMMAND: python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
Looking in indexes: https://download.pytorch.org/whl/cpu
Collecting torch
  Downloading torch-2.12.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (31 kB)
Collecting filelock (from torch)
  Downloading filelock-3.29.0-py3-none-any.whl.metadata (2.0 kB)
Requirement already satisfied: typing-extensions>=4.10.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch) (4.15.0)
Collecting setuptools<82 (from torch)
  Downloading setuptools-70.2.0-py3-none-any.whl.metadata (5.8 kB)
Collecting sympy>=1.13.3 (from torch)
  Downloading sympy-1.14.0-py3-none-any.whl.metadata (12 kB)
Requirement already satisfied: networkx>=2.5.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch) (3.6.1)
Collecting jinja2 (from torch)
  Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting fsspec>=0.8.5 (from torch)
  Downloading fsspec-2026.4.0-py3-none-any.whl.metadata (10 kB)
Collecting mpmath<1.4,>=1.1.0 (from sympy>=1.13.3->torch)
  Downloading mpmath-1.3.0-py3-none-any.whl.metadata (8.6 kB)
Requirement already satisfied: MarkupSafe>=2.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jinja2->torch) (3.0.3)
Downloading torch-2.12.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl (192.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 192.3/192.3 MB 95.7 MB/s  0:00:02
Downloading setuptools-70.2.0-py3-none-any.whl (930 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 930.8/930.8 kB 23.5 MB/s  0:00:00
Downloading fsspec-2026.4.0-py3-none-any.whl (203 kB)
Downloading sympy-1.14.0-py3-none-any.whl (6.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.3/6.3 MB 58.5 MB/s  0:00:00
Downloading mpmath-1.3.0-py3-none-any.whl (536 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 536.2/536.2 kB 28.4 MB/s  0:00:00
Downloading filelock-3.29.0-py3-none-any.whl (39 kB)
Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
Installing collected packages: mpmath, sympy, setuptools, jinja2, fsspec, filelock, torch
  Attempting uninstall: setuptools
    Found existing installation: setuptools 82.0.1
    Uninstalling setuptools-82.0.1:
      Successfully uninstalled setuptools-82.0.1

Successfully installed filelock-3.29.0 fsspec-2026.4.0 jinja2-3.1.6 mpmath-1.3.0 setuptools-70.2.0 sympy-1.14.0 torch-2.12.0+cpu
- [2026-06-15T19:08:53-04:00] EXIT_STATUS: 0
- [2026-06-15T19:08:53-04:00] COMMAND: python -m pip install jax[cpu]
Collecting jax[cpu]
  Downloading jax-0.10.1-py3-none-any.whl.metadata (13 kB)
Collecting jaxlib<=0.10.1,>=0.10.1 (from jax[cpu])
  Downloading jaxlib-0.10.1-cp312-cp312-manylinux_2_27_x86_64.whl.metadata (1.3 kB)
Collecting ml_dtypes>=0.5.0 (from jax[cpu])
  Downloading ml_dtypes-0.5.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (8.9 kB)
Requirement already satisfied: numpy>=2.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jax[cpu]) (2.4.6)
Collecting opt_einsum (from jax[cpu])
  Downloading opt_einsum-3.4.0-py3-none-any.whl.metadata (6.3 kB)
Requirement already satisfied: scipy>=1.14 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jax[cpu]) (1.17.1)
Downloading jax-0.10.1-py3-none-any.whl (3.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.2/3.2 MB 34.7 MB/s  0:00:00
Downloading jaxlib-0.10.1-cp312-cp312-manylinux_2_27_x86_64.whl (85.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 85.8/85.8 MB 83.0 MB/s  0:00:01
Downloading ml_dtypes-0.5.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (5.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.0/5.0 MB 73.5 MB/s  0:00:00
Downloading opt_einsum-3.4.0-py3-none-any.whl (71 kB)
Installing collected packages: opt_einsum, ml_dtypes, jaxlib, jax

Successfully installed jax-0.10.1 jaxlib-0.10.1 ml_dtypes-0.5.4 opt_einsum-3.4.0
- [2026-06-15T19:08:58-04:00] EXIT_STATUS: 0
- [2026-06-15T19:08:58-04:00] COMMAND: python -m pip install freegs
Collecting freegs
  Downloading FreeGS-0.8.2-py3-none-any.whl.metadata (8.3 kB)
Requirement already satisfied: numpy>=1.8 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from freegs) (2.4.6)
Requirement already satisfied: scipy>=0.14 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from freegs) (1.17.1)
Requirement already satisfied: matplotlib>=1.3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from freegs) (3.10.9)
Requirement already satisfied: h5py>=2.10.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from freegs) (3.16.0)
Collecting Shapely>=1.7.1 (from freegs)
  Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.8 kB)
Collecting freeqdsk>=0.1.0 (from freegs)
  Downloading freeqdsk-0.5.2-py3-none-any.whl.metadata (4.3 kB)
Collecting fortranformat~=2.0 (from freeqdsk>=0.1.0->freegs)
  Downloading fortranformat-2.0.3-py3-none-any.whl.metadata (1.2 kB)
Requirement already satisfied: contourpy>=1.0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (1.3.3)
Requirement already satisfied: cycler>=0.10 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (0.12.1)
Requirement already satisfied: fonttools>=4.22.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (4.63.0)
Requirement already satisfied: kiwisolver>=1.3.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (1.5.0)
Requirement already satisfied: packaging>=20.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (26.2)
Requirement already satisfied: pillow>=8 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (12.2.0)
Requirement already satisfied: pyparsing>=3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (3.3.2)
Requirement already satisfied: python-dateutil>=2.7 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=1.3->freegs) (2.9.0.post0)
Requirement already satisfied: six>=1.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from python-dateutil>=2.7->matplotlib>=1.3->freegs) (1.17.0)
Downloading FreeGS-0.8.2-py3-none-any.whl (106 kB)
Downloading freeqdsk-0.5.2-py3-none-any.whl (25 kB)
Downloading fortranformat-2.0.3-py3-none-any.whl (23 kB)
Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (3.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.1/3.1 MB 33.0 MB/s  0:00:00
Installing collected packages: Shapely, fortranformat, freeqdsk, freegs

Successfully installed Shapely-2.1.2 fortranformat-2.0.3 freegs-0.8.2 freeqdsk-0.5.2
- [2026-06-15T19:08:59-04:00] EXIT_STATUS: 0
- [2026-06-15T19:08:59-04:00] COMMAND: python -m pip install torax
Collecting torax
  Downloading torax-1.4.0-py3-none-any.whl.metadata (11 kB)
Collecting absl-py>=2.0.0 (from torax)
  Downloading absl_py-2.4.0-py3-none-any.whl.metadata (3.3 kB)
Requirement already satisfied: typing_extensions>=4.2.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (4.15.0)
Collecting immutabledict>=1.0.0 (from torax)
  Downloading immutabledict-4.3.1-py3-none-any.whl.metadata (3.5 kB)
Requirement already satisfied: jax>=0.10.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (0.10.1)
Requirement already satisfied: jaxlib>=0.10.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (0.10.1)
Collecting jaxopt>=0.8.2 (from torax)
  Downloading jaxopt-0.8.5-py3-none-any.whl.metadata (3.3 kB)
Collecting flax>=0.10.0 (from torax)
  Downloading flax-0.12.7-py3-none-any.whl.metadata (11 kB)
Collecting fusion_surrogates==0.4.6 (from fusion_surrogates[tglfnnukaea]==0.4.6->torax)
  Downloading fusion_surrogates-0.4.6-py3-none-any.whl.metadata (4.7 kB)
Requirement already satisfied: matplotlib>=3.3.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (3.10.9)
Requirement already satisfied: numpy>2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (2.4.6)
Requirement already satisfied: setuptools in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (70.2.0)
Collecting chex>=0.1.90 (from torax)
  Downloading chex-0.1.92-py3-none-any.whl.metadata (19 kB)
Collecting equinox>=0.11.3 (from torax)
  Downloading equinox-0.13.8-py3-none-any.whl.metadata (18 kB)
Requirement already satisfied: PyYAML>=6.0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (6.0.3)
Requirement already satisfied: xarray>=2024.11.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (2026.4.0)
Collecting netcdf4>=1.7.2 (from torax)
  Downloading netcdf4-1.7.4-cp311-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (2.1 kB)
Collecting h5netcdf>=1.3.0 (from torax)
  Downloading h5netcdf-1.8.1-py3-none-any.whl.metadata (15 kB)
Collecting h5py<3.15.0,>=3.1.0 (from torax)
  Downloading h5py-3.14.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.7 kB)
Requirement already satisfied: scipy>=1.13.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (1.17.1)
Collecting jaxtyping>=0.3.2 (from torax)
  Downloading jaxtyping-0.3.11-py3-none-any.whl.metadata (6.2 kB)
Requirement already satisfied: contourpy>=1.2.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (1.3.3)
Collecting eqdsk<0.8.0,>=0.7.0 (from torax)
  Downloading eqdsk-0.7.0-py3-none-any.whl.metadata (3.9 kB)
Requirement already satisfied: pydantic>=2.10.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (2.13.4)
Requirement already satisfied: tqdm>=4.67.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (4.68.2)
Collecting treelib>=1.3.2 (from torax)
  Downloading treelib-1.8.0-py3-none-any.whl.metadata (3.3 kB)
Collecting imas-python==2.1.0 (from torax)
  Downloading imas_python-2.1.0-py3-none-any.whl.metadata (14 kB)
Collecting typeguard==2.13.3 (from torax)
  Downloading typeguard-2.13.3-py3-none-any.whl.metadata (3.6 kB)
Requirement already satisfied: plotly>=6.0.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torax) (6.8.0)
Collecting tglfnn_ukaea==0.1.0 (from fusion_surrogates[tglfnnukaea]==0.4.6->torax)
  Downloading tglfnn_ukaea-0.1.0-py3-none-any.whl.metadata (4.6 kB)
Requirement already satisfied: rich in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from imas-python==2.1.0->torax) (15.0.0)
Requirement already satisfied: click in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from imas-python==2.1.0->torax) (8.4.1)
Requirement already satisfied: packaging in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from imas-python==2.1.0->torax) (26.2)
Collecting xxhash>=2 (from imas-python==2.1.0->torax)
  Downloading xxhash-3.7.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (13 kB)
Collecting imas_data_dictionaries (from imas-python==2.1.0->torax)
  Downloading imas_data_dictionaries-4.1.1-py3-none-any.whl.metadata (2.6 kB)
Collecting imas_core (from imas-python==2.1.0->torax)
  Downloading imas_core-5.7.0-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (5.3 kB)
Requirement already satisfied: fortranformat in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from eqdsk<0.8.0,>=0.7.0->torax) (2.0.3)
Collecting toolz>=1.0.0 (from chex>=0.1.90->torax)
  Downloading toolz-1.1.0-py3-none-any.whl.metadata (5.1 kB)
Collecting wadler-lindig>=0.1.0 (from equinox>=0.11.3->torax)
  Downloading wadler_lindig-0.1.7-py3-none-any.whl.metadata (17 kB)
Requirement already satisfied: msgpack in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from flax>=0.10.0->torax) (1.1.2)
Collecting optax (from flax>=0.10.0->torax)
  Downloading optax-0.2.8-py3-none-any.whl.metadata (7.9 kB)
Collecting orbax-checkpoint (from flax>=0.10.0->torax)
  Downloading orbax_checkpoint-0.12.0-py3-none-any.whl.metadata (3.3 kB)
Collecting tensorstore (from flax>=0.10.0->torax)
  Downloading tensorstore-0.1.84-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (3.3 kB)
Collecting treescope>=0.1.7 (from flax>=0.10.0->torax)
  Downloading treescope-0.1.10-py3-none-any.whl.metadata (6.6 kB)
Requirement already satisfied: ml_dtypes>=0.5.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jax>=0.10.0->torax) (0.5.4)
Requirement already satisfied: opt_einsum in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jax>=0.10.0->torax) (3.4.0)
Requirement already satisfied: cycler>=0.10 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (0.12.1)
Requirement already satisfied: fonttools>=4.22.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (4.63.0)
Requirement already satisfied: kiwisolver>=1.3.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (1.5.0)
Requirement already satisfied: pillow>=8 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (12.2.0)
Requirement already satisfied: pyparsing>=3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (3.3.2)
Requirement already satisfied: python-dateutil>=2.7 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib>=3.3.0->torax) (2.9.0.post0)
Collecting cftime (from netcdf4>=1.7.2->torax)
  Downloading cftime-1.6.5-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (8.7 kB)
Requirement already satisfied: certifi in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from netcdf4>=1.7.2->torax) (2026.5.20)
Requirement already satisfied: narwhals>=1.15.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from plotly>=6.0.0->torax) (2.22.1)
Requirement already satisfied: annotated-types>=0.6.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from pydantic>=2.10.5->torax) (0.7.0)
Requirement already satisfied: pydantic-core==2.46.4 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from pydantic>=2.10.5->torax) (2.46.4)
Requirement already satisfied: typing-inspection>=0.4.2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from pydantic>=2.10.5->torax) (0.4.2)
Requirement already satisfied: six>=1.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from python-dateutil>=2.7->matplotlib>=3.3.0->torax) (1.17.0)
Requirement already satisfied: markdown-it-py>=2.2.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from rich->imas-python==2.1.0->torax) (4.2.0)
Requirement already satisfied: pygments<3.0.0,>=2.13.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from rich->imas-python==2.1.0->torax) (2.20.0)
Requirement already satisfied: mdurl~=0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from markdown-it-py>=2.2.0->rich->imas-python==2.1.0->torax) (0.1.2)
Requirement already satisfied: pandas>=2.2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from xarray>=2024.11.0->torax) (3.0.3)
Collecting etils[epath,epy] (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading etils-1.14.0-py3-none-any.whl.metadata (6.5 kB)
Collecting prometheus-client>=0.20.0 (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading prometheus_client-0.25.0-py3-none-any.whl.metadata (2.1 kB)
Collecting aiofiles (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading aiofiles-25.1.0-py3-none-any.whl.metadata (6.3 kB)
Collecting protobuf (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading protobuf-7.35.1-cp310-abi3-manylinux2014_x86_64.whl.metadata (595 bytes)
Collecting humanize (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading humanize-4.15.0-py3-none-any.whl.metadata (7.8 kB)
Collecting simplejson>=3.16.0 (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading simplejson-4.1.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.8 kB)
Requirement already satisfied: psutil in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from orbax-checkpoint->flax>=0.10.0->torax) (7.2.2)
Collecting uvloop (from orbax-checkpoint->flax>=0.10.0->torax)
  Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Requirement already satisfied: fsspec in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from etils[epath,epy]->orbax-checkpoint->flax>=0.10.0->torax) (2026.4.0)
Requirement already satisfied: zipp in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from etils[epath,epy]->orbax-checkpoint->flax>=0.10.0->torax) (4.1.0)
Downloading torax-1.4.0-py3-none-any.whl (1.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 17.3 MB/s  0:00:00
Downloading fusion_surrogates-0.4.6-py3-none-any.whl (622 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 622.0/622.0 kB 25.2 MB/s  0:00:00
Downloading imas_python-2.1.0-py3-none-any.whl (2.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.4/2.4 MB 51.1 MB/s  0:00:00
Downloading tglfnn_ukaea-0.1.0-py3-none-any.whl (59.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 59.5/59.5 MB 80.6 MB/s  0:00:00
Downloading typeguard-2.13.3-py3-none-any.whl (17 kB)
Downloading eqdsk-0.7.0-py3-none-any.whl (30 kB)
Downloading h5py-3.14.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (4.9 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.9/4.9 MB 80.5 MB/s  0:00:00
Downloading absl_py-2.4.0-py3-none-any.whl (135 kB)
Downloading chex-0.1.92-py3-none-any.whl (102 kB)
Downloading equinox-0.13.8-py3-none-any.whl (185 kB)
Downloading flax-0.12.7-py3-none-any.whl (525 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 525.1/525.1 kB 18.2 MB/s  0:00:00
Downloading h5netcdf-1.8.1-py3-none-any.whl (62 kB)
Downloading immutabledict-4.3.1-py3-none-any.whl (5.0 kB)
Downloading jaxopt-0.8.5-py3-none-any.whl (172 kB)
Downloading jaxtyping-0.3.11-py3-none-any.whl (56 kB)
Downloading netcdf4-1.7.4-cp311-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (10.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10.1/10.1 MB 88.1 MB/s  0:00:00
Downloading toolz-1.1.0-py3-none-any.whl (58 kB)
Downloading treelib-1.8.0-py3-none-any.whl (30 kB)
Downloading treescope-0.1.10-py3-none-any.whl (182 kB)
Downloading wadler_lindig-0.1.7-py3-none-any.whl (20 kB)
Downloading xxhash-3.7.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (193 kB)
Downloading cftime-1.6.5-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (1.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB 30.1 MB/s  0:00:00
Downloading imas_core-5.7.0-cp312-cp312-manylinux_2_28_x86_64.whl (8.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.1/8.1 MB 27.3 MB/s  0:00:00
Downloading imas_data_dictionaries-4.1.1-py3-none-any.whl (32.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 32.3/32.3 MB 101.0 MB/s  0:00:00
Downloading optax-0.2.8-py3-none-any.whl (402 kB)
Downloading orbax_checkpoint-0.12.0-py3-none-any.whl (1.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 46.1 MB/s  0:00:00
Downloading prometheus_client-0.25.0-py3-none-any.whl (64 kB)
Downloading simplejson-4.1.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (190 kB)
Downloading tensorstore-0.1.84-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (21.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 21.0/21.0 MB 25.7 MB/s  0:00:00
Downloading aiofiles-25.1.0-py3-none-any.whl (14 kB)
Downloading etils-1.14.0-py3-none-any.whl (172 kB)
Downloading humanize-4.15.0-py3-none-any.whl (132 kB)
Downloading protobuf-7.35.1-cp310-abi3-manylinux2014_x86_64.whl (327 kB)
Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.4/4.4 MB 89.1 MB/s  0:00:00
Installing collected packages: xxhash, wadler-lindig, uvloop, typeguard, treescope, treelib, toolz, tglfnn_ukaea, simplejson, protobuf, prometheus-client, immutabledict, imas_data_dictionaries, imas_core, humanize, h5py, h5netcdf, etils, eqdsk, cftime, aiofiles, absl-py, tensorstore, netcdf4, jaxtyping, imas-python, orbax-checkpoint, optax, jaxopt, equinox, chex, flax, fusion_surrogates, torax
  Attempting uninstall: h5py
    Found existing installation: h5py 3.16.0
    Uninstalling h5py-3.16.0:
      Successfully uninstalled h5py-3.16.0

Successfully installed absl-py-2.4.0 aiofiles-25.1.0 cftime-1.6.5 chex-0.1.92 eqdsk-0.7.0 equinox-0.13.8 etils-1.14.0 flax-0.12.7 fusion_surrogates-0.4.6 h5netcdf-1.8.1 h5py-3.14.0 humanize-4.15.0 imas-python-2.1.0 imas_core-5.7.0 imas_data_dictionaries-4.1.1 immutabledict-4.3.1 jaxopt-0.8.5 jaxtyping-0.3.11 netcdf4-1.7.4 optax-0.2.8 orbax-checkpoint-0.12.0 prometheus-client-0.25.0 protobuf-7.35.1 simplejson-4.1.1 tensorstore-0.1.84 tglfnn_ukaea-0.1.0 toolz-1.1.0 torax-1.4.0 treelib-1.8.0 treescope-0.1.10 typeguard-2.13.3 uvloop-0.22.1 wadler-lindig-0.1.7 xxhash-3.7.0
- [2026-06-15T19:09:09-04:00] EXIT_STATUS: 0
- [2026-06-15T19:09:09-04:00] COMMAND: python -m pip install mlflow
Collecting mlflow
  Downloading mlflow-3.13.0-py3-none-any.whl.metadata (49 kB)
Collecting mlflow-skinny==3.13.0 (from mlflow)
  Downloading mlflow_skinny-3.13.0-py3-none-any.whl.metadata (50 kB)
Collecting mlflow-tracing==3.13.0 (from mlflow)
  Downloading mlflow_tracing-3.13.0-py3-none-any.whl.metadata (19 kB)
Collecting Flask-CORS<7 (from mlflow)
  Downloading flask_cors-6.0.5-py3-none-any.whl.metadata (5.4 kB)
Collecting Flask<4 (from mlflow)
  Downloading flask-3.1.3-py3-none-any.whl.metadata (3.2 kB)
Collecting aiohttp<4 (from mlflow)
  Downloading aiohttp-3.14.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (8.3 kB)
Requirement already satisfied: alembic!=1.10.0,<2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow) (1.18.4)
Collecting cryptography<49,>=43.0.0 (from mlflow)
  Downloading cryptography-48.0.1-cp311-abi3-manylinux_2_34_x86_64.whl.metadata (4.3 kB)
Collecting docker<8,>=4.0.0 (from mlflow)
  Downloading docker-7.1.0-py3-none-any.whl.metadata (3.8 kB)
Collecting graphene<4 (from mlflow)
  Downloading graphene-3.4.3-py2.py3-none-any.whl.metadata (6.9 kB)
Collecting gunicorn<27 (from mlflow)
  Downloading gunicorn-26.0.0-py3-none-any.whl.metadata (5.4 kB)
Collecting huey<4,>=2.5.4 (from mlflow)
  Downloading huey-3.0.3-py3-none-any.whl.metadata (4.5 kB)
Requirement already satisfied: matplotlib<4 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow) (3.10.9)
Requirement already satisfied: numpy<3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow) (2.4.6)
Collecting pandas<3 (from mlflow)
  Downloading pandas-2.3.3-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (91 kB)
Collecting pyarrow<25,>=4.0.0 (from mlflow)
  Downloading pyarrow-24.0.0-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (3.0 kB)
Collecting scikit-learn<2 (from mlflow)
  Downloading scikit_learn-1.9.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (11 kB)
Requirement already satisfied: scipy<2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow) (1.17.1)
Collecting skops<1 (from mlflow)
  Downloading skops-0.14.0-py3-none-any.whl.metadata (4.4 kB)
Requirement already satisfied: sqlalchemy<3,>=1.4.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow) (2.0.51)
Collecting cachetools<8,>=5.0.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading cachetools-7.1.4-py3-none-any.whl.metadata (5.5 kB)
Requirement already satisfied: click<9,>=7.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (8.4.1)
Collecting cloudpickle<4 (from mlflow-skinny==3.13.0->mlflow)
  Downloading cloudpickle-3.1.2-py3-none-any.whl.metadata (7.1 kB)
Collecting databricks-sdk<1,>=0.20.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading databricks_sdk-0.117.0-py3-none-any.whl.metadata (43 kB)
Collecting fastapi<1 (from mlflow-skinny==3.13.0->mlflow)
  Downloading fastapi-0.137.1-py3-none-any.whl.metadata (26 kB)
Collecting gitpython<4,>=3.1.9 (from mlflow-skinny==3.13.0->mlflow)
  Downloading gitpython-3.1.50-py3-none-any.whl.metadata (14 kB)
Requirement already satisfied: importlib_metadata!=4.7.0,<10,>=3.7.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (9.0.0)
Collecting opentelemetry-api<3,>=1.9.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading opentelemetry_api-1.42.1-py3-none-any.whl.metadata (1.4 kB)
Collecting opentelemetry-proto<3,>=1.9.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading opentelemetry_proto-1.42.1-py3-none-any.whl.metadata (2.3 kB)
Collecting opentelemetry-sdk<3,>=1.9.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading opentelemetry_sdk-1.42.1-py3-none-any.whl.metadata (1.7 kB)
Requirement already satisfied: packaging<27 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (26.2)
Requirement already satisfied: protobuf<8,>=3.12.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (7.35.1)
Requirement already satisfied: pydantic<3,>=2.0.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (2.13.4)
Collecting python-dotenv<2,>=0.19.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Requirement already satisfied: pyyaml<7,>=5.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (6.0.3)
Requirement already satisfied: requests<3,>=2.17.3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (2.34.2)
Collecting sqlparse<1,>=0.4.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading sqlparse-0.5.5-py3-none-any.whl.metadata (4.7 kB)
Collecting starlette<2 (from mlflow-skinny==3.13.0->mlflow)
  Downloading starlette-1.3.1-py3-none-any.whl.metadata (6.4 kB)
Requirement already satisfied: typing-extensions<5,>=4.0.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from mlflow-skinny==3.13.0->mlflow) (4.15.0)
Collecting uvicorn<1 (from mlflow-skinny==3.13.0->mlflow)
  Downloading uvicorn-0.49.0-py3-none-any.whl.metadata (6.7 kB)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp<4->mlflow)
  Downloading aiohappyeyeballs-2.6.2-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp<4->mlflow)
  Downloading aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting attrs>=17.3.0 (from aiohttp<4->mlflow)
  Downloading attrs-26.1.0-py3-none-any.whl.metadata (8.8 kB)
Collecting frozenlist>=1.1.1 (from aiohttp<4->mlflow)
  Downloading frozenlist-1.8.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (20 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp<4->mlflow)
  Downloading multidict-6.7.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.3 kB)
Collecting propcache>=0.2.0 (from aiohttp<4->mlflow)
  Downloading propcache-0.5.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (16 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp<4->mlflow)
  Downloading yarl-1.24.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (94 kB)
Requirement already satisfied: Mako in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from alembic!=1.10.0,<2->mlflow) (1.3.12)
Collecting cffi>=2.0.0 (from cryptography<49,>=43.0.0->mlflow)
  Downloading cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting google-auth~=2.0 (from databricks-sdk<1,>=0.20.0->mlflow-skinny==3.13.0->mlflow)
  Downloading google_auth-2.55.0-py3-none-any.whl.metadata (5.1 kB)
Collecting protobuf<8,>=3.12.0 (from mlflow-skinny==3.13.0->mlflow)
  Downloading protobuf-6.33.6-cp39-abi3-manylinux2014_x86_64.whl.metadata (593 bytes)
Requirement already satisfied: urllib3<3,>=1.26 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from databricks-sdk<1,>=0.20.0->mlflow-skinny==3.13.0->mlflow) (2.7.0)
Requirement already satisfied: typing-inspection>=0.4.2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from fastapi<1->mlflow-skinny==3.13.0->mlflow) (0.4.2)
Requirement already satisfied: annotated-doc>=0.0.2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from fastapi<1->mlflow-skinny==3.13.0->mlflow) (0.0.4)
Collecting blinker>=1.9.0 (from Flask<4->mlflow)
  Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting itsdangerous>=2.2.0 (from Flask<4->mlflow)
  Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Requirement already satisfied: jinja2>=3.1.2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from Flask<4->mlflow) (3.1.6)
Requirement already satisfied: markupsafe>=2.1.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from Flask<4->mlflow) (3.0.3)
Collecting werkzeug>=3.1.0 (from Flask<4->mlflow)
  Downloading werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Collecting gitdb<5,>=4.0.1 (from gitpython<4,>=3.1.9->mlflow-skinny==3.13.0->mlflow)
  Downloading gitdb-4.0.12-py3-none-any.whl.metadata (1.2 kB)
Collecting smmap<6,>=3.0.1 (from gitdb<5,>=4.0.1->gitpython<4,>=3.1.9->mlflow-skinny==3.13.0->mlflow)
  Downloading smmap-5.0.3-py3-none-any.whl.metadata (4.6 kB)
Collecting pyasn1-modules>=0.2.1 (from google-auth~=2.0->databricks-sdk<1,>=0.20.0->mlflow-skinny==3.13.0->mlflow)
  Downloading pyasn1_modules-0.4.2-py3-none-any.whl.metadata (3.5 kB)
Collecting graphql-core<3.3,>=3.1 (from graphene<4->mlflow)
  Downloading graphql_core-3.2.11-py3-none-any.whl.metadata (11 kB)
Collecting graphql-relay<3.3,>=3.1 (from graphene<4->mlflow)
  Downloading graphql_relay-3.2.0-py3-none-any.whl.metadata (12 kB)
Requirement already satisfied: python-dateutil<3,>=2.7.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from graphene<4->mlflow) (2.9.0.post0)
Requirement already satisfied: zipp>=3.20 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from importlib_metadata!=4.7.0,<10,>=3.7.0->mlflow-skinny==3.13.0->mlflow) (4.1.0)
Requirement already satisfied: contourpy>=1.0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (1.3.3)
Requirement already satisfied: cycler>=0.10 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (0.12.1)
Requirement already satisfied: fonttools>=4.22.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (4.63.0)
Requirement already satisfied: kiwisolver>=1.3.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (1.5.0)
Requirement already satisfied: pillow>=8 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (12.2.0)
Requirement already satisfied: pyparsing>=3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from matplotlib<4->mlflow) (3.3.2)
Collecting opentelemetry-semantic-conventions==0.63b1 (from opentelemetry-sdk<3,>=1.9.0->mlflow-skinny==3.13.0->mlflow)
  Downloading opentelemetry_semantic_conventions-0.63b1-py3-none-any.whl.metadata (2.4 kB)
Collecting pytz>=2020.1 (from pandas<3->mlflow)
  Downloading pytz-2026.2-py2.py3-none-any.whl.metadata (22 kB)
Collecting tzdata>=2022.7 (from pandas<3->mlflow)
  Downloading tzdata-2026.2-py2.py3-none-any.whl.metadata (1.4 kB)
Requirement already satisfied: annotated-types>=0.6.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from pydantic<3,>=2.0.0->mlflow-skinny==3.13.0->mlflow) (0.7.0)
Requirement already satisfied: pydantic-core==2.46.4 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from pydantic<3,>=2.0.0->mlflow-skinny==3.13.0->mlflow) (2.46.4)
Requirement already satisfied: six>=1.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from python-dateutil<3,>=2.7.0->graphene<4->mlflow) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from requests<3,>=2.17.3->mlflow-skinny==3.13.0->mlflow) (3.4.7)
Requirement already satisfied: idna<4,>=2.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from requests<3,>=2.17.3->mlflow-skinny==3.13.0->mlflow) (3.17)
Requirement already satisfied: certifi>=2023.5.7 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from requests<3,>=2.17.3->mlflow-skinny==3.13.0->mlflow) (2026.5.20)
Collecting joblib>=1.4.0 (from scikit-learn<2->mlflow)
  Downloading joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
Requirement already satisfied: narwhals>=2.0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from scikit-learn<2->mlflow) (2.22.1)
Collecting threadpoolctl>=3.5.0 (from scikit-learn<2->mlflow)
  Downloading threadpoolctl-3.6.0-py3-none-any.whl.metadata (13 kB)
Collecting prettytable>=3.9 (from skops<1->mlflow)
  Downloading prettytable-3.17.0-py3-none-any.whl.metadata (34 kB)
Requirement already satisfied: greenlet>=1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from sqlalchemy<3,>=1.4.0->mlflow) (3.5.1)
Collecting anyio<5,>=3.6.2 (from starlette<2->mlflow-skinny==3.13.0->mlflow)
  Downloading anyio-4.14.0-py3-none-any.whl.metadata (4.6 kB)
Collecting h11>=0.8 (from uvicorn<1->mlflow-skinny==3.13.0->mlflow)
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting pycparser (from cffi>=2.0.0->cryptography<49,>=43.0.0->mlflow)
  Downloading pycparser-3.0-py3-none-any.whl.metadata (8.2 kB)
Collecting wcwidth (from prettytable>=3.9->skops<1->mlflow)
  Downloading wcwidth-0.8.1-py3-none-any.whl.metadata (43 kB)
Collecting pyasn1<0.7.0,>=0.6.1 (from pyasn1-modules>=0.2.1->google-auth~=2.0->databricks-sdk<1,>=0.20.0->mlflow-skinny==3.13.0->mlflow)
  Downloading pyasn1-0.6.3-py3-none-any.whl.metadata (8.4 kB)
Downloading mlflow-3.13.0-py3-none-any.whl (10.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10.8/10.8 MB 62.1 MB/s  0:00:00
Downloading mlflow_skinny-3.13.0-py3-none-any.whl (3.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.4/3.4 MB 80.2 MB/s  0:00:00
Downloading mlflow_tracing-3.13.0-py3-none-any.whl (1.7 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.7/1.7 MB 59.5 MB/s  0:00:00
Downloading aiohttp-3.14.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (1.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 69.5 MB/s  0:00:00
Downloading cachetools-7.1.4-py3-none-any.whl (16 kB)
Downloading cloudpickle-3.1.2-py3-none-any.whl (22 kB)
Downloading cryptography-48.0.1-cp311-abi3-manylinux_2_34_x86_64.whl (4.7 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.7/4.7 MB 91.5 MB/s  0:00:00
Downloading databricks_sdk-0.117.0-py3-none-any.whl (936 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 936.9/936.9 kB 54.2 MB/s  0:00:00
Downloading docker-7.1.0-py3-none-any.whl (147 kB)
Downloading fastapi-0.137.1-py3-none-any.whl (121 kB)
Downloading flask-3.1.3-py3-none-any.whl (103 kB)
Downloading flask_cors-6.0.5-py3-none-any.whl (16 kB)
Downloading gitpython-3.1.50-py3-none-any.whl (212 kB)
Downloading gitdb-4.0.12-py3-none-any.whl (62 kB)
Downloading google_auth-2.55.0-py3-none-any.whl (252 kB)
Downloading graphene-3.4.3-py2.py3-none-any.whl (114 kB)
Downloading graphql_core-3.2.11-py3-none-any.whl (214 kB)
Downloading graphql_relay-3.2.0-py3-none-any.whl (16 kB)
Downloading gunicorn-26.0.0-py3-none-any.whl (212 kB)
Downloading huey-3.0.3-py3-none-any.whl (94 kB)
Downloading multidict-6.7.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (256 kB)
Downloading opentelemetry_api-1.42.1-py3-none-any.whl (61 kB)
Downloading opentelemetry_proto-1.42.1-py3-none-any.whl (71 kB)
Downloading opentelemetry_sdk-1.42.1-py3-none-any.whl (170 kB)
Downloading opentelemetry_semantic_conventions-0.63b1-py3-none-any.whl (203 kB)
Downloading pandas-2.3.3-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (12.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.4/12.4 MB 94.4 MB/s  0:00:00
Downloading protobuf-6.33.6-cp39-abi3-manylinux2014_x86_64.whl (323 kB)
Downloading pyarrow-24.0.0-cp312-cp312-manylinux_2_28_x86_64.whl (48.9 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 48.9/48.9 MB 89.1 MB/s  0:00:00
Downloading python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Downloading scikit_learn-1.9.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (9.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 9.1/9.1 MB 79.8 MB/s  0:00:00
Downloading skops-0.14.0-py3-none-any.whl (132 kB)
Downloading smmap-5.0.3-py3-none-any.whl (24 kB)
Downloading sqlparse-0.5.5-py3-none-any.whl (46 kB)
Downloading starlette-1.3.1-py3-none-any.whl (73 kB)
Downloading anyio-4.14.0-py3-none-any.whl (123 kB)
Downloading uvicorn-0.49.0-py3-none-any.whl (71 kB)
Downloading yarl-1.24.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (105 kB)
Downloading aiohappyeyeballs-2.6.2-py3-none-any.whl (15 kB)
Downloading aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Downloading attrs-26.1.0-py3-none-any.whl (67 kB)
Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (219 kB)
Downloading frozenlist-1.8.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (242 kB)
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading joblib-1.5.3-py3-none-any.whl (309 kB)
Downloading prettytable-3.17.0-py3-none-any.whl (34 kB)
Downloading propcache-0.5.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (61 kB)
Downloading pyasn1_modules-0.4.2-py3-none-any.whl (181 kB)
Downloading pyasn1-0.6.3-py3-none-any.whl (83 kB)
Downloading pytz-2026.2-py2.py3-none-any.whl (510 kB)
Downloading threadpoolctl-3.6.0-py3-none-any.whl (18 kB)
Downloading tzdata-2026.2-py2.py3-none-any.whl (349 kB)
Downloading werkzeug-3.1.8-py3-none-any.whl (226 kB)
Downloading pycparser-3.0-py3-none-any.whl (48 kB)
Downloading wcwidth-0.8.1-py3-none-any.whl (323 kB)
Installing collected packages: pytz, huey, werkzeug, wcwidth, tzdata, threadpoolctl, sqlparse, smmap, python-dotenv, pycparser, pyasn1, pyarrow, protobuf, propcache, opentelemetry-api, multidict, joblib, itsdangerous, h11, gunicorn, graphql-core, frozenlist, cloudpickle, cachetools, blinker, attrs, anyio, aiohappyeyeballs, yarl, uvicorn, starlette, scikit-learn, pyasn1-modules, prettytable, pandas, opentelemetry-semantic-conventions, opentelemetry-proto, graphql-relay, gitdb, Flask, docker, cffi, aiosignal, skops, opentelemetry-sdk, graphene, gitpython, Flask-CORS, fastapi, cryptography, aiohttp, google-auth, databricks-sdk, mlflow-tracing, mlflow-skinny, mlflow
  Attempting uninstall: protobuf
    Found existing installation: protobuf 7.35.1
    Uninstalling protobuf-7.35.1:
      Successfully uninstalled protobuf-7.35.1
  Attempting uninstall: pandas
    Found existing installation: pandas 3.0.3
    Uninstalling pandas-3.0.3:
      Successfully uninstalled pandas-3.0.3

Successfully installed Flask-3.1.3 Flask-CORS-6.0.5 aiohappyeyeballs-2.6.2 aiohttp-3.14.1 aiosignal-1.4.0 anyio-4.14.0 attrs-26.1.0 blinker-1.9.0 cachetools-7.1.4 cffi-2.0.0 cloudpickle-3.1.2 cryptography-48.0.1 databricks-sdk-0.117.0 docker-7.1.0 fastapi-0.137.1 frozenlist-1.8.0 gitdb-4.0.12 gitpython-3.1.50 google-auth-2.55.0 graphene-3.4.3 graphql-core-3.2.11 graphql-relay-3.2.0 gunicorn-26.0.0 h11-0.16.0 huey-3.0.3 itsdangerous-2.2.0 joblib-1.5.3 mlflow-3.13.0 mlflow-skinny-3.13.0 mlflow-tracing-3.13.0 multidict-6.7.1 opentelemetry-api-1.42.1 opentelemetry-proto-1.42.1 opentelemetry-sdk-1.42.1 opentelemetry-semantic-conventions-0.63b1 pandas-2.3.3 prettytable-3.17.0 propcache-0.5.2 protobuf-6.33.6 pyarrow-24.0.0 pyasn1-0.6.3 pyasn1-modules-0.4.2 pycparser-3.0 python-dotenv-1.2.2 pytz-2026.2 scikit-learn-1.9.0 skops-0.14.0 smmap-5.0.3 sqlparse-0.5.5 starlette-1.3.1 threadpoolctl-3.6.0 tzdata-2026.2 uvicorn-0.49.0 wcwidth-0.8.1 werkzeug-3.1.8 yarl-1.24.2
- [2026-06-15T19:09:30-04:00] EXIT_STATUS: 0
- [2026-06-15T19:09:30-04:00] COMMAND: python -m pip install botorch
Collecting botorch
  Downloading botorch-0.18.1-py3-none-any.whl.metadata (10 kB)
Requirement already satisfied: typing_extensions in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from botorch) (4.15.0)
Collecting pyre_extensions (from botorch)
  Downloading pyre_extensions-0.0.32-py3-none-any.whl.metadata (4.0 kB)
Collecting gpytorch>=1.15.2 (from botorch)
  Downloading gpytorch-1.15.2-py3-none-any.whl.metadata (8.2 kB)
Collecting linear_operator>=0.6.1 (from botorch)
  Downloading linear_operator-0.6.1-py3-none-any.whl.metadata (15 kB)
Requirement already satisfied: torch>=2.4 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from botorch) (2.12.0+cpu)
Requirement already satisfied: scipy in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from botorch) (1.17.1)
Collecting multipledispatch (from botorch)
  Downloading multipledispatch-1.0.0-py3-none-any.whl.metadata (3.8 kB)
Requirement already satisfied: threadpoolctl in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from botorch) (3.6.0)
Collecting ninja (from botorch)
  Downloading ninja-1.13.0-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.1 kB)
Requirement already satisfied: mpmath<=1.3,>=0.19 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from gpytorch>=1.15.2->botorch) (1.3.0)
Requirement already satisfied: scikit-learn in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from gpytorch>=1.15.2->botorch) (1.9.0)
Requirement already satisfied: numpy<2.7,>=1.26.4 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from scipy->botorch) (2.4.6)
Requirement already satisfied: filelock in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (3.29.0)
Requirement already satisfied: setuptools<82 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (70.2.0)
Requirement already satisfied: sympy>=1.13.3 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (1.14.0)
Requirement already satisfied: networkx>=2.5.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (3.6.1)
Requirement already satisfied: jinja2 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (3.1.6)
Requirement already satisfied: fsspec>=0.8.5 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from torch>=2.4->botorch) (2026.4.0)
Requirement already satisfied: MarkupSafe>=2.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from jinja2->torch>=2.4->botorch) (3.0.3)
Collecting typing-inspect (from pyre_extensions->botorch)
  Downloading typing_inspect-0.9.0-py3-none-any.whl.metadata (1.5 kB)
Requirement already satisfied: joblib>=1.4.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from scikit-learn->gpytorch>=1.15.2->botorch) (1.5.3)
Requirement already satisfied: narwhals>=2.0.1 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from scikit-learn->gpytorch>=1.15.2->botorch) (2.22.1)
Requirement already satisfied: mypy-extensions>=0.3.0 in /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages (from typing-inspect->pyre_extensions->botorch) (1.1.0)
Downloading botorch-0.18.1-py3-none-any.whl (6.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.0/6.0 MB 47.4 MB/s  0:00:00
Downloading gpytorch-1.15.2-py3-none-any.whl (291 kB)
Downloading linear_operator-0.6.1-py3-none-any.whl (174 kB)
Downloading multipledispatch-1.0.0-py3-none-any.whl (12 kB)
Downloading ninja-1.13.0-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (180 kB)
Downloading pyre_extensions-0.0.32-py3-none-any.whl (12 kB)
Downloading typing_inspect-0.9.0-py3-none-any.whl (8.8 kB)
Installing collected packages: multipledispatch, typing-inspect, ninja, pyre_extensions, linear_operator, gpytorch, botorch

Successfully installed botorch-0.18.1 gpytorch-1.15.2 linear_operator-0.6.1 multipledispatch-1.0.0 ninja-1.13.0 pyre_extensions-0.0.32 typing-inspect-0.9.0
- [2026-06-15T19:09:32-04:00] EXIT_STATUS: 0
- [2026-06-15T19:09:42-04:00] Starting WSL conda-forge CAD/neutronics install attempts.
- [2026-06-15T19:09:42-04:00] COMMAND: mamba install -y -c conda-forge cadquery

Pinned packages:

  - python=3.12


Transaction

  Prefix: /home/craig/miniforge/envs/mini-tokamak

  Updating specs:

   - cadquery


  Package                                            Version  Build                     Channel           Size
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Install:
────────────────────────────────────────────────────────────────────────────────────────────────────────────────

  + _x86_64-microarch-level                                3  3_x86_64_v3               conda-forge       10kB
  + aiohappyeyeballs                                   2.6.2  pyhd8ed1ab_0              conda-forge       21kB
  + aiohttp                                           3.14.1  py312h5d8c7f2_0           conda-forge        1MB
  + aiosignal                                          1.4.0  pyhd8ed1ab_0              conda-forge       14kB
  + ampl-asl                                           1.0.0  h5888daf_2                conda-forge      517kB
  + aom                                                3.9.1  hac33072_0                conda-forge        3MB
  + asttokens                                          3.0.1  pyhd8ed1ab_0              conda-forge       29kB
  + attrs                                             26.1.0  pyhcf101f3_0              conda-forge       65kB
  + blosc                                             1.21.6  hef167b5_0                conda-forge       49kB
  + cadquery                                           2.7.0  pyhcf101f3_0              conda-forge      374kB
  + casadi                                             3.7.2  py312h4238392_1           conda-forge        7MB
  + dav1d                                              1.2.1  hd590300_0                conda-forge      760kB
  + decorator                                          5.3.1  pyhd8ed1ab_0              conda-forge       16kB
  + eigen-abi                                      3.4.0.100  h3bcb7cf_2                conda-forge       13kB
  + executing                                          2.2.1  pyhd8ed1ab_0              conda-forge       31kB
  + ezdxf                                              1.4.2  py312hf890105_1           conda-forge        3MB
  + ffmpeg                                             7.1.1  gpl_h127656b_906          conda-forge       10MB
  + freeglut                                           3.2.2  h215f996_4                conda-forge      146kB
  + freeimage                                         3.18.0  hd1b7436_25               conda-forge      470kB
  + fribidi                                           1.0.16  hb03c661_0                conda-forge       61kB
  + frozenlist                                         1.8.0  py312h447239a_0           conda-forge       55kB
  + gdk-pixbuf                                        2.44.6  h2b0a6b4_0                conda-forge      577kB
  + gl2ps                                              1.4.2  h36e74d4_2                conda-forge       76kB
  + gmp                                                6.3.0  hac33072_2                conda-forge      460kB
  + hdf4                                              4.2.15  h2a13503_7                conda-forge      757kB
  + imath                                              3.2.2  hde8ca8f_0                conda-forge      160kB
  + ipopt                                            3.14.19  h0804adb_0                conda-forge        1MB
  + ipython                                           9.14.1  pyh53cf698_0              conda-forge      653kB
  + ipython_pygments_lexers                            1.1.1  pyhd8ed1ab_0              conda-forge       14kB
  + jasper                                             4.2.9  h1588d4d_1                conda-forge      684kB
  + jedi                                              0.19.2  pyhd8ed1ab_1              conda-forge      844kB
  + jsoncpp                                            1.9.6  hf42df4d_1                conda-forge      169kB
  + jxrlib                                               1.1  hd590300_3                conda-forge      239kB
  + lame                                               3.100  h166bdaf_1003             conda-forge      508kB
  + level-zero                                        1.29.0  hb700be7_0                conda-forge      876kB
  + libabseil                                     20240722.0  cxx17_hbbce691_4          conda-forge        1MB
  + libass                                            0.17.3  hba53ac1_1                conda-forge      153kB
  + libblasfeo                                       0.1.4.2  had105d5_300              conda-forge        1MB
  + libboost                                          1.86.0  hed09d94_4                conda-forge        3MB
  + libcap                                              2.78  hd0affe5_0                conda-forge      124kB
  + libfatrop                                          0.0.4  h5888daf_1                conda-forge      241kB
  + libflac                                            1.5.0  he200343_1                conda-forge      425kB
  + libgfortran-ng                                    15.2.0  h69a702a_19               conda-forge       28kB
  + libglu                                             9.0.3  h5888daf_1                conda-forge      325kB
  + libhwloc                                          2.12.1  default_h3d81e11_1000     conda-forge        2MB
  + libllvm20                                         20.1.8  hecd9e04_0                conda-forge       44MB
  + libllvm21                                         21.1.0  hecd9e04_0                conda-forge       44MB
  + liblzma-devel                                      5.8.3  hb03c661_0                conda-forge      491kB
  + libnetcdf                                          4.9.2  nompi_h5ddbaa4_116        conda-forge      833kB
  + libogg                                             1.3.5  hd0c01bc_1                conda-forge      218kB
  + libopenvino                                     2025.0.0  hac27bb2_0                conda-forge        6MB
  + libopenvino-auto-batch-plugin                   2025.0.0  h4d9b6c2_0                conda-forge      112kB
  + libopenvino-auto-plugin                         2025.0.0  h4d9b6c2_0                conda-forge      239kB
  + libopenvino-hetero-plugin                       2025.0.0  h3f63f65_0                conda-forge      196kB
  + libopenvino-intel-cpu-plugin                    2025.0.0  hac27bb2_0                conda-forge       12MB
  + libopenvino-intel-gpu-plugin                    2025.0.0  hac27bb2_0                conda-forge       10MB
  + libopenvino-intel-npu-plugin                    2025.0.0  hac27bb2_0                conda-forge        1MB
  + libopenvino-ir-frontend                         2025.0.0  h3f63f65_0                conda-forge      207kB
  + libopenvino-onnx-frontend                       2025.0.0  h6363af5_0                conda-forge        2MB
  + libopenvino-paddle-frontend                     2025.0.0  h6363af5_0                conda-forge      679kB
  + libopenvino-pytorch-frontend                    2025.0.0  h5888daf_0                conda-forge        1MB
  + libopenvino-tensorflow-frontend                 2025.0.0  h630ec5c_0                conda-forge        1MB
  + libopenvino-tensorflow-lite-frontend            2025.0.0  h5888daf_0                conda-forge      482kB
  + libopus                                            1.6.1  h280c20c_0                conda-forge      325kB
  + libosqp                                            1.0.0  np2py312h1a77e3e_2        conda-forge       86kB
  + libprotobuf                                       5.28.3  h6128344_1                conda-forge        3MB
  + libqdldl                                           0.1.8  h3f2d84a_1                conda-forge       22kB
  + libraw                                            0.22.1  h074291d_0                conda-forge      752kB
  + librsvg                                           2.58.4  h49af25d_2                conda-forge        6MB
  + libscotch                                          7.0.4  h2fe6a88_5                conda-forge      341kB
  + libsndfile                                         1.2.2  hc7d488a_2                conda-forge      356kB
  + libspral                                      2025.05.20  hfabd9d1_1                conda-forge      360kB
  + libsystemd0                                        260.2  h6f4a2f1_1                conda-forge      531kB
  + libtheora                                          1.1.1  h4ab18f5_1006             conda-forge      329kB
  + libudev1                                           260.2  h6f4a2f1_1                conda-forge      173kB
  + libunwind                                          1.8.3  h65a8314_0                conda-forge       76kB
  + liburing                                            2.12  hb700be7_0                conda-forge      128kB
  + libusb                                            1.0.29  h73b1eb8_0                conda-forge       90kB
  + libva                                             2.23.0  he1eb515_0                conda-forge      221kB
  + libvorbis                                          1.3.7  h54a6638_2                conda-forge      286kB
  + libvpx                                            1.14.1  hac33072_0                conda-forge        1MB
  + libzip                                            1.11.2  h6991a6a_0                conda-forge      109kB
  + loguru                                             0.7.3  pyh707e725_0              conda-forge       60kB
  + lz4-c                                              1.9.4  hcb278e6_0                conda-forge      143kB
  + matplotlib-inline                                  0.2.2  pyhd8ed1ab_0              conda-forge       16kB
  + mesalib                                           25.0.5  h57bcd07_2                conda-forge        6MB
  + metis                                              5.1.0  hd0bcaf9_1007             conda-forge        4MB
  + more-itertools                                    11.1.0  pyhcf101f3_0              conda-forge       71kB
  + mpg123                                            1.32.9  hc50e24c_0                conda-forge      491kB
  + multidict                                          6.7.1  py312h8a5da7c_0           conda-forge      100kB
  + multimethod                                         1.12  pyhd8ed1ab_1              conda-forge       16kB
  + mumps-include                                      5.7.3  h82cca05_10               conda-forge       21kB
  + mumps-seq                                          5.7.3  h27a6a8b_0                conda-forge        2MB
  + nlohmann_json                                     3.12.0  h54a6638_1                conda-forge      136kB
  + nlopt                                             2.11.0  np2py312h0f77346_1        conda-forge      459kB
  + occt                                               7.8.1  all_h4c4714a_203          conda-forge       29MB
  + ocl-icd                                            2.3.4  hb03c661_1                conda-forge      110kB
  + ocp                                              7.8.1.2  py312h2ef508c_0           conda-forge       36MB
  + opencl-headers                                2025.06.13  hecca717_0                conda-forge       56kB
  + openexr                                           3.4.12  hba76322_1                conda-forge        1MB
  + openh264                                           2.6.0  hc22cd8d_0                conda-forge      731kB
  + openjph                                           0.28.1  h8d634f6_0                conda-forge      290kB
  + pango                                             1.56.4  hadf4263_0                conda-forge      455kB
  + parso                                              0.8.7  pyhcf101f3_0              conda-forge       82kB
  + path                                              17.1.1  pyhd8ed1ab_0              conda-forge       28kB
  + pexpect                                            4.9.0  pyhd8ed1ab_1              conda-forge       54kB
  + proj                                               9.5.1  h0054346_0                conda-forge        3MB
  + prompt-toolkit                                    3.0.52  pyha770c72_0              conda-forge      274kB
  + propcache                                          0.5.2  py312h8a5da7c_0           conda-forge       52kB
  + ptyprocess                                         0.7.0  pyhd8ed1ab_1              conda-forge       19kB
  + pugixml                                             1.14  h59595ed_0                conda-forge      115kB
  + pulseaudio-client                                   17.0  h9a6aba3_3                conda-forge      751kB
  + pure_eval                                          0.2.3  pyhd8ed1ab_1              conda-forge       17kB
  + pybind11-abi                                           4  hd8ed1ab_3                conda-forge       10kB
  + rapidjson                             1.1.0.post20240409  h3f2d84a_2                conda-forge      156kB
  + runtype                                            0.5.3  pyhd8ed1ab_0              conda-forge       33kB
  + sdl2                                             2.32.56  h54a6638_0                conda-forge      589kB
  + sdl3                                              3.2.24  h68140b3_0                conda-forge        2MB
  + snappy                                             1.2.2  h03e3b7b_1                conda-forge       46kB
  + spirv-tools                                       2025.5  hb700be7_0                conda-forge        3MB
  + sqlite                                            3.53.2  hbc0de68_0                conda-forge      206kB
  + stack_data                                         0.6.3  pyhd8ed1ab_1              conda-forge       27kB
  + svt-av1                                            3.0.2  h5888daf_0                conda-forge        3MB
  + tbb                                             2022.3.0  h8d10470_1                conda-forge      181kB
  + tinyxml2                                          11.0.0  h3f2d84a_0                conda-forge      131kB
  + traitlets                                         5.15.1  pyhcf101f3_0              conda-forge      115kB
  + trame                                             3.13.2  pyhd8ed1ab_0              conda-forge       32kB
  + trame-client                                      3.13.2  pyhd8ed1ab_0              conda-forge      209kB
  + trame-common                                       1.2.4  pyhd8ed1ab_0              conda-forge       31kB
  + trame-components                                   2.5.0  pyhd8ed1ab_0              conda-forge       81kB
  + trame-server                                      3.12.5  pyhd8ed1ab_0              conda-forge       43kB
  + trame-vtk                                        2.11.12  pyh36a8613_0              conda-forge      586kB
  + trame-vuetify                                      3.2.2  pyhd8ed1ab_0              conda-forge        3MB
  + utfcpp                                              4.09  ha770c72_0                conda-forge       14kB
  + vtk                                                9.3.1  osmesa_py312h838d114_110  conda-forge       23kB
  + vtk-base                                           9.3.1  osmesa_py312h6f8e091_110  conda-forge       47MB
  + vtk-io-ffmpeg                                      9.3.1  osmesa_py312h838d114_110  conda-forge       81kB
  + wayland-protocols                                   1.49  hd8ed1ab_0                conda-forge      148kB
  + wcwidth                                            0.8.1  pyhd8ed1ab_0              conda-forge      134kB
  + wslink                                             2.5.7  pyhd8ed1ab_0              conda-forge       37kB
  + x264                                          1!164.3095  h166bdaf_2                conda-forge      898kB
  + x265                                                 3.5  h924138e_3                conda-forge        3MB
  + xorg-libxscrnsaver                                 1.2.4  hb9d3cd8_0                conda-forge       14kB
  + xorg-libxshmfence                                  1.3.3  hb9d3cd8_0                conda-forge       12kB
  + xorg-libxt                                         1.3.1  hb9d3cd8_0                conda-forge      380kB
  + xz                                                 5.8.3  ha02ee65_0                conda-forge       24kB
  + xz-gpl-tools                                       5.8.3  ha02ee65_0                conda-forge       34kB
  + xz-tools                                           5.8.3  hb03c661_0                conda-forge       96kB
  + yarl                                              1.24.2  py312h8a5da7c_0           conda-forge      155kB
  + zlib                                               1.3.2  h25fd6f3_2                conda-forge       96kB

  Remove:
────────────────────────────────────────────────────────────────────────────────────────────────────────────────

  - libllvm22                                         22.1.7  hf7376ad_0                conda-forge     Cached
  - libxml2-16                                        2.15.3  hca6bf5a_0                conda-forge     Cached
  - matplotlib                                        3.10.9  py312h7900ff3_0           conda-forge     Cached
  - pyside6                                           6.11.1  py312h50ac2ff_1           conda-forge     Cached
  - qt6-main                                          6.11.1  pl5321h16c4a6b_1          conda-forge     Cached

  Change:
────────────────────────────────────────────────────────────────────────────────────────────────────────────────

  - cairo                                             1.18.4  he90730b_1                conda-forge     Cached
  + cairo                                             1.18.4  h3394656_0                conda-forge      978kB
  - libxslt                                           1.1.43  h711ed8c_1                conda-forge     Cached
  + libxslt                                           1.1.43  h7a3aeb2_0                conda-forge      244kB

  Downgrade:
────────────────────────────────────────────────────────────────────────────────────────────────────────────────

  - double-conversion                                  3.4.0  hecca717_0                conda-forge     Cached
  + double-conversion                                  3.3.1  h5888daf_0                conda-forge       70kB
  - h5py                                              3.16.0  nompi_py312ha829cd9_102   conda-forge     Cached
  + h5py                                              3.12.1  nompi_py312hd203070_103   conda-forge        1MB
  - harfbuzz                                          14.2.1  h6083320_0                conda-forge     Cached
  + harfbuzz                                          12.2.0  h15599e2_0                conda-forge        2MB
  - hdf5                                               2.1.0  nompi_h735b18d_107        conda-forge     Cached
  + hdf5                                              1.14.4  nompi_h2d575fe_105        conda-forge        4MB
  - icu                                                 78.3  h33c6efd_0                conda-forge     Cached
  + icu                                                 75.1  he02047a_0                conda-forge       12MB
  - libclang13                                        22.1.7  default_h746c552_1        conda-forge     Cached
  + libclang13                                        21.1.0  default_h746c552_1        conda-forge       12MB
  - libpq                                               18.4  hd5a49e9_0                conda-forge     Cached
  + libpq                                              16.14  h3c8a8f5_0                conda-forge        3MB
  - libxkbcommon                                      1.13.2  hca5e8e5_0                conda-forge     Cached
  + libxkbcommon                                      1.11.0  he8b52b9_0                conda-forge      791kB
  - libxml2                                           2.15.3  h49c6c72_0                conda-forge     Cached
  + libxml2                                           2.13.9  h04c0eec_0                conda-forge      697kB

  Summary:

  Install: 150 packages
  Remove: 5 packages
  Change: 2 packages
  Downgrade: 9 packages

  Total download: 370MB

────────────────────────────────────────────────────────────────────────────────────────────────────────────────



Transaction starting
Unlinking matplotlib-3.10.9-py312h7900ff3_0
Unlinking pyside6-6.11.1-py312h50ac2ff_1
Unlinking qt6-main-6.11.1-pl5321h16c4a6b_1
Unlinking libxml2-16-2.15.3-hca6bf5a_0
Unlinking hdf5-2.1.0-nompi_h735b18d_107
Unlinking icu-78.3-h33c6efd_0
Unlinking libxml2-2.15.3-h49c6c72_0
Unlinking libclang13-22.1.7-default_h746c552_1
Unlinking libllvm22-22.1.7-hf7376ad_0
Unlinking h5py-3.16.0-nompi_py312ha829cd9_102
Unlinking libxkbcommon-1.13.2-hca5e8e5_0
Unlinking libxslt-1.1.43-h711ed8c_1
Unlinking libpq-18.4-hd5a49e9_0
Unlinking double-conversion-3.4.0-hecca717_0
Unlinking cairo-1.18.4-he90730b_1
Unlinking harfbuzz-14.2.1-h6083320_0
Linking hdf5-1.14.4-nompi_h2d575fe_105
Linking tinyxml2-11.0.0-h3f2d84a_0
Linking libgfortran-ng-15.2.0-h69a702a_19
Linking ezdxf-1.4.2-py312hf890105_1
Linking nlopt-2.11.0-np2py312h0f77346_1
Linking pugixml-1.14-h59595ed_0
Linking imath-3.2.2-hde8ca8f_0
Linking rapidjson-1.1.0.post20240409-h3f2d84a_2
Linking xorg-libxt-1.3.1-hb9d3cd8_0
Linking libogg-1.3.5-hd0c01bc_1
Linking libglu-9.0.3-h5888daf_1
Linking ampl-asl-1.0.0-h5888daf_2
Linking jxrlib-1.1-hd590300_3
Linking eigen-abi-3.4.0.100-h3bcb7cf_2
Linking aom-3.9.1-hac33072_0
Linking dav1d-1.2.1-hd590300_0
Linking libvpx-1.14.1-hac33072_0
Linking openh264-2.6.0-hc22cd8d_0
Linking svt-av1-3.0.2-h5888daf_0
Linking libabseil-20240722.0-cxx17_hbbce691_4
Linking snappy-1.2.2-h03e3b7b_1
Linking level-zero-1.29.0-hb700be7_0
Linking gmp-6.3.0-hac33072_2
Linking libopus-1.6.1-h280c20c_0
Linking lame-3.100-h166bdaf_1003
Linking x264-1!164.3095-h166bdaf_2
Linking x265-3.5-h924138e_3
Linking gl2ps-1.4.2-h36e74d4_2
Linking jsoncpp-1.9.6-hf42df4d_1
Linking hdf4-4.2.15-h2a13503_7
Linking libzip-1.11.2-h6991a6a_0
Linking zlib-1.3.2-h25fd6f3_2
Linking lz4-c-1.9.4-hcb278e6_0
Linking xorg-libxshmfence-1.3.3-hb9d3cd8_0
Linking nlohmann_json-3.12.0-h54a6638_1
Linking utfcpp-4.09-ha770c72_0
Linking libunwind-1.8.3-h65a8314_0
Linking liburing-2.12-hb700be7_0
Linking xorg-libxscrnsaver-1.2.4-hb9d3cd8_0
Linking mpg123-1.32.9-hc50e24c_0
Linking libcap-2.78-hd0affe5_0
Linking sqlite-3.53.2-hbc0de68_0
Linking openjph-0.28.1-h8d634f6_0
Linking spirv-tools-2025.5-hb700be7_0
Linking gdk-pixbuf-2.44.6-h2b0a6b4_0

Linking fribidi-1.0.16-hb03c661_0
Linking frozenlist-1.8.0-py312h447239a_0
warning  libmamba [frozenlist-1.8.0-py312h447239a_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/INSTALLER
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/METADATA
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/RECORD
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/WHEEL
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/frozenlist-1.8.0.dist-info/top_level.txt
    - lib/python3.12/site-packages/frozenlist/__init__.py
    - lib/python3.12/site-packages/frozenlist/__init__.pyi
    - lib/python3.12/site-packages/frozenlist/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/frozenlist/_frozenlist.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/frozenlist/_frozenlist.pyx
    - lib/python3.12/site-packages/frozenlist/py.typed
Linking multidict-6.7.1-py312h8a5da7c_0
warning  libmamba [multidict-6.7.1-py312h8a5da7c_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/INSTALLER
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/METADATA
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/RECORD
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/WHEEL
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/multidict-6.7.1.dist-info/top_level.txt
    - lib/python3.12/site-packages/multidict/__init__.py
    - lib/python3.12/site-packages/multidict/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/multidict/__pycache__/_abc.cpython-312.pyc
    - lib/python3.12/site-packages/multidict/__pycache__/_compat.cpython-312.pyc
    - lib/python3.12/site-packages/multidict/__pycache__/_multidict_py.cpython-312.pyc
    - lib/python3.12/site-packages/multidict/_abc.py
    - lib/python3.12/site-packages/multidict/_compat.py
    - lib/python3.12/site-packages/multidict/_multidict.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/multidict/_multidict_py.py
    - lib/python3.12/site-packages/multidict/py.typed
Linking propcache-0.5.2-py312h8a5da7c_0
warning  libmamba [propcache-0.5.2-py312h8a5da7c_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/INSTALLER
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/METADATA
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/RECORD
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/WHEEL
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/licenses/NOTICE
    - lib/python3.12/site-packages/propcache-0.5.2.dist-info/top_level.txt
    - lib/python3.12/site-packages/propcache/__init__.py
    - lib/python3.12/site-packages/propcache/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/propcache/__pycache__/_helpers.cpython-312.pyc
    - lib/python3.12/site-packages/propcache/__pycache__/_helpers_py.cpython-312.pyc
    - lib/python3.12/site-packages/propcache/__pycache__/api.cpython-312.pyc
    - lib/python3.12/site-packages/propcache/_helpers.py
    - lib/python3.12/site-packages/propcache/_helpers_c.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/propcache/_helpers_c.pyx
    - lib/python3.12/site-packages/propcache/_helpers_py.py
    - lib/python3.12/site-packages/propcache/api.py
    - lib/python3.12/site-packages/propcache/py.typed
Linking liblzma-devel-5.8.3-hb03c661_0
Linking xz-gpl-tools-5.8.3-ha02ee65_0
Linking xz-tools-5.8.3-hb03c661_0
Linking metis-5.1.0-hd0bcaf9_1007
Linking mumps-include-5.7.3-h82cca05_10
Linking opencl-headers-2025.06.13-hecca717_0
Linking libqdldl-0.1.8-h3f2d84a_1
Linking icu-75.1-he02047a_0
Linking libxml2-2.13.9-h04c0eec_0
Linking libllvm21-21.1.0-hecd9e04_0
Linking libclang13-21.1.0-default_h746c552_1
Linking h5py-3.12.1-nompi_py312hd203070_103
Linking libflac-1.5.0-he200343_1
Linking libvorbis-1.3.7-h54a6638_2
Linking freeglut-3.2.2-h215f996_4
Linking libprotobuf-5.28.3-h6128344_1
Linking blosc-1.21.6-hef167b5_0
Linking libudev1-260.2-h6f4a2f1_1
Linking libsystemd0-260.2-h6f4a2f1_1
Linking proj-9.5.1-h0054346_0
Linking openexr-3.4.12-hba76322_1
Linking yarl-1.24.2-py312h8a5da7c_0
warning  libmamba [yarl-1.24.2-py312h8a5da7c_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/INSTALLER
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/METADATA
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/RECORD
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/WHEEL
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/licenses/NOTICE
    - lib/python3.12/site-packages/yarl-1.24.2.dist-info/top_level.txt
    - lib/python3.12/site-packages/yarl/__init__.py
    - lib/python3.12/site-packages/yarl/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_parse.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_path.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_query.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_quoters.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_quoting.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_quoting_py.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/__pycache__/_url.cpython-312.pyc
    - lib/python3.12/site-packages/yarl/_parse.py
    - lib/python3.12/site-packages/yarl/_path.py
    - lib/python3.12/site-packages/yarl/_query.py
    - lib/python3.12/site-packages/yarl/_quoters.py
    - lib/python3.12/site-packages/yarl/_quoting.py
    - lib/python3.12/site-packages/yarl/_quoting_c.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/yarl/_quoting_c.pyx
    - lib/python3.12/site-packages/yarl/_quoting_py.py
    - lib/python3.12/site-packages/yarl/_url.py
    - lib/python3.12/site-packages/yarl/py.typed
Linking xz-5.8.3-ha02ee65_0
Linking ocl-icd-2.3.4-hb03c661_1
Linking libosqp-1.0.0-np2py312h1a77e3e_2
Linking libxkbcommon-1.11.0-he8b52b9_0
Linking libsndfile-1.2.2-hc7d488a_2
Linking libtheora-1.1.1-h4ab18f5_1006
Linking jasper-4.2.9-h1588d4d_1
Linking libusb-1.0.29-h73b1eb8_0
Linking libscotch-7.0.4-h2fe6a88_5
Linking libxslt-1.1.43-h7a3aeb2_0
Linking pulseaudio-client-17.0-h9a6aba3_3
Linking libraw-0.22.1-h074291d_0
Linking mumps-seq-5.7.3-h27a6a8b_0
Linking libhwloc-2.12.1-default_h3d81e11_1000
Linking libllvm20-20.1.8-hecd9e04_0
Linking libnetcdf-4.9.2-nompi_h5ddbaa4_116
Linking libboost-1.86.0-hed09d94_4
Linking libpq-16.14-h3c8a8f5_0
Linking double-conversion-3.3.1-h5888daf_0
Linking cairo-1.18.4-h3394656_0
Linking sdl3-3.2.24-h68140b3_0
Linking freeimage-3.18.0-hd1b7436_25
Linking libspral-2025.05.20-hfabd9d1_1
Linking tbb-2022.3.0-h8d10470_1
Linking mesalib-25.0.5-h57bcd07_2
warning  libmamba [mesalib-25.0.5-h57bcd07_2] The following files were already present in the environment:
    - include/GL/gl.h
    - include/GL/glcorearb.h
    - include/GL/glext.h
    - include/KHR/khrplatform.h
Linking harfbuzz-12.2.0-h15599e2_0
Linking sdl2-2.32.56-h54a6638_0
Linking ipopt-3.14.19-h0804adb_0
Linking libopenvino-2025.0.0-hac27bb2_0
Linking pango-1.56.4-hadf4263_0
Linking libass-0.17.3-hba53ac1_1
Linking libopenvino-tensorflow-lite-frontend-2025.0.0-h5888daf_0
Linking libopenvino-tensorflow-frontend-2025.0.0-h630ec5c_0
Linking libopenvino-pytorch-frontend-2025.0.0-h5888daf_0
Linking libopenvino-paddle-frontend-2025.0.0-h6363af5_0
Linking libopenvino-onnx-frontend-2025.0.0-h6363af5_0
Linking libopenvino-ir-frontend-2025.0.0-h3f63f65_0
Linking libopenvino-intel-npu-plugin-2025.0.0-hac27bb2_0
Linking libopenvino-intel-gpu-plugin-2025.0.0-hac27bb2_0
Linking libopenvino-intel-cpu-plugin-2025.0.0-hac27bb2_0
Linking libopenvino-hetero-plugin-2025.0.0-h3f63f65_0
Linking libopenvino-auto-plugin-2025.0.0-h4d9b6c2_0
Linking libopenvino-auto-batch-plugin-2025.0.0-h4d9b6c2_0
Linking librsvg-2.58.4-h49af25d_2

Linking path-17.1.1-pyhd8ed1ab_0
Linking ipython_pygments_lexers-1.1.1-pyhd8ed1ab_0
Linking multimethod-1.12-pyhd8ed1ab_1
Linking runtype-0.5.3-pyhd8ed1ab_0
Linking pybind11-abi-4-hd8ed1ab_3
Linking trame-common-1.2.4-pyhd8ed1ab_0
Linking decorator-5.3.1-pyhd8ed1ab_0
Linking traitlets-5.15.1-pyhcf101f3_0
Linking _x86_64-microarch-level-3-3_x86_64_v3
Linking more-itertools-11.1.0-pyhcf101f3_0
Linking asttokens-3.0.1-pyhd8ed1ab_0
Linking executing-2.2.1-pyhd8ed1ab_0
Linking pure_eval-0.2.3-pyhd8ed1ab_1
Linking wcwidth-0.8.1-pyhd8ed1ab_0
warning  libmamba [wcwidth-0.8.1-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/wcwidth-0.8.1.dist-info/INSTALLER
    - lib/python3.12/site-packages/wcwidth-0.8.1.dist-info/METADATA
    - lib/python3.12/site-packages/wcwidth-0.8.1.dist-info/RECORD
    - lib/python3.12/site-packages/wcwidth-0.8.1.dist-info/WHEEL
    - lib/python3.12/site-packages/wcwidth-0.8.1.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/wcwidth/__init__.py
    - lib/python3.12/site-packages/wcwidth/_clip.py
    - lib/python3.12/site-packages/wcwidth/_constants.py
    - lib/python3.12/site-packages/wcwidth/_wcswidth.py
    - lib/python3.12/site-packages/wcwidth/_wcwidth.py
    - lib/python3.12/site-packages/wcwidth/_width.py
    - lib/python3.12/site-packages/wcwidth/align.py
    - lib/python3.12/site-packages/wcwidth/bisearch.py
    - lib/python3.12/site-packages/wcwidth/control_codes.py
    - lib/python3.12/site-packages/wcwidth/escape_sequences.py
    - lib/python3.12/site-packages/wcwidth/grapheme.py
    - lib/python3.12/site-packages/wcwidth/hyperlink.py
    - lib/python3.12/site-packages/wcwidth/py.typed
    - lib/python3.12/site-packages/wcwidth/sgr_state.py
    - lib/python3.12/site-packages/wcwidth/table_ambiguous.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/__init__.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_27e0693f.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_3d4826b8.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_45d92e98.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_4cdf59ce.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_50bf0759.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_529fbb4a.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_5bfac390.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_813fee16.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_8589765c.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_8f94b404.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_970dbe10.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_c0a2cdbf.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_c2157f7e.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_c3db41c0.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_da9ceb0a.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_e08bd75e.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_e22030f3.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_fcc05a0f.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_known_fd9d4c44.py
    - lib/python3.12/site-packages/wcwidth/table_grapheme_overrides/_registry.py
    - lib/python3.12/site-packages/wcwidth/table_mc.py
    - lib/python3.12/site-packages/wcwidth/table_overrides.py
    - lib/python3.12/site-packages/wcwidth/table_term_programs.py
    - lib/python3.12/site-packages/wcwidth/table_vs15.py
    - lib/python3.12/site-packages/wcwidth/table_vs16.py
    - lib/python3.12/site-packages/wcwidth/table_wide.py
    - lib/python3.12/site-packages/wcwidth/table_zero.py
    - lib/python3.12/site-packages/wcwidth/text_sizing.py
    - lib/python3.12/site-packages/wcwidth/textwrap.py
    - lib/python3.12/site-packages/wcwidth/unicode_versions.py
    - lib/python3.12/site-packages/wcwidth/wcwidth.py
Linking ptyprocess-0.7.0-pyhd8ed1ab_1
Linking parso-0.8.7-pyhcf101f3_0
Linking loguru-0.7.3-pyh707e725_0
Linking wayland-protocols-1.49-hd8ed1ab_0
Linking aiohappyeyeballs-2.6.2-pyhd8ed1ab_0
warning  libmamba [aiohappyeyeballs-2.6.2-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/aiohappyeyeballs-2.6.2.dist-info/INSTALLER
    - lib/python3.12/site-packages/aiohappyeyeballs-2.6.2.dist-info/METADATA
    - lib/python3.12/site-packages/aiohappyeyeballs-2.6.2.dist-info/RECORD
    - lib/python3.12/site-packages/aiohappyeyeballs-2.6.2.dist-info/WHEEL
    - lib/python3.12/site-packages/aiohappyeyeballs-2.6.2.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/aiohappyeyeballs/__init__.py
    - lib/python3.12/site-packages/aiohappyeyeballs/_staggered.py
    - lib/python3.12/site-packages/aiohappyeyeballs/impl.py
    - lib/python3.12/site-packages/aiohappyeyeballs/py.typed
    - lib/python3.12/site-packages/aiohappyeyeballs/types.py
    - lib/python3.12/site-packages/aiohappyeyeballs/utils.py
Linking attrs-26.1.0-pyhcf101f3_0
warning  libmamba [attrs-26.1.0-pyhcf101f3_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/attr/__init__.py
    - lib/python3.12/site-packages/attr/__init__.pyi
    - lib/python3.12/site-packages/attr/_cmp.py
    - lib/python3.12/site-packages/attr/_cmp.pyi
    - lib/python3.12/site-packages/attr/_compat.py
    - lib/python3.12/site-packages/attr/_config.py
    - lib/python3.12/site-packages/attr/_funcs.py
    - lib/python3.12/site-packages/attr/_make.py
    - lib/python3.12/site-packages/attr/_next_gen.py
    - lib/python3.12/site-packages/attr/_typing_compat.pyi
    - lib/python3.12/site-packages/attr/_version_info.py
    - lib/python3.12/site-packages/attr/_version_info.pyi
    - lib/python3.12/site-packages/attr/converters.py
    - lib/python3.12/site-packages/attr/converters.pyi
    - lib/python3.12/site-packages/attr/exceptions.py
    - lib/python3.12/site-packages/attr/exceptions.pyi
    - lib/python3.12/site-packages/attr/filters.py
    - lib/python3.12/site-packages/attr/filters.pyi
    - lib/python3.12/site-packages/attr/py.typed
    - lib/python3.12/site-packages/attr/setters.py
    - lib/python3.12/site-packages/attr/setters.pyi
    - lib/python3.12/site-packages/attr/validators.py
    - lib/python3.12/site-packages/attr/validators.pyi
    - lib/python3.12/site-packages/attrs/__init__.py
    - lib/python3.12/site-packages/attrs/__init__.pyi
    - lib/python3.12/site-packages/attrs/converters.py
    - lib/python3.12/site-packages/attrs/exceptions.py
    - lib/python3.12/site-packages/attrs/filters.py
    - lib/python3.12/site-packages/attrs/py.typed
    - lib/python3.12/site-packages/attrs/setters.py
    - lib/python3.12/site-packages/attrs/validators.py
    - lib/python3.12/site-packages/attrs-26.1.0.dist-info/INSTALLER
    - lib/python3.12/site-packages/attrs-26.1.0.dist-info/METADATA
    - lib/python3.12/site-packages/attrs-26.1.0.dist-info/RECORD
    - lib/python3.12/site-packages/attrs-26.1.0.dist-info/WHEEL
    - lib/python3.12/site-packages/attrs-26.1.0.dist-info/licenses/LICENSE
Linking aiosignal-1.4.0-pyhd8ed1ab_0
warning  libmamba [aiosignal-1.4.0-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/INSTALLER
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/METADATA
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/RECORD
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/WHEEL
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/aiosignal-1.4.0.dist-info/top_level.txt
    - lib/python3.12/site-packages/aiosignal/__init__.py
    - lib/python3.12/site-packages/aiosignal/py.typed
Linking trame-client-3.13.2-pyhd8ed1ab_0
Linking matplotlib-inline-0.2.2-pyhd8ed1ab_0
Linking stack_data-0.6.3-pyhd8ed1ab_1
Linking prompt-toolkit-3.0.52-pyha770c72_0
Linking pexpect-4.9.0-pyhd8ed1ab_1
Linking jedi-0.19.2-pyhd8ed1ab_1
Linking trame-vuetify-3.2.2-pyhd8ed1ab_0
warning  libmamba [trame-vuetify-3.2.2-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/trame/modules/__init__.py
    - lib/python3.12/site-packages/trame/ui/__init__.py
Linking trame-vtk-2.11.12-pyh36a8613_0
warning  libmamba [trame-vtk-2.11.12-pyh36a8613_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/trame/__init__.py
    - lib/python3.12/site-packages/trame/modules/__init__.py
    - lib/python3.12/site-packages/trame/widgets/__init__.py
Linking trame-components-2.5.0-pyhd8ed1ab_0
warning  libmamba [trame-components-2.5.0-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/trame/__init__.py
    - lib/python3.12/site-packages/trame/modules/__init__.py
    - lib/python3.12/site-packages/trame/widgets/__init__.py
Linking ipython-9.14.1-pyh53cf698_0
Linking libblasfeo-0.1.4.2-had105d5_300
Linking libva-2.23.0-he1eb515_0
Linking aiohttp-3.14.1-py312h5d8c7f2_0
warning  libmamba [aiohttp-3.14.1-py312h5d8c7f2_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/INSTALLER
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/METADATA
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/RECORD
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/WHEEL
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/licenses/LICENSE.txt
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/licenses/vendor/llhttp/LICENSE
    - lib/python3.12/site-packages/aiohttp-3.14.1.dist-info/top_level.txt
    - lib/python3.12/site-packages/aiohttp/.hash/_cparser.pxd.hash
    - lib/python3.12/site-packages/aiohttp/.hash/_find_header.pxd.hash
    - lib/python3.12/site-packages/aiohttp/.hash/_http_parser.pyx.hash
    - lib/python3.12/site-packages/aiohttp/.hash/_http_writer.pyx.hash
    - lib/python3.12/site-packages/aiohttp/.hash/hdrs.py.hash
    - lib/python3.12/site-packages/aiohttp/__init__.py
    - lib/python3.12/site-packages/aiohttp/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/_cookie_helpers.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/abc.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/base_protocol.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_exceptions.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_middleware_digest_auth.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_middlewares.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_proto.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_reqrep.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/client_ws.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/compression_utils.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/connector.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/cookiejar.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/formdata.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/hdrs.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/helpers.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/http.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/http_exceptions.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/http_parser.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/http_websocket.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/http_writer.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/log.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/multipart.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/payload.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/payload_streamer.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/pytest_plugin.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/resolver.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/streams.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/tcp_helpers.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/test_utils.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/tracing.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/typedefs.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_app.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_exceptions.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_fileresponse.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_log.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_middlewares.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_protocol.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_request.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_response.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_routedef.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_runner.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_server.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_urldispatcher.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/web_ws.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/__pycache__/worker.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_cookie_helpers.py
    - lib/python3.12/site-packages/aiohttp/_cparser.pxd
    - lib/python3.12/site-packages/aiohttp/_find_header.pxd
    - lib/python3.12/site-packages/aiohttp/_headers.pxi
    - lib/python3.12/site-packages/aiohttp/_http_parser.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/aiohttp/_http_parser.pyx
    - lib/python3.12/site-packages/aiohttp/_http_writer.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/aiohttp/_http_writer.pyx
    - lib/python3.12/site-packages/aiohttp/_websocket/.hash/mask.pxd.hash
    - lib/python3.12/site-packages/aiohttp/_websocket/.hash/mask.pyx.hash
    - lib/python3.12/site-packages/aiohttp/_websocket/.hash/reader_c.pxd.hash
    - lib/python3.12/site-packages/aiohttp/_websocket/__init__.py
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/__init__.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/helpers.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/models.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/reader.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/reader_c.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/reader_py.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/__pycache__/writer.cpython-312.pyc
    - lib/python3.12/site-packages/aiohttp/_websocket/helpers.py
    - lib/python3.12/site-packages/aiohttp/_websocket/mask.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/aiohttp/_websocket/mask.pxd
    - lib/python3.12/site-packages/aiohttp/_websocket/mask.pyx
    - lib/python3.12/site-packages/aiohttp/_websocket/models.py
    - lib/python3.12/site-packages/aiohttp/_websocket/reader.py
    - lib/python3.12/site-packages/aiohttp/_websocket/reader_c.cpython-312-x86_64-linux-gnu.so
    - lib/python3.12/site-packages/aiohttp/_websocket/reader_c.pxd
    - lib/python3.12/site-packages/aiohttp/_websocket/reader_c.py
    - lib/python3.12/site-packages/aiohttp/_websocket/reader_py.py
    - lib/python3.12/site-packages/aiohttp/_websocket/writer.py
    - lib/python3.12/site-packages/aiohttp/abc.py
    - lib/python3.12/site-packages/aiohttp/base_protocol.py
    - lib/python3.12/site-packages/aiohttp/client.py
    - lib/python3.12/site-packages/aiohttp/client_exceptions.py
    - lib/python3.12/site-packages/aiohttp/client_middleware_digest_auth.py
    - lib/python3.12/site-packages/aiohttp/client_middlewares.py
    - lib/python3.12/site-packages/aiohttp/client_proto.py
    - lib/python3.12/site-packages/aiohttp/client_reqrep.py
    - lib/python3.12/site-packages/aiohttp/client_ws.py
    - lib/python3.12/site-packages/aiohttp/compression_utils.py
    - lib/python3.12/site-packages/aiohttp/connector.py
    - lib/python3.12/site-packages/aiohttp/cookiejar.py
    - lib/python3.12/site-packages/aiohttp/formdata.py
    - lib/python3.12/site-packages/aiohttp/hdrs.py
    - lib/python3.12/site-packages/aiohttp/helpers.py
    - lib/python3.12/site-packages/aiohttp/http.py
    - lib/python3.12/site-packages/aiohttp/http_exceptions.py
    - lib/python3.12/site-packages/aiohttp/http_parser.py
    - lib/python3.12/site-packages/aiohttp/http_websocket.py
    - lib/python3.12/site-packages/aiohttp/http_writer.py
    - lib/python3.12/site-packages/aiohttp/log.py
    - lib/python3.12/site-packages/aiohttp/multipart.py
    - lib/python3.12/site-packages/aiohttp/payload.py
    - lib/python3.12/site-packages/aiohttp/payload_streamer.py
    - lib/python3.12/site-packages/aiohttp/py.typed
    - lib/python3.12/site-packages/aiohttp/pytest_plugin.py
    - lib/python3.12/site-packages/aiohttp/resolver.py
    - lib/python3.12/site-packages/aiohttp/streams.py
    - lib/python3.12/site-packages/aiohttp/tcp_helpers.py
    - lib/python3.12/site-packages/aiohttp/test_utils.py
    - lib/python3.12/site-packages/aiohttp/tracing.py
    - lib/python3.12/site-packages/aiohttp/typedefs.py
    - lib/python3.12/site-packages/aiohttp/web.py
    - lib/python3.12/site-packages/aiohttp/web_app.py
    - lib/python3.12/site-packages/aiohttp/web_exceptions.py
    - lib/python3.12/site-packages/aiohttp/web_fileresponse.py
    - lib/python3.12/site-packages/aiohttp/web_log.py
    - lib/python3.12/site-packages/aiohttp/web_middlewares.py
    - lib/python3.12/site-packages/aiohttp/web_protocol.py
    - lib/python3.12/site-packages/aiohttp/web_request.py
    - lib/python3.12/site-packages/aiohttp/web_response.py
    - lib/python3.12/site-packages/aiohttp/web_routedef.py
    - lib/python3.12/site-packages/aiohttp/web_runner.py
    - lib/python3.12/site-packages/aiohttp/web_server.py
    - lib/python3.12/site-packages/aiohttp/web_urldispatcher.py
    - lib/python3.12/site-packages/aiohttp/web_ws.py
    - lib/python3.12/site-packages/aiohttp/worker.py
Linking libfatrop-0.0.4-h5888daf_1
Linking ffmpeg-7.1.1-gpl_h127656b_906
Linking casadi-3.7.2-py312h4238392_1
Linking wslink-2.5.7-pyhd8ed1ab_0
Linking trame-server-3.12.5-pyhd8ed1ab_0
Linking trame-3.13.2-pyhd8ed1ab_0
warning  libmamba [trame-3.13.2-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/trame/__init__.py
    - lib/python3.12/site-packages/trame/modules/__init__.py
    - lib/python3.12/site-packages/trame/tools/__init__.py
    - lib/python3.12/site-packages/trame/ui/__init__.py
    - lib/python3.12/site-packages/trame/widgets/__init__.py
Linking vtk-base-9.3.1-osmesa_py312h6f8e091_110
Linking vtk-io-ffmpeg-9.3.1-osmesa_py312h838d114_110
Linking vtk-9.3.1-osmesa_py312h838d114_110
Linking occt-7.8.1-all_h4c4714a_203
Linking ocp-7.8.1.2-py312h2ef508c_0
Linking cadquery-2.7.0-pyhcf101f3_0

Transaction finished

- [2026-06-15T19:10:45-04:00] EXIT_STATUS: 0
- [2026-06-15T19:10:45-04:00] COMMAND: mamba install -y -c conda-forge openmc
conda-forge/linux-64                                        Using cache
conda-forge/noarch                                          Using cache

Pinned packages:

  - python=3.12


Transaction

  Prefix: /home/craig/miniforge/envs/mini-tokamak

  Updating specs:

   - openmc


  Package            Version  Build                                Channel           Size
───────────────────────────────────────────────────────────────────────────────────────────
  Install:
───────────────────────────────────────────────────────────────────────────────────────────

  + dagmc              3.2.4  mpi_openmpi_doubledown_h79c499a_2    conda-forge       11MB
  + eigen              3.4.0  h54a6638_2                           conda-forge        1MB
  + embree             4.4.1  hcc6314f_3                           conda-forge       14MB
  + endf              0.1.12  py312h1289d80_0                      conda-forge      171kB
  + future             1.0.0  pyhd8ed1ab_2                         conda-forge      365kB
  + libcbor           0.10.2  hcb278e6_0                           conda-forge       43kB
  + libevent          2.1.12  hf998b51_1                           conda-forge      427kB
  + libfabric          2.5.1  ha770c72_1                           conda-forge       15kB
  + libfabric1         2.5.1  h6b3ec72_1                           conda-forge      711kB
  + libfido2          1.17.0  h8c08ba8_0                           conda-forge      288kB
  + libnl             3.11.0  hb9d3cd8_0                           conda-forge      741kB
  + libpmix            5.0.8  h4bd6b51_2                           conda-forge      731kB
  + libpnetcdf        1.14.0  mpi_openmpi_h521bef2_0               conda-forge        2MB
  + lxml               6.0.2  py312h70dad80_0                      conda-forge        2MB
  + mcpl               2.2.8  pyhd9e7ec7_0                         conda-forge       12kB
  + mcpl-core          2.2.8  pyh8af1aa0_0                         conda-forge       15kB
  + mcpl-lib           2.2.8  h4dac143_0                           conda-forge      120kB
  + mcpl-python        2.2.8  pyh8af1aa0_0                         conda-forge       35kB
  + moab               5.5.1  mpi_openmpi_tempest_py312hc5bf31d_5  conda-forge        7MB
  + mpi                1.0.1  openmpi                              conda-forge        7kB
  + mpi4py             4.1.2  py312hd140a38_100                    conda-forge      890kB
  + ncrystal           4.4.4  pyh2c5f401_0                         conda-forge       21kB
  + ncrystal-core      4.4.4  pyhf450f58_0                         conda-forge       17kB
  + ncrystal-lib       4.4.4  h7033f15_0                           conda-forge        2MB
  + ncrystal-python    4.4.4  pyhf450f58_0                         conda-forge      252kB
  + njoy2016         2016.78  py312hd9fe3b9_1                      conda-forge        1MB
  + openmc            0.15.3  dagmc_mpi_openmpi_py312h2fffaed_100  conda-forge        7MB
  + openmpi            5.0.8  h2fe1745_110                         conda-forge        4MB
  + openssh           10.2p1  hcbcca31_1                           conda-forge        1MB
  + perl              5.32.1  7_hd590300_perl5                     conda-forge       13MB
  + rdma-core           63.0  h192683f_1                           conda-forge        1MB
  + tempest-remap      2.2.0  heeae502_5                           conda-forge      988kB
  + ucc                1.6.0  hb729f83_1                           conda-forge        9MB
  + ucx               1.19.1  h567e125_0                           conda-forge        8MB
  + uncertainties      3.2.3  pyhd8ed1ab_0                         conda-forge       57kB
  + zoltan             3.901  mpi_openmpi_hdd8c722_3               conda-forge      518kB

  Change:
───────────────────────────────────────────────────────────────────────────────────────────

  - libnetcdf          4.9.2  nompi_h5ddbaa4_116                   conda-forge     Cached
  + libnetcdf          4.9.2  mpi_openmpi_h5fda6ee_16              conda-forge      846kB
  - vtk                9.3.1  osmesa_py312h838d114_110             conda-forge     Cached
  + vtk                9.3.1  osmesa_py312h838d114_112             conda-forge       23kB
  - vtk-base           9.3.1  osmesa_py312h6f8e091_110             conda-forge     Cached
  + vtk-base           9.3.1  osmesa_py312h5592cea_112             conda-forge       47MB
  - vtk-io-ffmpeg      9.3.1  osmesa_py312h838d114_110             conda-forge     Cached
  + vtk-io-ffmpeg      9.3.1  osmesa_py312h838d114_112             conda-forge       82kB

  Upgrade:
───────────────────────────────────────────────────────────────────────────────────────────

  - h5py              3.12.1  nompi_py312hd203070_103              conda-forge     Cached
  + h5py              3.13.0  mpi_openmpi_py312h6b5221c_0          conda-forge        1MB

  Downgrade:
───────────────────────────────────────────────────────────────────────────────────────────

  - hdf5              1.14.4  nompi_h2d575fe_105                   conda-forge     Cached
  + hdf5              1.14.3  mpi_openmpi_h39ae36c_9               conda-forge        4MB

  Summary:

  Install: 36 packages
  Change: 4 packages
  Upgrade: 1 packages
  Downgrade: 1 packages

  Total download: 142MB

───────────────────────────────────────────────────────────────────────────────────────────



Transaction starting
Unlinking hdf5-1.14.4-nompi_h2d575fe_105
Unlinking h5py-3.12.1-nompi_py312hd203070_103
Unlinking libnetcdf-4.9.2-nompi_h5ddbaa4_116
Unlinking vtk-base-9.3.1-osmesa_py312h6f8e091_110
Unlinking vtk-io-ffmpeg-9.3.1-osmesa_py312h838d114_110
Unlinking vtk-9.3.1-osmesa_py312h838d114_110
Linking libcbor-0.10.2-hcb278e6_0
Linking lxml-6.0.2-py312h70dad80_0
Linking njoy2016-2016.78-py312hd9fe3b9_1
Linking libnl-3.11.0-hb9d3cd8_0
Linking libevent-2.1.12-hf998b51_1
Linking eigen-3.4.0-h54a6638_2
Linking embree-4.4.1-hcc6314f_3
Linking ncrystal-lib-4.4.4-h7033f15_0
Linking mcpl-lib-2.2.8-h4dac143_0
Linking perl-5.32.1-7_hd590300_perl5
Linking libfido2-1.17.0-h8c08ba8_0
Linking rdma-core-63.0-h192683f_1
Linking libpmix-5.0.8-h4bd6b51_2
Linking openssh-10.2p1-hcbcca31_1
Linking ucx-1.19.1-h567e125_0

To enable CUDA support, UCX requires the CUDA Runtime library (libcudart).
The library can be installed with the appropriate command below:

* For CUDA 12, run:    conda install cuda-cudart cuda-version=12
* For CUDA 13, run:    conda install cuda-cudart cuda-version=13

If any of the packages you requested use CUDA then CUDA should already
have been installed for you.


Linking libfabric1-2.5.1-h6b3ec72_1
Linking ucc-1.6.0-hb729f83_1
setting libfabric environment variables for conda-build
FI_PROVIDER=tcp

To enable CUDA support, UCX requires the CUDA Runtime library (libcudart).
The library can be installed with the appropriate command below:

* For CUDA 12, run:    conda install cuda-cudart cuda-version=12
* For CUDA 13, run:    conda install cuda-cudart cuda-version=13

If any of the packages you requested use CUDA then CUDA should already
have been installed for you.


To enable CUDA support, please follow UCX's instruction above.

To additionally enable NCCL support, run:    conda install nccl


Linking libfabric-2.5.1-ha770c72_1
Linking mpi-1.0.1-openmpi
Linking future-1.0.0-pyhd8ed1ab_2
Linking ncrystal-python-4.4.4-pyhf450f58_0
Linking mcpl-python-2.2.8-pyh8af1aa0_0
Linking ncrystal-core-4.4.4-pyhf450f58_0
Linking mcpl-core-2.2.8-pyh8af1aa0_0
Linking uncertainties-3.2.3-pyhd8ed1ab_0
Linking ncrystal-4.4.4-pyh2c5f401_0
Linking mcpl-2.2.8-pyhd9e7ec7_0
Linking openmpi-5.0.8-h2fe1745_110
setting libfabric environment variables for conda-build
FI_PROVIDER=tcp
setting openmpi environment variables for conda-build

To enable CUDA support, UCX requires the CUDA Runtime library (libcudart).
The library can be installed with the appropriate command below:

* For CUDA 12, run:    conda install cuda-cudart cuda-version=12
* For CUDA 13, run:    conda install cuda-cudart cuda-version=13

If any of the packages you requested use CUDA then CUDA should already
have been installed for you.


To enable CUDA support, please follow UCX's instruction above.

To additionally enable NCCL support, run:    conda install nccl


On Linux, Open MPI is built with CUDA awareness but it is disabled by default.
To enable it, please set the environment variable
OMPI_MCA_opal_cuda_support=true
before launching your MPI processes.
Equivalently, you can set the MCA parameter in the command line:
mpiexec --mca opal_cuda_support 1 ...
Note that you might also need to set UCX_MEMTYPE_CACHE=n for CUDA awareness via
UCX. Please consult UCX documentation for further details.


Linking endf-0.1.12-py312h1289d80_0
Linking zoltan-3.901-mpi_openmpi_hdd8c722_3
Linking mpi4py-4.1.2-py312hd140a38_100
Linking libpnetcdf-1.14.0-mpi_openmpi_h521bef2_0
Linking hdf5-1.14.3-mpi_openmpi_h39ae36c_9
Linking h5py-3.13.0-mpi_openmpi_py312h6b5221c_0
Linking libnetcdf-4.9.2-mpi_openmpi_h5fda6ee_16
Linking tempest-remap-2.2.0-heeae502_5
Linking vtk-base-9.3.1-osmesa_py312h5592cea_112
Linking moab-5.5.1-mpi_openmpi_tempest_py312hc5bf31d_5
Linking vtk-io-ffmpeg-9.3.1-osmesa_py312h838d114_112
Linking dagmc-3.2.4-mpi_openmpi_doubledown_h79c499a_2
Linking vtk-9.3.1-osmesa_py312h838d114_112
Linking openmc-0.15.3-dagmc_mpi_openmpi_py312h2fffaed_100
warning  libmamba [openmc-0.15.3-dagmc_mpi_openmpi_py312h2fffaed_100] The following files were already present in the environment:
    - include/pugiconfig.hpp
    - include/pugixml.hpp
    - lib/cmake/pugixml/pugixml-config-version.cmake
    - lib/cmake/pugixml/pugixml-config.cmake
    - lib/cmake/pugixml/pugixml-targets-release.cmake
    - lib/cmake/pugixml/pugixml-targets.cmake
    - lib/pkgconfig/pugixml.pc

Transaction finished

- [2026-06-15T19:29:55-04:00] EXIT_STATUS: 0
- [2026-06-15T19:29:55-04:00] COMMAND: mamba install -y -c conda-forge paramak

Pinned packages:

  - python=3.12


Transaction

  Prefix: /home/craig/miniforge/envs/mini-tokamak

  Updating specs:

   - paramak


  Package    Version  Build            Channel          Size
──────────────────────────────────────────────────────────────
  Install:
──────────────────────────────────────────────────────────────

  + gmpy2      2.3.0  py312hcaba1f9_1  conda-forge     253kB
  + mpc        1.4.0  he0a73b1_0       conda-forge     100kB
  + mpfr       4.2.2  he0a73b1_0       conda-forge     730kB
  + mpmath     1.4.1  pyhd8ed1ab_0     conda-forge     465kB
  + paramak   0.9.11  pyhd8ed1ab_0     conda-forge      57kB
  + sympy     1.14.0  pyh2585a3b_106   conda-forge       5MB

  Summary:

  Install: 6 packages

  Total download: 6MB

──────────────────────────────────────────────────────────────



Transaction starting
Linking mpmath-1.4.1-pyhd8ed1ab_0
warning  libmamba [mpmath-1.4.1-pyhd8ed1ab_0] The following files were already present in the environment:
    - lib/python3.12/site-packages/mpmath/__init__.py
    - lib/python3.12/site-packages/mpmath/calculus/__init__.py
    - lib/python3.12/site-packages/mpmath/calculus/approximation.py
    - lib/python3.12/site-packages/mpmath/calculus/calculus.py
    - lib/python3.12/site-packages/mpmath/calculus/differentiation.py
    - lib/python3.12/site-packages/mpmath/calculus/extrapolation.py
    - lib/python3.12/site-packages/mpmath/calculus/inverselaplace.py
    - lib/python3.12/site-packages/mpmath/calculus/odes.py
    - lib/python3.12/site-packages/mpmath/calculus/optimization.py
    - lib/python3.12/site-packages/mpmath/calculus/polynomials.py
    - lib/python3.12/site-packages/mpmath/calculus/quadrature.py
    - lib/python3.12/site-packages/mpmath/ctx_base.py
    - lib/python3.12/site-packages/mpmath/ctx_fp.py
    - lib/python3.12/site-packages/mpmath/ctx_iv.py
    - lib/python3.12/site-packages/mpmath/ctx_mp.py
    - lib/python3.12/site-packages/mpmath/ctx_mp_python.py
    - lib/python3.12/site-packages/mpmath/function_docs.py
    - lib/python3.12/site-packages/mpmath/functions/__init__.py
    - lib/python3.12/site-packages/mpmath/functions/bessel.py
    - lib/python3.12/site-packages/mpmath/functions/elliptic.py
    - lib/python3.12/site-packages/mpmath/functions/expintegrals.py
    - lib/python3.12/site-packages/mpmath/functions/factorials.py
    - lib/python3.12/site-packages/mpmath/functions/functions.py
    - lib/python3.12/site-packages/mpmath/functions/hypergeometric.py
    - lib/python3.12/site-packages/mpmath/functions/orthogonal.py
    - lib/python3.12/site-packages/mpmath/functions/qfunctions.py
    - lib/python3.12/site-packages/mpmath/functions/rszeta.py
    - lib/python3.12/site-packages/mpmath/functions/signals.py
    - lib/python3.12/site-packages/mpmath/functions/theta.py
    - lib/python3.12/site-packages/mpmath/functions/zeta.py
    - lib/python3.12/site-packages/mpmath/functions/zetazeros.py
    - lib/python3.12/site-packages/mpmath/identification.py
    - lib/python3.12/site-packages/mpmath/libmp/__init__.py
    - lib/python3.12/site-packages/mpmath/libmp/backend.py
    - lib/python3.12/site-packages/mpmath/libmp/gammazeta.py
    - lib/python3.12/site-packages/mpmath/libmp/libelefun.py
    - lib/python3.12/site-packages/mpmath/libmp/libhyper.py
    - lib/python3.12/site-packages/mpmath/libmp/libintmath.py
    - lib/python3.12/site-packages/mpmath/libmp/libmpc.py
    - lib/python3.12/site-packages/mpmath/libmp/libmpf.py
    - lib/python3.12/site-packages/mpmath/libmp/libmpi.py
    - lib/python3.12/site-packages/mpmath/math2.py
    - lib/python3.12/site-packages/mpmath/matrices/__init__.py
    - lib/python3.12/site-packages/mpmath/matrices/calculus.py
    - lib/python3.12/site-packages/mpmath/matrices/eigen.py
    - lib/python3.12/site-packages/mpmath/matrices/eigen_symmetric.py
    - lib/python3.12/site-packages/mpmath/matrices/linalg.py
    - lib/python3.12/site-packages/mpmath/matrices/matrices.py
    - lib/python3.12/site-packages/mpmath/rational.py
    - lib/python3.12/site-packages/mpmath/tests/test_basic_ops.py
    - lib/python3.12/site-packages/mpmath/tests/test_bitwise.py
    - lib/python3.12/site-packages/mpmath/tests/test_calculus.py
    - lib/python3.12/site-packages/mpmath/tests/test_compatibility.py
    - lib/python3.12/site-packages/mpmath/tests/test_convert.py
    - lib/python3.12/site-packages/mpmath/tests/test_diff.py
    - lib/python3.12/site-packages/mpmath/tests/test_division.py
    - lib/python3.12/site-packages/mpmath/tests/test_eigen.py
    - lib/python3.12/site-packages/mpmath/tests/test_eigen_symmetric.py
    - lib/python3.12/site-packages/mpmath/tests/test_elliptic.py
    - lib/python3.12/site-packages/mpmath/tests/test_fp.py
    - lib/python3.12/site-packages/mpmath/tests/test_functions.py
    - lib/python3.12/site-packages/mpmath/tests/test_functions2.py
    - lib/python3.12/site-packages/mpmath/tests/test_gammazeta.py
    - lib/python3.12/site-packages/mpmath/tests/test_hp.py
    - lib/python3.12/site-packages/mpmath/tests/test_identify.py
    - lib/python3.12/site-packages/mpmath/tests/test_interval.py
    - lib/python3.12/site-packages/mpmath/tests/test_levin.py
    - lib/python3.12/site-packages/mpmath/tests/test_linalg.py
    - lib/python3.12/site-packages/mpmath/tests/test_matrices.py
    - lib/python3.12/site-packages/mpmath/tests/test_mpmath.py
    - lib/python3.12/site-packages/mpmath/tests/test_ode.py
    - lib/python3.12/site-packages/mpmath/tests/test_pickle.py
    - lib/python3.12/site-packages/mpmath/tests/test_power.py
    - lib/python3.12/site-packages/mpmath/tests/test_quad.py
    - lib/python3.12/site-packages/mpmath/tests/test_rootfinding.py
    - lib/python3.12/site-packages/mpmath/tests/test_special.py
    - lib/python3.12/site-packages/mpmath/tests/test_str.py
    - lib/python3.12/site-packages/mpmath/tests/test_summation.py
    - lib/python3.12/site-packages/mpmath/tests/test_trig.py
    - lib/python3.12/site-packages/mpmath/tests/test_visualization.py
    - lib/python3.12/site-packages/mpmath/usertools.py
    - lib/python3.12/site-packages/mpmath/visualization.py
Linking mpfr-4.2.2-he0a73b1_0
Linking mpc-1.4.0-he0a73b1_0
Linking gmpy2-2.3.0-py312hcaba1f9_1
Linking sympy-1.14.0-pyh2585a3b_106
warning  libmamba [sympy-1.14.0-pyh2585a3b_106] The following files were already present in the environment:
    - share/man/man1/isympy.1
    - lib/python3.12/site-packages/isympy.py
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/INSTALLER
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/METADATA
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/RECORD
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/WHEEL
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/entry_points.txt
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/licenses/AUTHORS
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/licenses/LICENSE
    - lib/python3.12/site-packages/sympy-1.14.0.dist-info/top_level.txt
    - lib/python3.12/site-packages/sympy/__init__.py
    - lib/python3.12/site-packages/sympy/abc.py
    - lib/python3.12/site-packages/sympy/algebras/__init__.py
    - lib/python3.12/site-packages/sympy/algebras/quaternion.py
    - lib/python3.12/site-packages/sympy/algebras/tests/__init__.py
    - lib/python3.12/site-packages/sympy/algebras/tests/test_quaternion.py
    - lib/python3.12/site-packages/sympy/assumptions/__init__.py
    - lib/python3.12/site-packages/sympy/assumptions/ask.py
    - lib/python3.12/site-packages/sympy/assumptions/ask_generated.py
    - lib/python3.12/site-packages/sympy/assumptions/assume.py
    - lib/python3.12/site-packages/sympy/assumptions/cnf.py
    - lib/python3.12/site-packages/sympy/assumptions/facts.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/__init__.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/calculus.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/common.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/matrices.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/ntheory.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/order.py
    - lib/python3.12/site-packages/sympy/assumptions/handlers/sets.py
    - lib/python3.12/site-packages/sympy/assumptions/lra_satask.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/__init__.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/calculus.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/common.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/matrices.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/ntheory.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/order.py
    - lib/python3.12/site-packages/sympy/assumptions/predicates/sets.py
    - lib/python3.12/site-packages/sympy/assumptions/refine.py
    - lib/python3.12/site-packages/sympy/assumptions/relation/__init__.py
    - lib/python3.12/site-packages/sympy/assumptions/relation/binrel.py
    - lib/python3.12/site-packages/sympy/assumptions/relation/equality.py
    - lib/python3.12/site-packages/sympy/assumptions/satask.py
    - lib/python3.12/site-packages/sympy/assumptions/sathandlers.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/__init__.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_assumptions_2.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_context.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_matrices.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_query.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_refine.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_rel_queries.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_satask.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_sathandlers.py
    - lib/python3.12/site-packages/sympy/assumptions/tests/test_wrapper.py
    - lib/python3.12/site-packages/sympy/assumptions/wrapper.py
    - lib/python3.12/site-packages/sympy/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/benchmarks/bench_discrete_log.py
    - lib/python3.12/site-packages/sympy/benchmarks/bench_meijerint.py
    - lib/python3.12/site-packages/sympy/benchmarks/bench_symbench.py
    - lib/python3.12/site-packages/sympy/calculus/__init__.py
    - lib/python3.12/site-packages/sympy/calculus/accumulationbounds.py
    - lib/python3.12/site-packages/sympy/calculus/euler.py
    - lib/python3.12/site-packages/sympy/calculus/finite_diff.py
    - lib/python3.12/site-packages/sympy/calculus/singularities.py
    - lib/python3.12/site-packages/sympy/calculus/tests/__init__.py
    - lib/python3.12/site-packages/sympy/calculus/tests/test_accumulationbounds.py
    - lib/python3.12/site-packages/sympy/calculus/tests/test_euler.py
    - lib/python3.12/site-packages/sympy/calculus/tests/test_finite_diff.py
    - lib/python3.12/site-packages/sympy/calculus/tests/test_singularities.py
    - lib/python3.12/site-packages/sympy/calculus/tests/test_util.py
    - lib/python3.12/site-packages/sympy/calculus/util.py
    - lib/python3.12/site-packages/sympy/categories/__init__.py
    - lib/python3.12/site-packages/sympy/categories/baseclasses.py
    - lib/python3.12/site-packages/sympy/categories/diagram_drawing.py
    - lib/python3.12/site-packages/sympy/categories/tests/__init__.py
    - lib/python3.12/site-packages/sympy/categories/tests/test_baseclasses.py
    - lib/python3.12/site-packages/sympy/categories/tests/test_drawing.py
    - lib/python3.12/site-packages/sympy/codegen/__init__.py
    - lib/python3.12/site-packages/sympy/codegen/abstract_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/algorithms.py
    - lib/python3.12/site-packages/sympy/codegen/approximations.py
    - lib/python3.12/site-packages/sympy/codegen/ast.py
    - lib/python3.12/site-packages/sympy/codegen/cfunctions.py
    - lib/python3.12/site-packages/sympy/codegen/cnodes.py
    - lib/python3.12/site-packages/sympy/codegen/cutils.py
    - lib/python3.12/site-packages/sympy/codegen/cxxnodes.py
    - lib/python3.12/site-packages/sympy/codegen/fnodes.py
    - lib/python3.12/site-packages/sympy/codegen/futils.py
    - lib/python3.12/site-packages/sympy/codegen/matrix_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/numpy_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/pynodes.py
    - lib/python3.12/site-packages/sympy/codegen/pyutils.py
    - lib/python3.12/site-packages/sympy/codegen/rewriting.py
    - lib/python3.12/site-packages/sympy/codegen/scipy_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/__init__.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_abstract_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_algorithms.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_applications.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_approximations.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_ast.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_cfunctions.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_cnodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_cxxnodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_fnodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_matrix_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_numpy_nodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_pynodes.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_pyutils.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_rewriting.py
    - lib/python3.12/site-packages/sympy/codegen/tests/test_scipy_nodes.py
    - lib/python3.12/site-packages/sympy/combinatorics/__init__.py
    - lib/python3.12/site-packages/sympy/combinatorics/coset_table.py
    - lib/python3.12/site-packages/sympy/combinatorics/fp_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/free_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/galois.py
    - lib/python3.12/site-packages/sympy/combinatorics/generators.py
    - lib/python3.12/site-packages/sympy/combinatorics/graycode.py
    - lib/python3.12/site-packages/sympy/combinatorics/group_constructs.py
    - lib/python3.12/site-packages/sympy/combinatorics/group_numbers.py
    - lib/python3.12/site-packages/sympy/combinatorics/homomorphisms.py
    - lib/python3.12/site-packages/sympy/combinatorics/named_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/partitions.py
    - lib/python3.12/site-packages/sympy/combinatorics/pc_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/perm_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/permutations.py
    - lib/python3.12/site-packages/sympy/combinatorics/polyhedron.py
    - lib/python3.12/site-packages/sympy/combinatorics/prufer.py
    - lib/python3.12/site-packages/sympy/combinatorics/rewritingsystem.py
    - lib/python3.12/site-packages/sympy/combinatorics/rewritingsystem_fsm.py
    - lib/python3.12/site-packages/sympy/combinatorics/schur_number.py
    - lib/python3.12/site-packages/sympy/combinatorics/subsets.py
    - lib/python3.12/site-packages/sympy/combinatorics/tensor_can.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_coset_table.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_fp_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_free_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_galois.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_generators.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_graycode.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_group_constructs.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_group_numbers.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_homomorphisms.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_named_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_partitions.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_pc_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_perm_groups.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_permutations.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_polyhedron.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_prufer.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_rewriting.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_schur_number.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_subsets.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_tensor_can.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_testutil.py
    - lib/python3.12/site-packages/sympy/combinatorics/tests/test_util.py
    - lib/python3.12/site-packages/sympy/combinatorics/testutil.py
    - lib/python3.12/site-packages/sympy/combinatorics/util.py
    - lib/python3.12/site-packages/sympy/concrete/__init__.py
    - lib/python3.12/site-packages/sympy/concrete/delta.py
    - lib/python3.12/site-packages/sympy/concrete/expr_with_intlimits.py
    - lib/python3.12/site-packages/sympy/concrete/expr_with_limits.py
    - lib/python3.12/site-packages/sympy/concrete/gosper.py
    - lib/python3.12/site-packages/sympy/concrete/guess.py
    - lib/python3.12/site-packages/sympy/concrete/products.py
    - lib/python3.12/site-packages/sympy/concrete/summations.py
    - lib/python3.12/site-packages/sympy/concrete/tests/__init__.py
    - lib/python3.12/site-packages/sympy/concrete/tests/test_delta.py
    - lib/python3.12/site-packages/sympy/concrete/tests/test_gosper.py
    - lib/python3.12/site-packages/sympy/concrete/tests/test_guess.py
    - lib/python3.12/site-packages/sympy/concrete/tests/test_products.py
    - lib/python3.12/site-packages/sympy/concrete/tests/test_sums_products.py
    - lib/python3.12/site-packages/sympy/conftest.py
    - lib/python3.12/site-packages/sympy/core/__init__.py
    - lib/python3.12/site-packages/sympy/core/_print_helpers.py
    - lib/python3.12/site-packages/sympy/core/add.py
    - lib/python3.12/site-packages/sympy/core/alphabets.py
    - lib/python3.12/site-packages/sympy/core/assumptions.py
    - lib/python3.12/site-packages/sympy/core/assumptions_generated.py
    - lib/python3.12/site-packages/sympy/core/backend.py
    - lib/python3.12/site-packages/sympy/core/basic.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_arit.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_assumptions.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_basic.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_expand.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_numbers.py
    - lib/python3.12/site-packages/sympy/core/benchmarks/bench_sympify.py
    - lib/python3.12/site-packages/sympy/core/cache.py
    - lib/python3.12/site-packages/sympy/core/compatibility.py
    - lib/python3.12/site-packages/sympy/core/containers.py
    - lib/python3.12/site-packages/sympy/core/core.py
    - lib/python3.12/site-packages/sympy/core/coreerrors.py
    - lib/python3.12/site-packages/sympy/core/decorators.py
    - lib/python3.12/site-packages/sympy/core/evalf.py
    - lib/python3.12/site-packages/sympy/core/expr.py
    - lib/python3.12/site-packages/sympy/core/exprtools.py
    - lib/python3.12/site-packages/sympy/core/facts.py
    - lib/python3.12/site-packages/sympy/core/function.py
    - lib/python3.12/site-packages/sympy/core/intfunc.py
    - lib/python3.12/site-packages/sympy/core/kind.py
    - lib/python3.12/site-packages/sympy/core/logic.py
    - lib/python3.12/site-packages/sympy/core/mod.py
    - lib/python3.12/site-packages/sympy/core/mul.py
    - lib/python3.12/site-packages/sympy/core/multidimensional.py
    - lib/python3.12/site-packages/sympy/core/numbers.py
    - lib/python3.12/site-packages/sympy/core/operations.py
    - lib/python3.12/site-packages/sympy/core/parameters.py
    - lib/python3.12/site-packages/sympy/core/power.py
    - lib/python3.12/site-packages/sympy/core/random.py
    - lib/python3.12/site-packages/sympy/core/relational.py
    - lib/python3.12/site-packages/sympy/core/rules.py
    - lib/python3.12/site-packages/sympy/core/singleton.py
    - lib/python3.12/site-packages/sympy/core/sorting.py
    - lib/python3.12/site-packages/sympy/core/symbol.py
    - lib/python3.12/site-packages/sympy/core/sympify.py
    - lib/python3.12/site-packages/sympy/core/tests/__init__.py
    - lib/python3.12/site-packages/sympy/core/tests/test_args.py
    - lib/python3.12/site-packages/sympy/core/tests/test_arit.py
    - lib/python3.12/site-packages/sympy/core/tests/test_assumptions.py
    - lib/python3.12/site-packages/sympy/core/tests/test_basic.py
    - lib/python3.12/site-packages/sympy/core/tests/test_cache.py
    - lib/python3.12/site-packages/sympy/core/tests/test_compatibility.py
    - lib/python3.12/site-packages/sympy/core/tests/test_complex.py
    - lib/python3.12/site-packages/sympy/core/tests/test_constructor_postprocessor.py
    - lib/python3.12/site-packages/sympy/core/tests/test_containers.py
    - lib/python3.12/site-packages/sympy/core/tests/test_count_ops.py
    - lib/python3.12/site-packages/sympy/core/tests/test_diff.py
    - lib/python3.12/site-packages/sympy/core/tests/test_equal.py
    - lib/python3.12/site-packages/sympy/core/tests/test_eval.py
    - lib/python3.12/site-packages/sympy/core/tests/test_evalf.py
    - lib/python3.12/site-packages/sympy/core/tests/test_expand.py
    - lib/python3.12/site-packages/sympy/core/tests/test_expr.py
    - lib/python3.12/site-packages/sympy/core/tests/test_exprtools.py
    - lib/python3.12/site-packages/sympy/core/tests/test_facts.py
    - lib/python3.12/site-packages/sympy/core/tests/test_function.py
    - lib/python3.12/site-packages/sympy/core/tests/test_kind.py
    - lib/python3.12/site-packages/sympy/core/tests/test_logic.py
    - lib/python3.12/site-packages/sympy/core/tests/test_match.py
    - lib/python3.12/site-packages/sympy/core/tests/test_multidimensional.py
    - lib/python3.12/site-packages/sympy/core/tests/test_noncommutative.py
    - lib/python3.12/site-packages/sympy/core/tests/test_numbers.py
    - lib/python3.12/site-packages/sympy/core/tests/test_operations.py
    - lib/python3.12/site-packages/sympy/core/tests/test_parameters.py
    - lib/python3.12/site-packages/sympy/core/tests/test_power.py
    - lib/python3.12/site-packages/sympy/core/tests/test_priority.py
    - lib/python3.12/site-packages/sympy/core/tests/test_random.py
    - lib/python3.12/site-packages/sympy/core/tests/test_relational.py
    - lib/python3.12/site-packages/sympy/core/tests/test_rules.py
    - lib/python3.12/site-packages/sympy/core/tests/test_singleton.py
    - lib/python3.12/site-packages/sympy/core/tests/test_sorting.py
    - lib/python3.12/site-packages/sympy/core/tests/test_subs.py
    - lib/python3.12/site-packages/sympy/core/tests/test_symbol.py
    - lib/python3.12/site-packages/sympy/core/tests/test_sympify.py
    - lib/python3.12/site-packages/sympy/core/tests/test_traversal.py
    - lib/python3.12/site-packages/sympy/core/tests/test_truediv.py
    - lib/python3.12/site-packages/sympy/core/tests/test_var.py
    - lib/python3.12/site-packages/sympy/core/trace.py
    - lib/python3.12/site-packages/sympy/core/traversal.py
    - lib/python3.12/site-packages/sympy/crypto/__init__.py
    - lib/python3.12/site-packages/sympy/crypto/crypto.py
    - lib/python3.12/site-packages/sympy/crypto/tests/__init__.py
    - lib/python3.12/site-packages/sympy/crypto/tests/test_crypto.py
    - lib/python3.12/site-packages/sympy/diffgeom/__init__.py
    - lib/python3.12/site-packages/sympy/diffgeom/diffgeom.py
    - lib/python3.12/site-packages/sympy/diffgeom/rn.py
    - lib/python3.12/site-packages/sympy/diffgeom/tests/__init__.py
    - lib/python3.12/site-packages/sympy/diffgeom/tests/test_class_structure.py
    - lib/python3.12/site-packages/sympy/diffgeom/tests/test_diffgeom.py
    - lib/python3.12/site-packages/sympy/diffgeom/tests/test_function_diffgeom_book.py
    - lib/python3.12/site-packages/sympy/diffgeom/tests/test_hyperbolic_space.py
    - lib/python3.12/site-packages/sympy/discrete/__init__.py
    - lib/python3.12/site-packages/sympy/discrete/convolutions.py
    - lib/python3.12/site-packages/sympy/discrete/recurrences.py
    - lib/python3.12/site-packages/sympy/discrete/tests/__init__.py
    - lib/python3.12/site-packages/sympy/discrete/tests/test_convolutions.py
    - lib/python3.12/site-packages/sympy/discrete/tests/test_recurrences.py
    - lib/python3.12/site-packages/sympy/discrete/tests/test_transforms.py
    - lib/python3.12/site-packages/sympy/discrete/transforms.py
    - lib/python3.12/site-packages/sympy/external/__init__.py
    - lib/python3.12/site-packages/sympy/external/gmpy.py
    - lib/python3.12/site-packages/sympy/external/importtools.py
    - lib/python3.12/site-packages/sympy/external/ntheory.py
    - lib/python3.12/site-packages/sympy/external/pythonmpq.py
    - lib/python3.12/site-packages/sympy/external/tests/__init__.py
    - lib/python3.12/site-packages/sympy/external/tests/test_autowrap.py
    - lib/python3.12/site-packages/sympy/external/tests/test_codegen.py
    - lib/python3.12/site-packages/sympy/external/tests/test_gmpy.py
    - lib/python3.12/site-packages/sympy/external/tests/test_importtools.py
    - lib/python3.12/site-packages/sympy/external/tests/test_ntheory.py
    - lib/python3.12/site-packages/sympy/external/tests/test_numpy.py
    - lib/python3.12/site-packages/sympy/external/tests/test_pythonmpq.py
    - lib/python3.12/site-packages/sympy/external/tests/test_scipy.py
    - lib/python3.12/site-packages/sympy/functions/__init__.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/__init__.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/factorials.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/numbers.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/tests/__init__.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/tests/test_comb_factorials.py
    - lib/python3.12/site-packages/sympy/functions/combinatorial/tests/test_comb_numbers.py
    - lib/python3.12/site-packages/sympy/functions/elementary/__init__.py
    - lib/python3.12/site-packages/sympy/functions/elementary/_trigonometric_special.py
    - lib/python3.12/site-packages/sympy/functions/elementary/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/functions/elementary/benchmarks/bench_exp.py
    - lib/python3.12/site-packages/sympy/functions/elementary/complexes.py
    - lib/python3.12/site-packages/sympy/functions/elementary/exponential.py
    - lib/python3.12/site-packages/sympy/functions/elementary/hyperbolic.py
    - lib/python3.12/site-packages/sympy/functions/elementary/integers.py
    - lib/python3.12/site-packages/sympy/functions/elementary/miscellaneous.py
    - lib/python3.12/site-packages/sympy/functions/elementary/piecewise.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/__init__.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_complexes.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_exponential.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_hyperbolic.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_integers.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_interface.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_miscellaneous.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_piecewise.py
    - lib/python3.12/site-packages/sympy/functions/elementary/tests/test_trigonometric.py
    - lib/python3.12/site-packages/sympy/functions/elementary/trigonometric.py
    - lib/python3.12/site-packages/sympy/functions/special/__init__.py
    - lib/python3.12/site-packages/sympy/functions/special/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/functions/special/benchmarks/bench_special.py
    - lib/python3.12/site-packages/sympy/functions/special/bessel.py
    - lib/python3.12/site-packages/sympy/functions/special/beta_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/bsplines.py
    - lib/python3.12/site-packages/sympy/functions/special/delta_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/elliptic_integrals.py
    - lib/python3.12/site-packages/sympy/functions/special/error_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/gamma_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/hyper.py
    - lib/python3.12/site-packages/sympy/functions/special/mathieu_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/polynomials.py
    - lib/python3.12/site-packages/sympy/functions/special/singularity_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/spherical_harmonics.py
    - lib/python3.12/site-packages/sympy/functions/special/tensor_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/__init__.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_bessel.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_beta_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_bsplines.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_delta_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_elliptic_integrals.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_error_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_gamma_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_hyper.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_mathieu.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_singularity_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_spec_polynomials.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_spherical_harmonics.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_tensor_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/tests/test_zeta_functions.py
    - lib/python3.12/site-packages/sympy/functions/special/zeta_functions.py
    - lib/python3.12/site-packages/sympy/galgebra.py
    - lib/python3.12/site-packages/sympy/geometry/__init__.py
    - lib/python3.12/site-packages/sympy/geometry/curve.py
    - lib/python3.12/site-packages/sympy/geometry/ellipse.py
    - lib/python3.12/site-packages/sympy/geometry/entity.py
    - lib/python3.12/site-packages/sympy/geometry/exceptions.py
    - lib/python3.12/site-packages/sympy/geometry/line.py
    - lib/python3.12/site-packages/sympy/geometry/parabola.py
    - lib/python3.12/site-packages/sympy/geometry/plane.py
    - lib/python3.12/site-packages/sympy/geometry/point.py
    - lib/python3.12/site-packages/sympy/geometry/polygon.py
    - lib/python3.12/site-packages/sympy/geometry/tests/__init__.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_curve.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_ellipse.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_entity.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_geometrysets.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_line.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_parabola.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_plane.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_point.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_polygon.py
    - lib/python3.12/site-packages/sympy/geometry/tests/test_util.py
    - lib/python3.12/site-packages/sympy/geometry/util.py
    - lib/python3.12/site-packages/sympy/holonomic/__init__.py
    - lib/python3.12/site-packages/sympy/holonomic/holonomic.py
    - lib/python3.12/site-packages/sympy/holonomic/holonomicerrors.py
    - lib/python3.12/site-packages/sympy/holonomic/numerical.py
    - lib/python3.12/site-packages/sympy/holonomic/recurrence.py
    - lib/python3.12/site-packages/sympy/holonomic/tests/__init__.py
    - lib/python3.12/site-packages/sympy/holonomic/tests/test_holonomic.py
    - lib/python3.12/site-packages/sympy/holonomic/tests/test_recurrence.py
    - lib/python3.12/site-packages/sympy/integrals/__init__.py
    - lib/python3.12/site-packages/sympy/integrals/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/integrals/benchmarks/bench_integrate.py
    - lib/python3.12/site-packages/sympy/integrals/benchmarks/bench_trigintegrate.py
    - lib/python3.12/site-packages/sympy/integrals/deltafunctions.py
    - lib/python3.12/site-packages/sympy/integrals/heurisch.py
    - lib/python3.12/site-packages/sympy/integrals/integrals.py
    - lib/python3.12/site-packages/sympy/integrals/intpoly.py
    - lib/python3.12/site-packages/sympy/integrals/laplace.py
    - lib/python3.12/site-packages/sympy/integrals/manualintegrate.py
    - lib/python3.12/site-packages/sympy/integrals/meijerint.py
    - lib/python3.12/site-packages/sympy/integrals/meijerint_doc.py
    - lib/python3.12/site-packages/sympy/integrals/prde.py
    - lib/python3.12/site-packages/sympy/integrals/quadrature.py
    - lib/python3.12/site-packages/sympy/integrals/rationaltools.py
    - lib/python3.12/site-packages/sympy/integrals/rde.py
    - lib/python3.12/site-packages/sympy/integrals/risch.py
    - lib/python3.12/site-packages/sympy/integrals/singularityfunctions.py
    - lib/python3.12/site-packages/sympy/integrals/tests/__init__.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_deltafunctions.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_failing_integrals.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_heurisch.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_integrals.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_intpoly.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_laplace.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_lineintegrals.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_manual.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_meijerint.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_prde.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_quadrature.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_rationaltools.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_rde.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_risch.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_singularityfunctions.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_transforms.py
    - lib/python3.12/site-packages/sympy/integrals/tests/test_trigonometry.py
    - lib/python3.12/site-packages/sympy/integrals/transforms.py
    - lib/python3.12/site-packages/sympy/integrals/trigonometry.py
    - lib/python3.12/site-packages/sympy/interactive/__init__.py
    - lib/python3.12/site-packages/sympy/interactive/printing.py
    - lib/python3.12/site-packages/sympy/interactive/session.py
    - lib/python3.12/site-packages/sympy/interactive/tests/__init__.py
    - lib/python3.12/site-packages/sympy/interactive/tests/test_interactive.py
    - lib/python3.12/site-packages/sympy/interactive/tests/test_ipython.py
    - lib/python3.12/site-packages/sympy/interactive/traversal.py
    - lib/python3.12/site-packages/sympy/liealgebras/__init__.py
    - lib/python3.12/site-packages/sympy/liealgebras/cartan_matrix.py
    - lib/python3.12/site-packages/sympy/liealgebras/cartan_type.py
    - lib/python3.12/site-packages/sympy/liealgebras/dynkin_diagram.py
    - lib/python3.12/site-packages/sympy/liealgebras/root_system.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/__init__.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_cartan_matrix.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_cartan_type.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_dynkin_diagram.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_root_system.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_A.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_B.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_C.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_D.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_E.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_F.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_type_G.py
    - lib/python3.12/site-packages/sympy/liealgebras/tests/test_weyl_group.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_a.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_b.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_c.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_d.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_e.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_f.py
    - lib/python3.12/site-packages/sympy/liealgebras/type_g.py
    - lib/python3.12/site-packages/sympy/liealgebras/weyl_group.py
    - lib/python3.12/site-packages/sympy/logic/__init__.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/__init__.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/dpll.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/dpll2.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/lra_theory.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/minisat22_wrapper.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/pycosat_wrapper.py
    - lib/python3.12/site-packages/sympy/logic/algorithms/z3_wrapper.py
    - lib/python3.12/site-packages/sympy/logic/boolalg.py
    - lib/python3.12/site-packages/sympy/logic/inference.py
    - lib/python3.12/site-packages/sympy/logic/tests/__init__.py
    - lib/python3.12/site-packages/sympy/logic/tests/test_boolalg.py
    - lib/python3.12/site-packages/sympy/logic/tests/test_dimacs.py
    - lib/python3.12/site-packages/sympy/logic/tests/test_inference.py
    - lib/python3.12/site-packages/sympy/logic/tests/test_lra_theory.py
    - lib/python3.12/site-packages/sympy/logic/utilities/__init__.py
    - lib/python3.12/site-packages/sympy/logic/utilities/dimacs.py
    - lib/python3.12/site-packages/sympy/matrices/__init__.py
    - lib/python3.12/site-packages/sympy/matrices/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/matrices/benchmarks/bench_matrix.py
    - lib/python3.12/site-packages/sympy/matrices/common.py
    - lib/python3.12/site-packages/sympy/matrices/decompositions.py
    - lib/python3.12/site-packages/sympy/matrices/dense.py
    - lib/python3.12/site-packages/sympy/matrices/determinant.py
    - lib/python3.12/site-packages/sympy/matrices/eigen.py
    - lib/python3.12/site-packages/sympy/matrices/exceptions.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/__init__.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/_shape.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/adjoint.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/applyfunc.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/blockmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/companion.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/determinant.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/diagonal.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/dotproduct.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/factorizations.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/fourier.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/funcmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/hadamard.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/inverse.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/kronecker.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/matadd.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/matexpr.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/matmul.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/matpow.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/permutation.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/sets.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/slice.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/special.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/__init__.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_adjoint.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_applyfunc.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_blockmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_companion.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_derivatives.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_determinant.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_diagonal.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_dotproduct.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_factorizations.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_fourier.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_funcmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_hadamard.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_indexing.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_inverse.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_kronecker.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_matadd.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_matexpr.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_matmul.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_matpow.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_permutation.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_sets.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_slice.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_special.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_trace.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/tests/test_transpose.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/trace.py
    - lib/python3.12/site-packages/sympy/matrices/expressions/transpose.py
    - lib/python3.12/site-packages/sympy/matrices/graph.py
    - lib/python3.12/site-packages/sympy/matrices/immutable.py
    - lib/python3.12/site-packages/sympy/matrices/inverse.py
    - lib/python3.12/site-packages/sympy/matrices/kind.py
    - lib/python3.12/site-packages/sympy/matrices/matrices.py
    - lib/python3.12/site-packages/sympy/matrices/matrixbase.py
    - lib/python3.12/site-packages/sympy/matrices/normalforms.py
    - lib/python3.12/site-packages/sympy/matrices/reductions.py
    - lib/python3.12/site-packages/sympy/matrices/repmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/solvers.py
    - lib/python3.12/site-packages/sympy/matrices/sparse.py
    - lib/python3.12/site-packages/sympy/matrices/sparsetools.py
    - lib/python3.12/site-packages/sympy/matrices/subspaces.py
    - lib/python3.12/site-packages/sympy/matrices/tests/__init__.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_commonmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_decompositions.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_determinant.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_domains.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_eigen.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_graph.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_immutable.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_interactions.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_matrices.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_matrixbase.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_normalforms.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_reductions.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_repmatrix.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_solvers.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_sparse.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_sparsetools.py
    - lib/python3.12/site-packages/sympy/matrices/tests/test_subspaces.py
    - lib/python3.12/site-packages/sympy/matrices/utilities.py
    - lib/python3.12/site-packages/sympy/multipledispatch/__init__.py
    - lib/python3.12/site-packages/sympy/multipledispatch/conflict.py
    - lib/python3.12/site-packages/sympy/multipledispatch/core.py
    - lib/python3.12/site-packages/sympy/multipledispatch/dispatcher.py
    - lib/python3.12/site-packages/sympy/multipledispatch/tests/__init__.py
    - lib/python3.12/site-packages/sympy/multipledispatch/tests/test_conflict.py
    - lib/python3.12/site-packages/sympy/multipledispatch/tests/test_core.py
    - lib/python3.12/site-packages/sympy/multipledispatch/tests/test_dispatcher.py
    - lib/python3.12/site-packages/sympy/multipledispatch/utils.py
    - lib/python3.12/site-packages/sympy/ntheory/__init__.py
    - lib/python3.12/site-packages/sympy/ntheory/bbp_pi.py
    - lib/python3.12/site-packages/sympy/ntheory/continued_fraction.py
    - lib/python3.12/site-packages/sympy/ntheory/digits.py
    - lib/python3.12/site-packages/sympy/ntheory/ecm.py
    - lib/python3.12/site-packages/sympy/ntheory/egyptian_fraction.py
    - lib/python3.12/site-packages/sympy/ntheory/elliptic_curve.py
    - lib/python3.12/site-packages/sympy/ntheory/factor_.py
    - lib/python3.12/site-packages/sympy/ntheory/generate.py
    - lib/python3.12/site-packages/sympy/ntheory/modular.py
    - lib/python3.12/site-packages/sympy/ntheory/multinomial.py
    - lib/python3.12/site-packages/sympy/ntheory/partitions_.py
    - lib/python3.12/site-packages/sympy/ntheory/primetest.py
    - lib/python3.12/site-packages/sympy/ntheory/qs.py
    - lib/python3.12/site-packages/sympy/ntheory/residue_ntheory.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/__init__.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_bbp_pi.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_continued_fraction.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_digits.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_ecm.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_egyptian_fraction.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_elliptic_curve.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_factor_.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_generate.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_hypothesis.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_modular.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_multinomial.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_partitions.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_primetest.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_qs.py
    - lib/python3.12/site-packages/sympy/ntheory/tests/test_residue.py
    - lib/python3.12/site-packages/sympy/parsing/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/ast_parser.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/Autolev.g4
    - lib/python3.12/site-packages/sympy/parsing/autolev/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_antlr/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_antlr/autolevlexer.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_antlr/autolevlistener.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_antlr/autolevparser.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_build_autolev_antlr.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_listener_autolev_antlr.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/_parse_autolev_antlr.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/README.txt
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/chaos_pendulum.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/chaos_pendulum.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/double_pendulum.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/double_pendulum.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/mass_spring_damper.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/mass_spring_damper.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/non_min_pendulum.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/pydy-example-repo/non_min_pendulum.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest1.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest1.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest10.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest10.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest11.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest11.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest12.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest12.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest2.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest2.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest3.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest3.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest4.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest4.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest5.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest5.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest6.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest6.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest7.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest7.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest8.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest8.py
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest9.al
    - lib/python3.12/site-packages/sympy/parsing/autolev/test-examples/ruletest9.py
    - lib/python3.12/site-packages/sympy/parsing/c/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/c/c_parser.py
    - lib/python3.12/site-packages/sympy/parsing/fortran/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/fortran/fortran_parser.py
    - lib/python3.12/site-packages/sympy/parsing/latex/LICENSE.txt
    - lib/python3.12/site-packages/sympy/parsing/latex/LaTeX.g4
    - lib/python3.12/site-packages/sympy/parsing/latex/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/latex/_antlr/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/latex/_antlr/latexlexer.py
    - lib/python3.12/site-packages/sympy/parsing/latex/_antlr/latexparser.py
    - lib/python3.12/site-packages/sympy/parsing/latex/_build_latex_antlr.py
    - lib/python3.12/site-packages/sympy/parsing/latex/_parse_latex_antlr.py
    - lib/python3.12/site-packages/sympy/parsing/latex/errors.py
    - lib/python3.12/site-packages/sympy/parsing/latex/lark/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/latex/lark/grammar/greek_symbols.lark
    - lib/python3.12/site-packages/sympy/parsing/latex/lark/grammar/latex.lark
    - lib/python3.12/site-packages/sympy/parsing/latex/lark/latex_parser.py
    - lib/python3.12/site-packages/sympy/parsing/latex/lark/transformer.py
    - lib/python3.12/site-packages/sympy/parsing/mathematica.py
    - lib/python3.12/site-packages/sympy/parsing/maxima.py
    - lib/python3.12/site-packages/sympy/parsing/sym_expr.py
    - lib/python3.12/site-packages/sympy/parsing/sympy_parser.py
    - lib/python3.12/site-packages/sympy/parsing/tests/__init__.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_ast_parser.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_autolev.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_c_parser.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_custom_latex.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_fortran_parser.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_implicit_multiplication_application.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_latex.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_latex_deps.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_latex_lark.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_mathematica.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_maxima.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_sym_expr.py
    - lib/python3.12/site-packages/sympy/parsing/tests/test_sympy_parser.py
    - lib/python3.12/site-packages/sympy/physics/__init__.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/__init__.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/_mixin.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/activation.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/curve.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/musculotendon.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/tests/test_activation.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/tests/test_curve.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/tests/test_mixin.py
    - lib/python3.12/site-packages/sympy/physics/biomechanics/tests/test_musculotendon.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/__init__.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/arch.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/beam.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/cable.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/tests/test_arch.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/tests/test_beam.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/tests/test_cable.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/tests/test_truss.py
    - lib/python3.12/site-packages/sympy/physics/continuum_mechanics/truss.py
    - lib/python3.12/site-packages/sympy/physics/control/__init__.py
    - lib/python3.12/site-packages/sympy/physics/control/control_plots.py
    - lib/python3.12/site-packages/sympy/physics/control/lti.py
    - lib/python3.12/site-packages/sympy/physics/control/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/control/tests/test_control_plots.py
    - lib/python3.12/site-packages/sympy/physics/control/tests/test_lti.py
    - lib/python3.12/site-packages/sympy/physics/hep/__init__.py
    - lib/python3.12/site-packages/sympy/physics/hep/gamma_matrices.py
    - lib/python3.12/site-packages/sympy/physics/hep/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/hep/tests/test_gamma_matrices.py
    - lib/python3.12/site-packages/sympy/physics/hydrogen.py
    - lib/python3.12/site-packages/sympy/physics/matrices.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/__init__.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/actuator.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/body.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/body_base.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/functions.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/inertia.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/joint.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/jointsmethod.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/kane.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/lagrange.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/linearize.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/loads.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/method.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/models.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/particle.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/pathway.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/rigidbody.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/system.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_actuator.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_body.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_functions.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_inertia.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_joint.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_jointsmethod.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_kane.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_kane2.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_kane3.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_kane4.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_kane5.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_lagrange.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_lagrange2.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_linearity_of_velocity_constraints.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_linearize.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_loads.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_method.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_models.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_particle.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_pathway.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_rigidbody.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_system.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_system_class.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/tests/test_wrapping_geometry.py
    - lib/python3.12/site-packages/sympy/physics/mechanics/wrapping_geometry.py
    - lib/python3.12/site-packages/sympy/physics/optics/__init__.py
    - lib/python3.12/site-packages/sympy/physics/optics/gaussopt.py
    - lib/python3.12/site-packages/sympy/physics/optics/medium.py
    - lib/python3.12/site-packages/sympy/physics/optics/polarization.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/test_gaussopt.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/test_medium.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/test_polarization.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/test_utils.py
    - lib/python3.12/site-packages/sympy/physics/optics/tests/test_waves.py
    - lib/python3.12/site-packages/sympy/physics/optics/utils.py
    - lib/python3.12/site-packages/sympy/physics/optics/waves.py
    - lib/python3.12/site-packages/sympy/physics/paulialgebra.py
    - lib/python3.12/site-packages/sympy/physics/pring.py
    - lib/python3.12/site-packages/sympy/physics/qho_1d.py
    - lib/python3.12/site-packages/sympy/physics/quantum/__init__.py
    - lib/python3.12/site-packages/sympy/physics/quantum/anticommutator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/boson.py
    - lib/python3.12/site-packages/sympy/physics/quantum/cartesian.py
    - lib/python3.12/site-packages/sympy/physics/quantum/cg.py
    - lib/python3.12/site-packages/sympy/physics/quantum/circuitplot.py
    - lib/python3.12/site-packages/sympy/physics/quantum/circuitutils.py
    - lib/python3.12/site-packages/sympy/physics/quantum/commutator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/constants.py
    - lib/python3.12/site-packages/sympy/physics/quantum/dagger.py
    - lib/python3.12/site-packages/sympy/physics/quantum/density.py
    - lib/python3.12/site-packages/sympy/physics/quantum/fermion.py
    - lib/python3.12/site-packages/sympy/physics/quantum/gate.py
    - lib/python3.12/site-packages/sympy/physics/quantum/grover.py
    - lib/python3.12/site-packages/sympy/physics/quantum/hilbert.py
    - lib/python3.12/site-packages/sympy/physics/quantum/identitysearch.py
    - lib/python3.12/site-packages/sympy/physics/quantum/innerproduct.py
    - lib/python3.12/site-packages/sympy/physics/quantum/kind.py
    - lib/python3.12/site-packages/sympy/physics/quantum/matrixcache.py
    - lib/python3.12/site-packages/sympy/physics/quantum/matrixutils.py
    - lib/python3.12/site-packages/sympy/physics/quantum/operator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/operatorordering.py
    - lib/python3.12/site-packages/sympy/physics/quantum/operatorset.py
    - lib/python3.12/site-packages/sympy/physics/quantum/pauli.py
    - lib/python3.12/site-packages/sympy/physics/quantum/piab.py
    - lib/python3.12/site-packages/sympy/physics/quantum/qapply.py
    - lib/python3.12/site-packages/sympy/physics/quantum/qasm.py
    - lib/python3.12/site-packages/sympy/physics/quantum/qexpr.py
    - lib/python3.12/site-packages/sympy/physics/quantum/qft.py
    - lib/python3.12/site-packages/sympy/physics/quantum/qubit.py
    - lib/python3.12/site-packages/sympy/physics/quantum/represent.py
    - lib/python3.12/site-packages/sympy/physics/quantum/sho1d.py
    - lib/python3.12/site-packages/sympy/physics/quantum/shor.py
    - lib/python3.12/site-packages/sympy/physics/quantum/spin.py
    - lib/python3.12/site-packages/sympy/physics/quantum/state.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tensorproduct.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_anticommutator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_boson.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_cartesian.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_cg.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_circuitplot.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_circuitutils.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_commutator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_constants.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_dagger.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_density.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_fermion.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_gate.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_grover.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_hilbert.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_identitysearch.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_innerproduct.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_kind.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_matrixutils.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_operator.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_operatorordering.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_operatorset.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_pauli.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_piab.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_printing.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_qapply.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_qasm.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_qexpr.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_qft.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_qubit.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_represent.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_sho1d.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_shor.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_spin.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_state.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_tensorproduct.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_trace.py
    - lib/python3.12/site-packages/sympy/physics/quantum/tests/test_transforms.py
    - lib/python3.12/site-packages/sympy/physics/quantum/trace.py
    - lib/python3.12/site-packages/sympy/physics/quantum/transforms.py
    - lib/python3.12/site-packages/sympy/physics/secondquant.py
    - lib/python3.12/site-packages/sympy/physics/sho.py
    - lib/python3.12/site-packages/sympy/physics/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_clebsch_gordan.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_hydrogen.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_paulialgebra.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_physics_matrices.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_pring.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_qho_1d.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_secondquant.py
    - lib/python3.12/site-packages/sympy/physics/tests/test_sho.py
    - lib/python3.12/site-packages/sympy/physics/units/__init__.py
    - lib/python3.12/site-packages/sympy/physics/units/definitions/__init__.py
    - lib/python3.12/site-packages/sympy/physics/units/definitions/dimension_definitions.py
    - lib/python3.12/site-packages/sympy/physics/units/definitions/unit_definitions.py
    - lib/python3.12/site-packages/sympy/physics/units/dimensions.py
    - lib/python3.12/site-packages/sympy/physics/units/prefixes.py
    - lib/python3.12/site-packages/sympy/physics/units/quantities.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/__init__.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/cgs.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/length_weight_time.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/mks.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/mksa.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/natural.py
    - lib/python3.12/site-packages/sympy/physics/units/systems/si.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_dimensions.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_dimensionsystem.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_prefixes.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_quantities.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_unit_system_cgs_gauss.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_unitsystem.py
    - lib/python3.12/site-packages/sympy/physics/units/tests/test_util.py
    - lib/python3.12/site-packages/sympy/physics/units/unitsystem.py
    - lib/python3.12/site-packages/sympy/physics/units/util.py
    - lib/python3.12/site-packages/sympy/physics/vector/__init__.py
    - lib/python3.12/site-packages/sympy/physics/vector/dyadic.py
    - lib/python3.12/site-packages/sympy/physics/vector/fieldfunctions.py
    - lib/python3.12/site-packages/sympy/physics/vector/frame.py
    - lib/python3.12/site-packages/sympy/physics/vector/functions.py
    - lib/python3.12/site-packages/sympy/physics/vector/point.py
    - lib/python3.12/site-packages/sympy/physics/vector/printing.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/__init__.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_dyadic.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_fieldfunctions.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_frame.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_functions.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_output.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_point.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_printing.py
    - lib/python3.12/site-packages/sympy/physics/vector/tests/test_vector.py
    - lib/python3.12/site-packages/sympy/physics/vector/vector.py
    - lib/python3.12/site-packages/sympy/physics/wigner.py
    - lib/python3.12/site-packages/sympy/plotting/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/backends/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/backends/base_backend.py
    - lib/python3.12/site-packages/sympy/plotting/backends/matplotlibbackend/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/backends/matplotlibbackend/matplotlib.py
    - lib/python3.12/site-packages/sympy/plotting/backends/textbackend/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/backends/textbackend/text.py
    - lib/python3.12/site-packages/sympy/plotting/experimental_lambdify.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/interval_arithmetic.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/interval_membership.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/lib_interval.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/tests/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/tests/test_interval_functions.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/tests/test_interval_membership.py
    - lib/python3.12/site-packages/sympy/plotting/intervalmath/tests/test_intervalmath.py
    - lib/python3.12/site-packages/sympy/plotting/plot.py
    - lib/python3.12/site-packages/sympy/plotting/plot_implicit.py
    - lib/python3.12/site-packages/sympy/plotting/plotgrid.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/color_scheme.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/managed_window.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_axes.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_camera.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_controller.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_curve.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_interval.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_mode.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_mode_base.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_modes.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_object.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_rotation.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_surface.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/plot_window.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/tests/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/tests/test_plotting.py
    - lib/python3.12/site-packages/sympy/plotting/pygletplot/util.py
    - lib/python3.12/site-packages/sympy/plotting/series.py
    - lib/python3.12/site-packages/sympy/plotting/tests/__init__.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_experimental_lambdify.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_plot.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_plot_implicit.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_region_and.png
    - lib/python3.12/site-packages/sympy/plotting/tests/test_region_not.png
    - lib/python3.12/site-packages/sympy/plotting/tests/test_region_or.png
    - lib/python3.12/site-packages/sympy/plotting/tests/test_region_xor.png
    - lib/python3.12/site-packages/sympy/plotting/tests/test_series.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_textplot.py
    - lib/python3.12/site-packages/sympy/plotting/tests/test_utils.py
    - lib/python3.12/site-packages/sympy/plotting/textplot.py
    - lib/python3.12/site-packages/sympy/plotting/utils.py
    - lib/python3.12/site-packages/sympy/polys/__init__.py
    - lib/python3.12/site-packages/sympy/polys/agca/__init__.py
    - lib/python3.12/site-packages/sympy/polys/agca/extensions.py
    - lib/python3.12/site-packages/sympy/polys/agca/homomorphisms.py
    - lib/python3.12/site-packages/sympy/polys/agca/ideals.py
    - lib/python3.12/site-packages/sympy/polys/agca/modules.py
    - lib/python3.12/site-packages/sympy/polys/agca/tests/__init__.py
    - lib/python3.12/site-packages/sympy/polys/agca/tests/test_extensions.py
    - lib/python3.12/site-packages/sympy/polys/agca/tests/test_homomorphisms.py
    - lib/python3.12/site-packages/sympy/polys/agca/tests/test_ideals.py
    - lib/python3.12/site-packages/sympy/polys/agca/tests/test_modules.py
    - lib/python3.12/site-packages/sympy/polys/appellseqs.py
    - lib/python3.12/site-packages/sympy/polys/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/polys/benchmarks/bench_galoispolys.py
    - lib/python3.12/site-packages/sympy/polys/benchmarks/bench_groebnertools.py
    - lib/python3.12/site-packages/sympy/polys/benchmarks/bench_solvers.py
    - lib/python3.12/site-packages/sympy/polys/compatibility.py
    - lib/python3.12/site-packages/sympy/polys/constructor.py
    - lib/python3.12/site-packages/sympy/polys/densearith.py
    - lib/python3.12/site-packages/sympy/polys/densebasic.py
    - lib/python3.12/site-packages/sympy/polys/densetools.py
    - lib/python3.12/site-packages/sympy/polys/dispersion.py
    - lib/python3.12/site-packages/sympy/polys/distributedmodules.py
    - lib/python3.12/site-packages/sympy/polys/domainmatrix.py
    - lib/python3.12/site-packages/sympy/polys/domains/__init__.py
    - lib/python3.12/site-packages/sympy/polys/domains/algebraicfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/characteristiczero.py
    - lib/python3.12/site-packages/sympy/polys/domains/complexfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/compositedomain.py
    - lib/python3.12/site-packages/sympy/polys/domains/domain.py
    - lib/python3.12/site-packages/sympy/polys/domains/domainelement.py
    - lib/python3.12/site-packages/sympy/polys/domains/expressiondomain.py
    - lib/python3.12/site-packages/sympy/polys/domains/expressionrawdomain.py
    - lib/python3.12/site-packages/sympy/polys/domains/field.py
    - lib/python3.12/site-packages/sympy/polys/domains/finitefield.py
    - lib/python3.12/site-packages/sympy/polys/domains/fractionfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/gaussiandomains.py
    - lib/python3.12/site-packages/sympy/polys/domains/gmpyfinitefield.py
    - lib/python3.12/site-packages/sympy/polys/domains/gmpyintegerring.py
    - lib/python3.12/site-packages/sympy/polys/domains/gmpyrationalfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/groundtypes.py
    - lib/python3.12/site-packages/sympy/polys/domains/integerring.py
    - lib/python3.12/site-packages/sympy/polys/domains/modularinteger.py
    - lib/python3.12/site-packages/sympy/polys/domains/mpelements.py
    - lib/python3.12/site-packages/sympy/polys/domains/old_fractionfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/old_polynomialring.py
    - lib/python3.12/site-packages/sympy/polys/domains/polynomialring.py
    - lib/python3.12/site-packages/sympy/polys/domains/pythonfinitefield.py
    - lib/python3.12/site-packages/sympy/polys/domains/pythonintegerring.py
    - lib/python3.12/site-packages/sympy/polys/domains/pythonrational.py
    - lib/python3.12/site-packages/sympy/polys/domains/pythonrationalfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/quotientring.py
    - lib/python3.12/site-packages/sympy/polys/domains/rationalfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/realfield.py
    - lib/python3.12/site-packages/sympy/polys/domains/ring.py
    - lib/python3.12/site-packages/sympy/polys/domains/simpledomain.py
    - lib/python3.12/site-packages/sympy/polys/domains/tests/__init__.py
    - lib/python3.12/site-packages/sympy/polys/domains/tests/test_domains.py
    - lib/python3.12/site-packages/sympy/polys/domains/tests/test_polynomialring.py
    - lib/python3.12/site-packages/sympy/polys/domains/tests/test_quotientring.py
    - lib/python3.12/site-packages/sympy/polys/euclidtools.py
    - lib/python3.12/site-packages/sympy/polys/factortools.py
    - lib/python3.12/site-packages/sympy/polys/fglmtools.py
    - lib/python3.12/site-packages/sympy/polys/fields.py
    - lib/python3.12/site-packages/sympy/polys/galoistools.py
    - lib/python3.12/site-packages/sympy/polys/groebnertools.py
    - lib/python3.12/site-packages/sympy/polys/heuristicgcd.py
    - lib/python3.12/site-packages/sympy/polys/matrices/__init__.py
    - lib/python3.12/site-packages/sympy/polys/matrices/_dfm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/_typing.py
    - lib/python3.12/site-packages/sympy/polys/matrices/ddm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/dense.py
    - lib/python3.12/site-packages/sympy/polys/matrices/dfm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/domainmatrix.py
    - lib/python3.12/site-packages/sympy/polys/matrices/domainscalar.py
    - lib/python3.12/site-packages/sympy/polys/matrices/eigen.py
    - lib/python3.12/site-packages/sympy/polys/matrices/exceptions.py
    - lib/python3.12/site-packages/sympy/polys/matrices/linsolve.py
    - lib/python3.12/site-packages/sympy/polys/matrices/lll.py
    - lib/python3.12/site-packages/sympy/polys/matrices/normalforms.py
    - lib/python3.12/site-packages/sympy/polys/matrices/rref.py
    - lib/python3.12/site-packages/sympy/polys/matrices/sdm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/__init__.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_ddm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_dense.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_domainmatrix.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_domainscalar.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_eigen.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_fflu.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_inverse.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_linsolve.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_lll.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_normalforms.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_nullspace.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_rref.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_sdm.py
    - lib/python3.12/site-packages/sympy/polys/matrices/tests/test_xxm.py
    - lib/python3.12/site-packages/sympy/polys/modulargcd.py
    - lib/python3.12/site-packages/sympy/polys/monomials.py
    - lib/python3.12/site-packages/sympy/polys/multivariate_resultants.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/__init__.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/basis.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/exceptions.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/galois_resolvents.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/galoisgroups.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/minpoly.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/modules.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/primes.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/resolvent_lookup.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/subfield.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/__init__.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_basis.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_galoisgroups.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_minpoly.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_modules.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_numbers.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_primes.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_subfield.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/tests/test_utilities.py
    - lib/python3.12/site-packages/sympy/polys/numberfields/utilities.py
    - lib/python3.12/site-packages/sympy/polys/orderings.py
    - lib/python3.12/site-packages/sympy/polys/orthopolys.py
    - lib/python3.12/site-packages/sympy/polys/partfrac.py
    - lib/python3.12/site-packages/sympy/polys/polyclasses.py
    - lib/python3.12/site-packages/sympy/polys/polyconfig.py
    - lib/python3.12/site-packages/sympy/polys/polyerrors.py
    - lib/python3.12/site-packages/sympy/polys/polyfuncs.py
    - lib/python3.12/site-packages/sympy/polys/polymatrix.py
    - lib/python3.12/site-packages/sympy/polys/polyoptions.py
    - lib/python3.12/site-packages/sympy/polys/polyquinticconst.py
    - lib/python3.12/site-packages/sympy/polys/polyroots.py
    - lib/python3.12/site-packages/sympy/polys/polytools.py
    - lib/python3.12/site-packages/sympy/polys/polyutils.py
    - lib/python3.12/site-packages/sympy/polys/puiseux.py
    - lib/python3.12/site-packages/sympy/polys/rationaltools.py
    - lib/python3.12/site-packages/sympy/polys/ring_series.py
    - lib/python3.12/site-packages/sympy/polys/rings.py
    - lib/python3.12/site-packages/sympy/polys/rootisolation.py
    - lib/python3.12/site-packages/sympy/polys/rootoftools.py
    - lib/python3.12/site-packages/sympy/polys/solvers.py
    - lib/python3.12/site-packages/sympy/polys/specialpolys.py
    - lib/python3.12/site-packages/sympy/polys/sqfreetools.py
    - lib/python3.12/site-packages/sympy/polys/subresultants_qq_zz.py
    - lib/python3.12/site-packages/sympy/polys/tests/__init__.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_appellseqs.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_constructor.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_densearith.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_densebasic.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_densetools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_dispersion.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_distributedmodules.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_euclidtools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_factortools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_fields.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_galoistools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_groebnertools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_heuristicgcd.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_hypothesis.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_injections.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_modulargcd.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_monomials.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_multivariate_resultants.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_orderings.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_orthopolys.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_partfrac.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polyclasses.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polyfuncs.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polymatrix.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polyoptions.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polyroots.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polytools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_polyutils.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_puiseux.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_pythonrational.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_rationaltools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_ring_series.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_rings.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_rootisolation.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_rootoftools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_solvers.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_specialpolys.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_sqfreetools.py
    - lib/python3.12/site-packages/sympy/polys/tests/test_subresultants_qq_zz.py
    - lib/python3.12/site-packages/sympy/printing/__init__.py
    - lib/python3.12/site-packages/sympy/printing/aesaracode.py
    - lib/python3.12/site-packages/sympy/printing/c.py
    - lib/python3.12/site-packages/sympy/printing/codeprinter.py
    - lib/python3.12/site-packages/sympy/printing/conventions.py
    - lib/python3.12/site-packages/sympy/printing/cxx.py
    - lib/python3.12/site-packages/sympy/printing/defaults.py
    - lib/python3.12/site-packages/sympy/printing/dot.py
    - lib/python3.12/site-packages/sympy/printing/fortran.py
    - lib/python3.12/site-packages/sympy/printing/glsl.py
    - lib/python3.12/site-packages/sympy/printing/gtk.py
    - lib/python3.12/site-packages/sympy/printing/jscode.py
    - lib/python3.12/site-packages/sympy/printing/julia.py
    - lib/python3.12/site-packages/sympy/printing/lambdarepr.py
    - lib/python3.12/site-packages/sympy/printing/latex.py
    - lib/python3.12/site-packages/sympy/printing/llvmjitcode.py
    - lib/python3.12/site-packages/sympy/printing/maple.py
    - lib/python3.12/site-packages/sympy/printing/mathematica.py
    - lib/python3.12/site-packages/sympy/printing/mathml.py
    - lib/python3.12/site-packages/sympy/printing/numpy.py
    - lib/python3.12/site-packages/sympy/printing/octave.py
    - lib/python3.12/site-packages/sympy/printing/precedence.py
    - lib/python3.12/site-packages/sympy/printing/pretty/__init__.py
    - lib/python3.12/site-packages/sympy/printing/pretty/pretty.py
    - lib/python3.12/site-packages/sympy/printing/pretty/pretty_symbology.py
    - lib/python3.12/site-packages/sympy/printing/pretty/stringpict.py
    - lib/python3.12/site-packages/sympy/printing/pretty/tests/__init__.py
    - lib/python3.12/site-packages/sympy/printing/pretty/tests/test_pretty.py
    - lib/python3.12/site-packages/sympy/printing/preview.py
    - lib/python3.12/site-packages/sympy/printing/printer.py
    - lib/python3.12/site-packages/sympy/printing/pycode.py
    - lib/python3.12/site-packages/sympy/printing/python.py
    - lib/python3.12/site-packages/sympy/printing/pytorch.py
    - lib/python3.12/site-packages/sympy/printing/rcode.py
    - lib/python3.12/site-packages/sympy/printing/repr.py
    - lib/python3.12/site-packages/sympy/printing/rust.py
    - lib/python3.12/site-packages/sympy/printing/smtlib.py
    - lib/python3.12/site-packages/sympy/printing/str.py
    - lib/python3.12/site-packages/sympy/printing/tableform.py
    - lib/python3.12/site-packages/sympy/printing/tensorflow.py
    - lib/python3.12/site-packages/sympy/printing/tests/__init__.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_aesaracode.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_c.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_codeprinter.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_conventions.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_cupy.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_cxx.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_dot.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_fortran.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_glsl.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_gtk.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_jax.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_jscode.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_julia.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_lambdarepr.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_latex.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_llvmjit.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_maple.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_mathematica.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_mathml.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_numpy.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_octave.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_precedence.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_preview.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_pycode.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_python.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_rcode.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_repr.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_rust.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_smtlib.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_str.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_tableform.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_tensorflow.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_theanocode.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_torch.py
    - lib/python3.12/site-packages/sympy/printing/tests/test_tree.py
    - lib/python3.12/site-packages/sympy/printing/theanocode.py
    - lib/python3.12/site-packages/sympy/printing/tree.py
    - lib/python3.12/site-packages/sympy/release.py
    - lib/python3.12/site-packages/sympy/sandbox/__init__.py
    - lib/python3.12/site-packages/sympy/sandbox/indexed_integrals.py
    - lib/python3.12/site-packages/sympy/sandbox/tests/__init__.py
    - lib/python3.12/site-packages/sympy/sandbox/tests/test_indexed_integrals.py
    - lib/python3.12/site-packages/sympy/series/__init__.py
    - lib/python3.12/site-packages/sympy/series/acceleration.py
    - lib/python3.12/site-packages/sympy/series/approximants.py
    - lib/python3.12/site-packages/sympy/series/aseries.py
    - lib/python3.12/site-packages/sympy/series/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/series/benchmarks/bench_limit.py
    - lib/python3.12/site-packages/sympy/series/benchmarks/bench_order.py
    - lib/python3.12/site-packages/sympy/series/formal.py
    - lib/python3.12/site-packages/sympy/series/fourier.py
    - lib/python3.12/site-packages/sympy/series/gruntz.py
    - lib/python3.12/site-packages/sympy/series/kauers.py
    - lib/python3.12/site-packages/sympy/series/limits.py
    - lib/python3.12/site-packages/sympy/series/limitseq.py
    - lib/python3.12/site-packages/sympy/series/order.py
    - lib/python3.12/site-packages/sympy/series/residues.py
    - lib/python3.12/site-packages/sympy/series/sequences.py
    - lib/python3.12/site-packages/sympy/series/series.py
    - lib/python3.12/site-packages/sympy/series/series_class.py
    - lib/python3.12/site-packages/sympy/series/tests/__init__.py
    - lib/python3.12/site-packages/sympy/series/tests/test_approximants.py
    - lib/python3.12/site-packages/sympy/series/tests/test_aseries.py
    - lib/python3.12/site-packages/sympy/series/tests/test_demidovich.py
    - lib/python3.12/site-packages/sympy/series/tests/test_formal.py
    - lib/python3.12/site-packages/sympy/series/tests/test_fourier.py
    - lib/python3.12/site-packages/sympy/series/tests/test_gruntz.py
    - lib/python3.12/site-packages/sympy/series/tests/test_kauers.py
    - lib/python3.12/site-packages/sympy/series/tests/test_limits.py
    - lib/python3.12/site-packages/sympy/series/tests/test_limitseq.py
    - lib/python3.12/site-packages/sympy/series/tests/test_lseries.py
    - lib/python3.12/site-packages/sympy/series/tests/test_nseries.py
    - lib/python3.12/site-packages/sympy/series/tests/test_order.py
    - lib/python3.12/site-packages/sympy/series/tests/test_residues.py
    - lib/python3.12/site-packages/sympy/series/tests/test_sequences.py
    - lib/python3.12/site-packages/sympy/series/tests/test_series.py
    - lib/python3.12/site-packages/sympy/sets/__init__.py
    - lib/python3.12/site-packages/sympy/sets/conditionset.py
    - lib/python3.12/site-packages/sympy/sets/contains.py
    - lib/python3.12/site-packages/sympy/sets/fancysets.py
    - lib/python3.12/site-packages/sympy/sets/handlers/__init__.py
    - lib/python3.12/site-packages/sympy/sets/handlers/add.py
    - lib/python3.12/site-packages/sympy/sets/handlers/comparison.py
    - lib/python3.12/site-packages/sympy/sets/handlers/functions.py
    - lib/python3.12/site-packages/sympy/sets/handlers/intersection.py
    - lib/python3.12/site-packages/sympy/sets/handlers/issubset.py
    - lib/python3.12/site-packages/sympy/sets/handlers/mul.py
    - lib/python3.12/site-packages/sympy/sets/handlers/power.py
    - lib/python3.12/site-packages/sympy/sets/handlers/union.py
    - lib/python3.12/site-packages/sympy/sets/ordinals.py
    - lib/python3.12/site-packages/sympy/sets/powerset.py
    - lib/python3.12/site-packages/sympy/sets/setexpr.py
    - lib/python3.12/site-packages/sympy/sets/sets.py
    - lib/python3.12/site-packages/sympy/sets/tests/__init__.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_conditionset.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_contains.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_fancysets.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_ordinals.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_powerset.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_setexpr.py
    - lib/python3.12/site-packages/sympy/sets/tests/test_sets.py
    - lib/python3.12/site-packages/sympy/simplify/__init__.py
    - lib/python3.12/site-packages/sympy/simplify/_cse_diff.py
    - lib/python3.12/site-packages/sympy/simplify/combsimp.py
    - lib/python3.12/site-packages/sympy/simplify/cse_main.py
    - lib/python3.12/site-packages/sympy/simplify/cse_opts.py
    - lib/python3.12/site-packages/sympy/simplify/epathtools.py
    - lib/python3.12/site-packages/sympy/simplify/fu.py
    - lib/python3.12/site-packages/sympy/simplify/gammasimp.py
    - lib/python3.12/site-packages/sympy/simplify/hyperexpand.py
    - lib/python3.12/site-packages/sympy/simplify/hyperexpand_doc.py
    - lib/python3.12/site-packages/sympy/simplify/powsimp.py
    - lib/python3.12/site-packages/sympy/simplify/radsimp.py
    - lib/python3.12/site-packages/sympy/simplify/ratsimp.py
    - lib/python3.12/site-packages/sympy/simplify/simplify.py
    - lib/python3.12/site-packages/sympy/simplify/sqrtdenest.py
    - lib/python3.12/site-packages/sympy/simplify/tests/__init__.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_combsimp.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_cse.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_cse_diff.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_epathtools.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_fu.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_function.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_gammasimp.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_hyperexpand.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_powsimp.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_radsimp.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_ratsimp.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_rewrite.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_simplify.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_sqrtdenest.py
    - lib/python3.12/site-packages/sympy/simplify/tests/test_trigsimp.py
    - lib/python3.12/site-packages/sympy/simplify/traversaltools.py
    - lib/python3.12/site-packages/sympy/simplify/trigsimp.py
    - lib/python3.12/site-packages/sympy/solvers/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/benchmarks/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/benchmarks/bench_solvers.py
    - lib/python3.12/site-packages/sympy/solvers/bivariate.py
    - lib/python3.12/site-packages/sympy/solvers/decompogen.py
    - lib/python3.12/site-packages/sympy/solvers/deutils.py
    - lib/python3.12/site-packages/sympy/solvers/diophantine/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/diophantine/diophantine.py
    - lib/python3.12/site-packages/sympy/solvers/diophantine/tests/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/diophantine/tests/test_diophantine.py
    - lib/python3.12/site-packages/sympy/solvers/inequalities.py
    - lib/python3.12/site-packages/sympy/solvers/ode/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/ode/hypergeometric.py
    - lib/python3.12/site-packages/sympy/solvers/ode/lie_group.py
    - lib/python3.12/site-packages/sympy/solvers/ode/nonhomogeneous.py
    - lib/python3.12/site-packages/sympy/solvers/ode/ode.py
    - lib/python3.12/site-packages/sympy/solvers/ode/riccati.py
    - lib/python3.12/site-packages/sympy/solvers/ode/single.py
    - lib/python3.12/site-packages/sympy/solvers/ode/subscheck.py
    - lib/python3.12/site-packages/sympy/solvers/ode/systems.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_lie_group.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_ode.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_riccati.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_single.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_subscheck.py
    - lib/python3.12/site-packages/sympy/solvers/ode/tests/test_systems.py
    - lib/python3.12/site-packages/sympy/solvers/pde.py
    - lib/python3.12/site-packages/sympy/solvers/polysys.py
    - lib/python3.12/site-packages/sympy/solvers/recurr.py
    - lib/python3.12/site-packages/sympy/solvers/simplex.py
    - lib/python3.12/site-packages/sympy/solvers/solvers.py
    - lib/python3.12/site-packages/sympy/solvers/solveset.py
    - lib/python3.12/site-packages/sympy/solvers/tests/__init__.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_constantsimp.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_decompogen.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_inequalities.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_numeric.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_pde.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_polysys.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_recurr.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_simplex.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_solvers.py
    - lib/python3.12/site-packages/sympy/solvers/tests/test_solveset.py
    - lib/python3.12/site-packages/sympy/stats/__init__.py
    - lib/python3.12/site-packages/sympy/stats/compound_rv.py
    - lib/python3.12/site-packages/sympy/stats/crv.py
    - lib/python3.12/site-packages/sympy/stats/crv_types.py
    - lib/python3.12/site-packages/sympy/stats/drv.py
    - lib/python3.12/site-packages/sympy/stats/drv_types.py
    - lib/python3.12/site-packages/sympy/stats/error_prop.py
    - lib/python3.12/site-packages/sympy/stats/frv.py
    - lib/python3.12/site-packages/sympy/stats/frv_types.py
    - lib/python3.12/site-packages/sympy/stats/joint_rv.py
    - lib/python3.12/site-packages/sympy/stats/joint_rv_types.py
    - lib/python3.12/site-packages/sympy/stats/matrix_distributions.py
    - lib/python3.12/site-packages/sympy/stats/random_matrix.py
    - lib/python3.12/site-packages/sympy/stats/random_matrix_models.py
    - lib/python3.12/site-packages/sympy/stats/rv.py
    - lib/python3.12/site-packages/sympy/stats/rv_interface.py
    - lib/python3.12/site-packages/sympy/stats/sampling/__init__.py
    - lib/python3.12/site-packages/sympy/stats/sampling/sample_numpy.py
    - lib/python3.12/site-packages/sympy/stats/sampling/sample_pymc.py
    - lib/python3.12/site-packages/sympy/stats/sampling/sample_scipy.py
    - lib/python3.12/site-packages/sympy/stats/sampling/tests/__init__.py
    - lib/python3.12/site-packages/sympy/stats/sampling/tests/test_sample_continuous_rv.py
    - lib/python3.12/site-packages/sympy/stats/sampling/tests/test_sample_discrete_rv.py
    - lib/python3.12/site-packages/sympy/stats/sampling/tests/test_sample_finite_rv.py
    - lib/python3.12/site-packages/sympy/stats/stochastic_process.py
    - lib/python3.12/site-packages/sympy/stats/stochastic_process_types.py
    - lib/python3.12/site-packages/sympy/stats/symbolic_multivariate_probability.py
    - lib/python3.12/site-packages/sympy/stats/symbolic_probability.py
    - lib/python3.12/site-packages/sympy/stats/tests/__init__.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_compound_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_continuous_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_discrete_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_error_prop.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_finite_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_joint_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_matrix_distributions.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_mix.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_random_matrix.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_rv.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_stochastic_process.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_symbolic_multivariate.py
    - lib/python3.12/site-packages/sympy/stats/tests/test_symbolic_probability.py
    - lib/python3.12/site-packages/sympy/strategies/__init__.py
    - lib/python3.12/site-packages/sympy/strategies/branch/__init__.py
    - lib/python3.12/site-packages/sympy/strategies/branch/core.py
    - lib/python3.12/site-packages/sympy/strategies/branch/tests/__init__.py
    - lib/python3.12/site-packages/sympy/strategies/branch/tests/test_core.py
    - lib/python3.12/site-packages/sympy/strategies/branch/tests/test_tools.py
    - lib/python3.12/site-packages/sympy/strategies/branch/tests/test_traverse.py
    - lib/python3.12/site-packages/sympy/strategies/branch/tools.py
    - lib/python3.12/site-packages/sympy/strategies/branch/traverse.py
    - lib/python3.12/site-packages/sympy/strategies/core.py
    - lib/python3.12/site-packages/sympy/strategies/rl.py
    - lib/python3.12/site-packages/sympy/strategies/tests/__init__.py
    - lib/python3.12/site-packages/sympy/strategies/tests/test_core.py
    - lib/python3.12/site-packages/sympy/strategies/tests/test_rl.py
    - lib/python3.12/site-packages/sympy/strategies/tests/test_tools.py
    - lib/python3.12/site-packages/sympy/strategies/tests/test_traverse.py
    - lib/python3.12/site-packages/sympy/strategies/tests/test_tree.py
    - lib/python3.12/site-packages/sympy/strategies/tools.py
    - lib/python3.12/site-packages/sympy/strategies/traverse.py
    - lib/python3.12/site-packages/sympy/strategies/tree.py
    - lib/python3.12/site-packages/sympy/strategies/util.py
    - lib/python3.12/site-packages/sympy/tensor/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/array/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/array/array_comprehension.py
    - lib/python3.12/site-packages/sympy/tensor/array/array_derivatives.py
    - lib/python3.12/site-packages/sympy/tensor/array/arrayop.py
    - lib/python3.12/site-packages/sympy/tensor/array/dense_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/array_expressions.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/arrayexpr_derivatives.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/conv_array_to_indexed.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/conv_array_to_matrix.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/conv_indexed_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/conv_matrix_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/from_array_to_indexed.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/from_array_to_matrix.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/from_indexed_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/from_matrix_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_array_expressions.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_arrayexpr_derivatives.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_as_explicit.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_convert_array_to_indexed.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_convert_array_to_matrix.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_convert_indexed_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_convert_matrix_to_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/tests/test_deprecated_conv_modules.py
    - lib/python3.12/site-packages/sympy/tensor/array/expressions/utils.py
    - lib/python3.12/site-packages/sympy/tensor/array/mutable_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/sparse_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_array_comprehension.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_array_derivatives.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_arrayop.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_immutable_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_mutable_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_ndim_array.py
    - lib/python3.12/site-packages/sympy/tensor/array/tests/test_ndim_array_conversions.py
    - lib/python3.12/site-packages/sympy/tensor/functions.py
    - lib/python3.12/site-packages/sympy/tensor/index_methods.py
    - lib/python3.12/site-packages/sympy/tensor/indexed.py
    - lib/python3.12/site-packages/sympy/tensor/tensor.py
    - lib/python3.12/site-packages/sympy/tensor/tests/__init__.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_functions.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_index_methods.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_indexed.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_printing.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_tensor.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_tensor_element.py
    - lib/python3.12/site-packages/sympy/tensor/tests/test_tensor_operators.py
    - lib/python3.12/site-packages/sympy/tensor/toperators.py
    - lib/python3.12/site-packages/sympy/testing/__init__.py
    - lib/python3.12/site-packages/sympy/testing/matrices.py
    - lib/python3.12/site-packages/sympy/testing/pytest.py
    - lib/python3.12/site-packages/sympy/testing/quality_unicode.py
    - lib/python3.12/site-packages/sympy/testing/randtest.py
    - lib/python3.12/site-packages/sympy/testing/runtests.py
    - lib/python3.12/site-packages/sympy/testing/runtests_pytest.py
    - lib/python3.12/site-packages/sympy/testing/tests/__init__.py
    - lib/python3.12/site-packages/sympy/testing/tests/diagnose_imports.py
    - lib/python3.12/site-packages/sympy/testing/tests/test_code_quality.py
    - lib/python3.12/site-packages/sympy/testing/tests/test_deprecated.py
    - lib/python3.12/site-packages/sympy/testing/tests/test_module_imports.py
    - lib/python3.12/site-packages/sympy/testing/tests/test_pytest.py
    - lib/python3.12/site-packages/sympy/testing/tests/test_runtests_pytest.py
    - lib/python3.12/site-packages/sympy/testing/tmpfiles.py
    - lib/python3.12/site-packages/sympy/this.py
    - lib/python3.12/site-packages/sympy/unify/__init__.py
    - lib/python3.12/site-packages/sympy/unify/core.py
    - lib/python3.12/site-packages/sympy/unify/rewrite.py
    - lib/python3.12/site-packages/sympy/unify/tests/__init__.py
    - lib/python3.12/site-packages/sympy/unify/tests/test_rewrite.py
    - lib/python3.12/site-packages/sympy/unify/tests/test_sympy.py
    - lib/python3.12/site-packages/sympy/unify/tests/test_unify.py
    - lib/python3.12/site-packages/sympy/unify/usympy.py
    - lib/python3.12/site-packages/sympy/utilities/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/availability.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/compilation.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/runners.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/tests/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/tests/test_compilation.py
    - lib/python3.12/site-packages/sympy/utilities/_compilation/util.py
    - lib/python3.12/site-packages/sympy/utilities/autowrap.py
    - lib/python3.12/site-packages/sympy/utilities/codegen.py
    - lib/python3.12/site-packages/sympy/utilities/decorator.py
    - lib/python3.12/site-packages/sympy/utilities/enumerative.py
    - lib/python3.12/site-packages/sympy/utilities/exceptions.py
    - lib/python3.12/site-packages/sympy/utilities/iterables.py
    - lib/python3.12/site-packages/sympy/utilities/lambdify.py
    - lib/python3.12/site-packages/sympy/utilities/magic.py
    - lib/python3.12/site-packages/sympy/utilities/matchpy_connector.py
    - lib/python3.12/site-packages/sympy/utilities/mathml/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/mathml/data/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/mathml/data/mmlctop.xsl
    - lib/python3.12/site-packages/sympy/utilities/mathml/data/mmltex.xsl
    - lib/python3.12/site-packages/sympy/utilities/mathml/data/simple_mmlctop.xsl
    - lib/python3.12/site-packages/sympy/utilities/memoization.py
    - lib/python3.12/site-packages/sympy/utilities/misc.py
    - lib/python3.12/site-packages/sympy/utilities/pkgdata.py
    - lib/python3.12/site-packages/sympy/utilities/pytest.py
    - lib/python3.12/site-packages/sympy/utilities/randtest.py
    - lib/python3.12/site-packages/sympy/utilities/runtests.py
    - lib/python3.12/site-packages/sympy/utilities/source.py
    - lib/python3.12/site-packages/sympy/utilities/tests/__init__.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_autowrap.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_codegen.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_codegen_julia.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_codegen_octave.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_codegen_rust.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_decorator.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_deprecated.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_enumerative.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_exceptions.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_iterables.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_lambdify.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_matchpy_connector.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_mathml.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_misc.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_pickling.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_source.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_timeutils.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_wester.py
    - lib/python3.12/site-packages/sympy/utilities/tests/test_xxe.py
    - lib/python3.12/site-packages/sympy/utilities/timeutils.py
    - lib/python3.12/site-packages/sympy/utilities/tmpfiles.py
    - lib/python3.12/site-packages/sympy/vector/__init__.py
    - lib/python3.12/site-packages/sympy/vector/basisdependent.py
    - lib/python3.12/site-packages/sympy/vector/coordsysrect.py
    - lib/python3.12/site-packages/sympy/vector/deloperator.py
    - lib/python3.12/site-packages/sympy/vector/dyadic.py
    - lib/python3.12/site-packages/sympy/vector/functions.py
    - lib/python3.12/site-packages/sympy/vector/implicitregion.py
    - lib/python3.12/site-packages/sympy/vector/integrals.py
    - lib/python3.12/site-packages/sympy/vector/kind.py
    - lib/python3.12/site-packages/sympy/vector/operators.py
    - lib/python3.12/site-packages/sympy/vector/orienters.py
    - lib/python3.12/site-packages/sympy/vector/parametricregion.py
    - lib/python3.12/site-packages/sympy/vector/point.py
    - lib/python3.12/site-packages/sympy/vector/scalar.py
    - lib/python3.12/site-packages/sympy/vector/tests/__init__.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_coordsysrect.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_dyadic.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_field_functions.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_functions.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_implicitregion.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_integrals.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_operators.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_parametricregion.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_printing.py
    - lib/python3.12/site-packages/sympy/vector/tests/test_vector.py
    - lib/python3.12/site-packages/sympy/vector/vector.py
    - bin/isympy
Linking paramak-0.9.11-pyhd8ed1ab_0

Transaction finished

- [2026-06-15T19:30:12-04:00] EXIT_STATUS: 0
- [2026-06-15T19:33:18-04:00] Starting WSL Julia/FUSE install attempts.
- [2026-06-15T19:33:18-04:00] COMMAND: bash -lc curl -fsSL https://install.julialang.org | sh -s -- -y

info: downloading installer
Welcome to Julia!

This will download and install the official Julia Language distribution
and its version manager Juliaup.

Juliaup will be installed into the Juliaup home directory, located at:

  /home/craig/.juliaup

The julia, juliaup and other commands will be added to
Juliaup's bin directory, located at:

  /home/craig/.juliaup/bin

This path will then be added to your PATH environment variable by
modifying the profile files located at:

  /home/craig/.bashrc
  /home/craig/.profile

Julia will look for a new version of Juliaup itself every 1440 minutes when you start julia.

You can uninstall at any time with juliaup self uninstall and these
changes will be reverted.

Now installing Juliaup
    Checking for new Julia versions
  Installing Julia 1.12.6+0.x64.linux.gnu
         Add Installed Julia channel 'release'
   Configure Default Julia version set to 'release'.
Julia was successfully installed on your system.

Depending on which shell you are using, run one of the following
commands to reload the PATH environment variable:

  . /home/craig/.bashrc
  . /home/craig/.profile

- [2026-06-15T19:33:29-04:00] EXIT_STATUS: 0
- [2026-06-15T19:33:29-04:00] COMMAND: julia --version
julia version 1.12.6
- [2026-06-15T19:33:29-04:00] EXIT_STATUS: 0
- [2026-06-15T19:33:29-04:00] COMMAND: julia install/install_julia_fuse.jl
ERROR: SystemError: opening file "/mnt/c/Users/Craig/projects/mini_tokamak_designer/install/install_julia_fuse.jl\r": No such file or directory
Stacktrace:
 [1] include(mod::Module, _path::String)
   @ Base ./Base.jl:306
 [2] exec_options(opts::Base.JLOptions)
   @ Base ./client.jl:317
 [3] _start()
   @ Base ./client.jl:550
- [2026-06-15T19:33:30-04:00] EXIT_STATUS: 1

## PROCESS adapter v1 implementation on 2026-06-16

- Implemented `src/mini_tokamak/solvers/process_adapter.py` v1.
  - Default behavior: generate per-candidate PROCESS `IN.DAT` files from a validated template.
  - Execution behavior: opt-in only with `MINI_TOKAMAK_PROCESS_EXECUTE=1` to avoid turning a 100-candidate sweep into a long PROCESS batch.
  - Template selection:
    - `MINI_TOKAMAK_PROCESS_TEMPLATE` if set.
    - `/home/craig/src/PROCESS/examples/data/large_tokamak_eval_IN.DAT` in the WSL install.
  - Output location:
    - `data/runs/<run_id>/external_solvers/process/<candidate_id>/IN.DAT`
    - `stdout.txt`, `stderr.txt`, and `MFILE.DAT` when execution is enabled.
  - Safety/realism note: generated files are labelled simulation-only and low-fidelity; candidate `Ip` is recorded but not directly mapped because the current PROCESS template uses current-scaling variables.
- Added adapter run-directory hook:
  - `SolverAdapter.prepare_run(run_id, output_dir)`
  - Random-search now calls this for each adapter before screening starts.
- Added tests:
  - `tests/test_process_adapter.py`
  - Tests cover PROCESS deck generation without requiring PROCESS and text fallback parsing for small MFILE-like files.
- Validation commands completed on Windows:
  - `C:\Users\Craig\projects\mini_tokamak_designer\.venv\Scripts\python.exe -m pytest`
  - Result: `8 passed`
  - `C:\Users\Craig\projects\mini_tokamak_designer\.venv\Scripts\python.exe -m ruff check src tests`
  - Result: `All checks passed`
- Validation commands completed in WSL:
  - `source ~/miniforge/etc/profile.d/conda.sh && conda activate mini-tokamak && cd ~/projects/mini_tokamak_designer && python -m pytest`
  - Result: `8 passed`
  - `python -m ruff check src tests`
  - Result: `All checks passed`
- WSL default non-executing sweep:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T004031Z-293771db`
  - Result: three PROCESS input decks generated under `external_solvers/process/.../IN.DAT`; PROCESS execution skipped as designed.
- WSL explicit PROCESS execution smoke:
  - Command: `MINI_TOKAMAK_PROCESS_EXECUTE=1 MINI_TOKAMAK_PROCESS_TIMEOUT_S=180 mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random`
  - Initial result: PROCESS rejected `p_plant_electric_net_required_mw = 0` because the valid range is `(1.0, 10000.0)`.
  - Workaround implemented: set the MVP template override to `p_plant_electric_net_required_mw = 1.0`.
  - Final run ID: `20260616T004322Z-e8ee96c7`
  - Result: PROCESS executed and failed cleanly with return code `1`; adapter captured stdout/stderr/MFILE paths and failure hint:
    - `process.core.exceptions.ProcessValueError: Triangularity is negative without i_plasma_current = 8 selected: triang=-0.09750482383, i_plasma_current=4`
  - Interpretation: this is a useful systems-code failure for the sampled candidate/current-scaling mode, not an install failure and not a viability claim.
- Final WSL acceptance sweep after PROCESS adapter changes:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T004429Z-8468de06`
  - Result: 100 candidate JSON results, 100 PROCESS input decks, Markdown/HTML reports, plots, `top_candidates.csv`, and CAD PNG/SVG/STEP outputs were generated successfully.

## FUSE.jl adapter v1 implementation on 2026-06-16

- Official docs rechecked:
  - FUSE install guide: `https://fuse.help/dev/install.html`
  - FUSE GitHub repo: `https://github.com/ProjectTorreyPines/FUSE.jl`
  - Docs command path:
    - `using Pkg`
    - `Pkg.Registry.add(RegistrySpec(url="https://github.com/ProjectTorreyPines/FuseRegistry.jl.git"))`
    - `Pkg.Registry.add("General")`
    - `Pkg.add("FUSE")`
    - `using FUSE`
    - `ini, act = FUSE.case_parameters(:FPP)`
    - `dd = FUSE.init(ini, act)`
- Updated `install/install_julia_fuse.jl`:
  - Registry adds are now idempotent/tolerant of already-added registries.
  - Adds `FUSE`.
  - Adds `JSON` explicitly because generated standalone Julia runner scripts use `using JSON`; FUSE had JSON in its manifest tree, but it was not a direct top-level dependency for standalone `using JSON`.
  - Runs the official-style `FUSE.case_parameters(:FPP)` and `FUSE.init(ini, act)` smoke.
- Added `install/fuse_smoke.jl`:
  - Imports `FUSE` and `JSON`.
  - Runs `FUSE.case_parameters(:FPP)` and `FUSE.init`.
- FUSE install retry:
  - First retry still failed because Julia's LibGit2 did not honor the per-process Git URL rewrite and attempted to clone `git@github.com:ProjectTorreyPines/ALPHA.jl.git`.
  - Successful command used Julia's command-line Git mode plus a per-process Git rewrite:
    - `env JULIA_PKG_USE_CLI_GIT=true GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf GIT_CONFIG_VALUE_0=git@github.com: /home/craig/.juliaup/bin/julia install/install_julia_fuse.jl`
  - No global Git config was changed.
  - Result: `FUSE v1.1.4` installed and `FUSE import/init OK`.
  - FUSE package path: `/home/craig/.julia/packages/FUSE/bnnVV`
  - Smoke type: `IMASdd.dd{Float64}`
- Updated `src/mini_tokamak/solvers/fuse_adapter.py`:
  - Probes `using FUSE; using JSON`.
  - Uses `~/.juliaup/bin/julia` if `julia` is not on PATH.
  - Writes per-candidate:
    - `candidate.json`
    - `fuse_candidate_probe.jl`
  - Execution is opt-in with `MINI_TOKAMAK_FUSE_EXECUTE=1`.
  - Execution outputs:
    - `fuse_result.json`
    - `stdout.txt`
    - `stderr.txt`
  - MVP mapping currently attempts:
    - `ini.equilibrium.R0`
    - `ini.equilibrium.epsilon` via FUSE field symbol
    - `ini.equilibrium.kappa` via FUSE field symbol
    - `ini.equilibrium.delta` via FUSE field symbol
  - Successful `FUSE.init` is returned as `WARNING`, not `PASS`, because it proves adapter plumbing only and is not a full FUSE viability analysis.
- Added tests:
  - `tests/test_fuse_adapter.py`
  - Tests cover non-executing artifact generation and JSON result parsing without requiring Julia/FUSE.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `10 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `10 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `mini-tokamak verify`
    - Result: `FUSE.jl PASS`
- FUSE default non-executing sweep:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T015153Z-b239df8f`
  - Result: 3 FUSE `candidate.json` files and 3 FUSE Julia probe scripts generated.
- FUSE explicit execution smoke:
  - Initial run ID: `20260616T015222Z-74e57f34`
  - Result: failed before FUSE execution because `JSON` was not a direct Julia dependency.
  - Workaround implemented: `Pkg.add("JSON")` in `install/install_julia_fuse.jl`, and adapter probe now requires `using FUSE; using JSON`.
  - Final command: `MINI_TOKAMAK_FUSE_EXECUTE=1 MINI_TOKAMAK_FUSE_TIMEOUT_S=600 mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random`
  - Final run ID: `20260616T020333Z-11f79460`
  - Result: `FUSE.jl` solver result status `WARNING`, return code `0`, `julia_status=PASS`, and `dd_type=IMASdd.dd{Float64}`.
  - Mapped fields recorded in `fuse_result.json`: `ini.equilibrium.R0`, `ini.equilibrium.epsilon`, `ini.equilibrium.kappa`, and `ini.equilibrium.delta`.
- Final WSL acceptance sweep after FUSE adapter changes:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T020921Z-f30fc6c6`
  - Result: 100 candidate JSON results, 100 PROCESS input decks, 100 FUSE `candidate.json` files, 100 FUSE Julia probe scripts, Markdown/HTML reports, plots, `top_candidates.csv`, and CAD PNG/SVG/STEP outputs were generated successfully.

## FUSE.jl top-candidate actor pass on 2026-06-16

- Implemented a post-screening FUSE actor workflow:
  - New CLI option: `--fuse-top-n N`
  - New CLI option: `--fuse-actors ActorPFdesign,ActorCXbuild,...`
  - Default actor sequence: `ActorPFdesign`
  - Normal `--n 100` runs still do not execute heavyweight FUSE actor workflows unless `--fuse-top-n` is set.
- Updated `src/mini_tokamak/solvers/fuse_adapter.py`:
  - Added `run_actor_sequence(candidate, rank, actors)`.
  - Added generated Julia script `fuse_actor_sequence.jl`.
  - Writes `fuse_actor_sequence.json`, `actor_stdout.txt`, and `actor_stderr.txt`.
  - Captures per-actor status, elapsed time, error type, error text, stacktrace, and dominant failure actor.
  - Successful actor sequences return solver status `WARNING`, not `PASS`, to avoid viability claims.
  - Increased default FUSE timeout from `240` seconds to `600` seconds; override remains `MINI_TOKAMAK_FUSE_TIMEOUT_S`.
- Updated random-search flow:
  - Screens all candidates first.
  - Sorts by objective score.
  - Runs FUSE actor sequence only on the top N candidates.
  - Rewrites updated candidate JSON files and replaces the DuckDB result row for those candidates.
- Updated reports:
  - Best-candidate report now includes solver results and raw output paths.
- Added/updated tests:
  - `tests/test_fuse_adapter.py` now covers actor-sequence result handling and actor-list parsing.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `12 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `12 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
- First actor-pass smoke:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random --fuse-top-n 1`
  - Run ID: `20260616T022126Z-767d10da`
  - Result: actor pass reached the timeout at the previous 240-second default; solver result captured timeout failure cleanly.
- Final actor-pass smoke:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random --fuse-top-n 1`
  - Run ID: `20260616T023320Z-a823f1b0`
  - Result: `FUSE.jl actors` solver result status `WARNING`, `julia_status=PASS`, `init_status=PASS`, `dd_type=IMASdd.dd{Float64}`.
  - Actor result: `ActorPFdesign` returned `PASS` in about `10.1` seconds after initialization/startup.

## FreeGS adapter v1 implementation on 2026-06-16

- User-facing Linux visibility:
  - Opened a visible Windows Terminal Ubuntu tab so WSL is interactive rather than hidden in the background.
  - Command:
    - `Start-Process wt.exe -ArgumentList @('-p','Ubuntu','--title','MiniTokamak WSL','bash','-lc','cd ~/projects/mini_tokamak_designer; source ~/miniforge/etc/profile.d/conda.sh; conda activate mini-tokamak; echo "MiniTokamak Designer WSL is visible here."; echo "Try: mini-tokamak verify"; exec bash')`
  - Correction: this command is brittle because Windows Terminal treats semicolons as command separators and can try to launch each Linux shell fragment as a separate Windows command.
  - Added `scripts/open_wsl_terminal.ps1`, which uses Windows-compatible process argument quoting and joins the Linux startup commands with `&&` so the command is passed to `bash -lc` as one argument.
  - Corrected launch command:
    - `.\scripts\open_wsl_terminal.ps1`
  - Follow-up correction: the inline `bash -lc` approach could still open and immediately close Windows Terminal if any startup command exited early.
  - Added `scripts/start_wsl_shell.sh`, a Linux-side startup script that:
    - enters `/home/craig/projects/mini_tokamak_designer`
    - sources Miniforge
    - activates `mini-tokamak`
    - prints the active `python` and `mini-tokamak` paths
    - always ends with `exec bash -i` unless called with `--check`
  - Updated `scripts/open_wsl_terminal.ps1` to launch:
    - `wt.exe new-tab --title "MiniTokamak WSL" cmd.exe /d /k wsl.exe -d Ubuntu -- bash /mnt/c/Users/Craig/projects/mini_tokamak_designer/scripts/start_wsl_shell.sh`
  - The `cmd.exe /d /k` wrapper is intentional: if WSL startup fails, the tab remains open and shows the error instead of closing immediately.
  - Validation:
    - `.\scripts\open_wsl_terminal.ps1 -DryRun` prints the expected `wt.exe` command.
    - `wsl.exe -d Ubuntu -- bash /mnt/c/Users/Craig/projects/mini_tokamak_designer/scripts/start_wsl_shell.sh --check` reaches the repo and resolves the conda env `python` and `mini-tokamak`.
- Local FreeGS source inspected:
  - FreeGS version: `0.8.2`
  - Package path: `/home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/freegs/__init__.py`
  - Bundled fixed-boundary test pattern used: `freegs.tests.test_equilibrium`
  - Relevant API pattern:
    - `equilibrium.Equilibrium(..., boundary=boundary.fixedBoundary)`
    - `jtor.ConstrainPaxisIp(eq, p_axis, ip, fvac)`
    - `picard.solve(eq, profiles)`
- Updated `src/mini_tokamak/solvers/freegs_adapter.py`:
  - Generates a Miller-like target boundary from candidate `R`, `a`, `kappa`, and `delta`.
  - Records rough PF coil proxy clearances and geometry precheck failures.
  - Runs a fixed-boundary FreeGS Picard sanity check when geometry prechecks pass.
  - Writes per-candidate:
    - `candidate.json`
    - `miller_boundary.json`
    - `freegs_result.json`
    - `freegs_fields.npz` when the solve completes
    - `freegs_equilibrium.png` when the solve completes
  - Successful FreeGS solves return solver status `WARNING`, not `PASS`, because this is fixed-boundary consistency evidence only.
  - Geometry precheck or solver failures return `FAIL`.
- Workaround implemented:
  - Direct FreeGS smoke initially failed in `freegs.critical.find_critical` with `ValueError: setting an array element with a sequence`.
  - Added an adapter-local, in-process fixed-boundary critical-point fallback for this MVP path only.
  - Result JSON records this as `critical_point_finder=adapter_local_fixed_boundary_fallback`.
  - No FreeGS package files were modified.
- Added tests:
  - `tests/test_freegs_adapter.py`
  - Covers Miller boundary metrics, successful artifact reporting, exception failure reporting, and clean geometry-precheck failures without phantom artifact paths.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `16 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `16 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
- FreeGS smoke before artifact-path cleanup:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T030046Z-3cfab52e`
  - Result: 2 candidates reached `fixed_boundary_picard` with FreeGS `PASS` metrics and solver status `WARNING`; 1 candidate failed geometry precheck.
  - Artifacts: 3 `freegs_result.json`, 2 `freegs_equilibrium.png`, 2 `freegs_fields.npz`.
- Final FreeGS smoke after artifact-path cleanup:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T030224Z-5fc93e23`
  - Result: 2 candidates reached `fixed_boundary_picard` with FreeGS `PASS` metrics and solver status `WARNING`; 1 candidate failed geometry precheck.
  - Artifacts: 3 `freegs_result.json`, 2 `freegs_equilibrium.png`, 2 `freegs_fields.npz`.
  - Geometry-precheck failure now reports `field_path=null` and `plot_path=null`.
  - Runtime warnings observed from FreeGS/SciPy during the smoke were captured in terminal output and did not stop the run:
    - `RuntimeWarning: invalid value encountered in scalar divide` from `freegs/picard.py`
    - `IntegrationWarning: Extremely bad integrand behavior occurs at some points of the integration interval` from `freegs/jtor.py`
- Final 100-candidate acceptance run after FreeGS adapter changes:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T030457Z-a13d759f`
  - Result: command completed successfully.
  - Candidate results: 100 JSON result files.
  - FreeGS results: 100 `freegs_result.json` files.
  - FreeGS status summary:
    - 75 candidates: solver status `WARNING`, FreeGS metric status `PASS`, stage `fixed_boundary_picard`.
    - 25 candidates: solver status `FAIL`, FreeGS metric status `FAIL`, stage `geometry_precheck`.
  - FreeGS artifacts: 75 `freegs_equilibrium.png` files and 75 `freegs_fields.npz` files.
  - Run artifacts verified:
    - `all_results.json`
    - `top_candidates.csv`
    - `data/runs/mini_tokamak.duckdb`
    - `data/reports/20260616T030457Z-a13d759f/report.md`
    - `data/reports/20260616T030457Z-a13d759f/report.html`
    - CAD PNG, SVG, and STEP outputs under `data/cad/20260616T030457Z-a13d759f/`

## TokaMaker adapter v1 implementation on 2026-06-16

- Local OpenFUSIONToolkit/TokaMaker source inspected:
  - Package path: `/home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/OpenFUSIONToolkit`
  - TokaMaker core API source: `OpenFUSIONToolkit/TokaMaker/_core.py`
  - TokaMaker meshing helper source: `OpenFUSIONToolkit/TokaMaker/meshing.py`
  - Relevant local API pattern:
    - `from OpenFUSIONToolkit.TokaMaker.meshing import gs_Domain`
    - `domain.define_region(...)`
    - `domain.add_polygon(...)`
    - `domain.add_rectangle(...)`
    - `domain.build_mesh()`
    - `TokaMaker(OFT_env(...))`
    - `setup_mesh`, `setup_regions`, `setup`, `set_coil_currents`, `vac_solve`, `set_targets`, `solve`
- Environment/import note:
  - Direct `import OpenFUSIONToolkit` initially failed with:
    - `ImportError: ... h5py/defs... undefined symbol: H5Pget_dxpl_mpio`
  - Workaround verified:
    - `import h5py` before `import OpenFUSIONToolkit`
  - The adapter probe and generated TokaMaker runner use this import order.
  - No package files were modified.
- Updated `src/mini_tokamak/solvers/tokamaker_adapter.py`:
  - Replaced the stub with a staged adapter.
  - Generates per-candidate:
    - `candidate.json`
    - `tokamaker_input.json`
    - `tokamaker_runner.py`
  - Default execution remains off to keep standard 100-candidate sweeps fast.
  - Execution controls:
    - `MINI_TOKAMAK_TOKAMAKER_EXECUTE=1`
    - `MINI_TOKAMAK_TOKAMAKER_MODE=vacuum` for the default vacuum-solve preflight
    - `MINI_TOKAMAK_TOKAMAKER_MODE=free_boundary` for a controlled nonlinear target-solve attempt after vacuum solve
    - `MINI_TOKAMAK_TOKAMAKER_TIMEOUT_S`
    - `MINI_TOKAMAK_TOKAMAKER_MAXITS`
    - `MINI_TOKAMAK_TOKAMAKER_MESH_SCALE`
  - Uses a Miller-like plasma target boundary and two PF proxy coil rectangles.
  - Writes `tokamaker_mesh.npz` and `tokamaker_mesh.png` when mesh generation succeeds.
  - Successful vacuum solves return solver status `WARNING`, not `PASS`, because they are integration evidence only.
  - Geometry-precheck failures return `FAIL` and do not execute TokaMaker.
  - Free-boundary target-solve failures are captured as controlled `FAIL` results instead of crashing the CLI.
- Plotting workaround:
  - First opt-in TokaMaker smoke generated meshes but failed in the generated plot routine because region IDs are cell-based, not point-based:
    - `'c' argument has ... elements, which is inconsistent with 'x' and 'y'`
  - Fixed the runner plot to use `matplotlib.tripcolor(..., facecolors=reg)`.
- Added tests:
  - `tests/test_tokamaker_adapter.py`
  - Covers manifest generation, non-executing runner generation, vacuum execution success handling, and controlled free-boundary failure handling.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `20 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `20 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `mini-tokamak verify`
    - Result: `TokaMaker PASS` from the adapter probe.
- Default non-executing TokaMaker sweep:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T034627Z-b19b9556`
  - Result: command completed successfully.
  - TokaMaker artifacts: 3 `tokamaker_input.json`, 3 `tokamaker_runner.py`, 1 geometry-precheck `tokamaker_result.json`.
- Opt-in TokaMaker vacuum-solve smoke:
  - Command: `MINI_TOKAMAK_TOKAMAKER_EXECUTE=1 MINI_TOKAMAK_TOKAMAKER_TIMEOUT_S=180 mini-tokamak run --config configs/design_space.car_sized.yaml --n 5 --mode random --seed 7`
  - Final run ID: `20260616T034857Z-c3ebe47b`
  - Result: command completed successfully.
  - TokaMaker status summary:
    - 4 candidates: solver status `WARNING`, `tokamaker_status=PASS`, stage `vacuum_solve`.
    - 1 candidate: solver status `FAIL`, stage `geometry_precheck`.
  - Artifacts: 5 `tokamaker_input.json`, 5 `tokamaker_runner.py`, 5 `tokamaker_result.json`, 4 `tokamaker_mesh.npz`, 4 `tokamaker_mesh.png`.
- Opt-in TokaMaker free-boundary attempt smoke:
  - Command: `MINI_TOKAMAK_TOKAMAKER_EXECUTE=1 MINI_TOKAMAK_TOKAMAKER_MODE=free_boundary MINI_TOKAMAK_TOKAMAKER_TIMEOUT_S=180 mini-tokamak run --config configs/design_space.car_sized.yaml --n 2 --mode random --seed 7`
  - Run ID: `20260616T034935Z-aa75cab4`
  - Result: command completed successfully.
  - TokaMaker status summary:
    - 1 candidate: geometry precheck `FAIL`.
    - 1 candidate: vacuum solve `PASS`, free-boundary target solve `FAIL`.
  - Controlled free-boundary error captured:
    - `Error in solve: Matrix solve failed for targets`
- Final 100-candidate acceptance run after TokaMaker adapter changes:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T035005Z-a7b92f71`
  - Result: command completed successfully in WSL.
  - Candidate results: 100 JSON result files.
  - TokaMaker artifacts: 100 `tokamaker_input.json`, 100 `tokamaker_runner.py`, 29 geometry-precheck `tokamaker_result.json`.
  - TokaMaker default status summary:
    - 71 candidates: solver status `NOT_EVALUATED`, geometry status `PASS`, execution skipped by default.
    - 29 candidates: solver status `FAIL`, stage `geometry_precheck`.
  - Markdown and HTML reports were generated.

## TORAX adapter v1 implementation on 2026-06-16

- No GPU, ROCm, driver, ComfyUI, or image-generation installs were changed.
- No new TORAX install command was needed in this step; TORAX was already installed in the WSL `mini-tokamak` conda environment.
- Official/current source references already recorded for TORAX:
  - Install docs: `https://torax.readthedocs.io/en/v1.4.0/installation.html`
- Local TORAX package inspected in WSL:
  - Package path: `/home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/torax/__init__.py`
  - Example config: `/home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/torax/examples/basic_config.py`
  - CLI entry point: `/home/craig/miniforge/envs/mini-tokamak/bin/run_torax`
  - Runner source: `/home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/torax/run_simulation_main.py`
- Baseline TORAX example smoke:
  - Command: `run_torax --config /home/craig/miniforge/envs/mini-tokamak/lib/python3.12/site-packages/torax/examples/basic_config.py --quit --output_dir /tmp/mini_tokamak_torax_basic_smoke`
  - Result: completed successfully.
  - Output file: `/tmp/mini_tokamak_torax_basic_smoke/state_history_20260616_025537.nc`
  - Runtime note: TORAX/JAX ran on CPU backend; no GPU path was required.
- Updated `src/mini_tokamak/solvers/torax_adapter.py`:
  - Replaced the stub with a staged adapter.
  - Probes TORAX by importing `torax` and locating `run_torax`.
  - Generates per-candidate:
    - `candidate.json`
    - `torax_manifest.json`
    - `torax_config.py`
  - Default execution remains off to keep standard 100-candidate sweeps fast.
  - Execution controls:
    - `MINI_TOKAMAK_TORAX_EXECUTE=1`
    - `MINI_TOKAMAK_TORAX_TIMEOUT_S`
    - `MINI_TOKAMAK_TORAX_T_FINAL`
    - `MINI_TOKAMAK_TORAX_FIXED_DT`
    - `MINI_TOKAMAK_TORAX_N_RHO`
  - Generated configs use TORAX circular geometry with candidate-derived `R_major`, `a_minor`, `B_0`, and `elongation_LCFS`.
  - Candidate-derived profile and source values are explicitly treated as `LOW_FIDELITY_PLACEHOLDER`.
  - TORAX subprocesses set `JAX_PLATFORMS=cpu`, `CUDA_VISIBLE_DEVICES=""`, and `MPLBACKEND=Agg`.
  - Successful short TORAX executions return solver status `WARNING`, not `PASS`, because they are transport plumbing evidence only.
  - Geometry-precheck failures return `FAIL` and do not execute TORAX.
  - Output summaries record NetCDF state-history path, file size, time-step count, and sampled xarray variables when parseable.
- Added tests:
  - `tests/test_torax_adapter.py`
  - Covers manifest mapping, non-executing config generation, missing `run_torax` handling, and execution-success result handling.
- Test infrastructure workaround:
  - Windows pytest first failed before test bodies executed because `data/runs/pytest_tmp` and then `%TEMP%/pytest-of-Craig` had inaccessible ACLs.
  - Changed `pyproject.toml` pytest addopts to `--basetemp=.pytest_tmp`.
  - Added `.pytest_tmp/` to `.gitignore`.
  - This only affects test temporary files and does not change runtime data outputs.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `24 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `24 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `mini-tokamak verify`
    - Result: `TORAX PASS` from the adapter probe.
- Default non-executing TORAX sweep:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random`
  - Run ID: `20260616T070219Z-a7192e4a`
  - Result: command completed successfully.
  - TORAX artifacts: 3 `candidate.json`, 3 `torax_manifest.json`, 3 `torax_config.py`.
  - TORAX NetCDF outputs: 0, as expected when execution is skipped by default.
- Opt-in TORAX CPU transport smoke:
  - Command: `MINI_TOKAMAK_TORAX_EXECUTE=1 MINI_TOKAMAK_TORAX_TIMEOUT_S=240 mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random --seed 42`
  - Run ID: `20260616T070252Z-ab6d2c17`
  - Result: command completed successfully.
  - TORAX status: solver status `WARNING`, `torax_status=PASS`, stage `run_torax`.
  - Output file: `data/runs/20260616T070252Z-ab6d2c17/external_solvers/torax/e1674eed-943a-4e5e-bee8-88d347a2cf89/torax_output/state_history_20260616_030314.nc`
  - Output summary: 5 time steps, final simulated time 0.2 s.
  - Runtime note: stderr recorded `JAX running on a default cpu backend`.
  - TORAX warning recorded but non-fatal: legacy psi initialization fallback because `profile_conditions.psi` was not supplied.
- Final 100-candidate acceptance run after TORAX adapter changes:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T070338Z-22d2155b`
  - Result: command completed successfully in WSL.
  - Candidate results: 100 JSON result files.
  - TORAX artifacts: 100 `torax_manifest.json`, 100 `torax_config.py`.
  - TORAX default output summary:
    - 99 candidates: solver status `NOT_EVALUATED`, execution skipped by default.
    - 1 candidate: solver status `FAIL`, stage `geometry_precheck`.
    - 0 TORAX NetCDF outputs, as expected when `MINI_TOKAMAK_TORAX_EXECUTE` is not set.
  - Report artifacts:
    - `data/reports/20260616T070338Z-22d2155b/report.md`
    - `data/reports/20260616T070338Z-22d2155b/report.html`
  - CAD artifacts:
    - `data/cad/20260616T070338Z-22d2155b/bb2781b1-b7ca-4120-8a88-72e37845b5f1_cross_section.png`
    - `data/cad/20260616T070338Z-22d2155b/bb2781b1-b7ca-4120-8a88-72e37845b5f1_cross_section.svg`
    - `data/cad/20260616T070338Z-22d2155b/bb2781b1-b7ca-4120-8a88-72e37845b5f1_plasma_proxy.step`

## TORAX controlled profile/source model on 2026-06-16

- No GPU, ROCm, driver, ComfyUI, or image-generation installs were changed.
- No new package installation was performed.
- Updated `src/mini_tokamak/solvers/torax_adapter.py`:
  - Added `controlled_profile_source_v1`.
  - Density model:
    - Uses a configurable Greenwald-fraction target from `MINI_TOKAMAK_TORAX_GREENWALD_FRACTION`.
    - Clips the candidate density target into the MVP operating envelope.
    - Records target and actual Greenwald fractions in `torax_manifest.json`.
    - Records guardrails for density cap/floor clipping.
  - Temperature model:
    - Builds ion/electron profile shapes from candidate heating power and plasma volume.
    - Applies a beta-derived temperature cap.
    - Records whether the temperature was beta-capped.
  - Source model:
    - Maps candidate heating power to TORAX `generic_heat.P_total`.
    - Records power density and input SOL heat-load proxy.
  - Output extraction:
    - Extracts TORAX scalar/profile metrics from `state_history_*.nc`, including q95, Greenwald fraction, P_SOL, tau_E, volume-averaged temperatures/density, beta proxy, and profile edge/core values.
  - Transport comparison:
    - Compares executed TORAX outputs against MVP q95, Greenwald, beta, and SOL heat-load screens.
    - Stores `torax_transport_constraint_status`, `torax_transport_constraint_reasons`, and related metrics in `torax_result.json` and candidate result JSON.
    - These comparisons remain `LOW_FIDELITY_PLACEHOLDER` and are not viability claims.
- Updated `src/mini_tokamak/reporting/report_md.py`:
  - Adds a `TORAX Transport Summary` section to Markdown and HTML reports.
  - Non-executed default runs show status counts and the opt-in execution hint.
  - Executed TORAX runs show candidate ID, q95, Greenwald fraction, P_SOL, SOL heat load, and comparison status.
- Updated tests:
  - `tests/test_torax_adapter.py`
  - Added coverage for controlled profile generation, Greenwald-fraction env override, transport comparison flags, and execution-success comparison defaults.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `26 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `26 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `mini-tokamak verify`
    - Result: `TORAX PASS` from the adapter probe.
- Opt-in TORAX smoke after controlled profile/source implementation:
  - Command: `MINI_TOKAMAK_TORAX_EXECUTE=1 MINI_TOKAMAK_TORAX_TIMEOUT_S=240 mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random --seed 43`
  - Run ID: `20260616T071804Z-66b92c0f`
  - Result: command completed successfully.
  - TORAX status: solver status `WARNING`, `torax_status=PASS`, stage `run_torax`.
  - Output file: `data/runs/20260616T071804Z-66b92c0f/external_solvers/torax/94d095c8-d632-4855-9484-b6ad38466498/torax_output/state_history_20260616_031827.nc`
  - Extracted output summary:
    - `time_steps=5`
    - `t_final_s=0.2`
    - `torax_final_q95=3.811683711727687`
    - `torax_final_fgw_n_e_line_avg=0.017647332456675918`
    - `torax_final_P_SOL_total_MW=26.143847668849222`
    - `torax_final_SOL_heat_load_MW_m2=98.15042506561178`
    - `torax_final_beta_proxy_percent=0.24627100862762397`
    - `torax_transport_constraint_status=FAIL`
    - `torax_transport_constraint_reasons=['torax_sol_heat_exhaust_proxy_fail']`
  - Report summary verified in `data/reports/20260616T071804Z-66b92c0f/report.md`.
- Final 100-candidate acceptance run after controlled profile/source implementation:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T072001Z-d42bd2c9`
  - Result: command completed successfully in WSL.
  - Candidate results: 100 JSON result files.
  - TORAX artifacts: 100 `torax_manifest.json`, 100 `torax_config.py`.
  - TORAX NetCDF outputs: 0, as expected when `MINI_TOKAMAK_TORAX_EXECUTE` is not set.
  - TORAX solver status summary:
    - 99 candidates: solver status `NOT_EVALUATED`, execution skipped by default.
    - 1 candidate: solver status `FAIL`, stage `geometry_precheck`.
  - Controlled-profile guardrail summary:
    - 5 candidates: `PASS`
    - 45 candidates: `WARNING`
    - 50 candidates: `FAIL`
  - Report artifacts:
    - `data/reports/20260616T072001Z-d42bd2c9/report.md`
    - `data/reports/20260616T072001Z-d42bd2c9/report.html`
  - CAD artifacts:
    - `data/cad/20260616T072001Z-d42bd2c9/1f5764ee-56a0-4672-91ba-e475a38d0d41_cross_section.png`
    - `data/cad/20260616T072001Z-d42bd2c9/1f5764ee-56a0-4672-91ba-e475a38d0d41_cross_section.svg`
    - `data/cad/20260616T072001Z-d42bd2c9/1f5764ee-56a0-4672-91ba-e475a38d0d41_plasma_proxy.step`

## TORAX top-candidate post-screening pass on 2026-06-16

- No GPU, ROCm, driver, ComfyUI, or image-generation installs were changed.
- No new package installation was performed.
- Updated `src/mini_tokamak/solvers/torax_adapter.py`:
  - Added `run_transport_smoke(candidate, rank)`.
  - This method forces TORAX execution for a selected ranked candidate without requiring `MINI_TOKAMAK_TORAX_EXECUTE=1`.
  - Result metrics now include:
    - `execution_source=torax_top_n`
    - `top_candidate_rank`
- Updated `src/mini_tokamak/optimization/random_search.py`:
  - Added `torax_top_n` support.
  - Added a post-screening `TORAX transport pass` after the existing FUSE actor pass and before report generation.
  - Replaces the selected candidate's existing `TORAX` solver result instead of appending a duplicate TORAX result.
  - Rewrites the candidate JSON and DuckDB row after the TORAX pass.
- Updated `src/mini_tokamak/optimization/optuna_search.py`:
  - Forwarded `torax_top_n` through the current Optuna wrapper.
- Updated `src/mini_tokamak/cli.py`:
  - Added `--torax-top-n`.
- Updated tests:
  - `tests/test_torax_adapter.py` now covers forced top-candidate TORAX execution without the env var.
  - `tests/test_cli_smoke.py` now checks that `--torax-top-n` is exposed in CLI help.
- Validation commands completed:
  - Windows: `.venv\Scripts\python.exe -m pytest`
    - Result: `28 passed`
  - Windows: `.venv\Scripts\python.exe -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `python -m pytest`
    - Result: `28 passed`
  - WSL: `python -m ruff check src tests`
    - Result: `All checks passed`
  - WSL: `mini-tokamak verify`
    - Result: `TORAX PASS` from the adapter probe.
- Top-candidate TORAX execution smoke:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 3 --mode random --seed 43 --torax-top-n 1`
  - Run ID: `20260616T073239Z-f9204678`
  - Result: command completed successfully.
  - Screening stage completed first, then a separate `TORAX transport pass` ran.
  - Candidate results: 3 JSON result files.
  - TORAX artifacts: 3 `torax_manifest.json`, 3 `torax_config.py`.
  - TORAX NetCDF outputs: 1 `state_history_*.nc` for the top-ranked candidate only.
  - TORAX solver status summary:
    - 2 candidates: `NOT_EVALUATED`
    - 1 candidate: `WARNING`, `execution_source=torax_top_n`, `top_candidate_rank=1`, stage `run_torax`
  - Executed candidate output:
    - Candidate: `7df722b7-899c-48e9-b5f7-ac9dd80ca807`
    - Output file: `data/runs/20260616T073239Z-f9204678/external_solvers/torax/7df722b7-899c-48e9-b5f7-ac9dd80ca807/torax_output/state_history_20260616_033302.nc`
    - Report summary values: `q95=12.2`, `fgw_line=0.207`, `P_SOL=29.2 MW`, `SOL heat load=17.2 MW/m2`, comparison `WARNING`
  - Report summary verified in `data/reports/20260616T073239Z-f9204678/report.md`.
- Default 100-candidate acceptance run after `--torax-top-n` implementation:
  - Command: `mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random`
  - Run ID: `20260616T073331Z-7ee6b263`
  - Result: command completed successfully in WSL.
  - Candidate results: 100 JSON result files.
  - TORAX artifacts: 100 `torax_manifest.json`, 100 `torax_config.py`.
  - TORAX NetCDF outputs: 0, as expected when neither `--torax-top-n` nor `MINI_TOKAMAK_TORAX_EXECUTE=1` is used.
  - TORAX solver status summary:
    - 99 candidates: `NOT_EVALUATED`
    - 1 candidate: `FAIL`, stage `geometry_precheck`
  - CAD artifacts:
    - `data/cad/20260616T073331Z-7ee6b263/2abff7e3-7a23-493a-9aee-b7f915c641fa_cross_section.png`
    - `data/cad/20260616T073331Z-7ee6b263/2abff7e3-7a23-493a-9aee-b7f915c641fa_cross_section.svg`
    - `data/cad/20260616T073331Z-7ee6b263/2abff7e3-7a23-493a-9aee-b7f915c641fa_plasma_proxy.step`
