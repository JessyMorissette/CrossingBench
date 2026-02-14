# Cost Parameter Hypotheses

Every energy value used in CrossingBench is documented here with its
source, derivation, and assumptions.

## Compute Costs

| Key      | Value (pJ/byte) | Derivation                                              |
|----------|------------------|---------------------------------------------------------|
| `analog` | 0.0001           | 0.1 fJ/MAC, best CIM crossbar (Wan et al., Nature 2022). 1 MAC ≈ 1 byte (8b×8b). |
| `digital`| 0.25             | ~0.5 pJ per FP16 op on 7nm GPU. 1 op processes 2 bytes → 0.25 pJ/byte. |
| `lowv`   | 0.05             | Approximate near-threshold voltage scaling (~5× below nominal digital). |

## Crossing Costs (β, pJ/byte)

| Boundary  | β (pJ/byte) | Derivation                                              |
|-----------|-------------|---------------------------------------------------------|
| `analog`  | 3.20        | 6-bit SAR ADC, Walden FoM 50 fJ/conv-step. 50 × 2^6 = 3200 fJ per value. 1 value = 1 byte. Source: Murmann ADC Survey. |
| `memory`  | 1.25        | Horowitz (ISSCC 2014): ~20 pJ per 8-byte DRAM word at 45nm. Scaled to 7nm (~0.65× energy): ~10 pJ / 8 bytes = 1.25 pJ/byte. |
| `chiplet` | 5.00        | UCIe 1.0 spec: ~0.5 pJ/bit for short-reach die-to-die. With protocol/SerDes overhead: ~5 pJ/byte. |
| `hbm`     | 10.00       | Samsung HBM3 datasheet: ~3.9 pJ/bit. With memory controller overhead: ~10 pJ/byte. |
| `voltage` | 0.80        | Multi-Vdd DVFS literature: ~0.1 pJ/bit level-shifter cost = 0.8 pJ/byte. |

## Crossing Costs (α, pJ/event) — Currently Set to Zero

The α term models fixed per-event overhead (ADC calibration, chiplet link
setup, DRAM row activation). In v0, all α values are set to 0.0 because:

1. The β·bytes term dominates for typical burst sizes (≥32 bytes).
2. Published data on per-event fixed costs is sparse and inconsistent.
3. Setting α=0 is conservative — it underestimates total crossing cost,
   making the law's predictions a lower bound.

Future work should estimate α for at least ADC (calibration cycles) and
chiplet (link training latency amortized over packet count).

## Workload Parameters

| Parameter        | Value   | Rationale                                    |
|------------------|---------|----------------------------------------------|
| bytes_compute    | 262,144 | 256 KB — representative of a medium DNN layer |
| bytes_per_event  | 256     | One 256-element vector per conversion event  |
| cross_min        | 256     | 1 crossing event                             |
| cross_max        | 524,288 | 2× compute volume — fully crossing-dominated |

## References

1. M. Horowitz, "Computing's Energy Problem," ISSCC, 2014.
2. W. Wan et al., "A Compute-in-Memory Chip Based on RRAM," Nature, 2022.
3. UCIe Consortium, "UCIe 1.0 Specification," March 2022.
4. Samsung Electronics, "HBM3 DRAM Datasheet," Rev. 1.0, 2023.
5. B. Murmann, "ADC Performance Survey 1997–2024," Stanford University.
6. X. Peng et al., "DNN+NeuroSim V2.0," IEEE TCAD, 2021.
