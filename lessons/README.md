# EIS Analysis Lessons Learned

This directory contains hard-won lessons from ~20 rounds of debugging GPE_h3_131 + batch analysis of 12 additional EIS measurements. Each lesson is self-contained with problem, evidence, solution, and runnable code.

## Quick Reference

| # | Lesson | Key Takeaway |
|---|--------|-------------|
| 01 | [Data-Driven Initial Guesses](lesson-01-data-driven-guesses.md) | Never hardcode R1≈500; scale to z_span |
| 02 | [Multi-Model Selection](lesson-02-multi-model-selection.md) | Try R(RQ)/R(RQ)(RQ)/R(RQ)CPE/**R(R,C)CPE**; pick lowest χ² |
| 03 | [Zero-Crossing ≠ Rb](lesson-03-zero-crossing-not-Rb.md) | Intercept method fails when bulk arc is incomplete |
| 04 | [100 mV Nonlinearity](lesson-04-100mv-nonlinearity.md) | THD >5% proves pseudo-Faradaic Arc 2 |
| 05 | [Plotly Best Practices](lesson-05-plotly-patterns.md) | Independent axes, pre-computed hover, Plotly.react |
| 06 | [Quality Flags](lesson-06-quality-flags.md) | OK/WARN/**DO NOT USE** with explicit criteria |
| 07 | [Temperature Effects](lesson-07-temperature-effects.md) | χ² improves 10–100× from RT→80°C |
| 08 | [Cable-Dominated Data](lesson-08-cable-dominated.md) | Z range <1Ω → discard, not force-fit |
| 09 | [Ideal Capacitor vs CPE](lesson-09-ideal-cap-vs-cpe.md) | Near-ideal arc → R(R,C)CPE; depressed arc → R(RQ)CPE |

## Batch Analysis Summary (2026-05-12)

- **Total processed:** 13 measurements (5 sample types × 1–4 temperatures)
- **OK (usable for quantitative extraction):** 4/13
- **WARN (qualitative trends only):** 3/13
- **POOR / DO NOT USE:** 5/13

### Key Corrections from Re-fit

| Sample | Old Model | Old σ | New Model | New σ | Change |
|--------|-----------|-------|-----------|-------|--------|
| GPE_h4_201 RT | R(RQ) | 3.87×10⁻⁸ | **R(R,C)CPE** | **7.55×10⁻⁷** | **20×** |
| GPE_h4_201 60°C | R(RQ)(RQ) | 1.19×10⁻⁷ | **R(R,C)CPE** | **1.48×10⁻⁶** | **12×** |

**Lesson:** When the bulk arc is near-ideal (α ≈ 0.9) and a steep blocking tail dominates, forcing a depressed semicircle (CPE) or a second arc overestimates R₁ by 10–100×.

### Data Marked as DO NOT USE

| Sample | Reason |
|--------|--------|
| GPE_h3_101 RT & 40°C | Cable-dominated, Z < 1 Ω |
| GPE_h4_201 40°C | Arc unresolved, all models χ² > 10⁴ |
| SPE_3h_131 RT & 40°C | χ² > 10⁶, severe nonlinearity |

### Usable Arrhenius Points

| Sample | RT | 40°C | 60°C | 80°C |
|--------|-----|------|------|------|
| GPE_h3_131 | — | ✅ | — | — |
| GPE_h4_201 | ✅ | ❌ | ✅ | ✅ |
| SPE_3h_131 | ❌ | ❌ | ⚠️ | ✅ |
