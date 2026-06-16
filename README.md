# MiniTokamak Designer

MiniTokamak Designer is a CPU-first simulation and optimization framework for exploring the lower-size limits of tokamak and spherical tokamak concepts. The purpose is to map why miniature designs fail: envelope fit, confinement proxies, magnetic field pressure, coil stress, shielding, heat exhaust, divertor loading, and tritium-breeding volume.

This is a feasibility-research, simulation, and CAD-screening tool only. It is not a construction guide, procurement guide, hazardous-material workflow, radiation-operation workflow, tritium workflow, or reactor operating procedure.

## Why miniature-first

Searching the extreme small end of the design space is useful because failure modes become obvious quickly. Car-sized D-T power-reactor candidates should mostly fail in this MVP. That is expected. The useful output is the ranked failure map, not a claim that a compact power plant is viable.

## Current local status

This repo was created at `C:\Users\Craig\projects\mini_tokamak_designer`.

WSL2/Ubuntu is the preferred target runtime. WSL2 is now enabled, Ubuntu is installed, and the Linux-side repo exists at `/home/craig/projects/mini_tokamak_designer`. The Windows Python 3.12 virtual environment remains available as a fallback. Heavy solvers are optional and all adapters fall back cleanly when a tool is unavailable.

Installed and verified in the Windows MVP venv:

- Core: NumPy, SciPy, pandas, xarray, pydantic, matplotlib, plotly, rich, Typer, DuckDB, h5py, zarr
- Dev/test: pytest, ruff, black, mypy
- Optimization/ML: Optuna, PyTorch CPU, JAX CPU, BoTorch, MLflow
- Systems/physics Python packages: OpenMDAO, FreeGS, TORAX

Stubbed or unavailable in the Windows MVP venv:

- PROCESS: deferred to WSL/Linux path
- FUSE.jl: Julia is not installed
- OpenFUSIONToolkit/TokaMaker: `pip install openfusiontoolkit` had no compatible distribution here
- OpenMC: deferred to WSL conda-forge or Docker path
- CadQuery and Paramak: deferred to WSL conda-forge path for the more reliable CAD stack

Installed and verified in WSL:

- Core/science/dev stack from `environment-core.yml`
- PyTorch CPU, JAX CPU, BoTorch, MLflow
- PROCESS, with MVP input-deck generation wired into the adapter
- FUSE.jl v1.1.4, with MVP candidate-probe generation and opt-in `FUSE.init` execution wired into the adapter
- FreeGS 0.8.2, with fixed-boundary equilibrium sanity checks wired into the adapter
- OpenFUSIONToolkit/TokaMaker, with proxy mesh generation and opt-in vacuum/free-boundary smoke execution wired into the adapter
- TORAX 1.4.0, with candidate config generation and opt-in CPU transport smoke execution wired into the adapter
- CadQuery
- OpenMC
- Paramak
- OpenFUSIONToolkit/TokaMaker adapter import path
- Julia 1.12.6
- Julia JSON package, installed explicitly for the generated FUSE runner scripts

FUSE install note: the first `Pkg.add("FUSE")` attempt failed because dependency `ALPHA.jl` was referenced with a `git@github.com:` SSH URL. The successful retry used `JULIA_PKG_USE_CLI_GIT=true` plus a per-process Git rewrite from `git@github.com:` to `https://github.com/`, without changing global Git config.

See `install/INSTALL_LOG.md` for every install source, command, failure, and workaround recorded so far.

## Architecture

- `configs/`: design spaces, physics limit placeholders, and objective weights
- `src/mini_tokamak/design/`: candidate generation, constraints, scoring, dimensionless proxies
- `src/mini_tokamak/solvers/`: adapters for PROCESS, FUSE.jl, FreeGS, TokaMaker, TORAX, OpenMC, and thermal/structural placeholders
- `src/mini_tokamak/cad/`: Paramak/CadQuery probes, optional STEP export, and guaranteed 2D cross-section fallback
- `src/mini_tokamak/optimization/`: random search MVP, Optuna wrapper, BoTorch/surrogate interfaces
- `src/mini_tokamak/storage/`: DuckDB and JSON run storage
- `src/mini_tokamak/reporting/`: plots, Markdown reports, HTML reports, failure summaries
- `src/mini_tokamak/ml/`: future surrogate-model dataset/training interfaces
- `tests/`: smoke tests that pass without heavyweight external solvers

Every external solver adapter implements:

- `is_available()`
- `run(candidate)`
- `parse_results()`
- `fallback_result(candidate, reason)`

