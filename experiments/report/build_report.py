"""Assemble REPORT.md from the prose in report_text.py and the generated tables.

Run experiments/make_figures.py and experiments/make_om_report.py first; they
write results/tables_final.md, results/tables_single_change.md and
results/tables_om.md.  Every ``<<name>>`` placeholder in the prose is replaced
by the section of one of those files whose heading starts with the text
listed in ``TABLES``.
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

TABLES = {
    # results/tables_om.md: all models, including CMG and QKAN-FWP-O
    "ts_summary": ("tables_om.md", "Per-dataset summary"),
    "ts_matrix": ("tables_om.md", "Each model against every reference"),
    "ts_cells": ("tables_om.md", "All cells: test MSE"),
    "ts_linear": ("tables_om.md", "Closed-form linear autoregression"),
    "om_ablation_ts": ("tables_om.md", "QKAN-FWP-O ablation on the paper benchmarks"),
    "fam_main": ("tables_om.md", "Families of systems"),
    "fam_vs": ("tables_om.md", "QKAN-FWP-O against each model on the families"),
    "om_ablation_fam": ("tables_om.md", "QKAN-FWP-O ablation on the families"),
    "shots": ("tables_om.md", "Finite-shot sensitivity"),
    "solar_all": ("tables_om.md", "Solar cycle: all models"),
    # results/tables_final.md: gated models, reproduction gap, robustness, solar details
    "fwp_ablation": ("tables_final.md", "QKAN-FWP+ ablation"),
    "gap": ("tables_final.md", "Reproduction gap"),
    "robust": ("tables_final.md", "Robustness checks at N = 16"),
    "burnin": ("tables_final.md", "NARMA without the start-up transient"),
    "solar_parts": ("tables_final.md", "Solar cycle: final comparison"),
    "solar_grid": ("tables_final.md", "Solar cycle: the paper's learning-rate grid"),
    # results/tables_single_change.md
    "single_change": ("tables_single_change.md", "Time series: ablation"),
}
ORDER = ["HEADER", "SUMMARY", "BACKGROUND", "MODELS", "SETUP", "RESULTS_TS", "RESULTS_FAMILY", "RESULTS_SHOTS",
         "RESULTS_SOLAR", "NEGATIVE", "APPENDIX", "REFERENCES"]


def table(file: str, heading: str) -> str:
    text = (ROOT / "results" / file).read_text()
    m = re.search(r"^## " + re.escape(heading) + r".*?\n\n(.*?)(?=\n## |\Z)", text, re.S | re.M)
    if not m:
        raise KeyError(f"no section starting with {heading!r} in results/{file}")
    return m.group(1).strip()


def main():
    ns = {}
    exec((HERE / "report_text.py").read_text(), ns)
    body = "".join(ns[name] for name in ORDER)
    for name, (file, heading) in TABLES.items():
        if f"<<{name}>>" in body:
            body = body.replace(f"<<{name}>>", table(file, heading))
    left = re.findall(r"<<\w+>>", body)
    assert not left, f"unresolved placeholders: {left}"
    (ROOT / "REPORT.md").write_text(body)
    print(f"REPORT.md written: {len(body)} characters")


if __name__ == "__main__":
    main()
