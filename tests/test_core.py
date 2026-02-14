"""Comprehensive tests for CrossingBench core."""
from __future__ import annotations

from crossingbench.core import (
    BoundaryCost,
    ComputeCost,
    compare_baseline_vs_reduced,
    crossing_fraction,
    energy_cross,
    energy_intra,
    log_slope,
    sweep,
)


# ── Basic energy functions ──

def test_energy_intra_basic():
    assert energy_intra(100, ComputeCost(pj_per_byte=0.25)) == 25.0

def test_energy_intra_zero():
    assert energy_intra(0, ComputeCost(pj_per_byte=0.25)) == 0.0

def test_energy_cross_beta_only():
    b = BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.2)
    assert energy_cross(1000, 4, b) == 3200.0

def test_energy_cross_alpha_only():
    b = BoundaryCost(alpha_pj_per_event=100.0, beta_pj_per_byte=0.0)
    assert energy_cross(1000, 4, b) == 400.0

def test_energy_cross_alpha_and_beta():
    b = BoundaryCost(alpha_pj_per_event=2.0, beta_pj_per_byte=1.0)
    assert energy_cross(10, 3, b) == 16.0


# ── Crossing fraction ──

def test_crossing_fraction_zero_total():
    assert crossing_fraction(0.0, 0.0) == 0.0

def test_crossing_fraction_all_crossing():
    assert crossing_fraction(100.0, 100.0) == 1.0

def test_crossing_fraction_half():
    assert abs(crossing_fraction(50.0, 100.0) - 0.5) < 1e-10


# ── Log slope (elasticity) ──

def test_log_slope_doubling():
    s = log_slope(1.0, 10.0, 2.0, 20.0)
    assert abs(s - 1.0) < 1e-10

def test_log_slope_guards():
    assert log_slope(0.0, 1.0, 2.0, 3.0) == 0.0
    assert log_slope(1.0, 0.0, 2.0, 3.0) == 0.0
    assert log_slope(1.0, 1.0, 1.0, 2.0) == 0.0


# ── Sweep ──

def test_sweep_monotonic_total():
    rows = sweep(
        bytes_compute=262_144, cross_min=256, cross_max=524_288,
        steps=10, bytes_per_event=256,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.25),
    )
    totals = [r.c_total_pj for r in rows]
    assert all(t2 >= t1 for t1, t2 in zip(totals, totals[1:]))

def test_sweep_crossing_fraction_increases():
    rows = sweep(
        bytes_compute=262_144, cross_min=256, cross_max=524_288,
        steps=10, bytes_per_event=256,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.25),
    )
    fracs = [r.crossing_fraction for r in rows]
    assert all(f2 >= f1 for f1, f2 in zip(fracs, fracs[1:]))

def test_sweep_analog_epsilon_near_one():
    rows = sweep(
        bytes_compute=262_144, cross_min=256, cross_max=524_288,
        steps=12, bytes_per_event=256,
        compute=ComputeCost(pj_per_byte=0.0001),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.2),
    )
    eps_vals = [r.epsilon_local for r in rows[1:]]
    assert all(e > 0.95 for e in eps_vals), f"Expected ε > 0.95, got {eps_vals}"

def test_sweep_correct_length():
    rows = sweep(
        bytes_compute=100, cross_min=10, cross_max=1000,
        steps=5, bytes_per_event=10,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0),
    )
    assert len(rows) == 5

def test_sweep_first_epsilon_zero():
    rows = sweep(
        bytes_compute=100, cross_min=10, cross_max=1000,
        steps=5, bytes_per_event=10,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0),
    )
    assert rows[0].epsilon_local == 0.0

def test_sweep_equal_min_max():
    rows = sweep(
        bytes_compute=100, cross_min=1000, cross_max=1000,
        steps=2, bytes_per_event=256,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0),
    )
    assert len(rows) == 2
    assert rows[0].bytes_cross == rows[1].bytes_cross

def test_sweep_rejects_steps_1():
    try:
        sweep(bytes_compute=100, cross_min=10, cross_max=100, steps=1,
              bytes_per_event=10, compute=ComputeCost(pj_per_byte=0.25),
              boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_sweep_rejects_negative_cross():
    try:
        sweep(bytes_compute=100, cross_min=-1, cross_max=100, steps=5,
              bytes_per_event=10, compute=ComputeCost(pj_per_byte=0.25),
              boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# ── Compare ──

def test_compare_basic_gain():
    out = compare_baseline_vs_reduced(
        bytes_compute=262_144, cross_bytes=196_608, bytes_per_event=256,
        reduce_factor=3.0,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.2),
    )
    assert out["energy_gain_x"] > 1.0
    assert 0.0 <= out["baseline_cross_frac"] <= 1.0
    assert 0.0 <= out["reduced_cross_frac"] <= 1.0

def test_compare_elasticity_near_one():
    out = compare_baseline_vs_reduced(
        bytes_compute=262_144, cross_bytes=262_144, bytes_per_event=256,
        reduce_factor=3.0,
        compute=ComputeCost(pj_per_byte=0.0001),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.2),
    )
    assert out["elasticity_effective"] > 0.95

def test_compare_elasticity_near_zero():
    out = compare_baseline_vs_reduced(
        bytes_compute=262_144, cross_bytes=1024, bytes_per_event=256,
        reduce_factor=3.0,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.25),
    )
    assert out["elasticity_effective"] < 0.1

def test_compare_has_all_fields():
    out = compare_baseline_vs_reduced(
        bytes_compute=100, cross_bytes=100, bytes_per_event=10,
        reduce_factor=2.0,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0),
    )
    required = ["baseline_total_pj", "reduced_total_pj", "energy_gain_x",
                "baseline_cross_frac", "reduced_cross_frac", "elasticity_effective"]
    for key in required:
        assert key in out, f"Missing key: {key}"

def test_compare_rejects_negative_bytes():
    try:
        compare_baseline_vs_reduced(
            bytes_compute=100, cross_bytes=-1, bytes_per_event=256,
            reduce_factor=3.0,
            compute=ComputeCost(pj_per_byte=0.25),
            boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=1.0),
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_compare_with_alpha():
    out_no = compare_baseline_vs_reduced(
        bytes_compute=262_144, cross_bytes=196_608, bytes_per_event=256,
        reduce_factor=3.0,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=0.0, beta_pj_per_byte=3.2),
    )
    out_yes = compare_baseline_vs_reduced(
        bytes_compute=262_144, cross_bytes=196_608, bytes_per_event=256,
        reduce_factor=3.0,
        compute=ComputeCost(pj_per_byte=0.25),
        boundary=BoundaryCost(alpha_pj_per_event=100.0, beta_pj_per_byte=3.2),
    )
    assert out_yes["baseline_cross_frac"] >= out_no["baseline_cross_frac"]
