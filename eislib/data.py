import numpy as np
from galvani import BioLogic
from .fit import fit_model, MODELS_DEF
from .derive import Ceff, A_CM2, compute_sigma
from .quality import assign_quality


def process_mpr(filepath, L_um, sample_name, A_cm2=None, preferred_model=None):
    """Read .mpr, clean data, fit 4 models, return structured result.

    If preferred_model is given (e.g. "R(RQ)(RQ)"), only that model is fitted
    for speed; if it fails, falls back to full 4-model pool.
    """
    L_cm_val = L_um * 1e-4
    A_cm2 = A_cm2 if A_cm2 is not None else A_CM2
    mpr = BioLogic.MPRfile(filepath)
    d = mpr.data
    freq_all = d['freq/Hz'].astype(np.float64)
    z_re_all = d['Re(Z)/Ohm'].astype(np.float64)
    z_im_raw = d['-Im(Z)/Ohm'].astype(np.float64)
    Z_all = z_re_all + 1j * (-z_im_raw)
    thd_e = d['THD Ewe/%'].astype(np.float64)
    thd_i = d['THD I/%'].astype(np.float64)
    n_pts = len(freq_all)

    raw = {
        "freq": freq_all.tolist(), "z_re": z_re_all.tolist(),
        "z_im": Z_all.imag.tolist(), "z_mag": np.abs(Z_all).tolist(),
        "phase": np.angle(Z_all, deg=True).tolist(),
        "thd_e": thd_e.tolist(), "thd_i": thd_i.tolist(), "n_pts": n_pts
    }

    warnings_list = []
    n_thd = int(np.sum(thd_i > 5))
    if n_thd > n_pts * 0.2:
        warnings_list.append(f"High THD: {n_thd}/{n_pts} pts THD I>5%")

    cap = Z_all.imag <= 0
    freq = freq_all[cap]
    Z = Z_all[cap]
    n_rem = int((~cap).sum())
    if n_rem > n_pts * 0.5:
        warnings_list.append(f"Excessive inductive artifact: {n_rem}/{n_pts} pts removed")
    if len(freq) < 10:
        warnings_list.append(f"Too few capacitive pts ({len(freq)}), fitting unreliable")

    cross_idx = np.argmin(np.abs(Z_all.imag))
    z_cross = float(Z_all.real[cross_idx])
    f_cross = float(freq_all[cross_idx])
    z_range = float(np.max(np.abs(Z)) - np.min(np.abs(Z))) if len(Z) > 0 else 0
    if z_range < 1.0:
        warnings_list.append(f"Z range too small ({z_range:.2f}Ω) — cable-dominated measurement")

    cleaned = {
        "freq": freq.tolist(), "z_re": Z.real.tolist(), "z_im": Z.imag.tolist(),
        "n_removed": n_rem, "n_kept": len(freq),
        "f_cross_Hz": f_cross, "z_cross_Ohm": z_cross, "z_range_Ohm": z_range
    }

    # Multi-model fitting
    models = []
    if len(freq) >= 8:
        z_span = float(np.abs(Z).max())
        zc = float(Z.real[0])
        mid = len(freq) // 2

        _ALL_MODELS = [
            ("R(RQ)", "R0-p(R1,CPE1)",
             [zc * 0.7, max(z_span * 0.2, float(Z.real[-1] - zc)), 1e-5, 0.7],
             ([0, z_span * 0.001, 1e-12, 0.3], [z_span * 0.5, z_span * 5, 1e-1, 1.0]), 4),
            ("R(RQ)(RQ)", "R0-p(R1,CPE1)-p(R2,CPE2)",
             [zc * 0.7, max(z_span * 0.1, float(Z.real[mid] - zc)), 1e-5, 0.7,
              max(z_span * 0.3, float(Z.real[-1] - zc - max(z_span * 0.1, float(Z.real[mid] - zc)))), 3e-4, 0.5],
             ([0, z_span * 0.001, 1e-12, 0.3, z_span * 0.001, 1e-10, 0.2],
              [z_span * 0.5, z_span * 3, 1e-1, 1.0, z_span * 5, 1e-1, 0.9]), 7),
            ("R(RQ)CPE", "R0-p(R1,CPE1)-CPE2",
             [zc * 0.7, max(z_span * 0.2, float(Z.real[len(freq)//3] - zc)), 1e-5, 0.7, 1e-4, 0.5],
             ([0, z_span * 0.001, 1e-12, 0.3, 1e-10, 0.2],
              [z_span * 0.5, z_span * 5, 1e-1, 1.0, 1e-1, 0.9]), 6),
            ("R(R,C)CPE", "R0-p(R1,C1)-CPE2",
             [zc * 0.7, max(z_span * 0.2, float(Z.real[len(freq)//3] - zc)), 1e-6, 1e-4, 0.5],
             ([0, z_span * 0.001, 1e-12, 1e-10, 0.2],
              [z_span * 0.5, z_span * 5, 1e-1, 1e-1, 0.9]), 5),
        ]

        if preferred_model:
            # Only fit the preferred model first for speed
            for name, circ, guess, bounds, ndf in _ALL_MODELS:
                if name == preferred_model:
                    models.append(fit_model(freq, Z, name, circ, guess, bounds, ndf))
                    break
            # If preferred model failed, fall back to full pool
            if not any(m.get("converged") for m in models):
                warnings_list.append(f"Preferred model '{preferred_model}' failed, falling back to full pool")
                for name, circ, guess, bounds, ndf in _ALL_MODELS:
                    models.append(fit_model(freq, Z, name, circ, guess, bounds, ndf))
        else:
            for name, circ, guess, bounds, ndf in _ALL_MODELS:
                models.append(fit_model(freq, Z, name, circ, guess, bounds, ndf))

    valid_models = [m for m in models if m.get("converged")]
    valid_models.sort(key=lambda x: x["chi2_N"])
    best_model = valid_models[0] if valid_models else None

    fit = None
    Rb = z_cross
    if best_model:
        p = best_model["p"]
        fit = {"circuit": best_model["circuit"], "model_name": best_model["name"],
               "params": {}, "chi2_N": best_model["chi2_N"],
               "Z_fit_re": best_model["Zf"].real.tolist(),
               "Z_fit_im": best_model["Zf"].imag.tolist(),
               "converged": True, "all_models": []}

        _extract_params(best_model, fit, p)
        _check_boundary(best_model, fit, p, warnings_list)
        if best_model["chi2_N"] > 1e6:
            warnings_list.append(f"CRITICAL: χ²/N={best_model['chi2_N']:.0e} > 10⁶ — UNUSABLE")

        w = 2 * np.pi * freq
        Rb = _compute_derived(best_model, fit, p, freq, w)

        for m in valid_models:
            mp = m["p"]
            r1 = mp[1] if m["name"] in ("R(RQ)", "R(RQ)(RQ)", "R(RQ)CPE", "R(R,C)CPE") else 1
            sigma_m = compute_sigma(r1, L_cm_val, A_cm2) if r1 > 0 else 0
            fit["all_models"].append({
                "name": m["name"], "chi2_N": m["chi2_N"],
                "R0": float(mp[0]), "R1": float(r1), "sigma": float(sigma_m),
                "is_best": m == best_model,
                "Z_fit_re": m["Zf"].real.tolist(),
                "Z_fit_im": m["Zf"].imag.tolist(),
            })
    else:
        fit = {"circuit": "failed", "error": "All models failed", "converged": False}
        warnings_list.append("All fitting failed")

    sigma = compute_sigma(Rb, L_cm_val, A_cm2)
    quality = assign_quality(warnings_list)

    return {
        "raw": raw, "cleaned": cleaned, "fit": fit,
        "sigma_S_cm": float(sigma), "Rb_used_Ohm": float(Rb),
        "L_cm": L_cm_val, "A_cm2": A_cm2, "quality": quality,
        "warnings": warnings_list, "sample_name": sample_name,
        "L_um": L_um, "filepath": filepath
    }


def _extract_params(best_model, fit, p):
    """Extract named parameters from fit result."""
    name = best_model["name"]
    if name == "R(RQ)":
        fit["params"] = {"R0": float(p[0]), "R1": float(p[1]), "Q1": float(p[2]), "alpha1": float(p[3])}
    elif name == "R(RQ)(RQ)":
        fit["params"] = {"R0": float(p[0]), "R1": float(p[1]), "R2": float(p[4]),
                         "Q1": float(p[2]), "alpha1": float(p[3]),
                         "Q2": float(p[5]), "alpha2": float(p[6])}
    elif name == "R(RQ)CPE":
        fit["params"] = {"R0": float(p[0]), "R1": float(p[1]), "Q1": float(p[2]), "alpha1": float(p[3]),
                         "Q2": float(p[4]), "alpha2": float(p[5])}
    elif name == "R(R,C)CPE":
        fit["params"] = {"R0": float(p[0]), "R1": float(p[1]), "C1": float(p[2]),
                         "Q2": float(p[3]), "alpha2": float(p[4])}


def _check_boundary(best_model, fit, p, warnings_list):
    """Check for parameters stuck at bounds."""
    if not best_model.get("boundary_hits"):
        return
    param_names = {
        "R(RQ)": ["R0", "R1", "Q1", "alpha1"],
        "R(RQ)(RQ)": ["R0", "R1", "Q1", "alpha1", "R2", "Q2", "alpha2"],
        "R(RQ)CPE": ["R0", "R1", "Q1", "alpha1", "Q2", "alpha2"],
        "R(R,C)CPE": ["R0", "R1", "C1", "Q2", "alpha2"],
    }.get(best_model["name"], [f"p{i}" for i in range(len(p))])
    hit_names = [param_names[i] for i in best_model["boundary_hits"] if i < len(param_names)]
    if hit_names:
        warnings_list.append(f"Parameters at boundary: {', '.join(hit_names)}")


def _compute_derived(best_model, fit, p, freq, w):
    """Compute derived quantities (Ceff, fc, arc decomposition)."""
    name = best_model["name"]
    if name == "R(RQ)(RQ)":
        C1 = Ceff(p[2], p[3], p[1]); fc1 = 1 / (2 * np.pi * p[1] * C1) if C1 > 0 else 0
        C2 = Ceff(p[5], p[6], p[4]); fc2 = 1 / (2 * np.pi * p[4] * C2) if C2 > 0 else 0
        fit["derived"] = {"C_eff1_F": C1, "fc1_Hz": fc1, "C_eff2_F": C2, "fc2_Hz": fc2,
                          "R_DC_Ohm": float(p[0] + p[1] + p[4])}
        Za1 = 1 / (1 / p[1] + p[2] * (1j * w) ** p[3])
        Za2 = 1 / (1 / p[4] + p[5] * (1j * w) ** p[6])
        fit["Z_arc1"] = p[0] + Za1
        fit["Z_arc2"] = p[0] + p[1] + Za2
        return float(p[1])
    elif name == "R(RQ)":
        C1 = Ceff(p[2], p[3], p[1]); fc1 = 1 / (2 * np.pi * p[1] * C1) if C1 > 0 else 0
        fit["derived"] = {"C_eff1_F": C1, "fc1_Hz": fc1, "R_DC_Ohm": float(p[0] + p[1])}
        fit["Z_arc1"] = p[0] + 1 / (1 / p[1] + p[2] * (1j * w) ** p[3])
        return float(p[1])
    elif name == "R(RQ)CPE":
        C1 = Ceff(p[2], p[3], p[1]); fc1 = 1 / (2 * np.pi * p[1] * C1) if C1 > 0 else 0
        fit["derived"] = {"C_eff1_F": C1, "fc1_Hz": fc1, "R_DC_Ohm": float(p[0] + p[1])}
        fit["Z_arc1"] = p[0] + 1 / (1 / p[1] + p[2] * (1j * w) ** p[3])
        return float(p[1])
    elif name == "R(R,C)CPE":
        fc1 = 1 / (2 * np.pi * p[1] * p[2]) if p[2] > 0 else 0
        fit["derived"] = {"C1_F": float(p[2]), "fc1_Hz": fc1, "R_DC_Ohm": float(p[0] + p[1])}
        fit["Z_arc1"] = p[0] + 1 / (1 / p[1] + p[2] * (1j * 2 * np.pi * freq) ** 1)
        return float(p[1])
    return 0
