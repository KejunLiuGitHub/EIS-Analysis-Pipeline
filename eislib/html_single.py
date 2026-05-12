import os

CSS = """
:root { --bg:#fafafa; --text:#2d2d2d; --accent:#2166ac; --red:#d6604d; --green:#4dac26; --purple:#9467bd; --gray:#f0f0f0; --border:#e0e0e0; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Segoe UI',system-ui,sans-serif; line-height:1.7; color:var(--text); background:var(--bg); max-width:1100px; margin:0 auto; padding:2rem 1.5rem; }
h1 { font-size:1.75rem; border-bottom:3px solid var(--accent); padding-bottom:0.5rem; margin:2rem 0 0.5rem; }
h2 { font-size:1.35rem; margin:2.5rem 0 0.75rem; color:var(--accent); border-bottom:1px solid var(--border); padding-bottom:0.25rem; }
h3 { font-size:1.1rem; margin:1.5rem 0 0.5rem; color:#444; }
p,li { margin-bottom:0.5rem; }
.abstract { background:#f0f5fc; border-left:4px solid var(--accent); padding:1rem 1.2rem; margin:1.5rem 0; font-size:0.92rem; }
figure { margin:1.5rem 0; }
figcaption { font-size:0.88rem; color:#666; margin-top:0.3rem; }
table { width:100%; border-collapse:collapse; margin:1rem 0; font-size:0.92rem; }
th,td { padding:0.5rem 0.8rem; text-align:left; border-bottom:1px solid var(--border); }
th { background:var(--gray); font-weight:600; }
tr:hover { background:#fafafa; }
.note { background:#fff8e1; border-left:4px solid #ffa000; padding:0.8rem 1rem; margin:1rem 0; font-size:0.9rem; }
.warn { background:#ffe8e8; border-left:4px solid #d6604d; padding:0.8rem 1rem; margin:1rem 0; font-size:0.9rem; }
.info { background:#e8f5e9; border-left:4px solid var(--green); padding:0.8rem 1rem; margin:1rem 0; font-size:0.9rem; }
.okbox { background:#e8f5e9; border-left:4px solid var(--green); padding:0.8rem 1rem; margin:1rem 0; font-size:0.9rem; }
.quality-ok { color: var(--green); font-weight:bold; }
.quality-warn { color: #ffa000; font-weight:bold; }
.quality-poor { color: var(--red); font-weight:bold; }
.quality-dnu { color: var(--red); font-weight:bold; background:#ffe8e8; padding:0.2rem 0.4rem; border-radius:3px; }
.quality-limited { color: #e67e22; font-weight:bold; }
.dnubox { background:#ffe8e8; border:2px solid var(--red); border-left:8px solid var(--red); padding:1rem 1.2rem; margin:1.5rem 0; font-size:1.0rem; }
.limitedbox { background:#fef5e7; border-left:4px solid #e67e22; padding:0.8rem 1rem; margin:1rem 0; font-size:0.9rem; }
.author-box { background:var(--gray); border-radius:6px; padding:0.8rem 1.2rem; margin:1rem 0; font-size:0.9rem; }
.circuit-eq { background:#f8f8f8; padding:0.8rem 1rem; border-radius:4px; margin:0.8rem 0; font-family:'Courier New',monospace; font-size:0.95rem; }
.collapsible { background:var(--gray); color:var(--text); cursor:pointer; padding:0.6rem 1rem; width:100%; border:none; text-align:left; outline:none; font-size:1rem; font-weight:600; border-radius:4px; margin:0.5rem 0; }
.collapsible:hover { background:#e0e0e0; }
.collapsible-content { padding:0 1rem; max-height:0; overflow:hidden; transition:max-height 0.2s ease-out; }
.toc { background:var(--gray); padding:1rem 1.5rem; border-radius:4px; margin:1.5rem 0; }
.toc ol { margin-left:1.5rem; } .toc a { color:var(--accent); text-decoration:none; } .toc a:hover { text-decoration:underline; }
.highlight-box { border:2px solid var(--green); border-radius:6px; padding:1rem 1.2rem; margin:1.5rem 0; background:#f6faf3; }
"""


