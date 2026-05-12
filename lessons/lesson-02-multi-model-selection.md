# Lesson 2: Multi-Model Selection

## Problem
No single equivalent circuit fits all samples. R(RQ)(RQ) is great for GPE_h3_131 (two clear arcs) but gives χ² > 10⁷ for GPE_h4_201_RT (one arc + steep tail). Forcing the wrong model produces meaningless parameters.

## Evidence from Batch
| Sample | Best Model | χ²/(N−p) | Second-best | χ²/(N−p) |
|--------|-----------|----------|-------------|----------|
| GPE_h3_131 @ 40°C | R(RQ)(RQ) | **0.3** | R(RQ) | 0.4 |
| GPE_h4_201 @ RT | **R(R,C)CPE** | **4,741** | R(RQ) | 1.5×10⁵ |
| GPE_h4_201 @ 60°C | **R(R,C)CPE** | **5,521** | R(RQ)(RQ) | 7,944 |
| SPE_3h_131 @ 80°C | R(RQ)CPE | **6.8×10³** | R(RQ)(RQ) | 2.0×10⁷ |
| GPE_h4_201 @ 80°C | R(RQ)(RQ) | **457** | R(RQ) | 2606 |

> GPE_h4_201 RT was originally fit with R(RQ), giving χ²=1.5×10⁵ and σ=3.9×10⁻⁸. After adding R(R,C)CPE to the candidate pool, the best fit became χ²=4,741 with σ=7.6×10⁻⁷ — a **20× correction**.

## Solution
Always try **four** candidates and pick by χ²/(N−p):

```python
from impedance.models.circuits import CustomCircuit

def fit_r_rq(freq, Z, z_span): ...
def fit_r_rq_rq(freq, Z, z_span): ...
def fit_r_rq_cpe(freq, Z, z_span): ...
def fit_r_r_c_cpe(freq, Z, z_span): ...  # NEW: ideal capacitor + CPE tail

models = []
for fit_fn, name in [(fit_r_rq, "R(RQ)"), 
                      (fit_r_rq_rq, "R(RQ)(RQ)"), 
                      (fit_r_rq_cpe, "R(RQ)CPE"),
                      (fit_r_r_c_cpe, "R(R,C)CPE")]:
    try:
        r = fit_fn(freq, Z, z_span)
        if r["chi2_N"] < 1e12:  # filter absurd divergences
            models.append(r)
    except Exception:
        pass

models.sort(key=lambda x: x["chi2_N"])
best = models[0] if models else None
```

## Model Selection Guide
| Data Shape | Best Model | Visual Cue | Example |
|-----------|-----------|-----------|---------|
| Two well-resolved arcs | R(RQ)(RQ) | Two semicircles in Nyquist | GPE_h3_131, GPE_h4_201 @ 80°C |
| Near-ideal arc + steep tail | **R(R,C)CPE** | Arc looks like a circle, tail shoots up | GPE_h4_201 RT/60°C |
| Depressed arc + tail | R(RQ)CPE | Arc is flattened, tail follows | SPE_3h_131 60/80°C |
| One arc only | R(RQ) | Single depressed semicircle | GPE_h3_101_2 |
| Mostly tail, arc unresolved | R(RQ) or none | High impedance, shallow arc | GPE_h4_201 @ 40°C |
| All models χ² > 10⁶ | **None — data unusable** | No clear structure | SPE_3h_131 RT/40°C |

## The R(R,C)CPE Model (New)

For samples with a **near-ideal semicircle** (α ≈ 0.9–1.0) and a steep blocking tail, forcing a CPE on the arc is overkill. Use an ideal capacitor instead:

```python
circuit = 'R0-p(R1,C1)-CPE2'
guess = [zc*0.7, z_span*0.2, 1e-6, 1e-4, 0.5]
bounds = ([0, z_span*0.001, 1e-12, 1e-10, 0.2],
          [z_span*0.5, z_span*5, 1e-1, 1e-1, 0.9])
```

**When to use R(R,C)CPE vs R(RQ)CPE:**
- If the arc in Nyquist looks like a **quarter-circle or near-circle** → try R(R,C)CPE
- If the arc is **obviously flattened** (depressed) → stick with R(RQ)CPE
- Always let χ² decide, but if R(R,C)CPE's χ² is > 10× worse than R(RQ)CPE, the arc is depressed and CPE is needed

## Caveat
χ² is the primary selector, but inspect residuals. A model with slightly higher χ² but physically realistic parameters may be preferable to a lower-χ² model with negative R or α > 1.

**Red flag:** If the best model's χ² > 10⁶, **no model is correct** — the data itself is too noisy or nonlinear. Do not force a fit. Mark as "DO NOT USE" and move on.
