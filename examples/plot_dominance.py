import matplotlib.pyplot as plt

# ── Exact data from CrossingBench CSVs ──────────────────────────────────

bytes_cross = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]

# Analog: β=3.20 pJ/B, compute=0.1 pJ/B (c_intra=26.21 pJ)
cf_analog = [0.968992, 0.984252, 0.992063, 0.996016, 0.998004, 0.999001,
             0.999500, 0.999750, 0.999875, 0.999938, 0.999969, 0.999984]

# Chiplet: β=5.00 pJ/B, compute=0.25 pJ/B (c_intra=65536 pJ)
cf_chiplet = [0.019157, 0.037594, 0.072464, 0.135135, 0.238095, 0.384615,
              0.555556, 0.714286, 0.833333, 0.909091, 0.952381, 0.975610]

# Memory: β=1.25 pJ/B, compute=0.25 pJ/B (c_intra=65536 pJ)
cf_memory = [0.004859, 0.009671, 0.019157, 0.037594, 0.072464, 0.135135,
             0.238095, 0.384615, 0.555556, 0.714286, 0.833333, 0.909091]

# ── Uncertainty bands: ±20% on β ────────────────────────────────────────

def crossing_fraction(beta, bytes_cross_val, c_intra):
    c_cross = beta * bytes_cross_val
    return c_cross / (c_intra + c_cross)

c_intra_analog = 26.2144      # 262144 * 0.1e-3 ... actually 262144 * 0.0001 = 26.2144
c_intra_digital = 65536.0     # 262144 * 0.25

beta_analog = 3.20
beta_chiplet = 5.00
beta_memory = 1.25

uncertainty = 0.20  # ±20%

def get_band(beta, c_intra):
    lo = [crossing_fraction(beta * (1 - uncertainty), bc, c_intra) for bc in bytes_cross]
    hi = [crossing_fraction(beta * (1 + uncertainty), bc, c_intra) for bc in bytes_cross]
    return lo, hi

analog_lo, analog_hi = get_band(beta_analog, c_intra_analog)
chiplet_lo, chiplet_hi = get_band(beta_chiplet, c_intra_digital)
memory_lo, memory_hi = get_band(beta_memory, c_intra_digital)

# ── Plot ────────────────────────────────────────────────────────────────

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
})

fig, ax = plt.subplots(figsize=(11, 6.5))

# Uncertainty bands
ax.fill_between(bytes_cross, analog_lo, analog_hi, alpha=0.15, color='#1f77b4', linewidth=0)
ax.fill_between(bytes_cross, chiplet_lo, chiplet_hi, alpha=0.15, color='#e8811a', linewidth=0)
ax.fill_between(bytes_cross, memory_lo, memory_hi, alpha=0.15, color='#2ca02c', linewidth=0)

# Main curves
ax.plot(bytes_cross, cf_analog, 'o-', color='#1f77b4', linewidth=2.2, markersize=7,
        label=r'Analog (β = 3.20 pJ/B, compute = 0.1 pJ/B)', zorder=5)
ax.plot(bytes_cross, cf_chiplet, 's-', color='#e8811a', linewidth=2.2, markersize=7,
        label=r'Chiplet (β = 5.00 pJ/B, compute = 0.25 pJ/B)', zorder=5)
ax.plot(bytes_cross, cf_memory, '^-', color='#2ca02c', linewidth=2.2, markersize=7,
        label=r'Memory (β = 1.25 pJ/B, compute = 0.25 pJ/B)', zorder=5)

# 50% threshold line
ax.axhline(y=0.5, color='gray', linestyle='--', linewidth=1.0, alpha=0.7, zorder=2)
ax.text(bytes_cross[-1] * 1.05, 0.505, 'ε = 0.5 transition',
        fontsize=10, color='gray', va='bottom', ha='right', style='italic')

# Axes
ax.set_xscale('log')
ax.set_xlabel(r'Crossing Volume $V_b$ (Bytes)', fontsize=13)
ax.set_ylabel(r'Crossing Fraction  ($E_{\mathrm{cross}} \,/\, E_{\mathrm{total}}$)', fontsize=13)
ax.set_title(r'Domain Crossing Law: Energy Dominance by Boundary Cost $\beta$',
             fontsize=14, fontweight='bold', pad=12)

ax.set_ylim(-0.02, 1.05)
ax.set_xlim(bytes_cross[0] * 0.7, bytes_cross[-1] * 1.5)

# Grid
ax.grid(True, which='major', linestyle='-', alpha=0.15)
ax.grid(True, which='minor', linestyle='-', alpha=0.07)

# Legend
ax.legend(loc='lower right', fontsize=10, framealpha=0.9, edgecolor='0.8')

# Caption below figure
caption = (
    r"$\bf{Figure\ 1.}$ Crossing energy fraction vs. crossing volume for three boundary types. "
    "Analog CIM uses an ultra-low intra-domain compute cost (0.1 pJ/B); chiplet and memory\n"
    r"boundaries share a digital compute baseline (0.25 pJ/B)."
    r" Shaded regions: ±20% uncertainty on $\beta$. "
    "Data: CrossingBench sweep with 262 144 B compute volume."
)
fig.text(0.5, -0.01, caption, ha='center', fontsize=9.5, color='0.3',
         wrap=True, linespacing=1.4)

plt.tight_layout()
plt.savefig('/home/claude/crossing_dominance.png', dpi=300, bbox_inches='tight',
            facecolor='white', pad_inches=0.3)
plt.savefig('/home/claude/crossing_dominance.pdf', bbox_inches='tight',
            facecolor='white', pad_inches=0.3)
print("Done – PNG and PDF saved.")
