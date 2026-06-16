"""Low-fidelity dimensionless quantities."""

from __future__ import annotations


def q_star(R: float, a: float, Bt: float, Ip: float, kappa: float) -> float:
    if R <= 0 or Ip <= 0:
        return 0.0
    return (5.0 * a * a * Bt / (R * Ip)) * ((1.0 + kappa * kappa) / 2.0)


def greenwald_density_1e20(Ip: float, a: float) -> float:
    if a <= 0:
        return 0.0
    return Ip / (3.141592653589793 * a * a)


def beta_limit_percent(Ip: float, a: float, Bt: float, beta_n_limit: float = 3.5) -> float:
    if a <= 0 or Bt <= 0:
        return 0.0
    return beta_n_limit * Ip / (a * Bt)

