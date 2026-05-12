# Lesson 9: Ideal Capacitor vs CPE — When to Use R(R,C)CPE

## Problem
We discovered that some samples have near-ideal semicircles (α ≈ 0.9–1.0) while others have strongly depressed arcs (α ≈ 0.7). Forcing a CPE (α free) on a near-ideal arc adds an unnecessary degree of freedom and can destabilize the fit. Forcing an ideal capacitor (C) on a depressed arc creates systematic bias.

## Evidence: GPE_h4_201 vs SPE_3h_131

### GPE_h4_201 RT — Near-ideal arc
| Model | χ²/N | R₁ | Arc α | Verdict |
|-------|------|-----|-------|---------|
| **R(R,C)CPE** | **4,741** | 16,856 Ω | **1.000** (fixed) | ✅ Best |
| R(RQ) | 146,391 | 329,227 Ω | 0.899 | Forced tail into arc |
| R(RQ)CPE | 3.56×10⁷ | 13,169 Ω | 0.705 | Overparameterized |
| R(RQ)(RQ) | 7.08×10⁷ | 23,192 Ω | 0.737 | Second arc is fake |

The Nyquist arc looks like a **quarter-circle**. The ideal capacitor (C₁) captures it perfectly, and the CPE_tail (α₂ = 0.836) handles the blocking electrode.

### SPE_3h_131 80°C — Depressed arc
| Model | χ²/N | R₁ | Arc α | Verdict |
|-------|------|-----|-------|---------|
| R(RQ)CPE | **6,825** | 7,997 Ω | **0.705** | ✅ Best |
| R(R,C)CPE | 9,036 | 2,807 Ω | 1.000 (fixed) | Systematic bias from ideal constraint |
| R(RQ) | 130,166 | 192,030 Ω | 0.705 | Tail forced into arc |

The Nyquist arc is **visibly flattened**. Forcing α = 1.0 makes the fit systematically miss the data, inflating χ² by 30%.

## Visual Diagnostic

```
Near-ideal arc (use R(R,C)CPE):     Depressed arc (use R(RQ)CPE):
        ╭──╮                              ╭────╮
       ╱    ╲  ← circular                 ╱      ╲  ← flattened
      ╱      ╲                           ╱        ╲
     ╱        ╲‾‾‾‾                     ╱          ╲‾‾‾‾
    R0        CPE_tail                 R0          CPE_tail
    
    α_arc ≈ 0.9–1.0                    α_arc ≈ 0.6–0.8
```

## Decision Rule

```python
def choose_blocking_model(freq, Z):
    """Auto-select between R(R,C)CPE and R(RQ)CPE."""
    
    # Step 1: Try both
    models = []
    # ... fit R(R,C)CPE and R(RQ)CPE ...
    
    chi2_RC = models['R(R,C)CPE']['chi2_N']
    chi2_RQ = models['R(RQ)CPE']['chi2_N']
    
    # Step 2: If ideal-cap model is >10× worse, arc is depressed
    if chi2_RC > 10 * chi2_RQ:
        return "R(RQ)CPE", "Arc is depressed (α << 1); CPE required"
    
    # Step 3: If χ² comparable or better, arc is near-ideal
    elif chi2_RC < 2 * chi2_RQ:
        return "R(R,C)CPE", "Arc is near-ideal (α ≈ 1); ideal capacitor sufficient"
    
    # Step 4: Marginal — inspect visually
    else:
        return "R(RQ)CPE", "Marginal — default to CPE for safety"
```

## Physical Interpretation

| α value | Physical Meaning | Typical System |
|---------|-----------------|----------------|
| 0.95–1.00 | Near-ideal capacitor | Ordered polymer, low disorder |
| 0.70–0.90 | Moderately depressed | Amorphous polymer, salt distribution |
| 0.50–0.70 | Strongly depressed | Heterogeneous matrix, grain boundaries |
| 0.30–0.50 | Very broad dispersion | Composite, porous electrode |

**GPE_h4_201** has a relatively ordered polymer matrix (h4 = higher crosslinker?), giving near-ideal bulk capacitance. **SPE_3h_131** has more disorder (3h curing?), giving depressed arcs.

## Code: R(R,C)CPE Fitting

```python
from impedance.models.circuits import CustomCircuit

# R0 + (R1 || C1) + CPE2
circuit = 'R0-p(R1,C1)-CPE2'

# Initial guess: R0, R1, C1, Q2, alpha2
guess = [zc * 0.7, z_span * 0.2, 1e-6, 1e-4, 0.5]

# Bounds
bounds = (
    [0, z_span * 0.001, 1e-12, 1e-10, 0.2],
    [z_span * 0.5, z_span * 5, 1e-1, 1e-1, 0.9]
)

c = CustomCircuit(initial_guess=guess, circuit=circuit)
c.fit(freq, Z, bounds=bounds)
p = c.parameters_

# p[0] = R0
# p[1] = R1
# p[2] = C1 (ideal capacitor, F)
# p[3] = Q2 (CPE tail, S·s^α)
# p[4] = alpha2

fc1 = 1 / (2 * np.pi * p[1] * p[2])  # characteristic frequency
```

## Warning Signs

| Symptom | Cause | Fix |
|---------|-------|-----|
| R(R,C)CPE χ² >> R(RQ)CPE χ² | Arc is depressed, α < 1 | Use R(RQ)CPE |
| R(RQ)CPE α ≈ 0.95–1.0 | Arc is near-ideal | Try R(R,C)CPE for cleaner params |
| C1 comes out negative | Bad initial guess or wrong model | Switch to CPE |
| Both models give similar χ² | Arc is marginally depressed | Default to R(RQ)CPE (safer) |

## Summary

- **Start with R(RQ)CPE** as the default blocking-electrode model
- **Try R(R,C)CPE** if the arc looks circular or if R(RQ)CPE's α > 0.9
- **Let χ² decide**, but apply the 10× rule: if ideal-cap model is >10× worse, the arc is genuinely depressed
- **Never force R(R,C)CPE** when data clearly shows a flattened arc — this creates systematic bias and wrong R₁
