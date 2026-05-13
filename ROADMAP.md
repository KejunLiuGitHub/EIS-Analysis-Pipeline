# Roadmap

## Status

**Current version:** v1.0 — stable, used in production for polymer-electrolyte EIS screening.

---

## Completed ✅

| Feature | Description |
|---------|-------------|
| Zero-code batch pipeline | `scan` → `process` → `combine` CLI workflow |
| Auto filename parsing | Extracts operator, project, date, thickness, diameter, temperature from filename |
| 4-model fitting pool | R(RQ), R(RQ)(RQ), R(RQ)CPE, R(R,C)CPE with competitive χ² selection |
| Model preference memory | Per-project auto-learning of best model; manual override supported |
| Interactive HTML reports | Nyquist, Bode, THD, model comparison, parameter tables, quality flags |
| Multi-sample overlay | `combine` command for direct visual comparison across samples |
| Audit logging | `eis_pipeline.log` tracks every processing event |
| Kramers–Kronig validation | Lin-KK residuals (currently standalone; see roadmap below) |

---

## Short-term (Next 1–2 Months)

### 1. Kramers–Kronig Integration
- Embed Lin-KK directly into the `process` step
- Auto-generate K-K residual plots inside each per-sample HTML report
- Flag "K-K FAIL" samples before they enter the fitting stage

### 2. Arrhenius Auto-Analysis
- Detect temperature-series samples within the same project
- Auto-fit σ vs 1/T, extract activation energy Ea and R²
- Add Arrhenius plot section to `combine` overlay reports

### 3. Data Export
- One-click CSV / Excel export of all fitted parameters
- Columns: sample_name, project, temp_C, model, R0, R1, R2, Q1, α1, σ_S_cm, χ²_N, quality

### 4. Dynamic Diameter Display
- HTML template currently hard-codes "d = 1.0 cm"
- Read actual diameter from filename and render correct A = π·(d/2)² in reports

---

## Mid-term (3–6 Months)

### 5. Multi-Format Raw Data Support
**Goal:** Decouple the pipeline from BioLogic `.mpr` exclusively.

| Format | Status | Notes |
|--------|--------|-------|
| BioLogic `.mpr` | ✅ Supported | Current default via `galvani` |
| Gamry `.DTA` | 📋 Planned | Common in US labs |
| Zahner `.ism` / `.iss` | 📋 Planned | German potentiostats |
| Metrohm Autolab `.nox` | 📋 Planned | European market |
| ASCII CSV (freq, ReZ, ImZ) | 📋 Planned | Universal fallback |

**Approach:** Abstract a `BaseReader` class in `eislib/data.py`; each format implements `read(filepath) → (freq, Z_complex, metadata)`.

### 6. Web Dashboard (Streamlit)
- Drag-and-drop `.mpr` upload
- Sidebar: sample list with quality badges
- Tabs: Nyquist | Bode | THD | K-K | Parameters
- Built-in CSV export button
- No command line required

### 7. Extended Model Library
- Warburg diffusion element (for bulk electrolyte semi-infinite diffusion)
- Gerischer element (for porous electrodes)
- Custom model builder: user-defined circuit string input

---

## Long-term (6–12 Months)

### 8. Database Backend
- SQLite store for all processed samples
- Query interface: "show me all GPE_h4 samples with quality=OK and T≥60°C"
- Versioned re-analysis: re-fit old data with new models without overwriting

### 9. DRT (Distribution of Relaxation Times)
- Tikhonov-regularized DRT as complementary analysis to equivalent-circuit fitting
- Help users decide whether a second arc is real or an artifact

### 10. Machine-Learning Quality Classifier
- Train on historical OK/WARN/POOR labels + extracted features (THD, Z-range, K-K RMSE)
- Pre-screen new data and warn users before they waste time on bad measurements

---

## Contributing

This is primarily a research-group internal tool, but pull requests for multi-format readers, new models, or bug fixes are welcome.

Open an issue if you want to tackle any item on this roadmap.
