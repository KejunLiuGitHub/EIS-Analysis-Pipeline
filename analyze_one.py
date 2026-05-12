#!/usr/bin/env python3
"""Per-sample EIS analysis CLI. Usage: python3 analyze_one.py <mpr> --out <html> --thickness <um>"""

import argparse, os
from eislib import process_mpr, make_nyquist_figure, make_bode_figure, make_harmonics_figure, make_model_comparison_figure, build_html


def main():
    parser = argparse.ArgumentParser(description="Per-sample EIS analysis")
    parser.add_argument("mpr", help="Path to .mpr file")
    parser.add_argument("--out", required=True, help="Output HTML path")
    parser.add_argument("--name", default=None, help="Sample name")
    parser.add_argument("--thickness", type=int, default=100, help="Film thickness in µm")
    args = parser.parse_args()

    name = args.name or os.path.splitext(os.path.basename(args.mpr))[0]
    print(f"Processing {name} ...")
    data = process_mpr(args.mpr, args.thickness, name)
    fit = data['fit']
    print(f"  Quality: {data['quality']}", end="")
    if fit and fit.get("converged"):
        print(f", Best: {fit['model_name']}, χ²/N={fit['chi2_N']:.1f}")
    else:
        print(", Fit: FAILED")
    for w in data["warnings"]:
        print(f"  ⚠ {w}")

    nyq = make_nyquist_figure(data).to_html(full_html=False, include_plotlyjs=False)
    bode = make_bode_figure(data).to_html(full_html=False, include_plotlyjs=False)
    harm = make_harmonics_figure(data).to_html(full_html=False, include_plotlyjs=False)
    model_cmp = make_model_comparison_figure(data).to_html(full_html=False, include_plotlyjs=False)
    html = build_html(data, nyq, bode, harm, model_cmp)

    with open(args.out, 'w') as f:
        f.write(html)
    print(f"  Written: {args.out} ({os.path.getsize(args.out):,} bytes)")


if __name__ == "__main__":
    main()
