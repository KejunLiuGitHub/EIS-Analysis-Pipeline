import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _quality_label(data):
    q = data.get("quality", "")
    return f" [{q}]" if q else ""


# ── Single-sample figures ──

def make_nyquist_figure(data):
    raw = data["raw"]; cl = data["cleaned"]; fit = data["fit"]
    freq_all = np.array(raw["freq"]); Z_all_re = np.array(raw["z_re"]); Z_all_im = np.array(raw["z_im"])
    freq = np.array(cl["freq"]); Z_re = np.array(cl["z_re"]); Z_im = np.array(cl["z_im"])

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Raw Data with Cleaning", "Nyquist with Fit"), horizontal_spacing=0.08)

    ind_mask = Z_all_im > 0
    if ind_mask.sum() > 0:
        fig.add_trace(go.Scatter(
            x=Z_all_re[ind_mask], y=-Z_all_im[ind_mask], mode='markers',
            name=f'Inductive ({ind_mask.sum()} pts)', marker=dict(color='#d6604d', size=7, symbol='x', opacity=0.6),
            text=[f"f={f/1e6:.3f} MHz<br>Z'={Z_all_re[i]:.1f}<br>-Z''={-Z_all_im[i]:.1f}" for i,f in enumerate(freq_all[ind_mask])],
            hoverinfo='text'), row=1, col=1)

    cap_mask = Z_all_im <= 0
    fig.add_trace(go.Scatter(
        x=Z_all_re[cap_mask], y=-Z_all_im[cap_mask], mode='markers',
        name='Capacitive raw', marker=dict(color='#2166ac', size=5, opacity=0.4),
        text=[f"f={f/1e3:.2f} kHz<br>Z'={Z_all_re[i]:.1f}<br>-Z''={-Z_all_im[i]:.1f}" for i,f in enumerate(freq_all[cap_mask])],
        hoverinfo='text'), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=Z_re, y=-Z_im, mode='markers', name='Cleaned data', marker=dict(color='#2166ac', size=6, opacity=0.7),
        text=[f"f={f/1e3:.2f} kHz<br>Z'={Z_re[i]:.1f}<br>-Z''={-Z_im[i]:.1f}" for i,f in enumerate(freq)],
        hoverinfo='text'), row=1, col=2)

    if fit and fit.get("converged") and "Z_fit_re" in fit:
        Zf_re = np.array(fit["Z_fit_re"]); Zf_im = np.array(fit["Z_fit_im"])
        fig.add_trace(go.Scatter(x=Zf_re, y=-Zf_im, mode='lines', name='Fit', line=dict(color='#d6604d', width=2)), row=1, col=2)
        if "Z_arc1" in fit:
            Za1 = fit["Z_arc1"]
            fig.add_trace(go.Scatter(x=Za1.real, y=-Za1.imag, mode='lines', name='Arc 1 (bulk)', line=dict(color='#4dac26', width=1.5, dash='dash')), row=1, col=2)
        if "Z_arc2" in fit:
            Za2 = fit["Z_arc2"]
            fig.add_trace(go.Scatter(x=Za2.real, y=-Za2.imag, mode='lines', name='Arc 2 (interface)', line=dict(color='#9467bd', width=1.5, dash='dot')), row=1, col=2)

    fig.update_xaxes(title_text="Z' / Ω", row=1, col=1); fig.update_yaxes(title_text="−Z'' / Ω", row=1, col=1)
    fig.update_xaxes(title_text="Z' / Ω", row=1, col=2); fig.update_yaxes(title_text="−Z'' / Ω", row=1, col=2)
    fig.update_layout(title=f'{data["sample_name"]} — Nyquist Analysis  [{data["quality"]}]', template='plotly_white', hovermode='closest', height=550, legend=dict(orientation='h', y=-0.18), margin=dict(t=50, b=60, l=50, r=20))
    return fig


