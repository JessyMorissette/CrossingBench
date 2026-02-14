from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BoundaryCost:
    """Crossing cost model.

    C_cross = alpha_pj_per_event * events + beta_pj_per_byte * bytes
    """

    alpha_pj_per_event: float
    beta_pj_per_byte: float


@dataclass(frozen=True)
class ComputeCost:
    """Compute cost model.

    C_intra = pj_per_byte * bytes_compute
    """

    pj_per_byte: float


DEFAULT_BOUNDARIES: dict[str, BoundaryCost] = {
    "analog": BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.20),
    "memory": BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.25),
    "chiplet": BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=5.00),
    "hbm": BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=10.0),
    "voltage": BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=0.80),
}

DEFAULT_COMPUTE: dict[str, ComputeCost] = {
    "digital": ComputeCost(pj_per_byte=0.25),
    "analog": ComputeCost(pj_per_byte=0.0001),
    "lowv": ComputeCost(pj_per_byte=0.05),
}


@dataclass(frozen=True)
class ProgramPoint:
    bytes_compute: int
    bytes_cross: int
    events_cross: int


@dataclass(frozen=True)
class ResultPoint:
    bytes_compute: int
    bytes_cross: int
    events_cross: int
    c_intra_pj: float
    c_cross_pj: float
    c_total_pj: float
    crossing_fraction: float
    epsilon_local: float


def energy_intra(bytes_compute: int, compute: ComputeCost) -> float:
    return float(bytes_compute) * compute.pj_per_byte


def energy_cross(
    bytes_cross: int, events_cross: int, boundary: BoundaryCost,
) -> float:
    return (
        float(events_cross) * boundary.alpha_pj_per_event
        + float(bytes_cross) * boundary.beta_pj_per_byte
    )


def crossing_fraction(c_cross: float, c_total: float) -> float:
    if c_total <= 0:
        return 0.0
    return c_cross / c_total


def log_slope(x1: float, y1: float, x2: float, y2: float) -> float:
    """Local elasticity estimate: dlog(y)/dlog(x) between two points."""
    if x1 <= 0 or x2 <= 0 or y1 <= 0 or y2 <= 0 or x1 == x2:
        return 0.0
    return (math.log(y2) - math.log(y1)) / (math.log(x2) - math.log(x1))


def run_point(
    p: ProgramPoint, compute: ComputeCost, boundary: BoundaryCost,
) -> tuple[float, float, float, float]:
    c_intra = energy_intra(p.bytes_compute, compute)
    c_cross = energy_cross(p.bytes_cross, p.events_cross, boundary)
    c_total = c_intra + c_cross
    frac = crossing_fraction(c_cross, c_total)
    return c_intra, c_cross, c_total, frac


def sweep(
    *,
    bytes_compute: int,
    cross_min: int,
    cross_max: int,
    steps: int,
    bytes_per_event: int,
    compute: ComputeCost,
    boundary: BoundaryCost,
) -> list[ResultPoint]:
    """Log-spaced sweep of crossing bytes; returns per-point energies and local epsilon."""

    if steps < 2:
        raise ValueError("steps must be >= 2")
    if cross_min <= 0 or cross_max <= 0 or cross_min > cross_max:
        raise ValueError("Require 0 < cross_min <= cross_max")
    if bytes_per_event <= 0:
        raise ValueError("bytes_per_event must be > 0")

    log_min = math.log(cross_min)
    log_max = math.log(cross_max)

    points: list[ProgramPoint] = []
    for i in range(steps):
        t = i / (steps - 1)
        b = int(round(math.exp(log_min + t * (log_max - log_min))))
        ev = max(1, int(math.ceil(b / bytes_per_event)))
        points.append(ProgramPoint(
            bytes_compute=bytes_compute, bytes_cross=b, events_cross=ev,
        ))

    energies: list[tuple[ProgramPoint, float, float, float, float]] = []
    for p in points:
        c_intra, c_cross, c_total, frac = run_point(p, compute, boundary)
        energies.append((p, c_intra, c_cross, c_total, frac))

    results: list[ResultPoint] = []
    for i, (p, c_intra, c_cross, c_total, frac) in enumerate(energies):
        if i == 0:
            eps = 0.0
        else:
            p_prev, _, _, c_total_prev, _ = energies[i - 1]
            eps = log_slope(
                float(p_prev.bytes_cross), float(c_total_prev),
                float(p.bytes_cross), float(c_total),
            )

        results.append(
            ResultPoint(
                bytes_compute=p.bytes_compute,
                bytes_cross=p.bytes_cross,
                events_cross=p.events_cross,
                c_intra_pj=c_intra,
                c_cross_pj=c_cross,
                c_total_pj=c_total,
                crossing_fraction=frac,
                epsilon_local=eps,
            )
        )

    return results


def compare_baseline_vs_reduced(
    *,
    bytes_compute: int,
    cross_bytes: int,
    bytes_per_event: int,
    reduce_factor: float,
    compute: ComputeCost,
    boundary: BoundaryCost,
) -> dict[str, float]:
    """Compare baseline crossing volume to a reduced-crossing schedule."""

    if cross_bytes <= 0:
        raise ValueError("cross_bytes must be > 0")
    if bytes_per_event <= 0:
        raise ValueError("bytes_per_event must be > 0")
    if reduce_factor <= 0:
        raise ValueError("reduce_factor must be > 0")

    base_ev = max(1, int(math.ceil(cross_bytes / bytes_per_event)))
    red_bytes = max(1, int(round(cross_bytes / reduce_factor)))
    red_ev = max(1, int(math.ceil(red_bytes / bytes_per_event)))

    base = ProgramPoint(
        bytes_compute=bytes_compute,
        bytes_cross=cross_bytes,
        events_cross=base_ev,
    )
    red = ProgramPoint(
        bytes_compute=bytes_compute,
        bytes_cross=red_bytes,
        events_cross=red_ev,
    )

    base_intra, base_cross, base_total, base_frac = run_point(
        base, compute, boundary,
    )
    red_intra, red_cross, red_total, red_frac = run_point(
        red, compute, boundary,
    )

    gain = base_total / red_total if red_total > 0 else float("inf")

    # "effective elasticity" for the discrete change
    eff_eps = 0.0
    if reduce_factor != 1.0 and gain > 0:
        eff_eps = math.log(gain) / math.log(reduce_factor)

    return {
        "baseline_total_pj": base_total,
        "baseline_intra_pj": base_intra,
        "baseline_cross_pj": base_cross,
        "baseline_cross_frac": base_frac,
        "baseline_cross_bytes": float(cross_bytes),
        "baseline_events": float(base_ev),
        "reduced_total_pj": red_total,
        "reduced_intra_pj": red_intra,
        "reduced_cross_pj": red_cross,
        "reduced_cross_frac": red_frac,
        "reduced_cross_bytes": float(red_bytes),
        "reduced_events": float(red_ev),
        "reduce_factor": float(reduce_factor),
        "energy_gain_x": gain,
        "elasticity_effective": eff_eps,
    }
