import numpy as np
import impedance.validation as val_module
from impedance.models.circuits.elements import circuit_elements

# Monkey-patch: add np to circuit_elements namespace for eval()
ce_dict = dict(circuit_elements)
ce_dict['np'] = np
val_module.circuit_elements = ce_dict
from impedance.validation import linKK


def run_kk(data):
    """Run lin-KK on cleaned capacitive data."""
    freq = np.array(data["cleaned"]["freq"])
    Z_re = np.array(data["cleaned"]["z_re"])
    Z_im = np.array(data["cleaned"]["z_im"])
    Z = Z_re + 1j * Z_im
    M, mu, Z_fit, res_re, res_im = linKK(freq, Z, c=0.85, max_M=50, fit_type='real')
    Z_mag = np.abs(Z)
    rel_re = 100 * res_re / Z_mag
    rel_im = 100 * res_im / Z_mag
    rmse_rel = np.sqrt(np.mean(rel_re**2 + rel_im**2))
    max_rel = max(np.max(np.abs(rel_re)), np.max(np.abs(rel_im)))
    verdict = 'PASS' if rmse_rel < 1.0 and max_rel < 5.0 else ('MARGINAL' if rmse_rel < 5.0 and max_rel < 15.0 else 'FAIL')
    return {
        "M": M, "mu": mu, "freq": freq, "Z": Z, "Z_fit": Z_fit,
        "res_re": res_re, "res_im": res_im, "rel_re": rel_re, "rel_im": rel_im,
        "rmse_rel": rmse_rel, "max_rel": max_rel, "verdict": verdict,
    }


def kk_verdict(kk):
    return kk["verdict"]