def make_bode_figure(data):
    cl = data["cleaned"]; fit = data["fit"]
    freq = np.array(cl["freq"]); Z_re = np.array(cl["z_re"]); Z_im = np.array(cl["z_im"])
    Z_mag = np.sqrt(Z_re**2 + Z_im**2); phase = -np.arctan2(Z_im, Z_re) * 180 / np.pi

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=('|Z| / Ω', '−ϕ / deg', 'Residual Δ|Z|/|Z| / %'), vertical_spacing=0.08, row_heights=[0.38, 0.32, 0.30])
    fig.add_trace(go.Scatter(x=freq, y=Z_mag, mode='markers', name='|Z| data', marker=dict(color='#2166ac', size=4, opacity=0.6), text=[f"f={f:.2f} Hz<br>|Z|={Z_mag[i]:.2f}" for i,f in enumerate(freq)], hoverinfo='text'), row=1, col=1)
    fig.add_trace(go.Scatter(x=freq, y=phase, mode='markers', name='Phase data', marker=dict(color='#2166ac', size=4, opacity=0.6), showlegend=False, text=[f"f={f:.2f} Hz<br>ϕ={phase[i]:.2f}°" for i,f in enumerate(freq)], hoverinfo='text'), row=2, col=1)

    if fit and fit.get("converged") and "Z_fit_re" in fit:
        Zf_re = np.array(fit["Z_fit_re"]); Zf_im = np.array(fit["Z_fit_im"])
        Zf_mag = np.sqrt(Zf_re**2 + Zf_im**2); phase_f = -np.arctan2(Zf_im, Zf_re) * 180 / np.pi; resid = 100 * (Z_mag - Zf_mag) / Z_mag
        fig.add_trace(go.Scatter(x=freq, y=Zf_mag, mode='lines', name='Fit', line=dict(color='#d6604d', width=1.5), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=freq, y=phase_f, mode='lines', name='Fit phase', line=dict(color='#d6604d', width=1.5), showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=freq, y=resid, mode='lines+markers', name='Residual %', marker=dict(size=3, color='#9467bd'), line=dict(color='#9467bd', width=1), text=[f"f={f:.2f} Hz<br>Δ={resid[i]:.2f}%" for i,f in enumerate(freq)], hoverinfo='text'), row=3, col=1)

    fig.update_xaxes(type='log', title='f / Hz', row=3, col=1); fig.update_yaxes(type='log', row=1, col=1)
    fig.update_layout(title=f'{data["sample_name"]} — Bode & Residuals', template='plotly_white', hovermode='closest', height=750, legend=dict(orientation='h', y=-0.08), margin=dict(t=50, b=50, l=50, r=20))
    return fig


