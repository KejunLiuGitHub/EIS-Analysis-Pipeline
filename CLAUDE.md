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

## Output format

When generating analysis documents, figures, or reports → output HTML with MathJax for equations. Do not create LaTeX/PDF unless explicitly asked.