## Windows quick start

From Windows Terminal:

```powershell
cd $HOME\projects\mini_tokamak_designer
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\mini-tokamak.exe verify
```

Run the first search:

```powershell
cd $HOME\projects\mini_tokamak_designer
.\.venv\Scripts\mini-tokamak.exe run --config configs/design_space.car_sized.yaml --n 100 --mode random
```

Review runs:

```powershell
.\.venv\Scripts\mini-tokamak.exe list-runs
.\.venv\Scripts\mini-tokamak.exe show-best
```

## WSL2/Ubuntu target path

Open Ubuntu from Windows Terminal:

```powershell
wsl -d Ubuntu
```

Or open a visible Ubuntu tab already activated in this repo:

```powershell
.\scripts\open_wsl_terminal.ps1
```

If the tab closes unexpectedly, run the non-interactive startup check:

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/Craig/projects/mini_tokamak_designer/scripts/start_wsl_shell.sh --check
```

Then inside Ubuntu:

```bash
cd ~/projects/mini_tokamak_designer
conda activate mini-tokamak
mini-tokamak verify
mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random
```

Run a top-candidate FUSE actor pass after the fast screen:

```bash
mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random --fuse-top-n 1
```

## Specialized fusion tools

The install scripts use the current official docs checked on 2026-06-15 and rechecked for FUSE on 2026-06-16:

- PROCESS: clone from `https://github.com/ukaea/PROCESS` and install with `pip install .` inside Linux/WSL
- FUSE.jl: install Julia package registry `https://github.com/ProjectTorreyPines/FuseRegistry.jl.git`, then `Pkg.add("FUSE")`
- FreeGS: `pip install freegs`
- TORAX: `pip install torax`
- OpenFUSIONToolkit/TokaMaker: `pip install openfusiontoolkit`
- CadQuery/OpenMC/Paramak: prefer conda-forge in the WSL conda environment

Run optional fusion install attempts inside the activated WSL environment:

```bash
bash install/wsl_optional_tools.sh
```

## Interpreting results

Labels mean:

- `PASS`: the MVP check passed
- `WARNING`: the candidate is near or outside a rough screen
- `FAIL`: the candidate violates an MVP screen
- `NOT_EVALUATED`: a real solver workflow is not configured yet
- `LOW_FIDELITY_PLACEHOLDER`: a simplified proxy or fallback was used

The CLI will not claim a design is viable unless external solver results support it. Built-in screens are deliberately conservative placeholders.

## Outputs

A run creates:

- `data/runs/<run_id>/all_results.json`
- `data/runs/<run_id>/top_candidates.csv`
- `data/runs/<run_id>/plots/*.png`
- `data/runs/mini_tokamak.duckdb`
- `data/runs/<run_id>/external_solvers/process/<candidate_id>/IN.DAT` when PROCESS is available
- `data/runs/<run_id>/external_solvers/fuse.jl/<candidate_id>/candidate.json` and `fuse_candidate_probe.jl` when FUSE is available
- `data/runs/<run_id>/external_solvers/fuse.jl/<candidate_id>/fuse_result.json`, `stdout.txt`, and `stderr.txt` when FUSE execution is enabled
- `data/runs/<run_id>/external_solvers/fuse.jl/<candidate_id>/fuse_actor_sequence.json`, `actor_stdout.txt`, and `actor_stderr.txt` when `--fuse-top-n` is used
- `data/runs/<run_id>/external_solvers/freegs/<candidate_id>/miller_boundary.json`, `freegs_result.json`, and, when the solve reaches Picard completion, `freegs_fields.npz` and `freegs_equilibrium.png`
- `data/runs/<run_id>/external_solvers/tokamaker/<candidate_id>/tokamaker_input.json` and `tokamaker_runner.py` when TokaMaker is available
- `data/runs/<run_id>/external_solvers/tokamaker/<candidate_id>/tokamaker_result.json`, `stdout.txt`, `stderr.txt`, `tokamaker_mesh.npz`, and `tokamaker_mesh.png` when TokaMaker execution is enabled and reaches mesh/vacuum stages
- `data/runs/<run_id>/external_solvers/torax/<candidate_id>/candidate.json`, `torax_manifest.json`, and `torax_config.py` when TORAX is available
- `data/runs/<run_id>/external_solvers/torax/<candidate_id>/torax_result.json`, `stdout.txt`, `stderr.txt`, and `torax_output/state_history_*.nc` when TORAX execution is enabled
- `data/reports/<run_id>/report.md`
- `data/reports/<run_id>/report.html`
- `data/cad/<run_id>/*_cross_section.png`
- `data/cad/<run_id>/*_cross_section.svg`
- Optional STEP file if CadQuery is installed