def make_harmonics_figure(data):
    raw = data["raw"]; freq_all = np.array(raw["freq"]); thd_e = np.array(raw["thd_e"]); thd_i = np.array(raw["thd_i"])
    fig = make_subplots(rows=2, cols=2, subplot_titles=('THD vs Frequency', 'Current THD Scatter', '', ''), vertical_spacing=0.12, horizontal_spacing=0.1)
    fig.add_trace(go.Scatter(x=freq_all, y=thd_e, mode='lines+markers', name='THD Ewe', marker=dict(size=4, color='#2166ac'), line=dict(width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=freq_all, y=thd_i, mode='lines+markers', name='THD I', marker=dict(size=4, color='#d6604d'), line=dict(width=1.5)), row=1, col=1)
    fig.add_hline(y=5, line=dict(color='orange', dash='dash'), row=1, col=1)
    colors = ['#d6604d' if t > 5 else '#4dac26' for t in thd_i]
    fig.add_trace(go.Scatter(x=freq_all, y=thd_i, mode='markers', name='THD I', marker=dict(size=6, color=colors, opacity=0.7), text=[f"f={f:.2f} Hz<br>THD I={thd_i[i]:.2f}%<br>{'⚠ NONLINEAR' if thd_i[i]>5 else '✓ linear'}" for i,f in enumerate(freq_all)], hoverinfo='text', showlegend=False), row=1, col=2)
    fig.update_xaxes(type='log', title='f / Hz', row=1, col=1); fig.update_yaxes(title='THD / %', row=1, col=1)
    fig.update_xaxes(type='log', title='f / Hz', row=1, col=2); fig.update_yaxes(title='THD I / %', row=1, col=2)
    fig.update_layout(title=f'{data["sample_name"]} — Harmonic Distortion Analysis', template='plotly_white', hovermode='closest', height=550, legend=dict(orientation='h', y=-0.15), margin=dict(t=50, b=60, l=50, r=20))
    return fig


# ── Model comparison figure ──

def make_model_comparison_figure(data):
    """Overlay all fitted models on cleaned data for visual comparison."""
    cl = data["cleaned"]
    freq = np.array(cl["freq"]); Z_re = np.array(cl["z_re"]); Z_im = np.array(cl["z_im"])
    fit = data.get("fit")

    fig = go.Figure()

    # Cleaned data (faint background)
    fig.add_trace(go.Scatter(
        x=Z_re, y=-Z_im, mode='markers',
        name='Cleaned data', marker=dict(color='#aaaaaa', size=5, opacity=0.4),
        text=[f"f={f/1e3:.2f} kHz<br>Z'={Z_re[j]:.1f}<br>-Z''={-Z_im[j]:.1f}" for j,f in enumerate(freq)],
        hoverinfo='text'
    ))

    if fit and fit.get("converged") and "all_models" in fit:
        colors = {"R(RQ)": "#2166ac", "R(RQ)(RQ)": "#d6604d",
                  "R(RQ)CPE": "#4dac26", "R(R,C)CPE": "#9467bd"}
        for m in fit["all_models"]:
            if "Z_fit_re" not in m:
                continue
            Zf_re = np.array(m["Z_fit_re"])
            Zf_im = np.array(m["Z_fit_im"])
            name = m["name"]
            c = colors.get(name, "#7f7f7f")
            is_best = m.get("is_best", False)
            width = 3 if is_best else 1.5
            dash = 'solid' if is_best else 'dash'
            label = f"{name}  χ²/N={m['chi2_N']:.1f}"
            if is_best:
                label += "  ★BEST"
            fig.add_trace(go.Scatter(
                x=Zf_re, y=-Zf_im, mode='lines',
                name=label, line=dict(color=c, width=width, dash=dash),
            ))

    fig.update_xaxes(title_text="Z' / Ω")
    fig.update_yaxes(title_text="−Z'' / Ω")
    fig.update_layout(
        title=f'{data["sample_name"]} — Model Comparison  [{data["quality"]}]',
        template='plotly_white', hovermode='closest',
        height=600, width=750,
        legend=dict(orientation='h', y=-0.18),
        margin=dict(t=50, b=80, l=60, r=40)
    )
    return fig


# ── Comparison figures ──

def _add_trace(fig, data, i, colors, row=1, col=1, showleg=True):
    cl = data["cleaned"]; freq = np.array(cl["freq"]); Z_re = np.array(cl["z_re"]); Z_im = np.array(cl["z_im"])
    c = colors[i % len(colors)]
    name = data["sample_name"] + _quality_label(data)
    kwargs = dict(row=row, col=col) if getattr(fig, '_grid_ref', None) is not None else {}
    fig.add_trace(go.Scatter(x=Z_re, y=-Z_im, mode='markers', name=name, marker=dict(color=c, size=5, opacity=0.7),
        text=[f"{data['sample_name']}<br>f={f/1e3:.2f} kHz<br>Z'={Z_re[j]:.1f}<br>-Z''={-Z_im[j]:.1f}" for j,f in enumerate(freq)], hoverinfo='text'), **kwargs)
    fit = data.get("fit")
    if fit and fit.get("converged") and "Z_fit_re" in fit:
        Zf_re = np.array(fit["Z_fit_re"]); Zf_im = np.array(fit["Z_fit_im"])
        fig.add_trace(go.Scatter(x=Zf_re, y=-Zf_im, mode='lines', name=f"{data['sample_name']} fit", showlegend=False, line=dict(color=c, width=1.5)), **kwargs)


def make_nyquist_comparison(results, title, fig_id, include_quality=False):
    fig = go.Figure(); colors = ["#2166ac", "#d6604d", "#4dac26", "#9467bd", "#ff7f0e", "#e377c2", "#7f7f7f", "#bcbd22"]
    for i, d in enumerate(results):
        _add_trace(fig, d, i, colors)
    fig.update_xaxes(title_text="Z' / Ω"); fig.update_yaxes(title_text="−Z'' / Ω")
    fig.update_layout(title=title, template='plotly_white', hovermode='closest', height=600, width=750, legend=dict(orientation='h', y=-0.18), margin=dict(t=60, b=80, l=60, r=40))
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig_id)


