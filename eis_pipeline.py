#!/usr/bin/env python3
"""Zero-code EIS batch analysis pipeline.

Usage:
    python3 eis_pipeline.py scan <dir>       # list new .mpr files
    python3 eis_pipeline.py process <dir>    # batch process with auto-parse / interactive
    python3 eis_pipeline.py combine          # interactive overlay comparison

Filename convention (auto-parsed):
    实验人员_ProjectName_DATE_YYYYMMDD_Thickness_Diameter_Temperature_OtherCODE.mpr
    e.g. 张三_GPE_h3_131_DATE_20250513_30_1_25_C01.mpr
"""

import argparse
import glob
import json
import math
import os
import sys
from datetime import datetime

import numpy as np

# ── Monkey-patch np into circuit_elements before importing eislib ──
import impedance.validation as val_module
from impedance.models.circuits.elements import circuit_elements

ce_dict = dict(circuit_elements)
ce_dict["np"] = np
val_module.circuit_elements = ce_dict

from eislib.data import process_mpr
from eislib.plot import (
    make_nyquist_figure,
    make_bode_figure,
    make_harmonics_figure,
    make_model_comparison_figure,
    make_nyquist_comparison,
    make_bode_comparison,
    make_thd_comparison,
)
from eislib.html_single import build_html, CSS


# ═══════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════


