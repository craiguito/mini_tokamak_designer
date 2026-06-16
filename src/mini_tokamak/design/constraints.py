"""Low-fidelity physical sanity checks for compact tokamak candidates."""

from __future__ import annotations

import math

from mini_tokamak.design.design_space import envelope_dimensions
from mini_tokamak.design.dimensionless import beta_limit_percent, greenwald_density_1e20, q_star
from mini_tokamak.schemas import Candidate, ConstraintCheck, ConstraintEvaluation, DesignSpaceConfig
from mini_tokamak.units import MU0


FAIL_PRIORITY = [
    "envelope_fit",
    "center_column_clearance",
    "coil_stress_proxy",
    "divertor_heat_load_proxy",
    "dt_breeding_volume",
    "aspect_ratio_consistency",
    "q_star",
    "shielding_proxy",
    "confinement_proxy",
]


def _status_check(name: str, status: str, value: object, limit: object, message: str) -> ConstraintCheck:
    return ConstraintCheck(name=name, status=status, value=value, limit=limit, message=message)


def evaluate_constraints(candidate: Candidate, space: DesignSpaceConfig) -> ConstraintEvaluation:
    checks: list[ConstraintCheck] = []
    dims = envelope_dimensions(candidate)

    fits = (
        dims["length_m"] <= space.max_length_m
        and dims["width_m"] <= space.max_width_m
        and dims["height_m"] <= space.max_height_m
    )
    checks.append(
        _status_check(
            "envelope_fit",
            "PASS" if fits else "FAIL",
            f"{dims['length_m']:.2f} x {dims['width_m']:.2f} x {dims['height_m']:.2f} m",
            f"{space.max_length_m:.2f} x {space.max_width_m:.2f} x {space.max_height_m:.2f} m",
            "Candidate bounding envelope compared with requested package size.",
        )
    )

    actual_aspect = candidate.R / candidate.a if candidate.a > 0 else math.inf
    rel_error = abs(actual_aspect - candidate.aspect_ratio) / max(candidate.aspect_ratio, 1e-9)
    aspect_status = "PASS" if rel_error <= 0.08 else "FAIL"
    checks.append(
        _status_check(
            "aspect_ratio_consistency",
            aspect_status,
            actual_aspect,
            candidate.aspect_ratio,
            "Checks whether stored aspect ratio is consistent with R/a.",
        )
    )

    clear = candidate.center_column_radius < candidate.R - candidate.a
    checks.append(
        _status_check(
            "center_column_clearance",
            "PASS" if clear else "FAIL",
            candidate.center_column_radius,
            max(candidate.R - candidate.a, 0.0),
            "Center column radius must fit inside the inboard plasma-side space.",
        )
    )

    q = q_star(candidate.R, candidate.a, candidate.Bt, candidate.Ip, candidate.kappa)
    if q < 2.0:
        q_status = "FAIL"
    elif q < 3.0:
        q_status = "WARNING"
    else:
        q_status = "PASS"
    checks.append(
        _status_check(
            "q_star",
            q_status,
            q,
            "warning below 3, fail below 2",
            "Very rough edge safety-factor proxy.",
        )
    )

    greenwald = greenwald_density_1e20(candidate.Ip, candidate.a)
    checks.append(
        _status_check(
            "greenwald_density_limit",
            "WARNING" if greenwald > 12.0 else "PASS",
            greenwald,
            "proxy warning above 12 x 1e20 m^-3",
            "Greenwald density limit estimate; not a target operating density.",
        )
    )

    beta_limit = beta_limit_percent(candidate.Ip, candidate.a, candidate.Bt)
    beta_proxy = min(
        45.0,
        0.4 + 8.0 * candidate.heating_power / (candidate.heating_power + 20.0) / max(candidate.Bt / 5.0, 0.25),
    )
    if beta_limit <= 0 or beta_proxy > 1.5 * beta_limit:
        beta_status = "FAIL"
    elif beta_proxy > beta_limit:
        beta_status = "WARNING"
    else:
        beta_status = "PASS"
    checks.append(
        _status_check(
            "beta_proxy",
            beta_status,
            beta_proxy,
            beta_limit,
            "Placeholder beta pressure fraction compared with normalized beta-style limit.",
        )
    )

    magnetic_pressure_mpa = candidate.Bt**2 / (2.0 * MU0) / 1.0e6
    stress_proxy_mpa = magnetic_pressure_mpa * candidate.R / max(candidate.center_column_radius, 0.03)
    if stress_proxy_mpa > 900.0:
        stress_status = "FAIL"
    elif stress_proxy_mpa > 450.0:
        stress_status = "WARNING"
    else:
        stress_status = "PASS"
    checks.append(
        _status_check(
            "coil_stress_proxy",
            stress_status,
            stress_proxy_mpa,
            "warning above 450 MPa, fail above 900 MPa",
            "Hoop-stress screening proxy from magnetic pressure and compact geometry.",
        )
    )

    if candidate.fuel_mode == "DT_later_flag_only":
        min_shield = 0.8
    else:
        min_shield = 0.18
    if candidate.shield_thickness < 0.5 * min_shield:
        shield_status = "FAIL"
    elif candidate.shield_thickness < min_shield:
        shield_status = "WARNING"
    else:
        shield_status = "PASS"
    checks.append(
        _status_check(
            "shielding_proxy",
            shield_status,
            candidate.shield_thickness,
            min_shield,
            "Rough radial shielding screen; not a neutronics result.",
        )
    )

    wetted_area_proxy = max(0.15, 2.0 * math.pi * candidate.R * max(0.08, 0.25 * candidate.a))
    heat_load = candidate.heating_power / wetted_area_proxy
    if heat_load > 25.0:
        heat_status = "FAIL"
    elif heat_load > 10.0:
        heat_status = "WARNING"
    else:
        heat_status = "PASS"
    checks.append(
        _status_check(
            "divertor_heat_load_proxy",
            heat_status,
            heat_load,
            "warning above 10 MW/m2, fail above 25 MW/m2",
            "Scrape-off/divertor heat exhaust proxy.",
        )
    )

    dt_breeding_impossible = (
        candidate.fuel_mode == "DT_later_flag_only"
        and (space.max_width_m <= 2.0 or candidate.shield_thickness < 1.0)
    )
    checks.append(
        _status_check(
            "dt_breeding_volume",
            "FAIL" if dt_breeding_impossible else "NOT_EVALUATED",
            dt_breeding_impossible,
            "car-sized DT blanket/shield volume required",
            "Flags D-T breeding as impossible in this MVP for car-sized envelopes.",
        )
    )

    confinement_proxy = candidate.Bt * candidate.R * candidate.a * candidate.kappa / (
        1.0 + 0.05 * candidate.heating_power
    )
    checks.append(
        _status_check(
            "confinement_proxy",
            "WARNING" if confinement_proxy < 0.8 else "PASS",
            confinement_proxy,
            "proxy warning below 0.8",
            "Placeholder confinement quality indicator; real transport solvers required.",
        )
    )

    fail_count = sum(check.status == "FAIL" for check in checks)
    warning_count = sum(check.status == "WARNING" for check in checks)
    score = max(0.0, 100.0 - 22.0 * fail_count - 6.0 * warning_count)

    # Give a small performance-proxy boost without allowing failures to look viable.
    performance_proxy = (
        candidate.Bt * candidate.Ip * candidate.estimated_plasma_volume / (candidate.heating_power + 1.0)
    )
    score = min(100.0, score + min(10.0, performance_proxy))
    if fail_count:
        score = min(score, 59.0)

    dominant = "No dominant low-fidelity failure detected."
    failed_names = {check.name for check in checks if check.status == "FAIL"}
    for name in FAIL_PRIORITY:
        if name in failed_names:
            dominant = name
            break
    if not failed_names and warning_count:
        dominant = next(check.name for check in checks if check.status == "WARNING")

    metrics: dict[str, float | str | bool] = {
        **dims,
        "q_star": q,
        "greenwald_density_1e20_m3": greenwald,
        "beta_proxy_percent": beta_proxy,
        "beta_limit_percent": beta_limit,
        "magnetic_pressure_MPa": magnetic_pressure_mpa,
        "coil_stress_proxy_MPa": stress_proxy_mpa,
        "divertor_heat_load_proxy_MW_m2": heat_load,
        "confinement_proxy": confinement_proxy,
        "performance_proxy": performance_proxy,
        "fail_count": float(fail_count),
        "warning_count": float(warning_count),
    }

    return ConstraintEvaluation(
        checks=checks,
        metrics=metrics,
        feasibility_score=score,
        dominant_failure_reason=dominant,
        external_solver_support=False,
        viability_claim=False,
    )

