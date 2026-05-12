# Lesson 5: Plotly Best Practices for EIS Dashboards

## Problem
Shared axes, slow hover, and full re-renders make interactive EIS dashboards sluggish and confusing.

## Solutions

### 1. Independent Axes Between Subplots
Never use shared axes. Zooming one panel should not affect others.

```python
fig = make_subplots(
    rows=3, cols=1, 
    shared_xaxes=False,  # ← critical
    shared_yaxes=False,  # ← critical
    subplot_titles=('|Z|', 'Phase', 'Residuals')
)
```

### 2. Pre-Compute Hover Text as Arrays
`hoverformat` is slow. Build string arrays once:

```python
text = [
    f"f={f/1e3:.2f} kHz<br>Z'={z_re[i]:.1f}<br>-Z''={-z_im[i]:.1f}"
    for i, f in enumerate(freq)
]
fig.add_trace(go.Scatter(
    x=z_re, y=-z_im, mode='markers',
    text=text, hoverinfo='text'  # ← fast
))
```

### 3. Plotly.react() for Updates
For single-page apps with sample switching, use `Plotly.react()` not `newPlot()`:

```javascript
// Fast update without flicker
Plotly.react('plot-div', newData, newLayout);
```

### 4. Component Decomposition Traces
Show Arc 1 and Arc 2 as separate dashed/dotted traces so readers understand the fit:

```python
# Arc 1: R0 + ZARC1
fig.add_trace(go.Scatter(
    x=(p[0]+Za1).real, y=-(p[0]+Za1).imag,
    mode='lines', name='Arc 1 (bulk)',
    line=dict(color='#4dac26', width=1.5, dash='dash')
))

# Arc 2: R0 + R1 + ZARC2
fig.add_trace(go.Scatter(
    x=(p[0]+p[1]+Za2).real, y=-(p[0]+p[1]+Za2).imag,
    mode='lines', name='Arc 2 (interface)',
    line=dict(color='#9467bd', width=1.5, dash='dot')
))
```

### 5. Residuals as % of |Z|
More intuitive than absolute residuals:

```python
Z_mag = np.sqrt(Z.real**2 + Z.imag**2)
Zf_mag = np.sqrt(Zf.real**2 + Zf.imag**2)
resid_pct = 100 * (Z_mag - Zf_mag) / Z_mag
```

### 6. Self-Contained HTML
Each report should be a single `.html` file with CDN links — no server needed:

```html
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
```
