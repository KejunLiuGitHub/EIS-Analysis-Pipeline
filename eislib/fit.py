from impedance.models.circuits import CustomCircuit
import numpy as np


def fit_model(freq, Z, name, circuit_str, guess, bounds, ndf):
    """Fit a single equivalent circuit model and return structured result."""
    try:
        c = CustomCircuit(initial_guess=guess, circuit=circuit_str)
        c.fit(freq, Z, bounds=bounds)
        p = c.parameters_
        Zf = c.predict(freq)
        chi2 = float(np.sum((Z.real - Zf.real) ** 2 + (Z.imag - Zf.imag) ** 2) / (2 * len(freq) - ndf))

        boundary_hits = []
        for i, (val, lo, hi) in enumerate(zip(p, bounds[0], bounds[1])):
            if abs(val - lo) < 0.01 * (hi - lo) or abs(val - hi) < 0.01 * (hi - lo):
                boundary_hits.append(i)

        return {
            "name": name, "circuit": circuit_str, "p": p, "Zf": Zf,
            "chi2_N": chi2, "converged": True, "boundary_hits": boundary_hits,
            "ndf": ndf
        }
    except Exception as e:
        return {"name": name, "circuit": circuit_str, "error": str(e)[:200],
                "converged": False, "boundary_hits": []}


# Model definitions: (display_name, circuit_string, ndf)
MODELS_DEF = [
    ("R(RQ)",     "R0-p(R1,CPE1)",             4),
    ("R(RQ)(RQ)", "R0-p(R1,CPE1)-p(R2,CPE2)",  7),
    ("R(RQ)CPE",  "R0-p(R1,CPE1)-CPE2",        6),
    ("R(R,C)CPE", "R0-p(R1,C1)-CPE2",          5),
]
