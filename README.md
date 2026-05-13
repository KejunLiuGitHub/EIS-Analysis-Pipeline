# EIS Batch Analysis Pipeline

A zero-code batch analysis system for Electrochemical Impedance Spectroscopy (EIS). Auto-scans `.mpr` files, parses experimental parameters, fits equivalent-circuit models, generates interactive HTML reports, and learns model preferences per project.

[中文文档](README_CN.md)

---

## Installation

```bash
# 1. Clone / enter the repository
cd /path/to/this/repo

# 2. Install dependencies (Python 3.11+)
pip install -e .

# 3. Verify
eis-pipeline --help
```

**Dependencies**
- `galvani` — read BioLogic `.mpr` files
- `impedance==1.7.1` — equivalent-circuit fitting (known bug in 1.7.1 is internally patched)
- `numpy` — numerical computing
- `plotly` — interactive plots

---

## Filename Convention (Important)

**You must** follow this naming scheme so the program can auto-extract parameters:

```
Operator_ProjectName_DATE_YYYYMMDD_Thickness_um_Diameter_cm_Temperature_C_OtherCode.mpr
```

### Example

```
Zhangsan_GPE_h3_131_DATE_20250513_30_1_25_C01.mpr
```

| Field | Value | Description |
|-------|-------|-------------|
| Operator | `Zhangsan` | experimenter name |
| ProjectName | `GPE_h3_131` | project / sample series (underscores allowed) |
| `DATE` | fixed | anchor field, must be uppercase |
| YYYYMMDD | `20250513` | test date |
| Thickness | `30` | film thickness in µm |
| Diameter | `1` | electrode diameter in cm |
| Temperature | `25` | test temperature in °C |
| OtherCode | `C01` | batch / replicate ID |

### Non-compliant filenames

If the filename does not match the convention, the program will **prompt you manually** for all parameters.

---

## Usage

### 1. Scan — list new data

```bash
eis-pipeline scan data/
```

Sample output:

```
🔍 3 new samples found:

No.  Filename                                               Operator   Project           Date       L(µm)  d(cm)  T(°C)  Code
---------------------------------------------------------------------------------------------------------------------------------
1    Zhangsan_GPE_h3_131_DATE_20250513_30_1_25_C01          Zhangsan   GPE_h3_131      20250513   30.0   1.0    25.0   C01
2    Zhangsan_GPE_h3_131_DATE_20250513_30_1_60_C02          Zhangsan   GPE_h3_131      20250513   30.0   1.0    60.0   C02
3    Lisi_SPE_3h_131_DATE_20250513_40_1_80_C01              Lisi       SPE_3h_131      20250513   40.0   1.0    80.0   C01
```

Already-processed samples (with a corresponding `eis_analysis_*.html`) are skipped.

---

### 2. Process — generate per-sample reports

```bash
eis-pipeline process data/
```

Interactive flow:

**① Compliant filename (auto-parsed)**

```
[1/3] Zhangsan_GPE_h3_131_DATE_20250513_30_1_25_C01
  Parsed: operator=Zhangsan | project=GPE_h3_131 | date=20250513 | L=30µm | d=1cm | T=25°C | code=C01
  Process? [Y/n/edit(e)]: Y
  Processing: Zhangsan_GPE_h3_131_DATE_20250513_30_1_25_C01 ... ✅  WARN | σ=5.85e-06
```

**② Historical model preference available**

After a project has been processed ≥3 times, the system auto-learns the best model:

```
📌 Historical preference: R(RQ)(RQ) (source:auto, wins:3/4)
Use preferred model? [Y/all-models(a)/edit(e)]: Y
⚡ Using preferred model: R(RQ)(RQ)
```

| Option | Behavior |
|--------|----------|
| `Y` / Enter | fit only the preferred model (faster) |
| `a` | ignore preference, run full 4-model competition |
| `e` | edit parameters; can force a specific model |

**③ Edit mode (force a model)**

```
--- Edit parameters (press Enter to keep current) ---
  Operator [Zhangsan]:
  ...
  Available models: R(RQ), R(RQ)(RQ), R(RQ)CPE, R(R,C)CPE
  Leave blank for auto-selection
  Force model []: R(RQ)
    ✅ Forced: R(RQ)
```