## Tests

```powershell
cd $HOME\projects\mini_tokamak_designer
.\.venv\Scripts\python.exe -m pytest
```

The tests do not require PROCESS, FUSE, FreeGS, TokaMaker, TORAX, OpenMC, Paramak, or CadQuery.

## PROCESS adapter behavior

The PROCESS adapter now writes per-candidate input decks from a validated PROCESS template when PROCESS is installed. It uses the official `large_tokamak_eval_IN.DAT` example found at `/home/craig/src/PROCESS/examples/data/large_tokamak_eval_IN.DAT` in the WSL setup, or a custom path supplied with `MINI_TOKAMAK_PROCESS_TEMPLATE`.

Execution is off by default so that `--n 100` sweeps stay fast. To run PROCESS for generated candidates, use:

```bash
export MINI_TOKAMAK_PROCESS_EXECUTE=1
export MINI_TOKAMAK_PROCESS_TIMEOUT_S=180
mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random
```

PROCESS results are reported as a cautious `WARNING` when execution succeeds because the MVP mapping starts from a generic large-tokamak template. This is useful systems-code evidence, not a design viability claim.

## FUSE.jl adapter behavior

The FUSE adapter now verifies `using FUSE; using JSON`, then writes per-candidate `candidate.json` and runnable Julia probe scripts. Default sweeps do not execute heavyweight FUSE workflows, so `--n 100` remains fast.

To run the MVP FUSE initialization probe for generated candidates:

```bash
export MINI_TOKAMAK_FUSE_EXECUTE=1
export MINI_TOKAMAK_FUSE_TIMEOUT_S=600
mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random
```

The current mapping initializes FUSE case `FPP` and attempts to set major radius, inverse aspect ratio, elongation, and triangularity before `FUSE.init`. A successful run is labelled `WARNING`, not `PASS`, because this proves adapter plumbing and initialization only; it is not a full integrated FUSE analysis or viability result.

To run the controlled top-candidate actor sequence after screening:

```bash
mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random --fuse-top-n 1
```

The default actor sequence is `ActorPFdesign`. Override it with a comma-separated list:

```bash
mini-tokamak run --config configs/design_space.car_sized.yaml --n 20 --mode random --fuse-top-n 1 --fuse-actors ActorPFdesign,ActorCXbuild
```

Actor-pass results are stored as a separate solver result named `FUSE.jl actors`, with per-actor `PASS`/`FAIL`, elapsed time, and failure details. Successful actor passes are still labelled `WARNING`, not `PASS`, because this is controlled integration evidence rather than a viability result.

## FreeGS adapter behavior

The FreeGS adapter now runs a fixed-boundary Grad-Shafranov sanity check for candidates that pass a lightweight geometry precheck. It generates a Miller-like target plasma boundary from the candidate parameters, records rough PF coil proxy clearances, and attempts a FreeGS Picard solve.

Successful FreeGS solves are reported as `WARNING`, not `PASS`, because this is fixed-boundary plasma-boundary consistency evidence only. Geometry precheck failures or solver failures are reported as `FAIL` with the dominant stage and failure reason.

Outputs are written under:

```text
data/runs/<run_id>/external_solvers/freegs/<candidate_id>/
```

The adapter writes `candidate.json`, `miller_boundary.json`, and `freegs_result.json` for every evaluated candidate. It writes `freegs_fields.npz` and `freegs_equilibrium.png` only when the fixed-boundary solve completes.

Implementation note: FreeGS 0.8.2 hit a scalar/array issue in its critical-point finder with the current SciPy stack during the MVP fixed-boundary path. The adapter installs an in-process fixed-boundary critical-point fallback for this path only. This is documented as `adapter_local_fixed_boundary_fallback` in result JSON.

## TokaMaker adapter behavior

The TokaMaker adapter now probes OpenFUSIONToolkit by importing `h5py` before `OpenFUSIONToolkit`, which avoids the local HDF5 library-order issue observed in this environment. Default sweeps generate a candidate-specific TokaMaker manifest and a runnable Python runner, but do not execute TokaMaker by default.

To run the opt-in vacuum-solve preflight:

```bash
export MINI_TOKAMAK_TOKAMAKER_EXECUTE=1
mini-tokamak run --config configs/design_space.car_sized.yaml --n 5 --mode random
```

To additionally attempt the nonlinear free-boundary target solve:

