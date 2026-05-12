"""EIS analysis library for polymer electrolyte impedance spectroscopy."""

from .derive import Ceff, A_CM2, compute_sigma
from .fit import fit_model, MODELS_DEF
from .data import process_mpr
from .quality import assign_quality
from .plot import (
    make_nyquist_figure, make_bode_figure, make_harmonics_figure,
    make_model_comparison_figure,
    make_nyquist_comparison, make_bode_comparison, make_thd_comparison,
    make_arrhenius_figure, make_kk_figure,
)
from .kk import run_kk, kk_verdict
from .html_single import build_html, CSS

__all__ = [
    "Ceff", "A_CM2", "compute_sigma",
    "fit_model", "MODELS_DEF",
    "process_mpr", "assign_quality",
    "make_nyquist_figure", "make_bode_figure", "make_harmonics_figure",
    "make_model_comparison_figure",
    "make_nyquist_comparison", "make_bode_comparison", "make_thd_comparison",
    "make_arrhenius_figure", "make_kk_figure",
    "run_kk", "kk_verdict",
    "build_html", "CSS",
]
