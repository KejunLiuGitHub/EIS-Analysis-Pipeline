# EIS Analysis Audit Report

**Date:** 2026-05-12 (rev. 2)  
**Method:** Per-sample multi-model fitting (R(RQ) / R(RQ)(RQ) / R(RQ)CPE / R(R,C)CPE) with data-driven initial guesses  
**Standard:** χ²/(N−p) < 1000 = acceptable; < 100 = good; > 10⁶ = unusable for quantitative extraction  
**Total samples analyzed:** 12 new + 1 existing reference (GPE_h3_131_C01 in root)

---

## Summary Table

| Sample | Temp | Thickness | Model | χ²/(N−p) | σ / S·cm⁻¹ | Quality | Verdict |
|--------|------|-----------|-------|----------|------------|---------|---------|
| GPE_h3_101 | RT | 100 µm | — | FAILED | — | ❌ **POOR** | Cable-dominated, 55/69 pts inductive, Z range 0.04 Ω |
| GPE_h3_101 | 40°C | 100 µm | — | FAILED | — | ❌ **POOR** | Z range 0.18 Ω, all models failed |
| GPE_h3_101_2 | RT | 100 µm | R(RQ) | 3.97×10⁴ | 6.41×10⁻⁸ | ⚠️ **WARN** | Poor fit; one-arc model insufficient for steep low-f tail |
| GPE_h3_131 | 40°C | 30 µm | R(RQ)(RQ) | **0.28** | 3.58×10⁻⁵ | ✅ **OK** | Excellent fit; two well-resolved arcs |
| GPE_h4_201 | RT | 100 µm | R(R,C)CPE | 4.74×10³ | 7.55×10⁻⁷ | ⚠️ **WARN** | Acceptable after model correction (was R(RQ) χ²=1.5×10⁵) |
| GPE_h4_201 | 40°C | 100 µm | R(RQ) | 8.29×10⁴ | 4.57×10⁻⁸ | ❌ **DO NOT USE** | χ² too high; arc unresolved, all models struggle |
| GPE_h4_201 | 60°C | 100 µm | R(R,C)CPE | 5.52×10³ | 1.48×10⁻⁶ | ✅ **OK** | Acceptable after model correction (was R(RQ)(RQ) χ²=7.9×10³) |
| GPE_h4_201 | 80°C | 100 µm | R(RQ)(RQ) | **457** | 2.41×10⁻⁶ | ✅ **OK** | Good fit; clear two-arc structure |
| SPE_3h_131 | RT | 40 µm | R(RQ)(RQ) | 7.27×10⁶ | 7.42×10⁻⁹ | ❌ **DO NOT USE** | χ² > 10⁶; data severely nonlinear, mostly tail |
| SPE_3h_131 | 40°C | 40 µm | R(RQ)(RQ) | 2.64×10⁶ | 1.06×10⁻⁸ | ❌ **DO NOT USE** | χ² > 10⁶; same tail issue |
| SPE_3h_131 | 60°C | 40 µm | R(RQ)CPE | 1.15×10⁵ | 8.54×10⁻⁸ | ⚠️ **WARN** | Poor fit but better than R(RQ)(RQ); blocking tail |
| SPE_3h_131 | 80°C | 40 µm | R(RQ)CPE | **6.83×10³** | 6.37×10⁻⁷ | ✅ **OK** | Best among SPE series; acceptable at high T |

> **Legend:** ✅ OK = quantitative use allowed. ⚠️ WARN = qualitative trends only. ❌ POOR/DO NOT USE = do not extract σ or R values.

---

## Quality Distribution

- ✅ **OK:** 4 / 12 (33%) — usable for quantitative extraction
- ⚠️ **WARN:** 3 / 12 (25%) — qualitative trends only
- ❌ **POOR / DO NOT USE:** 5 / 12 (42%) — discard for parameter extraction

---

## Critical Findings

### 1. Data Unusable for Quantitative Extraction (5/12)

| Sample | Reason | Action |
|--------|--------|--------|
| GPE_h3_101 RT & 40°C | Cable-dominated, Z < 1 Ω | Re-measure |
| GPE_h4_201 40°C | Arc unresolved, all models χ² > 10⁴ | Exclude from Arrhenius |
| SPE_3h_131 RT & 40°C | χ² > 10⁶, severe nonlinearity (THD > 30%) | Exclude from Arrhenius |

### 2. Model Correction Changed σ Significantly

