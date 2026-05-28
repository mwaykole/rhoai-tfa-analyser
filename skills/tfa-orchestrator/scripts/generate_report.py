#!/usr/bin/env python3
"""Generate a detailed HTML report from TFA classification results.

Usage:
    generate_report.py --results <results.json> --output <report.html> [--launch-id <ID>] [--launch-name <name>]

The results JSON should be an array of classification objects with fields:
    test_id, test_name, classification, severity, confidence,
    root_cause, recommendation, rp_defect_type, suite, key_error, notes
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#65a30d",
}

CLASSIFICATION_COLORS = {
    "product_bug": "#dc2626",
    "infrastructure_issue": "#ea580c",
    "automation_bug": "#2563eb",
    "intermittent": "#7c3aed",
    "to_investigate": "#6b7280",
    "no_defect": "#16a34a",
}

CLASSIFICATION_LABELS = {
    "product_bug": "Product Bug",
    "infrastructure_issue": "Infrastructure Issue",
    "automation_bug": "Test Automation Bug",
    "intermittent": "Intermittent / Flaky",
    "to_investigate": "To Investigate",
    "no_defect": "No Defect",
}


def build_summary(results: list[dict]) -> dict:
    """Build summary statistics from results."""
    by_classification = {}
    by_severity = {}
    by_suite = {}
    for r in results:
        cls = r.get("classification", "to_investigate")
        sev = r.get("severity", "medium")
        suite = r.get("suite", r.get("parent", "Unknown"))
        by_classification[cls] = by_classification.get(cls, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_suite[suite] = by_suite.get(suite, 0) + 1
    return {
        "total": len(results),
        "by_classification": by_classification,
        "by_severity": by_severity,
        "by_suite": by_suite,
    }


def render_html(results: list[dict], launch_id: str = "", launch_name: str = "") -> str:
    """Render results into a standalone HTML report."""
    summary = build_summary(results)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cls_bars = ""
    for cls, count in sorted(summary["by_classification"].items(), key=lambda x: -x[1]):
        pct = (count / summary["total"] * 100) if summary["total"] else 0
        color = CLASSIFICATION_COLORS.get(cls, "#6b7280")
        label = CLASSIFICATION_LABELS.get(cls, cls)
        cls_bars += f"""
        <div class="bar-row">
          <span class="bar-label">{label}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>
          <span class="bar-count">{count}</span>
        </div>"""

    sev_pills = ""
    for sev in ["critical", "high", "medium", "low"]:
        count = summary["by_severity"].get(sev, 0)
        if count:
            color = SEVERITY_COLORS.get(sev, "#6b7280")
            sev_pills += f'<span class="pill" style="background:{color}">{sev.title()}: {count}</span> '

    rows = ""
    for i, r in enumerate(results):
        cls = r.get("classification", "to_investigate")
        cls_color = CLASSIFICATION_COLORS.get(cls, "#6b7280")
        cls_label = CLASSIFICATION_LABELS.get(cls, cls)
        sev = r.get("severity", "medium")
        sev_color = SEVERITY_COLORS.get(sev, "#6b7280")
        conf = r.get("confidence", 0)
        if isinstance(conf, (int, float)):
            conf_pct = f"{conf:.0%}" if conf <= 1 else f"{conf}%"
        else:
            conf_pct = str(conf)
        key_error = r.get("key_error", "")
        notes = r.get("notes", "")
        recommendation = r.get("recommendation", "")
        suite = r.get("suite", r.get("parent", ""))

        detail_rows = ""
        if key_error:
            detail_rows += f'<div class="detail"><strong>Key Error:</strong> <code>{key_error}</code></div>'
        if recommendation:
            detail_rows += f'<div class="detail"><strong>Recommendation:</strong> {recommendation}</div>'
        if notes:
            detail_rows += f'<div class="detail"><strong>Notes:</strong> {notes}</div>'

        rows += f"""
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <span class="test-id">#{r.get('test_id', r.get('id', i+1))}</span>
          <span class="test-name">{r.get('test_name', r.get('name', 'Unknown'))}</span>
        </div>
        <div class="card-badges">
          <span class="badge" style="background:{cls_color}">{cls_label}</span>
          <span class="badge" style="background:{sev_color}">{sev.title()}</span>
          <span class="badge conf">{conf_pct}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="suite-tag">{suite}</div>
        <div class="root-cause">{r.get('root_cause', 'No root cause determined')}</div>
        {detail_rows}
      </div>
    </div>"""

    title = f"TFA Report — Launch {launch_id}" if launch_id else "TFA Analysis Report"
    subtitle = launch_name or ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --bg: #0f172a; --card: #1e293b; --border: #334155; --text: #e2e8f0; --muted: #94a3b8; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 1.5rem; }}
  .summary {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
  .summary-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
  .summary-card h3 {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;
                      color: var(--muted); margin-bottom: 0.75rem; }}
  .big-number {{ font-size: 2.5rem; font-weight: 700; }}
  .pill {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px;
           font-size: 0.75rem; font-weight: 600; color: white; margin: 0.15rem; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.35rem 0; }}
  .bar-label {{ width: 160px; font-size: 0.82rem; text-align: right; color: var(--muted); }}
  .bar-track {{ flex: 1; height: 18px; background: #0f172a; border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s; }}
  .bar-count {{ width: 30px; font-size: 0.82rem; font-weight: 600; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px;
           margin-bottom: 1rem; overflow: hidden; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: flex-start;
                  padding: 1rem 1.25rem; flex-wrap: wrap; gap: 0.5rem; }}
  .card-title {{ display: flex; align-items: baseline; gap: 0.5rem; flex: 1; min-width: 200px; }}
  .test-id {{ color: var(--muted); font-size: 0.82rem; font-weight: 600; }}
  .test-name {{ font-weight: 600; font-size: 0.95rem; }}
  .card-badges {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px;
            font-size: 0.72rem; font-weight: 600; color: white; white-space: nowrap; }}
  .badge.conf {{ background: #475569; }}
  .card-body {{ padding: 0 1.25rem 1.25rem; }}
  .suite-tag {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
                background: #334155; font-size: 0.75rem; color: var(--muted); margin-bottom: 0.5rem; }}
  .root-cause {{ font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.5rem; }}
  .detail {{ font-size: 0.82rem; color: var(--muted); margin-top: 0.4rem; }}
  .detail code {{ background: #0f172a; padding: 0.15rem 0.4rem; border-radius: 4px;
                  font-size: 0.78rem; word-break: break-all; }}
  .footer {{ text-align: center; color: var(--muted); font-size: 0.78rem; margin-top: 2rem;
             padding-top: 1rem; border-top: 1px solid var(--border); }}
  @media (max-width: 700px) {{ .summary {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <div class="subtitle">{subtitle} &mdash; Generated {now}</div>

  <div class="summary">
    <div class="summary-card">
      <h3>Total Failures Analyzed</h3>
      <div class="big-number">{summary['total']}</div>
      <div style="margin-top:0.5rem">{sev_pills}</div>
    </div>
    <div class="summary-card">
      <h3>Classification Breakdown</h3>
      {cls_bars}
    </div>
  </div>

  <h2 style="font-size:1.15rem;margin-bottom:1rem;">Failure Details</h2>
  {rows}

  <div class="footer">
    TFA &mdash; Test Failure Analyzer for RHOAI/ODH &mdash; {now}
  </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate TFA HTML report")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--output", required=True, help="Path to write HTML report")
    parser.add_argument("--launch-id", default="", help="Launch ID for title")
    parser.add_argument("--launch-name", default="", help="Launch name for subtitle")
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    if isinstance(results, dict):
        results = results.get("classified_failures", results.get("failures", [results]))

    html = render_html(results, args.launch_id, args.launch_name)
    Path(args.output).write_text(html)
    print(f"Report written to {args.output}", file=sys.stderr)
    print(args.output)


if __name__ == "__main__":
    main()