def _param_rows(fit):
    rows = ""
    if not fit or not fit.get("converged"):
        return rows
    p = fit.get("params", {}); der = fit.get("derived", {})
    for key, val in p.items():
        if key.startswith("R"): rows += f"<tr><td>{key}</td><td>{val:.2f}</td><td>Ω</td></tr>\n"
        elif key.startswith("Q"): rows += f"<tr><td>{key}</td><td>{val:.3e}</td><td>S·s<sup>α</sup></td></tr>\n"
        elif key.startswith("C"): rows += f"<tr><td>{key}</td><td>{val*1e6:.3f}</td><td>µF</td></tr>\n"
        elif key.startswith("alpha"): rows += f"<tr><td>{key}</td><td>{val:.3f}</td><td>—</td></tr>\n"
    for key, val in der.items():
        if "C_eff" in key or "C1_F" in key: rows += f"<tr><td>{key}</td><td>{val*1e6:.2f}</td><td>µF</td></tr>\n"
        elif "fc" in key: rows += f"<tr><td>{key}</td><td>{val:.2f}</td><td>Hz</td></tr>\n"
        elif "R_DC" in key: rows += f"<tr><td>{key}</td><td>{val:.1f}</td><td>Ω</td></tr>\n"
    return rows


def _model_rows(fit):
    rows = ""
    if not fit or "all_models" not in fit: return rows
    for m in fit["all_models"]:
        bg = 'background:#e8f5e9' if m.get("is_best") else ''
        rows += f"<tr style='{bg}'><td>{m['name']}</td><td>{m['chi2_N']:.1f}</td><td>{m['R0']:.1f}</td><td>{m['R1']:.1f}</td><td>{m['sigma']:.3e}</td></tr>\n"
    return rows


def _warnings_html(data):
    if not data["warnings"]:
        return '<div class="okbox"><strong>✅ No warnings — data quality OK</strong></div>'
    is_critical = any("UNUSABLE" in w or "CRITICAL" in w for w in data["warnings"])
    box_class = "dnubox" if is_critical else "warn"
    icon = "🚫" if is_critical else "⚠️"
    header = 'DO NOT USE — This data is unsuitable for quantitative extraction' if is_critical else 'Warnings:'
    return f'<div class="{box_class}"><strong>{icon} {header}</strong><ul>' + "".join(f"<li>{w}</li>" for w in data["warnings"]) + "</ul></div>"


def build_html(data, nyq_div, bode_div, harm_div, model_cmp_div=""):
    fit = data["fit"]
    q = data["quality"]
    qclass = {"OK": "quality-ok", "WARN": "quality-warn", "POOR": "quality-poor", "DO NOT USE": "quality-dnu", "LIMITED": "quality-limited"}.get(q, "")
    qicon = {"OK": "✅", "WARN": "⚠️", "POOR": "❌", "DO NOT USE": "🚫", "LIMITED": "🔶"}.get(q, "")
    sigma_str = f'{data["sigma_S_cm"]:.3e}'
    chi_str = f'{fit["chi2_N"]:.1f}' if fit and fit.get("converged") else "FAILED"
    circuit_str = fit.get("model_name", "—") if fit else "—"
    full_circuit = fit.get("circuit", "—") if fit else "—"

    param_rows = _param_rows(fit)
    model_rows = _model_rows(fit)
    warnings_html = _warnings_html(data)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EIS Analysis — {data["sample_name"]}</title>
