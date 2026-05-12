# Lesson 7: Temperature Dramatically Improves Fit Quality

## Observation
For temperature-series samples, fit quality (χ²/N) improves by **1–2 orders of magnitude** from RT to 80°C. This is because faster ionic dynamics complete the bulk arc within the measurement window.

## Evidence

### GPE_h4_201
| Temp | Best Model | χ²/(N−p) | σ / S·cm⁻¹ | Improvement |
|------|-----------|----------|------------|-------------|
| RT | R(RQ) | 1.46×10⁵ | 3.9×10⁻⁸ | — |
| 40°C | R(RQ) | 8.29×10⁴ | 4.6×10⁻⁸ | 1.8× |
| 60°C | R(RQ)(RQ) | 7.94×10³ | 1.2×10⁻⁷ | 18× |
| 80°C | R(RQ)(RQ) | **457** | 2.4×10⁻⁶ | **320×** |

At RT and 40°C, only one arc is visible; the second arc is buried in the low-frequency tail. At 60°C and above, two distinct arcs emerge, and R(RQ)(RQ) becomes the best model.

### SPE_3h_131
| Temp | Best Model | χ²/(N−p) | σ / S·cm⁻¹ | Improvement |
|------|-----------|----------|------------|-------------|
| RT | R(RQ)(RQ) | 7.27×10⁶ | 7.4×10⁻⁹ | — |
| 40°C | R(RQ)(RQ) | 2.64×10⁶ | 1.1×10⁻⁸ | 2.8× |
| 60°C | R(RQ)CPE | 1.15×10⁵ | 8.5×10⁻⁸ | 63× |
| 80°C | R(RQ)CPE | **6.83×10³** | 6.4×10⁻⁷ | **1060×** |

SPE_3h_131 shows the most dramatic improvement (1000×), suggesting its RT data is severely limited by slow kinetics.

## Implications

1. **For analysis:** Always check if low-temperature data truly supports the model, or if the arc is incomplete. A single R(RQ) fit to data with a hidden second arc will give systematically wrong R₁.

2. **For experiments:** If RT data is ambiguous, measure at elevated temperatures first to identify the true arc structure, then extrapolate back to RT with Arrhenius.

3. **For Arrhenius plots:** Only use OK-quality points. Mixing POOR/WARN RT data with OK high-T data distorts the slope.

## Recommended Temperature Strategy
```
Step 1: Measure at 80°C first → identify true model (R(RQ) vs R(RQ)(RQ))
Step 2: Cool to 60°C, 40°C, RT → track arc evolution
Step 3: If RT arc is incomplete, note "RT σ estimated from R(RQ) fit; 
        true value may differ if second arc exists"
```