def make_bode_comparison(results, title, fig_id):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=('|Z| / Ω', '−ϕ / deg'), vertical_spacing=0.12)
    colors = ["#2166ac", "#d6604d", "#4dac26", "#9467bd", "#ff7f0e", "#e377c2", "#7f7f7f", "#bcbd22"]
    for i, d in enumerate(results):
        cl = d["cleaned"]; freq = np.array(cl["freq"]); Z_re = np.array(cl["z_re"]); Z_im = np.array(cl["z_im"])
        Z_mag = np.sqrt(Z_re**2 + Z_im**2); phase = -np.arctan2(Z_im, Z_re) * 180 / np.pi; c = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=freq, y=Z_mag, mode='markers', name=d["sample_name"], marker=dict(color=c, size=4, opacity=0.6), text=[f"{d['sample_name']}<br>f={f:.2f} Hz<br>|Z|={Z_mag[j]:.2f}" for j,f in enumerate(freq)], hoverinfo='text'), row=1, col=1)
        fig.add_trace(go.Scatter(x=freq, y=phase, mode='markers', name=d["sample_name"], marker=dict(color=c, size=4, opacity=0.6), showlegend=False, text=[f"{d['sample_name']}<br>f={f:.2f} Hz<br>ϕ={phase[j]:.2f}°" for j,f in enumerate(freq)], hoverinfo='text'), row=2, col=1)
    fig.update_xaxes(type='log', title='f / Hz', row=2, col=1); fig.update_yaxes(type='log', row=1, col=1)
    fig.update_layout(title=title, template='plotly_white', hovermode='closest', height=650, width=750, legend=dict(orientation='h', y=-0.12), margin=dict(t=60, b=60, l=60, r=40))
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig_id)


def make_thd_comparison(results, title, fig_id):
    fig = go.Figure(); colors = ["#2166ac", "#d6604d", "#4dac26", "#9467bd", "#ff7f0e", "#e377c2", "#7f7f7f", "#bcbd22"]
    for i, d in enumerate(results):
        raw = d["raw"]; freq_all = np.array(raw["freq"]); thd_i = np.array(raw["thd_i"])
        fig.add_trace(go.Scatter(x=freq_all, y=thd_i, mode='lines+markers', name=d["sample_name"], marker=dict(size=4, color=colors[i % len(colors)]), line=dict(width=1.5, color=colors[i % len(colors)])))
    fig.add_hline(y=5, line=dict(color='orange', dash='dash'))
    fig.add_annotation(x=0.95, y=5.5, xref='paper', text='5% threshold', showarrow=False, font=dict(color='orange', size=11))
    fig.update_xaxes(type='log', title='f / Hz'); fig.update_yaxes(title='THD I / %')
    fig.update_layout(title=title, template='plotly_white', hovermode='closest', height=500, width=750, legend=dict(orientation='h', y=-0.18), margin=dict(t=60, b=80, l=60, r=40))
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig_id)