def write_log(out_dir: str, action: str, details: str):
    """Append a line to eis_pipeline.log in out_dir."""
    log_path = os.path.join(out_dir, "eis_pipeline.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action} {details}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


# ═══════════════════════════════════════════════════════════════════════
#  Model preference tracking
# ═══════════════════════════════════════════════════════════════════════


def load_model_prefs(dir_path: str) -> dict:
    """Load eis_model_prefs.json if it exists."""
    path = os.path.join(dir_path, "eis_model_prefs.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_model_prefs(dir_path: str, prefs: dict):
    """Write eis_model_prefs.json."""
    path = os.path.join(dir_path, "eis_model_prefs.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


def update_model_prefs(prefs: dict, project: str, best_model: str):
    """Update win count for a project; if a model wins >=3 times with >50% rate,
    set it as the auto-preferred model."""
    entry = prefs.setdefault(project, {
        "preferred_model": None,
        "source": None,
        "stats": {},
        "total": 0,
        "last_updated": None,
    })
    entry["stats"][best_model] = entry["stats"].get(best_model, 0) + 1
    entry["total"] += 1
    entry["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Auto-promote if a model dominates (>=3 wins & >50%)
    for model, count in entry["stats"].items():
        if count >= 3 and count / entry["total"] > 0.5:
            if entry.get("preferred_model") != model:
                entry["preferred_model"] = model
                entry["source"] = "auto"
            break


def get_preferred_model(prefs: dict, project: str) -> str | None:
    """Return preferred model name if one is set."""
    entry = prefs.get(project)
    if entry and entry.get("preferred_model"):
        return entry["preferred_model"]
    return None


# ═══════════════════════════════════════════════════════════════════════
#  Filename parser
# ═══════════════════════════════════════════════════════════════════════


def parse_filename(stem: str):
    """Parse filename according to convention.

    Person_Project_DATE_YYYYMMDD_L_um_D_cm_T_C_Code...
    Project may contain underscores; DATE is the anchor, followed by 8-digit date.
    Returns dict or None if non-compliant.
    """
    parts = stem.split("_")
    try:
        data_idx = parts.index("DATE")
    except ValueError:
        return None

    # Need at least: [person] ... [project] DATE YYYYMMDD L D T [code...]
    if len(parts) < data_idx + 6:
        return None

    try:
        date_str = parts[data_idx + 1]
        L_um = float(parts[data_idx + 2])
        diam_cm = float(parts[data_idx + 3])
        temp_C = float(parts[data_idx + 4])
    except ValueError:
        return None

    person = parts[0] if data_idx >= 1 else ""
    project = "_".join(parts[1:data_idx]) if data_idx >= 2 else ""
    code = "_".join(parts[data_idx + 5:])

    return {
        "person": person,
        "project": project,
        "date": date_str,
        "L_um": L_um,
        "diam_cm": diam_cm,
        "temp_C": temp_C,
        "code": code,
        "name": stem,
    }


# ═══════════════════════════════════════════════════════════════════════
#  Directory scanning
# ═══════════════════════════════════════════════════════════════════════


def scan_directory(dir_path: str):
    """Return list of (filepath, stem) for new .mpr files."""
    mpr_files = sorted(glob.glob(os.path.join(dir_path, "*.mpr")))
    new_files = []
    for fp in mpr_files:
        stem = os.path.splitext(os.path.basename(fp))[0]
        html_name = f"eis_analysis_{stem}.html"
        if not os.path.exists(os.path.join(dir_path, html_name)):
            new_files.append((fp, stem))
    return new_files


# ═══════════════════════════════════════════════════════════════════════
#  Interactive helpers
# ═══════════════════════════════════════════════════════════════════════


def _input_float(prompt, default):
    """Prompt for a float with fallback."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("    ⚠️ 请输入数字")


def interactive_edit(parsed: dict) -> dict:
    """Allow user to edit any parsed parameter."""
    print("\n--- 编辑参数 (直接回车保留原值) ---")
    fields = [
        ("person", "实验人员", str),
        ("project", "项目名", str),
        ("date", "日期 (YYYYMMDD)", str),
        ("L_um", "厚度 (µm)", float),
        ("diam_cm", "直径 (cm)", float),
        ("temp_C", "温度 (°C)", float),
        ("code", "其他代码", str),
        ("name", "样品名称", str),
    ]
    for key, label, typ in fields:
        default = parsed.get(key, "")
        val = input(f"  {label} [{default}]: ").strip()
        if val:
            try:
                parsed[key] = typ(val)
            except ValueError:
                print(f"    ⚠️ 输入无效，保留原值 {default}")

    # Model override
    model_choices = ["R(RQ)", "R(RQ)(RQ)", "R(RQ)CPE", "R(R,C)CPE"]
    current_model = parsed.get("force_model", "")
    print(f"\n  可选模型: {', '.join(model_choices)}")
    print(f"  留空 = 自动选择（历史偏好或四模型竞争）")
    val = input(f"  强制指定模型 [{current_model}]: ").strip()
    if val:
        if val in model_choices:
            parsed["force_model"] = val
            print(f"    ✅ 已强制指定: {val}")
        else:
            print(f"    ⚠️ 无效模型名，忽略")
    elif current_model and input("  清除强制指定? [y/N]: ").strip().lower() == "y":
        parsed.pop("force_model", None)

    return parsed


def interactive_fallback(stem: str) -> dict:
    """Interactive input when filename doesn't match convention."""
    print(f"\n文件名 '{stem}' 不合规，请手动输入参数：")
    parsed = {
        "name": stem,
        "person": input("  实验人员: ").strip(),
        "project": input("  项目名: ").strip(),
        "date": input("  日期 (YYYYMMDD): ").strip(),
        "code": "",
    }
    parsed["L_um"] = _input_float("  厚度 (µm): ", 100.0)
    parsed["diam_cm"] = _input_float("  电极直径 (cm) [默认1.0]: ", 1.0)
    parsed["temp_C"] = _input_float("  温度 (°C) [默认25]: ", 25.0)
    parsed["code"] = input("  其他代码: ").strip()
    custom_name = input(f"  样品名称 [默认{stem}]: ").strip()
    if custom_name:
        parsed["name"] = custom_name
    return parsed


# ═══════════════════════════════════════════════════════════════════════
#  JSON serialization helper
# ═══════════════════════════════════════════════════════════════════════


def jsonify(obj):
    """Recursively convert numpy types → JSON-serializable Python types."""
    if isinstance(obj, np.ndarray):
        if obj.dtype == complex or obj.dtype == np.complex128:
            return [{"re": float(x.real), "im": float(x.imag)} for x in obj]
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    if isinstance(obj, np.complexfloating):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, dict):
        return {k: jsonify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [jsonify(v) for v in obj]
    return obj


# ═══════════════════════════════════════════════════════════════════════
#  Single-sample processing
# ═══════════════════════════════════════════════════════════════════════


def process_and_save(filepath: str, params: dict, out_dir: str, preferred_model=None):
    """Process one .mpr and write HTML + JSON sidecar."""
    stem = params["name"]
    L_um = params["L_um"]
    diam_cm = params["diam_cm"]
    temp_C = params["temp_C"]
    A_cm2 = math.pi * (diam_cm / 2) ** 2

    print(
        f"  处理中: {stem} (L={L_um}µm, d={diam_cm}cm, T={temp_C}°C, A={A_cm2:.4f}cm²) ...",
        end=" ",
        flush=True,
    )

    data = process_mpr(filepath, L_um, stem, A_cm2=A_cm2, preferred_model=preferred_model)
    data["temp_C"] = temp_C
    data["person"] = params.get("person", "")
    data["project"] = params.get("project", "")
    data["date"] = params.get("date", "")
    data["code"] = params.get("code", "")
    data["diam_cm"] = diam_cm

    # Generate Plotly figures
    nyq_fig = make_nyquist_figure(data)
    bode_fig = make_bode_figure(data)
    harm_fig = make_harmonics_figure(data)
    model_cmp_fig = make_model_comparison_figure(data)

    nyq_div = nyq_fig.to_html(full_html=False, include_plotlyjs=False, div_id="fig-nyq")
    bode_div = bode_fig.to_html(full_html=False, include_plotlyjs=False, div_id="fig-bode")
    harm_div = harm_fig.to_html(full_html=False, include_plotlyjs=False, div_id="fig-harm")
    model_cmp_div = model_cmp_fig.to_html(full_html=False, include_plotlyjs=False, div_id="fig-model-cmp")

    # Build & write HTML
    html = build_html(data, nyq_div, bode_div, harm_div, model_cmp_div)
    html_path = os.path.join(out_dir, f"eis_analysis_{stem}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Build minimal metadata for combine
    meta = {
        "sample_name": data["sample_name"],
        "quality": data["quality"],
        "sigma_S_cm": data["sigma_S_cm"],
        "L_um": data["L_um"],
        "temp_C": temp_C,
        "diam_cm": diam_cm,
        "A_cm2": A_cm2,
        "person": data.get("person", ""),
        "project": data.get("project", ""),
        "date": data.get("date", ""),
        "code": data.get("code", ""),
        "fit": {},
        "raw": {},
        "cleaned": {},
    }
    if data.get("fit") and data["fit"].get("converged"):
        meta["fit"] = {
            "converged": True,
            "model_name": data["fit"].get("model_name", ""),
            "chi2_N": data["fit"].get("chi2_N", 0),
            "Z_fit_re": data["fit"].get("Z_fit_re", []),
            "Z_fit_im": data["fit"].get("Z_fit_im", []),
            "params": data["fit"].get("params", {}),
            "derived": data["fit"].get("derived", {}),
        }
    meta["raw"] = {
        "freq": data["raw"]["freq"],
        "z_re": data["raw"]["z_re"],
        "z_im": data["raw"]["z_im"],
        "thd_i": data["raw"]["thd_i"],
    }
    meta["cleaned"] = {
        "freq": data["cleaned"]["freq"],
        "z_re": data["cleaned"]["z_re"],
        "z_im": data["cleaned"]["z_im"],
    }

    meta = jsonify(meta)
    json_path = os.path.join(out_dir, f"eis_meta_{stem}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"✅  {data['quality']} | σ={data['sigma_S_cm']:.2e}")

    # Log
    fit = data.get("fit", {})
    model_name = fit.get("model_name", "FAILED") if fit else "FAILED"
    chi2_str = f"{fit.get('chi2_N', 0):.1f}" if fit else "N/A"
    log_details = (
        f"{stem} | 人员={data.get('person','')} | 项目={data.get('project','')} | "
        f"日期={data.get('date','')} | L={L_um}µm | d={diam_cm}cm | T={temp_C}°C | "
        f"质量={data['quality']} | σ={data['sigma_S_cm']:.3e} | 模型={model_name} | χ²/N={chi2_str}"
    )
    write_log(out_dir, "PROCESS", log_details)

    return data


# ═══════════════════════════════════════════════════════════════════════
#  Commands
# ═══════════════════════════════════════════════════════════════════════


def cmd_scan(args):
    """List new .mpr files with auto-parsed parameters."""
    dir_path = args.dir
    new_files = scan_directory(dir_path)
    if not new_files:
        print(f"✅ 目录 '{dir_path}' 中没有新的 .mpr 文件（均已处理）")
        return

    print(f"\n🔍 发现 {len(new_files)} 个新样品：\n")
    hdr = f"{'序号':<4} {'文件名':<50} {'人员':<8} {'项目':<15} {'日期':<10} {'L(µm)':<8} {'d(cm)':<8} {'T(°C)':<8} {'代码':<10}"
    print(hdr)
    print("-" * len(hdr))

    for i, (fp, stem) in enumerate(new_files, 1):
        parsed = parse_filename(stem)
        if parsed:
            print(
                f"{i:<4} {stem:<50} {parsed['person']:<8} {parsed['project']:<15} "
                f"{parsed['date']:<10} {parsed['L_um']:<8.1f} {parsed['diam_cm']:<8.1f} "
                f"{parsed['temp_C']:<8.1f} {parsed['code']:<10}"
            )
        else:
            print(f"{i:<4} {stem:<50} {'❌ 不合规':<50}")


def cmd_process(args):
    """Batch process: scan → parse / interactive → HTML + JSON."""
    dir_path = args.dir
    new_files = scan_directory(dir_path)
    if not new_files:
        print(f"✅ 目录 '{dir_path}' 中没有新的 .mpr 文件")
        return

    prefs = load_model_prefs(dir_path)
    print(f"\n🚀 批量处理 {len(new_files)} 个新样品\n")

    processed = []
    for i, (fp, stem) in enumerate(new_files, 1):
        print(f"\n[{i}/{len(new_files)}] {stem}")
        parsed = parse_filename(stem)

        if parsed:
            print(
                f"  解析: 人员={parsed['person']} | 项目={parsed['project']} | 日期={parsed['date']} | "
                f"L={parsed['L_um']}µm | d={parsed['diam_cm']}cm | T={parsed['temp_C']}°C | 代码={parsed['code']}"
            )
            choice = input("  确认处理? [Y/n/编辑(e)]: ").strip().lower()
            if choice == "n":
                print("  ⏭️  跳过")
                write_log(dir_path, "SKIP", f"{stem} | 用户手动跳过")
                continue
            if choice == "e":
                parsed = interactive_edit(parsed)
        else:
            parsed = interactive_fallback(stem)

        project = parsed.get("project", "")
        force_model = parsed.get("force_model")
        pref_model = get_preferred_model(prefs, project)

        # Determine which model strategy to use
        use_model = None  # None = fit all 4 models
        if force_model:
            use_model = force_model
            print(f"  🔒 强制使用模型: {force_model}")
            write_log(dir_path, "MODEL_FORCE", f"{stem} | 强制模型={force_model}")
        elif pref_model:
            pref_entry = prefs.get(project, {})
            src = pref_entry.get("source", "auto")
            stats = pref_entry.get("stats", {})
            win_count = stats.get(pref_model, 0)
            total = pref_entry.get("total", 0)
            print(f"  📌 历史偏好模型: {pref_model} (来源:{src}, 胜出:{win_count}/{total})")
            choice = input("  使用偏好模型? [Y/四模型竞争(a)/编辑(e)]: ").strip().lower()
            if choice == "a":
                use_model = None
                print("  🔄 使用四模型竞争")
            elif choice == "e":
                parsed = interactive_edit(parsed)
                force_model = parsed.get("force_model")
                if force_model:
                    use_model = force_model
                    print(f"  🔒 强制使用模型: {force_model}")
                else:
                    use_model = pref_model
            else:
                use_model = pref_model
                print(f"  ⚡ 使用偏好模型: {pref_model}")

        data = process_and_save(fp, parsed, dir_path, preferred_model=use_model)
        processed.append(data)

        # Update preference stats
        fit = data.get("fit")
        if fit and fit.get("converged"):
            best_name = fit.get("model_name", "")
            if best_name and project:
                update_model_prefs(prefs, project, best_name)
                save_model_prefs(dir_path, prefs)

    # Summary table
    print(f"\n{'=' * 65}")
    print(f"📋 处理完成: {len(processed)}/{len(new_files)} 个样品")
    print(f"{'=' * 65}")
    print(f"{'样品名':<35} {'质量':<12} {'σ(S/cm)':<15}")
    print("-" * 65)
    for d in processed:
        print(f"{d['sample_name']:<35} {d['quality']:<12} {d['sigma_S_cm']:<15.3e}")
    print("=" * 65)


def load_meta(filepath: str):
    """Load a sidecar JSON and reconstruct a data dict for plot functions."""
    with open(filepath, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return {
        "sample_name": meta["sample_name"],
        "quality": meta["quality"],
        "raw": meta["raw"],
        "cleaned": meta["cleaned"],
        "fit": meta.get("fit", {}),
    }


def cmd_combine(args):
    """Interactive picker → overlay comparison HTML."""
    meta_files = sorted(glob.glob("eis_meta_*.json"))
    if not meta_files:
        print("❌ 当前目录中没有 eis_meta_*.json，请先运行 process 命令")
        return

    print(f"\n📦 发现 {len(meta_files)} 个已有样品：\n")
    hdr = f"{'编号':<4} {'样品名':<40} {'人员':<8} {'项目':<12} {'日期':<10} {'温度':<8} {'质量':<10} {'σ(S/cm)':<12}"
    print(hdr)
    print("-" * len(hdr))

    metas = []
    for i, fp in enumerate(meta_files, 1):
        with open(fp, "r", encoding="utf-8") as f:
            meta = json.load(f)
        metas.append((i, fp, meta))
        print(
            f"{i:<4} {meta['sample_name']:<40} {meta.get('person', ''):<8} "
            f"{meta.get('project', ''):<12} {meta.get('date', ''):<10} "
            f"{meta.get('temp_C', ''):<8} {meta['quality']:<10} {meta['sigma_S_cm']:<12.3e}"
        )

    sel = input("\n请选择样品编号（逗号分隔，如 1,3,5）: ").strip()
    if not sel:
        print("❌ 未选择样品，取消")
        return
    try:
        indices = [int(x.strip()) for x in sel.split(",")]
        selected = [metas[i - 1] for i in indices if 1 <= i <= len(metas)]
    except ValueError:
        print("❌ 输入格式错误")
        return

    if len(selected) < 2:
        print("❌ 至少选择 2 个样品进行对比")
        return

    title = input("对比标题: ").strip() or "EIS Multi-Sample Comparison"

    print("\n生成对比图...")
    results = [load_meta(fp) for _, fp, _ in selected]
    nyq_div = make_nyquist_comparison(results, title, "fig-compare-nyq")
    bode_div = make_bode_comparison(results, title + " — Bode", "fig-compare-bode")
    thd_div = make_thd_comparison(results, title + " — THD", "fig-compare-thd")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = f"eis_compare_{timestamp}.html"

    sample_rows = "".join(
        f"<tr><td>{meta['sample_name']}</td><td>{meta.get('person', '')}</td>"
        f"<td>{meta.get('project', '')}</td><td>{meta.get('date', '')}</td>"
        f"<td>{meta.get('temp_C', '')}</td><td>{meta['quality']}</td>"
        f"<td>{meta['sigma_S_cm']:.3e}</td></tr>"
        for _, _, meta in selected
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<h1>{title}</h1>
<table>
<tr><th>样品名</th><th>人员</th><th>项目</th><th>日期</th><th>温度(°C)</th><th>质量</th><th>σ(S/cm)</th></tr>
{sample_rows}
</table>
<h2>Nyquist 对比</h2>
<figure>{nyq_div}</figure>
<h2>Bode 对比</h2>
<figure>{bode_div}</figure>
<h2>THD 对比</h2>
<figure>{thd_div}</figure>
<p style="margin-top:2rem;font-size:0.8rem;color:#aaa">
Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · eis_pipeline combine
</p>
</body></html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Log
    sample_names = ", ".join(meta["sample_name"] for _, _, meta in selected)
    write_log(".", "COMBINE", f"{html_path} | {len(selected)} samples: {sample_names}")

    print(f"\n✅ 对比报告已保存: {html_path}")


# ═══════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="EIS 批量分析流水线")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="扫描新样品")
    p_scan.add_argument("dir", help="数据目录路径")

    p_proc = sub.add_parser("process", help="批量处理新样品")
    p_proc.add_argument("dir", help="数据目录路径")

    sub.add_parser("combine", help="生成对比报告")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "combine":
        cmd_combine(args)


if __name__ == "__main__":
    main()
