# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Electrochemical Impedance Spectroscopy (EIS) data for GPE (Gel Polymer Electrolyte) samples, collected with a BioLogic potentiostat (EC-Lab v11.62, 2024-12-19).

## File formats

- **`.mpr`** — EC-Lab binary data file. Use `galvani` to read directly (no EC-Lab needed). Contains 34 columns per data point: `freq/Hz`, `Re(Z)/Ohm`, `-Im(Z)/Ohm`, `|Z|/Ohm`, `Phase(Z)/deg`, `time/s`, plus voltage/current, harmonics (h2–h7), THD, NSD, NSR, etc.
- **`.mgr`** — EC-Lab graph display settings only (XML). Contains axis ranges, trace colors, plot layout. No measurement data.
- **`.txt`** — Exported EIS data (freq/Hz, Re(Z)/Ohm, Im(Z)/Ohm). Only 3 of the 34 columns from `.mpr`.

**Sign convention**: the `.mpr` column is named `-Im(Z)/Ohm` (stores the negative of imaginary impedance). The `.txt` column is `Im(Z)/Ohm`. They are negatives of each other: `mpr['-Im(Z)/Ohm'] = -txt['Im(Z)/Ohm']`.

## Reading data with Python

```python
from galvani import BioLogic

mpr = BioLogic.MPRfile("GPE_h3_131_C01.mpr")
data = mpr.data  # numpy structured array, shape (69,)

# Key columns for Nyquist/Bode plots
freq = data['freq/Hz']
z_re = data['Re(Z)/Ohm']
z_im = -data['-Im(Z)/Ohm']   # negate to get standard Im(Z)
z_mag = data['|Z|/Ohm']
phase = data['Phase(Z)/deg']
```

## Equivalent circuit fitting

`impedance` (v1.7.1) — note: `fit()` takes complex impedance, not separate real/imag:

```python
from impedance.models.circuits import CustomCircuit

Z = z_re + 1j * z_im  # complex impedance

circuit = CustomCircuit(initial_guess=[27, 1300, 1e-5, 0.8], circuit='R0-p(R1,CPE1)')
circuit.fit(freq, Z)
print(circuit)  # fitted parameter names and values
```

Common circuits:
- `R0-p(R1,CPE1)` — one depressed semicircle (R(RQ))
- `R0-p(R1,CPE1)-p(R2,CPE2)` — two semicircles (best fit for GPE_h3_131_C01, χ²/N≈52)
- `R0-p(R1,CPE1)-CPE2` — SPE blocking electrode model (R(RQ)CPE)

## Materials Performance Benchmark

Ion conductivity (σ) and activation energy (Ea) benchmark for this GPE/SPE dataset, measured at 100 mV AC amplitude.

### Room-temperature ion conductivity σ (S/cm)

| Sample | Type | Thickness | σ_RT | Grade |
|--------|------|-----------|------|-------|
| GPE-h3-131 | GPE | 30 µm | **5.85 × 10⁻⁶** | Low (usable) |
| GPE-h3-101-2 | GPE | 100 µm | **3.29 × 10⁻⁷** | Low |
| GPE-h4-201 | GPE | 100 µm | **2.01 × 10⁻⁷** | Low |
| SPE-3h-131 | SPE | 40 µm | **7.42 × 10⁻⁹** | Unreliable (POOR) |
| GPE-h3-101 | GPE | 100 µm | — | Fit failed |

**Context**: Typical GPE σ_RT = 10⁻⁴–10⁻³ S/cm; typical SPE σ_RT = 10⁻⁷–10⁻⁵ S/cm. Current GPE samples sit at the **SPE level** — 1–2 orders of magnitude below practical GPE targets. The 100 mV amplitude drives nonlinearity (THD I > 5% in many points), so true σ may be underestimated.

### Activation energy Ea (eV)

| Sample | Type | Ea | R² | Assessment |
|--------|------|-----|-----|-----------|
| SPE-3h-131 | SPE | **0.961** | 0.839 | High (questionable fit) |
| GPE-h4-201 | GPE | **0.944** | 0.999 | High (very linear) |

**Context**: Typical GPE Ea = 0.3–0.6 eV; typical SPE Ea = 0.5–0.8 eV. The ~0.95 eV observed here is **unusually high for GPE** — closer to ceramic oxide values — suggesting strong polymer-segment transport barriers or sub-optimal plasticizer/salt ratio.

### Key take-aways

1. **σ improves with temperature**: GPE-h3-131 reaches 3.58 × 10⁻⁵ S/cm at 40 °C — approaching the 10⁻⁵ practical threshold.
2. **Thickness matters**: 30 µm (GPE-h3-131) gives much cleaner data than 100 µm samples, which are dominated by blocking-electrode tails and cable artifacts.
3. **Reduce amplitude**: Re-measure at 10 mV to eliminate nonlinear distortion; the second arc (R₂) in GPE-h3-131 is partly a 100 mV artifact.
4. **Formulation gap**: If these are truly GPEs, σ_RT should be ~100× higher. Check plasticizer content, crosslink density, and salt loading.

## Output format

When generating analysis documents, figures, or reports → output HTML with MathJax for equations. Do not create LaTeX/PDF unless explicitly asked.