<script>
MathJax = {{
  tex: {{
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']],
    macros: {{
      Re: '\\operatorname{{Re}}', Im: '\\operatorname{{Im}}',
      CPE: '\\mathrm{{CPE}}',
      Ohm: '\\,\\Omega', kHz: '\\,\\mathrm{{kHz}}',
      MHz: '\\,\\mathrm{{MHz}}', Hz: '\\,\\mathrm{{Hz}}',
      um: '\\,\\mu\\mathrm{{m}}', uF: '\\,\\mu\\mathrm{{F}}',
      Spercm: '\\,\\mathrm{{S\\,cm^{{-1}}}}',
    }}
  }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<h1>Electrochemical Impedance Spectroscopy Analysis</h1>
<p style="font-size:1.05rem;"><strong>Sample:</strong> {data["sample_name"]} &ensp;|&ensp; <strong>Thickness:</strong> {data["L_um"]} µm &ensp;|&ensp; <strong>Quality:</strong> <span class="{qclass}">{qicon} {q}</span></p>
<div class="author-box">
<strong>File:</strong> {os.path.basename(data["filepath"])}<br>
<strong>Analysis date:</strong> 2026-05-12 &ensp;|&ensp; <strong>Instrument:</strong> BioLogic Potentiostat (EC-Lab v11.62)<br>
<strong>Engine:</strong> eislib v1 (4-model pool)
</div>
<div class="abstract">
<strong>Abstract.</strong> EIS analysis of {data["sample_name"]} in symmetric SS | electrolyte | SS configuration, 7 MHz → 1 Hz. 
Data cleaning removed {data["cleaned"]["n_removed"]} inductive artifact point(s). 
Best-fitting model: <strong>{circuit_str}</strong> ({full_circuit}) with χ²/(N−p) = {chi_str}. 
Ionic conductivity σ = {sigma_str} S·cm⁻¹. 
Quality rating: <span class="{qclass}">{q}</span>.
</div>
{warnings_html}
<h2>1. Experimental Parameters</h2>
<table>
<tr><th>Parameter</th><th>Value</th></tr>
<tr><td>Sample</td><td>{data["sample_name"]}</td></tr>
<tr><td>Thickness <i>L</i></td><td>{data["L_um"]} µm = {data["L_cm"]:.4f} cm</td></tr>
<tr><td>Electrode area <i>A</i></td><td>{data["A_cm2"]:.4f} cm² (d = 1.0 cm)</td></tr>
<tr><td>AC amplitude</td><td>100 mV</td></tr>
<tr><td>Frequency range</td><td>7 MHz → 1 Hz</td></tr>
<tr><td>Data points</td><td>{data["raw"]["n_pts"]} total / {data["cleaned"]["n_kept"]} capacitive</td></tr>
<tr><td>Zero-crossing</td><td>Re(Z) = {data["cleaned"]["z_cross_Ohm"]:.2f} Ω at f = {data["cleaned"]["f_cross_Hz"]/1e3:.1f} kHz</td></tr>
</table>
<div class="note"><strong>Note:</strong> The zero-crossing Re(Z) = {data["cleaned"]["z_cross_Ohm"]:.2f} Ω is <em>R₀ + residual bulk tail</em>, <strong>not</strong> the true bulk resistance <i>R</i><sub>b</sub>. Always trust the fitted R₁ over the intercept.</div>
<h2>2. Nyquist & Fitting</h2>
<figure>{nyq_div}<figcaption><strong>Figure 1.</strong> Left: raw data with inductive artifacts (red ×). Right: cleaned data with best-fit equivalent circuit.</figcaption></figure>
<h2>3. Model Comparison</h2>
<figure>{model_cmp_div}<figcaption><strong>Figure 2.</strong> All four candidate models overlaid on cleaned data. Solid thick line = best fit (lowest χ²/(N−p)); dashed = alternatives.</figcaption></figure>
<h2>4. Bode & Residuals</h2>
<figure>{bode_div}<figcaption><strong>Figure 3.</strong> Bode magnitude (top), phase (middle), and relative residuals (bottom).</figcaption></figure>
<h2>5. Harmonic Distortion</h2>
<figure>{harm_div}<figcaption><strong>Figure 4.</strong> THD analysis from .mpr file. Orange dashed line marks 5% nonlinearity threshold.</figcaption></figure>
<h2>5. Fitted Parameters</h2>
<table>
<tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
<tr><td>Model</td><td>{circuit_str}</td><td>—</td></tr>
<tr><td>Circuit</td><td>{full_circuit}</td><td>—</td></tr>
<tr><td>χ²/(N−p)</td><td>{chi_str}</td><td>—</td></tr>
{param_rows}
<tr><td><i>σ</i> (ionic conductivity)</td><td>{sigma_str}</td><td>S·cm⁻¹</td></tr>
</table>
<h2>6. Model Comparison</h2>
<table>
<tr><th>Model</th><th>χ²/(N−p)</th><th>R₀/Ω</th><th>R₁/Ω</th><th>σ/S·cm⁻¹</th></tr>
{model_rows}
</table>
<h2>7. Model Selection Rationale</h2>
<p>Four candidate models were tested for this dataset:</p>
<ul>
<li><strong>R(RQ)</strong> — single depressed semicircle ($R_0 + (R_1 \\parallel \\mathrm{{CPE}}_1)$)</li>
<li><strong>R(RQ)(RQ)</strong> — two depressed semicircles in series</li>
<li><strong>R(RQ)CPE</strong> — blocking electrode with depressed semicircle</li>
<li><strong>R(R,C)CPE</strong> — blocking electrode with <em>ideal</em> capacitor semicircle (v2)</li>
</ul>
<p>The model with the lowest χ²/(N−p) was selected. If χ² > 10⁶, all models are considered unusable regardless of ranking.</p>
<p style="margin-top:3rem;font-size:0.8rem;color:#aaa">Generated 2026-05-12 · eislib v1 · 4-model pool</p>
</body></html>'''
