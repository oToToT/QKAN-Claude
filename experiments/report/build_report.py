"""Assemble REPORT.md from the prose in this directory and the generated tables.

report_om.py      part A (observable-memory FWP; tables from results/tables_om.md)
report_text.py    sections 0-10 (tables from results/tables_final.md)
REPORT_stage1.md  sections 1-3 and the appendix (first-round text)

Run experiments/make_figures.py and experiments/make_om_report.py first.
"""
import re
from pathlib import Path

scratch = Path(__file__).resolve().parent  # this directory holds the prose sources
root = scratch.parent.parent
old = (scratch / 'REPORT_stage1.md').read_text()
final = (root / 'results' / 'tables_final.md').read_text()


def cut(text, start, end=None):
    a = text.index(start)
    b = text.index(end, a) if end else len(text)
    return text[a:b].rstrip() + '\n'


def table(title_start):
    m = re.search(r'## ' + re.escape(title_start) + r'.*?\n\n(.*?)(?=\n## |\Z)', final, re.S)
    assert m, title_start
    return m.group(1).strip()


ns = {}
exec((scratch / 'report_text.py').read_text(), ns)

sec1 = cut(old, '## 1. 論文在做什麼', '## 2. 可以改進的地方')
sec2 = cut(old, '## 2. 可以改進的地方', '---\n\n## 3. 實驗設定')
sec3 = cut(old, '## 3. 實驗設定', '---\n\n## 4. 結果一')
stage1 = cut(old, '## 4. 結果一', '---\n\n## 6. 沒有效果的想法')
refs = cut(old, '## 參考文獻')
refs = refs.replace('- Gated QKAN-FWP — arXiv:2605.06734；後續應用：traffic-matrix forecasting — arXiv:2606.27821',
    '- Gated QKAN-FWP — arXiv:2605.06734；後續應用：traffic-matrix forecasting — arXiv:2606.27821\n'
    '- 同一團隊關於更新規則的後續工作：Self-Modulating QFWP — arXiv:2606.24933；bounded memory gates — arXiv:2607.02363；\n'
    '  **Complementary Matrix-Gated QKAN-FWP（CMG）— arXiv:2607.27945**')
assert '2607.27945' in refs

# appendix: demote headings, point to the stage-1 figures, fix cross references
stage1 = stage1.replace('## 4. 結果一：time-series benchmarks（論文 Sec. 6.1）', '### A.1 Time-series（第一階段）')
stage1 = stage1.replace('## 5. 結果二：太陽黑子週期預測（論文 Sec. 6.2，主結果）', '### A.2 太陽黑子（第一階段）')
stage1 = re.sub(r'^### 4\.(\d)', r'#### A.1.\1', stage1, flags=re.M)
stage1 = re.sub(r'^### 5\.(\d)', r'#### A.2.\1', stage1, flags=re.M)
for a, b in [('figures/timeseries_main.png', 'figures/stage1_main.png'),
             ('figures/timeseries_ablation.png', 'figures/stage1_ablation.png'),
             ('figures/solar_forecast.png', 'figures/stage1_solar_forecast.png'),
             ('figures/solar_memory_kernel.png', 'figures/stage1_solar_memory_kernel.png'),
             ('figures/solar_error_by_start.png', 'figures/stage1_solar_error_by_start.png'),
             ('figures/solar_error_by_start_split622.png', 'figures/stage1_solar_error_by_start_split622.png'),
             ('（4.3 節）', '（A.1.3 節）'), ('（5.2 節）', '（A.2.2 節）'), ('（＝5.1）', '（＝A.2.1）'), ('\n---\n', '\n')]:
    stage1 = stage1.replace(a, b)

body = ns['HEADER'] + ns['SUMMARY'].format(per_dataset=table('Per-dataset summary')) + '\n---\n\n'
body += ns['SEC0_REVIEW'].format() + '\n---\n\n'
body += sec1 + '\n---\n\n' + sec2 + ns['SEC2_NOTE'] + '\n---\n\n' + sec3 + ns['SEC3_RULES'] + '\n---\n\n'
body += ns['SEC4_MODELS'] + '\n---\n\n'
body += ns['SEC5_TS'].format(
    main=table('Final time-series comparison'),
    vs_fwp=table('QKAN-FWP+ (ours) (149 params) vs each baseline'),
    vs_static=table('HQKAN-Δ, no fast weights (ours) (136 params) vs each baseline'),
    vs_wf=table('QKAN-FWP+ write-first (ours) (149 params) vs each baseline') if 'write-first (ours) (149 params) vs' in final else '（尚未完成）',
    paper=table('Ours vs the numbers printed in the paper'),
    ablation=table('Final-model ablation'),
    linear=table('Closed-form linear reference'),
    gap=table('Reproduction gap'),
    robust=table('Robustness checks at N = 16'),
    burnin=table('NARMA without the start-up transient'),
) + '\n---\n\n'
body += ns['SEC6_SOLAR'].format(
    main=table('Solar cycle: final comparison'),
    grid=table("Solar cycle: the paper's learning-rate grid"),
    split622=table('Solar cycle: second split') if 'Solar cycle: second split' in final else '（尚未完成）',
    split715=table('Solar cycle: third split') if 'Solar cycle: third split' in final else '（尚未完成）',
) + '\n---\n\n'
body += ns['SEC7_NEGATIVE'] + '\n---\n\n' + ns['SEC8_TODO'] + ns['SEC9_LIMITS'] + ns['SEC10_REPRO'] + '\n---\n\n'
body += ns['APPENDIX_INTRO'] + stage1 + '\n---\n\n' + refs
(root / 'REPORT.md').write_text(body)
print('REPORT.md written', len(body), 'chars;', body.count('尚未完成'), 'pending placeholders')