```bash
export MINI_TOKAMAK_TOKAMAKER_EXECUTE=1
export MINI_TOKAMAK_TOKAMAKER_MODE=free_boundary
mini-tokamak run --config configs/design_space.car_sized.yaml --n 2 --mode random
```

The adapter first builds a proxy Miller-boundary plasma region and two PF coil proxy rectangles using `gs_Domain`, then runs a TokaMaker vacuum solve. A vacuum-solve success is labelled `WARNING`, not `PASS`, because it proves OpenFUSIONToolkit plumbing and mesh/coil consistency only. Free-boundary target-solve failures are expected at this stage and are recorded as controlled `FAIL` results with the solver stage and error text.

## TORAX adapter behavior

The TORAX adapter maps each candidate into a short circular-geometry TORAX config for transport plumbing checks. Default sweeps generate `candidate.json`, `torax_manifest.json`, and `torax_config.py`, but do not execute TORAX so that 100-candidate screening remains fast.

The generated manifest includes a controlled low-fidelity profile/source model:

- density target as a configurable Greenwald-fraction proxy
- clipped line-averaged density and shaped density profile
- beta-capped ion/electron temperature profiles
- candidate heating power mapped to TORAX generic heat
- guardrail reasons for density clipping, beta capping, heat-exhaust stress, and power-density excursions

To run the short CPU transport smoke for generated candidates:

```bash
export MINI_TOKAMAK_TORAX_EXECUTE=1
export MINI_TOKAMAK_TORAX_TIMEOUT_S=240
mini-tokamak run --config configs/design_space.car_sized.yaml --n 1 --mode random --seed 42
```

To keep the broad screen fast and execute TORAX only for the best ranked candidates, use the post-screening pass:

```bash
mini-tokamak run --config configs/design_space.car_sized.yaml --n 100 --mode random --torax-top-n 1
```

`--torax-top-n` does not require `MINI_TOKAMAK_TORAX_EXECUTE=1`; it forces TORAX only for the selected top candidates after the normal ranking pass. The selected candidates keep a single TORAX solver result in their JSON, updated from `NOT_EVALUATED` to the executed `WARNING`/`FAIL` result.

When more than one TORAX candidate is executed, the report includes a ranked comparison table and `data/runs/<run_id>/plots/torax_transport_comparison.png` showing q95, line-averaged Greenwald fraction, and SOL heat-load proxy against MVP warning/fail thresholds.

Optional TORAX profile controls:

```bash
export MINI_TOKAMAK_TORAX_GREENWALD_FRACTION=0.25
export MINI_TOKAMAK_TORAX_T_FINAL=0.2
export MINI_TOKAMAK_TORAX_FIXED_DT=0.05
export MINI_TOKAMAK_TORAX_N_RHO=12
```

The adapter forces TORAX subprocesses onto the CPU backend with `JAX_PLATFORMS=cpu`. Successful TORAX runs are labelled `WARNING`, not `PASS`, because the MVP uses candidate-derived placeholder profiles and circular geometry. Executed runs extract TORAX output summaries such as `q95`, Greenwald fraction, `P_SOL_total`, volume-averaged temperatures/density, beta proxy, and SOL heat-load proxy. Reports include a TORAX transport summary comparing those outputs against the MVP screening thresholds. This completes the Phase 4 MVP transport workflow, but it is not a validated pulse, profile, or viability result.

## Known limitations

- Built-in physics is low-fidelity and intended only for failure mapping.
- PROCESS input generation is wired, but the candidate-to-PROCESS mapping is still low fidelity and does not directly set candidate `Ip`; the template uses PROCESS current-scaling variables.
- FUSE initialization and a top-candidate actor pass are wired, but the candidate-to-FUSE mapping is intentionally minimal and does not yet run stationary plasma actors, systems optimization, or time-dependent simulations by default.
- FreeGS fixed-boundary checks and TokaMaker proxy vacuum solves are wired, but high-fidelity free-boundary equilibrium, neutronics, CAD-neutronics, and structural analysis remain placeholders until their external workflows are validated.
- TORAX config generation, controlled low-fidelity profile/source initialization, output extraction, and a short opt-in CPU transport smoke are wired, but source calibration, pulse scenarios, and transport validation remain placeholders.
- D-T breeding is intentionally flagged as impossible for car-sized MVP envelopes.
- OpenMC is not run until cross-section data and a validated geometry workflow are configured.
- CAD fallback geometry is a visualization aid, not construction geometry.

## Next milestones

See `docs/ROADMAP.md`.