A forced model overrides the historical preference and is recorded as `source: manual`.

**④ Non-compliant filename (manual input)**

```
Filename 'GPE_h3_101_C02' is non-compliant, please enter manually:
  Operator: Zhangsan
  Project: GPE_h3_101
  Date (YYYYMMDD): 20250513
  Thickness (µm): 100
  Electrode diameter (cm) [default 1.0]: 1
  Temperature (°C) [default 25]: 25
  Other code: C02
  Sample name [default GPE_h3_101_C02]:
```

---

### 3. Combine — overlay comparison report

```bash
eis-pipeline combine
```

Interactive flow:

```
📦 5 processed samples found:

No.  Sample name                                      Operator   Project         Date       Temp   Quality   σ(S/cm)
---------------------------------------------------------------------------------------------------------------
1    Zhangsan_GPE_h3_131_DATE_20250513_30_1_25_C01    Zhangsan   GPE_h3_131    20250513   25.0   WARN      5.850e-06
...

Select sample numbers (comma-separated, e.g. 1,3,5): 1,2,3
Comparison title: GPE_h3_131 temperature series
Generating plots...

✅ Comparison saved: eis_compare_20250513_143052.html
```

The comparison report includes:
- Nyquist overlay (data points + fitted curves)
- Bode overlay (|Z| and phase)
- THD overlay

---

## Model Preference Mechanism

The system automatically tracks the best-fitting model per project:

- After each sample is processed, the winning model is recorded
- When a model wins **≥3 times** with **>50%** win rate for a project → auto-promoted to preference
- Next time a sample from the same project is processed, the preferred model is recommended (single-model fit = faster)
- You can always override with `a` (all models) or `e` (force a model)

Preference file `eis_model_prefs.json` example:

```json
{
  "GPE_h3_131": {
    "preferred_model": "R(RQ)(RQ)",
    "source": "auto",
    "stats": {"R(RQ)(RQ)": 5, "R(RQ)": 1},
    "total": 6
  }
}
```

---

## Output Files

After processing a sample, the following are created in the **data directory**:

| File | Description |
|------|-------------|
| `eis_analysis_<name>.html` | Full per-sample report (Nyquist / Bode / THD / model comparison / parameters) |
| `eis_meta_<name>.json` | Metadata for `combine` |
| `eis_pipeline.log` | Audit trail (append-only) |
| `eis_model_prefs.json` | Model preference memory (auto-maintained) |

`combine` creates in the **current directory**:

| File | Description |
|------|-------------|
| `eis_compare_<timestamp>.html` | Multi-sample overlay comparison report |

---

## Directory Structure

```
.
├── data/                    ← raw .mpr data (gitignored)
│   ├── readme.txt
│   ├── *.mpr / *.mps / *.sta
│   └── activity_energy/
├── eislib/                  ← core library
│   ├── data.py              data I/O + fitting
│   ├── fit.py               equivalent-circuit fitting
│   ├── plot.py              Plotly figures
│   ├── html_single.py       HTML report template
│   ├── kk.py                Kramers–Kronig validation
│   └── ...
├── eis_pipeline.py          ← main entry (scan / process / combine)
├── analyze_one.py           ← quick single-sample CLI
├── figures/                 ← publication-grade figures
├── reports/                 ← report templates (gitignored)
├── lessons/                 ← analysis knowledge base
├── archive/                 ← old scripts & reports (gitignored)
├── README.md
├── README_CN.md
└── .gitignore
```

---

## FAQ

**Q: Why does scan say "non-compliant"?**
> The filename must contain the `DATE_YYYYMMDD` anchor. Check underscores and 8-digit date format.

**Q: My electrode diameter is not 1 cm.**
> Put the actual diameter in the 6th field (e.g. `1.5`). Area is auto-computed as `A = π·(d/2)²`.

**Q: Preferred model failed to fit.**
> The program automatically falls back to the full 4-model pool. Log shows `Preferred model 'X' failed, falling back to full pool`.

**Q: How to reset all preferences?**
> Delete `eis_model_prefs.json` in the data directory.

**Q: HTML report opens blank.**
> Internet is required to load Plotly CDN. For offline use, modify `eislib/html_single.py` to use a local plotly.js.

---

## License

MIT
