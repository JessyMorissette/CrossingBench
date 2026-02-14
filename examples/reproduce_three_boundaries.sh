#!/usr/bin/env bash
set -euo pipefail

# Reproduce the three-boundary evidence used in the paper.
# Outputs CSVs in the current directory.

crossingbench sweep --boundary analog  --compute analog  --out analog.csv
crossingbench sweep --boundary memory  --compute digital --out memory.csv
crossingbench sweep --boundary chiplet --compute digital --out chiplet.csv

echo "Done. Wrote: analog.csv memory.csv chiplet.csv"