def make_arrhenius_figure(all_results, fig_id):
    fig = go.Figure()
    groups = {}
    for data in all_results:
        g = data["group"]
        groups.setdefault(g, []).append(data)
    colors = {"GPE_h4_201": "#2166ac", "GPE_h3_131": "#d6604d", "SPE_3h_131": "#4dac26", "GPE_h3_101": "#9467bd", "GPE_h3_101_2": "#ff7f0e"}
    for gname, gdata in groups.items():
        usable = [d for d in gdata if d["quality"] in ("OK", "WARN", "LIMITED")]
        if not usable: continue
        temps = np.array([d["temp_C"] for d in usable]); inv_T = 1000.0 / (temps + 273.15)
        sigmas = np.array([d["sigma_S_cm"] for d in usable]); ln_sig = np.log(sigmas)
        labels = [d["sample_name"] for d in usable]; color = colors.get(gname, "#7f7f7f")
        fig.add_trace(go.Scatter(x=inv_T, y=ln_sig, mode='markers', name=gname, marker=dict(color=color, size=10, symbol='circle'),
            text=[f"{lab}<br>T={temps[j]}°C<br>σ={sigmas[j]:.2e} S/cm" for j,lab in enumerate(labels)], hoverinfo='text'))
        if len(usable) >= 3:
            coeffs = np.polyfit(inv_T, ln_sig, 1); slope, intercept = coeffs
            kB, eV = 1.380649e-23, 1.602176634e-19
            Ea_eV = -slope * 1000 * kB / eV
            T_fit = np.linspace(inv_T.min() - 0.05, inv_T.max() + 0.05, 100)
            ln_fit = slope * T_fit + intercept
            fig.add_trace(go.Scatter(x=T_fit, y=ln_fit, mode='lines', name=f"{gname} fit (Ea={Ea_eV*1000:.1f} meV)", line=dict(color=color, width=1.5, dash='dash'), showlegend=True))
    fig.update_xaxes(title='1000 / T / K⁻¹'); fig.update_yaxes(title='ln(σ / S·cm⁻¹)')
    fig.update_layout(title='Arrhenius Analysis — Ionic Conductivity', template='plotly_white', hovermode='closest', height=550, width=750, legend=dict(orientation='h', y=-0.18), margin=dict(t=60, b=80, l=60, r=40))
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig_id)


# ── K-K figure ──

def make_kk_figure(results, fig_id="fig-kk"):
    n = len(results)
    fig = make_subplots(rows=n, cols=2, vertical_spacing=0.06)
    colors = {"OK": "#4dac26", "WARN": "#ffa000", "DO NOT USE": "#d6604d", "POOR": "#d6604d", "LIMITED": "#e67e22"}
    for i, (name, quality, kk) in enumerate(results):
        freq = kk["freq"]; rel_re = kk["rel_re"]; rel_im = kk["rel_im"]; c = colors.get(quality, "#7f7f7f")
        fig.add_trace(go.Scatter(x=freq, y=rel_re, mode='lines+markers', name=f"{name} Re", marker=dict(size=3, color=c), line=dict(color=c, width=1), showlegend=False), row=i+1, col=1)
        fig.add_trace(go.Scatter(x=freq, y=rel_im, mode='lines+markers', name=f"{name} Im", marker=dict(size=3, color=c), line=dict(color=c, width=1), showlegend=False), row=i+1, col=2)
        for col in (1, 2):
            fig.add_hline(y=1, line=dict(color='green', dash='dash', width=0.5), row=i+1, col=col)
            fig.add_hline(y=-1, line=dict(color='green', dash='dash', width=0.5), row=i+1, col=col)
            fig.add_hline(y=5, line=dict(color='orange', dash='dash', width=0.5), row=i+1, col=col)
            fig.add_hline(y=-5, line=dict(color='orange', dash='dash', width=0.5), row=i+1, col=col)
        vcolor = {"PASS": "green", "MARGINAL": "orange", "FAIL": "red"}.get(kk["verdict"], "gray")
        fig.add_annotation(x=0.02, y=0.98, xref='paper', yref=f'y{i+1}', text=f"<b>{name}</b><br>K-K: {kk['verdict']}<br>RMSE_rel: {kk['rmse_rel']:.2f}%", showarrow=False, align='left', valign='top', font=dict(size=9, color=vcolor), bgcolor='rgba(255,255,255,0.8)', borderpad=2)
    for i in range(n):
        fig.update_xaxes(type='log', title='f / Hz', row=i+1, col=1); fig.update_xaxes(type='log', title='f / Hz', row=i+1, col=2)
        fig.update_yaxes(title='ΔRe/|Z| / %', row=i+1, col=1); fig.update_yaxes(title='ΔIm/|Z| / %', row=i+1, col=2)
    fig.update_layout(title='Kramers-Kronig Validation — Lin-KK Residuals', template='plotly_white', hovermode='closest', height=200*n+80, width=900, margin=dict(t=60, b=40, l=60, r=40))
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig_id)
