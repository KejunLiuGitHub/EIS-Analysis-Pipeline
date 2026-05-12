# Lesson 3: Zero-Crossing ≠ Rb

## Problem
The standard "textbook" method takes Rb from the Nyquist x-axis intercept where Im(Z)=0. This is wrong when the bulk arc is partially above the measurement bandwidth.

## Evidence
| Sample | Zero-Crossing Re(Z) | Fitted R1 | Error | σ if using crossing |
|--------|-------------------|-----------|-------|-------------------|
| GPE_h3_131 | 29.7 Ω | 653 Ω | **22×** | 1.3×10⁻⁷ (too low) |
| GPE_h3_101_C02 | 0.68 Ω | — (fit failed) | — | 1.9×10⁻² (absurd) |

For GPE_h3_131, the zero-crossing at 171.6 kHz is actually **R₀ + residual bulk tail**. The full bulk arc peaks at fc₁ = 46 Hz — far below the crossing frequency. Most of the arc is "hidden" above the bandwidth.

## Physical Explanation
```
Textbook assumption:        Reality for thin GPE:
    ───●───→ Z'                ───╭──╮──→ Z'
   Rb  ↑  CPE                 R₀  │Arc1│  Arc2
      Im=0                        (fc=46Hz)
                                 crossing here ≠ Rb
```

## Solution
**Always trust the fitted R₁ over the intercept.** In the analysis HTML, explicitly warn:

```html
<div class="note">
  <strong>Note:</strong> The zero-crossing Re(Z) = {z_cross:.2f} Ω 
  is <em>R₀ + residual bulk tail</em>, <strong>not</strong> the true 
  bulk resistance <i>R</i><sub>b</sub>. Always trust the fitted R₁.
</div>
```

## When Is the Intercept Valid?
Only when the entire bulk semicircle is visible — i.e., fc₁ is well above the lowest measured frequency (typically fc₁ > 10 Hz for a 1 Hz–7 MHz sweep). For our samples:
- GPE_h3_131: fc₁ = 46 Hz → arc partially visible, intercept **invalid**
- GPE_h3_131 @ 40°C: fc₁ = 2568 Hz → arc fully visible, intercept **still underestimates** (120 Ω vs fitted 107 Ω)

## Code Pattern
```python
# WRONG
Rb = z_cross  # zero-crossing Re(Z)
sigma = L_cm / (Rb * A_cm2)

# RIGHT
Rb = fit["params"]["R1"] if fit.get("converged") else z_cross
sigma = L_cm / (Rb * A_cm2)
```
