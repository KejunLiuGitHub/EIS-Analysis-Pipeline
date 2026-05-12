import numpy as np

A_CM2 = np.pi * 0.25  # electrode area, d=1cm


def Ceff(Q, a, R):
    """Effective capacitance from CPE parameters."""
    if Q > 0 and R > 0 and a > 0:
        return float(Q ** (1 / a) * R ** ((1 - a) / a))
    return 0.0


def compute_sigma(Rb, L_cm, A_cm2=A_CM2):
    """Ionic conductivity from bulk resistance."""
    if Rb > 0:
        return L_cm / (Rb * A_cm2)
    return 0.0
