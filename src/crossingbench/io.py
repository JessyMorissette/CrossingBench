from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from .core import ResultPoint


def write_csv(path: str | Path, rows: Iterable[ResultPoint]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "bytes_compute",
                "bytes_cross",
                "events_cross",
                "c_intra_pj",
                "c_cross_pj",
                "c_total_pj",
                "crossing_fraction",
                "epsilon_local",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.bytes_compute,
                    r.bytes_cross,
                    r.events_cross,
                    f"{r.c_intra_pj:.6f}",
                    f"{r.c_cross_pj:.6f}",
                    f"{r.c_total_pj:.6f}",
                    f"{r.crossing_fraction:.6f}",
                    f"{r.epsilon_local:.6f}",
                ]
            )
