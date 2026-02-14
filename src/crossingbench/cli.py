from __future__ import annotations

import argparse
import json

from .core import (
    DEFAULT_BOUNDARIES,
    DEFAULT_COMPUTE,
    BoundaryCost,
    ComputeCost,
    compare_baseline_vs_reduced,
    sweep,
)
from .io import write_csv


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--boundary",
        choices=sorted(DEFAULT_BOUNDARIES.keys()),
        default="analog",
    )
    parser.add_argument(
        "--compute",
        choices=sorted(DEFAULT_COMPUTE.keys()),
        default="digital",
    )
    parser.add_argument(
        "--beta", type=float, default=None, help="Override beta (pJ/byte)",
    )
    parser.add_argument(
        "--alpha", type=float, default=None, help="Override alpha (pJ/event)",
    )
    parser.add_argument(
        "--compute_pj_per_byte",
        type=float,
        default=None,
        help="Override compute cost (pJ/byte)",
    )
    parser.add_argument(
        "--bytes_per_event",
        type=int,
        default=256,
        help="Bytes amortized per crossing event (default: 256)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CrossingBench")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser(
        "sweep", help="Log-sweep crossing bytes and estimate local epsilon",
    )
    _add_common(s)
    s.add_argument(
        "--bytes", type=int, default=262_144,
        help="Intra-domain compute bytes",
    )
    s.add_argument("--cross_min", type=int, default=256)
    s.add_argument("--cross_max", type=int, default=524_288)
    s.add_argument("--steps", type=int, default=12)
    s.add_argument("--out", type=str, default="sweep.csv")
    s.add_argument(
        "--json", type=str, default=None,
        help="Optional JSON summary output path",
    )

    c = sub.add_parser(
        "compare", help="Compare baseline vs reduced crossing volume",
    )
    _add_common(c)
    c.add_argument(
        "--bytes", type=int, default=262_144,
        help="Intra-domain compute bytes",
    )
    c.add_argument("--cross_bytes", type=int, default=196_608)
    c.add_argument("--reduce_factor", type=float, default=3.0)
    c.add_argument(
        "--json", type=str, default=None, help="Optional JSON output path",
    )

    return p


def _resolve_costs(
    args: argparse.Namespace,
) -> tuple[ComputeCost, BoundaryCost]:
    boundary = DEFAULT_BOUNDARIES[args.boundary]
    compute = DEFAULT_COMPUTE[args.compute]

    if args.beta is not None or args.alpha is not None:
        alpha = (
            args.alpha
            if args.alpha is not None
            else boundary.alpha_pj_per_event
        )
        beta = (
            args.beta
            if args.beta is not None
            else boundary.beta_pj_per_byte
        )
        boundary = BoundaryCost(
            alpha_pj_per_event=alpha,
            beta_pj_per_byte=beta,
        )

    if args.compute_pj_per_byte is not None:
        compute = ComputeCost(pj_per_byte=args.compute_pj_per_byte)

    return compute, boundary


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compute, boundary = _resolve_costs(args)

    if args.cmd == "sweep":
        rows = sweep(
            bytes_compute=args.bytes,
            cross_min=args.cross_min,
            cross_max=args.cross_max,
            steps=args.steps,
            bytes_per_event=args.bytes_per_event,
            compute=compute,
            boundary=boundary,
        )
        write_csv(args.out, rows)

        eps_vals = [r.epsilon_local for r in rows[1:]]
        frac_vals = [r.crossing_fraction for r in rows]

        summary = {
            "boundary": args.boundary,
            "compute": args.compute,
            "alpha_pj_per_event": boundary.alpha_pj_per_event,
            "beta_pj_per_byte": boundary.beta_pj_per_byte,
            "compute_pj_per_byte": compute.pj_per_byte,
            "bytes_compute": args.bytes,
            "cross_min": args.cross_min,
            "cross_max": args.cross_max,
            "steps": args.steps,
            "bytes_per_event": args.bytes_per_event,
            "crossing_fraction_min": min(frac_vals),
            "crossing_fraction_max": max(frac_vals),
            "epsilon_local_min": min(eps_vals) if eps_vals else 0.0,
            "epsilon_local_max": max(eps_vals) if eps_vals else 0.0,
        }

        print(f"Wrote {args.out}")
        print(
            " "
            f"Boundary={args.boundary} Compute={args.compute} "
            f"alpha={boundary.alpha_pj_per_event} "
            f"beta={boundary.beta_pj_per_byte} "
            f"compute={compute.pj_per_byte}"
        )
        frac_min = summary["crossing_fraction_min"]
        frac_max = summary["crossing_fraction_max"]
        print(
            f"Crossing fraction range: {frac_min:.3f} .. {frac_max:.3f}"
        )
        if eps_vals:
            eps_min = summary["epsilon_local_min"]
            eps_max = summary["epsilon_local_max"]
            print(
                f"Epsilon local range:     {eps_min:.3f} .. {eps_max:.3f}"
            )

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

    elif args.cmd == "compare":
        out = compare_baseline_vs_reduced(
            bytes_compute=args.bytes,
            cross_bytes=args.cross_bytes,
            bytes_per_event=args.bytes_per_event,
            reduce_factor=args.reduce_factor,
            compute=compute,
            boundary=boundary,
        )

        # human-readable output
        for k in [
            "baseline_total_pj",
            "baseline_cross_frac",
            "reduced_total_pj",
            "reduced_cross_frac",
            "energy_gain_x",
            "elasticity_effective",
        ]:
            print(f"{k}: {out[k]:.6f}")

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)

    else:
        raise SystemExit("Unknown command")
