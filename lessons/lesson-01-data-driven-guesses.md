# Lesson 1: Data-Driven Initial Guesses

## Problem
Hardcoded initial guesses (e.g., R1≈500 Ω, R2≈3000 Ω) work for one sample but fail catastrophically for others. In our batch, impedance spans **0.7 Ω to 228 kΩ** — 5 orders of magnitude. A guess scaled to GPE_h3_131 is absurd for SPE_3h_131.

## Evidence
```
Sample          z_span      Hardcoded R1=500 result
GPE_h3_131      ~4 kΩ       OK (same order)
SPE_3h_131      ~228 kΩ     FAILED — guess 2× too small
GPE_h3_101      ~0.04 Ω     FAILED — guess 10⁴× too large
```

## Solution
Scale every guess to the actual data:

```python
import numpy as np

# After cleaning (capacitive points only)
zc = float(Z.real[0])           # first capacitive Re(Z)
z_span = float(np.abs(Z).max())  # max |Z| in cleaned data

# R(RQ)(RQ) guesses
mid = len(freq) // 2
r1_guess = max(z_span * 0.1, float(Z.real[mid] - zc))
r2_guess = max(z_span * 0.3, float(Z.real[-1] - zc - r1_guess))

guess = [zc * 0.7, r1_guess, 1e-5, 0.7, r2_guess, 3e-4, 0.5]

# Bounds also scale
bounds = (
    [0, z_span * 0.001, 1e-12, 0.3, z_span * 0.001, 1e-10, 0.2],
    [z_span * 0.5, z_span * 3, 1e-1, 1.0, z_span * 5, 1e-1, 0.9]
)
```

## Rule of Thumb
| Parameter | Guess formula | Rationale |
|-----------|--------------|-----------|
| R0 | zc × 0.7 | Contact + residual tail |
| R1 | max(0.1·z_span, Z_real[mid]−zc) | Bulk arc diameter |
| R2 | max(0.3·z_span, Z_real[−1]−zc−R1) | Interface/tail contribution |
| Q1, Q2 | 1e-5, 3e-4 | Typical CPE magnitudes |
| α1, α2 | 0.7, 0.5 | Moderately depressed |

## Verification
After switching to z_span-scaled guesses, the batch failure rate dropped from ~30% (hardcoded) to ~8% (only GPE_h3_101 cable-dominated data truly could not fit).
