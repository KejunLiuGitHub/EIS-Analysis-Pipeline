# EIS Analysis Lessons Learned

This directory contains hard-won lessons from ~20 rounds of debugging GPE_h3_131 + batch analysis of 12 additional EIS measurements. Each lesson is self-contained with problem, evidence, solution, and runnable code.

## Quick Reference

| # | Lesson | Key Takeaway |
|---|--------|-------------|
| 01 | [Data-Driven Initial Guesses](lesson-01-data-driven-guesses.md) | Never hardcode R1≈500; scale to z_span |
| 02 | [Multi-Model Selection](lesson-02-multi-model-selection.md) | Try R(RQ)/R(RQ)(RQ)/R(RQ)CPE; pick lowest χ² |
| 03 | [Zero-Crossing ≠ Rb](lesson-03-zero-crossing-not-Rb.md) | Intercept method fails when bulk arc is incomplete |
| 04 | [100 mV Nonlinearity](lesson-04-100mv-nonlinearity.md) | THD >5% proves pseudo-Faradaic Arc 2 |
| 05 | [Plotly Best Practices](lesson-05-plotly-patterns.md) | Independent axes, pre-computed hover, Plotly.react |
| 06 | [Quality Flags](lesson-06-quality-flags.md) | OK/WARN/POOR with explicit criteria |
| 07 | [Temperature Effects](lesson-07-temperature-effects.md) | χ² improves 10–100× from RT→80°C |
| 08 | [Cable-Dominated Data](lesson-08-cable-dominated.md) | Z range <1Ω → discard, not force-fit |
| 09 | [Interactive Report Bugs](lesson-09-interactive-report-bugs.md) | IIFE crash, Plotly.react on empty DOM, JSON field mismatch |

## Batch Analysis Summary (2026-05-12)

- **Total processed:** 13 measurements (5 sample types × 1–4 temperatures)
- **OK (usable for quantitative extraction):** 4/13
- **WARN (qualitative trends only):** 6/13
- **POOR (unusable):** 2/13 (GPE_h3_101 RT & 40°C)
- **Best performer:** GPE_h3_131 @ 40°C, σ = 3.6×10⁻⁵ S·cm⁻¹, χ²=0.3
