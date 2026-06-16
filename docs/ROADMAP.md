# Roadmap

## Phase 1

- CPU-first random design-space exploration
- Constraint failure map
- CAD cross-section export

## Phase 2

- PROCESS and FUSE integration
- More realistic systems screening

## Phase 3

- FreeGS/TokaMaker equilibrium integration
- Coil geometry and plasma boundary consistency

Status on 2026-06-16: FreeGS fixed-boundary MVP is implemented for candidate sanity checks and artifact generation. TokaMaker proxy mesh generation and opt-in vacuum-solve execution are implemented. TokaMaker nonlinear free-boundary target solves are wired as controlled attempts, but higher-fidelity convergence, coil geometry, and target mapping remain open.

## Phase 4

- TORAX transport integration
- Pulse/profile simulation

Status on 2026-06-16: TORAX 1.4.0 is installed in the WSL `mini-tokamak` environment. The adapter generates per-candidate circular-geometry TORAX configs with a controlled low-fidelity profile/source model and can run an opt-in short CPU transport smoke that writes a TORAX `state_history_*.nc` file. Executed runs now extract transport output metrics and compare them against the MVP q95, Greenwald, beta, and heat-exhaust screens. The CLI also supports `--torax-top-n` to run TORAX only for the top ranked candidates after fast screening. Source calibration, pulse scenario definition, and transport-model validation remain open.

## Phase 5

- Paramak/OpenMC CAD-neutronics workflow
- Shielding and neutron transport estimates

## Phase 6

- Surrogate ML model
- Bayesian optimization
- Pareto frontier dashboard

## Phase 7

- Compare car-sized, van-sized, container-sized, and small-building-sized designs
