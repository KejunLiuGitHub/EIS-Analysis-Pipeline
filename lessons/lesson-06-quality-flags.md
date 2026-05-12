# Lesson 6: Data Quality Three-Level Flags

## Rationale
Not all EIS data is created equal. A quantitative parameter table without quality context is misleading. We need explicit, reproducible criteria.

## Flag Definitions

### ✅ OK (Green)
**Criteria (ALL must be met):**
- Fit converged successfully
- χ²/(N−p) < 1000
- THD I > 5% at < 20% of frequencies
- No more than 50% points inductive
- Z range > 1 Ω

**Usage:** Parameters can be used quantitatively in papers. σ, R₁, C_eff are trustworthy.

### ⚠️ WARN (Yellow)
**Criteria (ANY of the following):**
- χ²/(N−p) = 1000–100000
- THD I > 5% at 20–50% of frequencies
- χ² acceptable but model is fallback (e.g., R(RQ) instead of R(RQ)(RQ))
- Minor data quality issues (< 3 warnings)

**Usage:** Usable for qualitative comparison (trends, Arrhenius slope) but individual parameters have large uncertainty. Always caveat in text.

### ❌ POOR / DO NOT USE (Red)
**Criteria (ANY of the following):**
- > 50% points inductive
- Z range < 1 Ω (cable-dominated)
- All models failed to converge
- **χ²/(N−p) > 100000** with residuals showing systematic bias
- < 10 capacitive points after cleaning
- **χ²/(N−p) > 10⁶** regardless of other indicators — fit is meaningless

**Usage:** Do not extract quantitative parameters. Do not include in Arrhenius plots. The data may still be plotted for visual comparison, but σ and R values are meaningless.

> **Critical rule:** χ² > 10⁶ is an automatic "DO NOT USE". It does not matter which model was nominally "best" — all models failed to capture the data, and any extracted σ is noise.

## Batch Results (2026-05-12)
| Flag | Count | Examples |
|------|-------|----------|
| ✅ OK | 4/13 | GPE_h3_131 @ 40°C, GPE_h4_201 @ RT/60/80°C (after correction), SPE_3h_131 @ 80°C |
| ⚠️ WARN | 3/13 | GPE_h3_101_2 RT, GPE_h4_201 RT (model-corrected), SPE_3h_131 @ 60°C |
| ❌ POOR / DO NOT USE | 5/13 | GPE_h3_101 RT & 40°C, GPE_h4_201 @ 40°C, SPE_3h_131 RT & 40°C |

### Unusable Data Detailed
| Sample | χ² | Why Unusable |
|--------|-----|-------------|
| GPE_h3_101 RT | FAILED | Cable-dominated, Z range 0.04 Ω |
| GPE_h3_101 40°C | FAILED | Cable-dominated, Z range 0.18 Ω |
| GPE_h4_201 40°C | 8.3×10⁴ | Arc unresolved; all models struggle |
| SPE_3h_131 RT | 7.3×10⁶ | Severe nonlinearity (THD 33%), mostly tail |
| SPE_3h_131 40°C | 2.6×10⁶ | Same as RT |

## Code Implementation
```python
warnings = []

# THD check
n_thd = int(np.sum(thd_i > 5))
if n_thd > len(freq_all) * 0.2:
    warnings.append(f"High THD: {n_thd}/{len(freq_all)} pts > 5%")

# Inductive artifact check
cap = Z_all.imag <= 0
n_rem = int((~cap).sum())
if n_rem > len(freq_all) * 0.5:
    warnings.append(f"Excessive inductive: {n_rem}/{len(freq_all)} pts")

# Z range check
z_range = float(np.max(np.abs(Z)) - np.min(np.abs(Z)))
if z_range < 1.0:
    warnings.append(f"Z range {z_range:.2f}Ω — cable-dominated")

# Fit quality check
if fit.get("converged"):
    if fit["chi2_N"] > 1e6:
        warnings.append(f"CRITICAL: χ²/N={fit['chi2_N']:.0e} > 10⁶ — UNUSABLE")
    elif fit["chi2_N"] > 100000:
        warnings.append(f"Poor fit: χ²/N={fit['chi2_N']:.0f}")

# Assign flag
if any("CRITICAL" in w or "UNUSABLE" in w for w in warnings):
    quality = "DO NOT USE"
elif any("Excessive" in w or "cable-dominated" in w for w in warnings):
    quality = "POOR"
elif not warnings:
    quality = "OK"
else:
    quality = "WARN"
```

## UI Badge
In HTML reports, make the flag visually prominent and impossible to miss:

```html
<p><strong>Quality:</strong> 
  <span class="quality-ok">✅ OK</span> |
  <span class="quality-warn">⚠️ WARN</span> |
  <span class="quality-poor">❌ POOR / DO NOT USE</span>
</p>

<div class="warn" style="border:2px solid #d6604d;">
  <strong>❌ DO NOT USE — χ²/N = 7.3×10⁶</strong><br>
  This data exceeds the quantitative usability threshold (χ² > 10⁶).
  Do not extract σ or R values. Plot for visual comparison only.
</div>
```

## Decision Tree
```
Data cleaned?
  ├─ No (inductive > 50% or Z < 1Ω) → ❌ POOR
  └─ Yes
       └─ Fit converged?
            ├─ No → ❌ POOR
            └─ Yes
                 └─ χ² < 1000?
                      ├─ Yes → ✅ OK
                      └─ No
                           └─ χ² < 10⁶?
                                ├─ Yes → ⚠️ WARN
                                └─ No → ❌ DO NOT USE
```