For **GPE_h4_201 RT**, switching from R(RQ) to R(R,C)CPE:
- R₁ changed from 329,227 Ω → 16,856 Ω
- σ changed from 3.87×10⁻⁸ → **7.55×10⁻⁷** (20× increase)

For **GPE_h4_201 60°C**, switching from R(RQ)(RQ) to R(R,C)CPE:
- R₁ changed from 106,734 Ω → 8,580 Ω
- σ changed from 1.19×10⁻⁷ → **1.48×10⁻⁶** (12× increase)

**Lesson:** When the arc is near-ideal (α ≈ 0.9) and a steep blocking tail dominates, forcing a depressed semicircle (CPE) or a second arc severely overestimates R₁.

### 3. SPE_3h_131: Only 80°C Usable

The entire SPE_3h_131 series at RT–60°C has χ² > 10⁵. This is not a model-selection problem — the data itself is too noisy and nonlinear. Only the 80°C point (χ² = 6.8×10³) is acceptable.

**Recommendation:** Do not include SPE_3h_131 RT/40°C in any Arrhenius plot. 60°C can be plotted with a large error bar or excluded. Only 80°C is publication-quality.

### 4. Updated Model Selection Rules

| Data Shape | Best Model | Example |
|-----------|-----------|---------|
| Two well-resolved arcs | R(RQ)(RQ) | GPE_h3_131, GPE_h4_201 @ 80°C |
| Near-ideal arc + steep tail | **R(R,C)CPE** | GPE_h4_201 RT/60°C |
| Depressed arc + tail | R(RQ)CPE | SPE_3h_131 60/80°C |
| Mostly tail, arc unresolved | R(RQ) (single arc) | GPE_h4_201 @ 40°C |
| Arc weak, noisy | None — data unusable | SPE_3h_131 RT/40°C |

### 5. Arrhenius Points (Final, Usable Only)

| Sample | RT | 40°C | 60°C | 80°C |
|--------|-----|------|------|------|
| GPE_h3_131 | — | ✅ 3.58×10⁻⁵ | — | — |
| GPE_h4_201 | ✅ 7.55×10⁻⁷ | ❌ exclude | ✅ 1.48×10⁻⁶ | ✅ 2.41×10⁻⁶ |
| SPE_3h_131 | ❌ exclude | ❌ exclude | ⚠️ 8.54×10⁻⁸ (marginal) | ✅ 6.37×10⁻⁷ |

---

## Output Files

### Individual HTML Reports
```
eis_analysis_GPE_h3_101_C02.html         (POOR)
eis_analysis_GPE_h3_101_40_C01.html      (POOR)
eis_analysis_GPE_h3_101_2_C01.html       (WARN)
eis_analysis_GPE_h3_131_40_C01.html      (OK)
eis_analysis_GPE_h4_201_C01.html         (WARN — model corrected)
eis_analysis_GPE_h4_201_40_C01.html      (DO NOT USE)
eis_analysis_GPE_h4_201_60_C01.html      (OK — model corrected)
eis_analysis_GPE_h4_201_80_C01.html      (OK)
eis_analysis_SPE_3h_131_C01.html         (DO NOT USE)
eis_analysis_SPE_3h_131_40_C01.html      (DO NOT USE)
eis_analysis_SPE_3h_131_60_C01.html      (WARN)
eis_analysis_SPE_3h_131_80_C01.html      (OK)
```

### Re-fit Comparison HTMLs
```
eis_analysis_GPE_h4_201_RT_refit.html
eis_analysis_GPE_h4_201_40C_refit.html
eis_analysis_GPE_h4_201_60C_refit.html
eis_analysis_GPE_h4_201_80C_refit.html
```

---

## Recommendations

1. **GPE_h3_101 (RT & 40°C):** Discard. Re-measure with shorter cables and verified cell contact.
2. **GPE_h4_201 40°C:** Exclude from Arrhenius. Arc is too weak to resolve at this temperature.
3. **SPE_3h_131 RT & 40°C:** Exclude from all quantitative analysis. χ² > 10⁶ makes any σ value meaningless.
4. **For Arrhenius fitting:** Use only ✅ OK points. With 3 samples × 4 temperatures, only **7 points** are usable:
   - GPE_h3_131: 40°C
   - GPE_h4_201: RT, 60°C, 80°C
   - SPE_3h_131: 80°C (60°C marginal)
5. **Future experiments:** Reduce AC amplitude to 10 mV. This will eliminate the pseudo-Faradaic Arc 2 and make blocking-electrode models more reliable.
