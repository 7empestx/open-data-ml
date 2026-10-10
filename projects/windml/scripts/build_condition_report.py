"""Assemble reports/condition_report/condition_report.md from src/template.md + computed tables, then render the PDF
(python-markdown -> HTML with print CSS -> headless Chrome --print-to-pdf)."""
import json
import re
import subprocess
from pathlib import Path
import markdown

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
R = cfg.REPORTS_DIR / "condition_report"
T = R / "tables"

CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
  @bottom-center { content: counter(page); } }
body { font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1d2733; }
h1 { font-size: 20pt; color: #12324d; border-bottom: 3px solid #12324d; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 14pt; color: #12324d; border-bottom: 1px solid #b8c4d0; padding-bottom: 2px; margin-top: 20px; break-after: avoid; }
h3 { font-size: 11.5pt; color: #1f4e79; margin-top: 14px; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
blockquote { border-left: 4px solid #c0504d; background: #fbf1f0; margin: 10px 0; padding: 6px 12px; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; margin: 8px 0 12px 0; break-inside: auto; }
th { background: #12324d; color: white; text-align: left; padding: 3px 4px; font-weight: 600; }
td { border-bottom: 1px solid #d5dde5; padding: 2.5px 4px; vertical-align: top; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #f5f8fb; }
img { max-width: 100%; display: block; margin: 8px auto 2px auto; break-inside: avoid; }
code { font-size: 8pt; background: #eef2f6; padding: 0 2px; }
strong { color: #10263a; }
.flag-RED { color: #fff; background: #c0392b; padding: 0 4px; border-radius: 2px; font-weight: bold; }
.flag-AMBER { color: #1d2733; background: #f5b041; padding: 0 4px; border-radius: 2px; font-weight: bold; }
.flag-GREEN { color: #fff; background: #27ae60; padding: 0 4px; border-radius: 2px; font-weight: bold; }
"""


def for_html(md: str) -> str:
    """python-markdown needs a blank line before a list and 4-space indents for nested items (GitHub does not)."""
    out, prev = [], ""
    for line in md.split("\n"):
        m = re.match(r"^( *)([-*]|\d+\.) ", line)
        if m:
            ind = len(m.group(1))
            line = " " * (ind * 2) + line[ind:]
            if prev.strip() and not re.match(r"^ *([-*]|\d+\.) ", prev):
                out.append("")
        out.append(line); prev = line
    return "\n".join(out)


def main():
    t = (cfg.CONDITION_TEMPLATE_DIR / "template.md").read_text()
    h = json.loads((T / "headline.json").read_text())
    k, p = h["kelmarsh"], h["penmanshiel"]
    import pandas as pd
    dt = pd.read_csv(T / "downtime_by_cause.csv")
    kk = dt[(dt.farm == "kelmarsh") & (dt.year >= 2021) & (dt.cause.str.startswith("fault") | (dt.cause == "maintenance"))]
    s = kk.groupby("turbine_id")["hours"].sum()
    vals = {
        "k_avail": f"{k['avail_time_mean']:.1%}", "k_eavail": f"{k['avail_energy_all']:.1%}",
        "k_conc": f"{s[['KEL04', 'KEL05', 'KEL06']].sum() / s.sum():.0%}",
        "k_lost": f"{k['lost_gwh'] * 1000:,.0f}", "k_maint_share": f"{k['maint_share_lost']:.1%}",
        "p_avail": f"{p['avail_time_mean']:.1%}", "p_eavail": f"{p['avail_energy_all']:.1%}", "p_lost": f"{p['lost_gwh'] * 1000:,.0f}",
        "k_ty": f"{k['turbine_years']:.0f}", "p_ty": f"{p['turbine_years']:.0f}",
    }
    for f in T.glob("*.md"):
        vals[f.stem] = f.read_text().strip()
    md = re.sub(r"\{(\w+)\}", lambda m: vals[m.group(1)] if m.group(1) in vals else m.group(0), t)
    left = re.findall(r"\{(\w+)\}", md)
    assert not left, left
    assert "\u2014" not in md and "\u2013" not in md, "dash found"
    (R / "condition_report.md").write_text(md)
    html = markdown.markdown(for_html(md), extensions=["tables", "sane_lists"])
    html = re.sub(r"<strong>(RED|AMBER|GREEN)</strong>", r'<span class="flag-\1">\1</span>', html)
    html = re.sub(r"<td>(RED|AMBER|GREEN)</td>", r'<td><span class="flag-\1">\1</span></td>', html)
    html = html.replace('src="figures/', 'src="../figures/')
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>Wind Farm Condition Report (sample)</title><style>{CSS}</style></head><body>{html}</body></html>"
    (R / "src").mkdir(parents=True, exist_ok=True)
    (R / "src/condition_report.html").write_text(doc)
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={R / 'condition_report.pdf'}", (R / "src/condition_report.html").as_uri()],
                   check=True, capture_output=True, timeout=120)
    print("wrote", R / "condition_report.pdf")


if __name__ == "__main__":
    main()
