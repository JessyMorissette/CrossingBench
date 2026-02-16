# The Domain Crossing Law — v1.0

## 1. Definitions

A **domain boundary** is any transition that changes the representation,
transport mechanism, or constraint space of data. Examples:

| Boundary              | Representation Change                 |
|-----------------------|---------------------------------------|
| Analog ↔ Digital      | Continuous voltage → discrete code    |
| Memory ↔ Compute      | Storage location → processing element |
| Chiplet ↔ Chiplet     | Die A → Die B (inter-die link)        |
| Near ↔ Far Memory     | SRAM/L1 → HBM/DRAM                   |
| Voltage ↔ Voltage     | V_dd1 → V_dd2 (level shifter)        |

Let:

- **V_b** = total bytes crossing boundary *b* during execution
- **k_b** = energy cost per byte for boundary *b* (pJ/byte)
- **C_intra** = intra-domain compute cost (pJ)

All costs are expressed in **pJ/byte**, ensuring unit consistency across
heterogeneous domains.

---

## 2. Cost Decomposition

For any program *P* on heterogeneous architecture *H*:

```
C(P,H) = C_intra(P,H) + Σ_b V_b(P,H) · k_b(H)
```

This decomposition is accurate when crossing costs are independent and
per-byte cost is approximately constant (burst-amortizable). Empirically,
it matches within 10–15% across five boundary types under burst-amortized
conditions.

The full model, accounting for fixed per-event overhead, is:

```
C_cross = α_b · events + β_b · bytes
```

where α_b captures setup costs (ADC calibration, chiplet link
establishment) and β_b captures per-byte transfer cost. The β term
dominates for typical burst sizes (≥32 bytes).

---

## 3. Crossing Dominance and Elasticity

Define **elasticity** with respect to crossing volume:

```
ε_b = ∂log(C) / ∂log(V_b)
```

Interpretation:

- **ε → 1**: cost scales linearly with crossings → *crossing-dominant regime*
- **ε → 0**: crossings negligible → *compute-dominant regime*

The crossing-dominant regime is empirically observed when crossing energy
fraction exceeds ~70% of total energy.

### Structural Property (Dominance ⇒ Linearity)

For any heterogeneous architecture *H* and program *P*, if
Σ_b V_b · k_b >> C_intra, then ε_b → 1 and ∂C/∂V_b ≈ k_b.

Consequently, reducing crossing volume V_b yields near-linear system-level
energy reduction in crossing-dominated regimes. The dominance condition is
measurable via ε and does not require a priori workload classification.

### Structural Ratio

The dominance transition is governed by the dimensionless ratio:
```
R = β_b · V_b / C_intra
```

When R >> 1, the system is crossing-dominant (ε → 1). When R << 1, it is
compute-dominant (ε → 0).

This clarifies why analog CIM reaches dominance at very low crossing
volumes: with C_intra = 0.0001 pJ/byte, even modest V_b produces R >> 1.
Chiplet and memory boundaries share a higher compute baseline (0.25 pJ/byte),
requiring proportionally larger V_b to cross the same threshold. The
transition depends on β/C_intra, not on β alone.

---

## 4. Empirical Results (7nm, pJ/byte)

| Boundary           | c_compute | c_crossing | Ratio    | Source                    |
|--------------------|-----------|------------|----------|---------------------------|
| Analog ↔ Digital   | 0.0001    | 3.20       | 32,000×  | Wan et al., Nature 2022   |
| Memory ↔ Compute   | 0.25      | 1.25       | 5×       | Horowitz 2014, 7nm scaled |
| Chiplet ↔ Chiplet  | 0.25      | 5.00       | 20×      | UCIe 1.0 Specification    |
| Near ↔ Far Memory  | 0.25      | 10.00      | 40×      | Samsung HBM3 Datasheet    |
| Voltage ↔ Voltage  | 0.05      | 0.80       | 16×      | Multi-Vdd DVFS literature |

**Geometric mean ratio: 73×** (computed across the five boundary types).

### Technology Invariance

Tested across 3nm–28nm. Ratios decrease at advanced nodes (compute
improves faster than crossing) but remain ≥2× at all nodes for all
boundary types.

### Scale Invariance

Tipping points (crossing fraction > 50%) range from 0.1% (analog,
extreme sensitivity) to 50% (memory, low sensitivity). All fall within
realistic workload parameters.

### Elasticity Measurements

In crossing-dominated regimes (>70% crossing fraction):

| Boundary           | ε (crossing) |
|--------------------|--------------|
| Analog ↔ Digital   | 0.996        |
| Memory ↔ Compute   | 0.763        |
| Chiplet ↔ Chiplet  | 0.838        |
| Near ↔ Far Memory  | 0.862        |
| Voltage ↔ Voltage  | 0.865        |

---

## 5. Corollaries

1. **Diminishing returns of hardware improvement.** Improving c_b (better
   ADC, faster memory) yields bounded gains when V_b is structurally high.

2. **Near-linear architectural gains.** Reducing V_b (fusion, co-location,
   domain extension) gives near-linear energy reduction when ε → 1.

3. **Correct optimization target.** The compiler objective for
   heterogeneous systems is:
   ```
   min Σ_b V_b · k_b   subject to   error ≤ τ,  latency ≤ L
   ```

---

## 6. Conditions of Validity

The law does **not** claim universal crossing dominance. It provides ε as
the metric to distinguish regimes:

- When ε ≈ 1: optimize crossings (architecture)
- When ε ≈ 0: optimize compute (technology)

The linear cost model (C = β·bytes) is accurate for burst sizes ≥32 bytes.
For very small transfers, the α·events term becomes significant.

Time-domain encoding advantages are bounded to ≤8-bit regimes; at higher
resolutions, jitter and counter precision may restore exponential scaling.

Crossing costs k_b may vary over device lifetime due to conductance drift
(analog), electromigration (interconnect), and HBM degradation.

---

## 7. The Core Insight

> The correct unit of optimization in heterogeneous computing is not the
> operation — it is the crossing.

---

*Version 1.0 — February 2026*
