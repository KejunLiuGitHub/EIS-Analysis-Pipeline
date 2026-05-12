# Lesson 8: Recognizing Cable-Dominated Data

## Problem
Some measurements are dominated by cable parasitics rather than the sample. Forcing a fit produces meaningless parameters with absurd σ values.

## Signature
Cable-dominated data has three unmistakable signatures:

1. **Z range < 1 Ω** after cleaning
2. **> 50% points inductive** (Im(Z) > 0, cable inductance L ≈ 1 μH)
3. **Residuals show no arc structure** — data is flat line near origin

## Evidence: GPE_h3_101
```
File: GPE_h3_101_C02.mpr
Total points: 69
Inductive points removed: 55/69 (80%)
Capacitive points kept: 14
Z range (cleaned): 0.04 Ω
σ (from z_cross): 1.87×10⁻² S·cm⁻¹  ← ABSURD for polymer
```

The Nyquist plot shows no semicircle — just a flat cluster near 0.7 Ω. This is pure cable resistance + inductance. The "capacitive" tail at f < 20 Hz is just noise.

## When to Discard
**Do not fit if ANY of the following is true:**
```python
if n_removed > n_total * 0.5:
    verdict = "DISCARD — cable-dominated"
elif z_range < 1.0:
    verdict = "DISCARD — impedance too low"
elif len(freq_capacitive) < 10:
    verdict = "DISCARD — insufficient data"
```

For GPE_h3_101, **all three criteria triggered.** The HTML report was still generated (for documentation), but marked ❌ POOR with explicit warnings.

## Root Causes & Fixes
| Cause | Check | Fix |
|-------|-------|-----|
| Poor cell contact | R0 > 100 Ω with no arc | Re-assemble cell, check pressure |
| Cable too long | Inductive artifacts at >100 kHz | Use shorter cables, twist pairs |
| Instrument calibration | Z offset at high f | Run calibration with short/open/load |
| Sample not connected | |Z| ≈ 0 | Check electrodes, film continuity |
| Film too thick / too resistive | |Z| > 100 kΩ, mostly tail | Reduce thickness or increase salt |

## Contrast: What Good Data Looks Like
| Feature | Good (GPE_h3_131) | Bad (GPE_h3_101) |
|---------|-------------------|------------------|
| Inductive pts | 16/69 (23%) | 55/69 (80%) |
| Z range | ~4 kΩ | 0.04 Ω |
| Arc visible? | Yes, two arcs | No arcs |
| σ | 5.9×10⁻⁶ (reasonable) | 1.9×10⁻² (absurd) |

## Code Pattern
```python
def assess_data_quality(freq_all, Z_all):
    cap_mask = Z_all.imag <= 0
    n_removed = int((~cap_mask).sum())
    freq = freq_all[cap_mask]
    Z = Z_all[cap_mask]
    
    issues = []
    if n_removed > len(freq_all) * 0.5:
        issues.append("Excessive inductive artifacts — check cables/cell")
    if len(Z) > 0:
        z_range = float(np.max(np.abs(Z)) - np.min(np.abs(Z)))
        if z_range < 1.0:
            issues.append("Z range < 1Ω — cable-dominated measurement")
    if len(freq) < 10:
        issues.append("<10 capacitive points — insufficient for fitting")
    
    return issues, len(freq) > 10 and z_range > 1.0
```
