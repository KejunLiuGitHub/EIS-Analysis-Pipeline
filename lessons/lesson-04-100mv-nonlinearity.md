# Lesson 4: 100 mV Amplitude Causes Nonlinearity

## Problem
Standard EIS uses 5–10 mV AC amplitude for linear response. Our measurements used 100 mV — 10–20× too large. This drives the system into nonlinear regime, especially at low frequencies where electrode polarization is strongest.

## Evidence: THD from .mpr Files
The `.mpr` binary contains THD (total harmonic distortion) data — 34 columns vs 3 in `.txt`. This is **direct proof** of nonlinearity.

| Sample | THD I > 5% | THD I > 10% | THD at 1 Hz | Arc 2 region? |
|--------|-----------|-------------|-------------|---------------|
| GPE_h3_131 RT | 29/69 (42%) | 18/69 (26%) | 19.9% | ❌ nonlinear |
| SPE_3h_131 RT | 14/42 (33%) | — | — | ❌ nonlinear |
| GPE_h3_131 @ 40°C | 0/32 (0%) | 0/32 (0%) | <1% | ✅ linear |
| GPE_h4_201 @ 80°C | — | — | <1% | ✅ mostly linear |

**Two nonlinear zones identified:**
1. **High-frequency (>2 MHz):** Cable artifact, THD from parasitic inductance
2. **Low-frequency (<10 Hz):** Arc 2 region, pseudo-Faradaic charge transfer at SS electrode

## Critical Observation
For GPE_h3_131 RT:
- **Mid-frequency (100 Hz–100 kHz):** THD I < 1% → **linear regime**
- **Arc 1 (fc = 46 Hz)** falls in this linear zone → **R₁ = 653 Ω is trustworthy**
- **Arc 2 (fc = 0.13 Hz)** falls in nonlinear zone → **R₂ = 3455 Ω is questionable**

## Solution
1. **For future experiments:** Reduce amplitude to 10 mV.
2. **For existing data:** Use THD to demarcate trustworthy vs untrustworthy frequency regions.
3. **In reporting:** Flag Arc 2 as "100 mV-induced pseudo-Faradaic process, not intrinsic."

## Code Pattern
```python
mpr = BioLogic.MPRfile("GPE_h3_131_C01.mpr")
d = mpr.data
thd_i = d['THD I/%'].astype(np.float64)

# Nonlinearity check
n_nonlinear = np.sum(thd_i > 5)
if n_nonlinear > len(thd_i) * 0.2:
    warnings.append(f"High THD: {n_nonlinear}/{len(thd_i)} pts > 5%")

# Arc 2 trustworthiness
if thd_i[-1] > 10:  # 1 Hz is last point
    arc2_note = "Arc 2 likely nonlinear artifact"
```

## Physical Interpretation
Under 10 mV linear excitation, the SS blocking electrode should show only capacitive behavior (CPE_dl). The 100 mV overpotential is sufficient to drive weak charge-transfer at the SS surface, creating a finite R₂ that disappears at proper amplitude. This explains why:
- Arc 2 has anomalously large C_eff (361 μF = 460 μF/cm²)
- α₂ = 0.55 is unusually low for a double-layer
- DC bias ⟨E_we⟩ = 0.425 V (not zero!) — rectification from nonlinearity
