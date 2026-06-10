#!/usr/bin/env python3
"""Generate a detailed component-specific HTML report with collapsible sections and index.

Usage:
    generate_report.py --results <results.json> --output <report.html> [--launch-id <ID>] [--launch-name <name>]

The results JSON should be an array of classification objects with fields:
    test_id, test_name, classification, severity, confidence,
    root_cause, recommendation, rp_defect_type, suite, key_error, notes
"""

import argparse
import html as html_lib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#65a30d",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

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


def esc(text: str) -> str:
    return html_lib.escape(str(text)) if text else ""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_summary(results: list[dict]) -> dict:
    by_classification: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_suite: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        cls = r.get("classification", "to_investigate")
        sev = r.get("severity", "medium")
        suite = r.get("suite", r.get("parent", r.get("launch_name", "Unknown")))
        if not suite:
            suite = "Uncategorized"
        by_classification[cls] = by_classification.get(cls, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_suite[suite].append(r)
    return {
        "total": len(results),
        "by_classification": by_classification,
        "by_severity": by_severity,
        "by_suite": dict(by_suite),
    }


def render_html(results: list[dict], launch_id: str = "", launch_name: str = "") -> str:
    summary = build_summary(results)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    suites_sorted: list[tuple[str, list[dict]]] = sorted(
        summary["by_suite"].items(), key=lambda x: -len(x[1])
    )

    # --- Summary bars ---
    cls_bars = ""
    for cls, count in sorted(summary["by_classification"].items(), key=lambda x: -x[1]):
        pct = (count / summary["total"] * 100) if summary["total"] else 0
        color = CLASSIFICATION_COLORS.get(cls, "#6b7280")
        label = CLASSIFICATION_LABELS.get(cls, cls)
        cls_bars += f"""
        <div class="bar-row">
          <span class="bar-label">{esc(label)}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>
          <span class="bar-count">{count}</span>
        </div>"""

    sev_pills_html = ""
    for sev in ["critical", "high", "medium", "low"]:
        count = summary["by_severity"].get(sev, 0)
        if count:
            color = SEVERITY_COLORS.get(sev, "#6b7280")
            sev_pills_html += f'<span class="pill" style="background:{color}">{sev.title()}: {count}</span> '

    # --- Sidebar index ---
    index_items = ""
    for suite_name, failures in suites_sorted:
        sid = slug(suite_name)
        suite_cls: dict[str, int] = {}
        for f in failures:
            c = f.get("classification", "to_investigate")
            suite_cls[c] = suite_cls.get(c, 0) + 1
        dom_cls = max(suite_cls, key=suite_cls.get) if suite_cls else "to_investigate"
        dom_color = CLASSIFICATION_COLORS.get(dom_cls, "#6b7280")
        index_items += f"""
      <a href="#sect-{sid}" class="idx-item" onclick="openSection('{sid}')">
        <span class="idx-dot" style="background:{dom_color}"></span>
        <span class="idx-name">{esc(suite_name)}</span>
        <span class="idx-count">{len(failures)}</span>
      </a>"""

    # --- Per-component collapsible sections ---
    comp_sections = ""
    for suite_name, failures in suites_sorted:
        sid = slug(suite_name)
        suite_cls: dict[str, int] = {}
        suite_sev: dict[str, int] = {}
        for f in failures:
            c = f.get("classification", "to_investigate")
            s = f.get("severity", "medium")
            suite_cls[c] = suite_cls.get(c, 0) + 1
            suite_sev[s] = suite_sev.get(s, 0) + 1

        dom_cls = max(suite_cls, key=suite_cls.get) if suite_cls else "to_investigate"
        dom_color = CLASSIFICATION_COLORS.get(dom_cls, "#6b7280")
        dom_label = CLASSIFICATION_LABELS.get(dom_cls, dom_cls)
        worst_sev = min(suite_sev.keys(), key=lambda x: SEVERITY_ORDER.get(x, 9)) if suite_sev else "medium"
        worst_sev_color = SEVERITY_COLORS.get(worst_sev, "#6b7280")

        comp_pills = ""
        for cls, cnt in sorted(suite_cls.items(), key=lambda x: -x[1]):
            color = CLASSIFICATION_COLORS.get(cls, "#6b7280")
            label = CLASSIFICATION_LABELS.get(cls, cls)
            comp_pills += f'<span class="pill" style="background:{color}">{esc(label)}: {cnt}</span> '

        sev_pills = ""
        for sev in ["critical", "high", "medium", "low"]:
            cnt = suite_sev.get(sev, 0)
            if cnt:
                color = SEVERITY_COLORS.get(sev, "#6b7280")
                sev_pills += f'<span class="pill" style="background:{color}">{sev.title()}: {cnt}</span> '

        sorted_failures = sorted(
            failures, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium"), 9)
        )

        failure_cards = ""
        for i, r in enumerate(sorted_failures):
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
            recommendation = r.get("recommendation", "")
            notes = r.get("notes", "")
            root_cause = r.get("root_cause", "No root cause determined")

            detail_rows = ""
            if key_error:
                detail_rows += f'<div class="detail"><strong>Key Error:</strong> <code>{esc(key_error)}</code></div>'
            if recommendation:
                detail_rows += f'<div class="detail"><strong>Recommendation:</strong> {esc(recommendation)}</div>'
            if notes:
                detail_rows += f'<div class="detail"><strong>Notes:</strong> {esc(notes)}</div>'

            test_id = esc(str(r.get("test_id", r.get("id", i + 1))))
            test_name = esc(r.get("test_name", r.get("name", "Unknown")))

            failure_cards += f"""
        <details class="failure-item">
          <summary class="failure-summary">
            <div class="failure-left">
              <span class="test-id">#{test_id}</span>
              <span class="test-name">{test_name}</span>
            </div>
            <div class="card-badges">
              <span class="badge" style="background:{cls_color}">{esc(cls_label)}</span>
              <span class="badge" style="background:{sev_color}">{sev.title()}</span>
              <span class="badge conf">{conf_pct}</span>
            </div>
          </summary>
          <div class="failure-body">
            <div class="root-cause">{esc(root_cause)}</div>
            {detail_rows}
          </div>
        </details>"""

        comp_sections += f"""
    <details class="comp-section" id="sect-{sid}">
      <summary class="comp-toggle">
        <div class="comp-toggle-left">
          <span class="comp-dot-lg" style="background:{dom_color}"></span>
          <span class="comp-title">{esc(suite_name)}</span>
          <span class="comp-count-badge" style="border-color:{worst_sev_color};color:{worst_sev_color}">{len(failures)}</span>
        </div>
        <div class="comp-toggle-right">
          {sev_pills}
        </div>
      </summary>
      <div class="comp-body">
        <div class="comp-cls-row">{comp_pills}</div>
        {failure_cards}
      </div>
    </details>"""

    title = f"TFA Report &mdash; Launch {esc(launch_id)}" if launch_id else "TFA Analysis Report"
    subtitle = esc(launch_name) or ""

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
         background: var(--bg); color: var(--text); line-height: 1.6; }}

  /* Layout: sidebar + main */
  .layout {{ display: flex; min-height: 100vh; }}

  /* Sidebar index */
  .sidebar {{ width: 240px; flex-shrink: 0; background: #0b1120; border-right: 1px solid var(--border);
              position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 1rem 0; }}
  .sidebar-title {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em;
                    color: var(--muted); padding: 0 1rem; margin-bottom: 0.75rem; font-weight: 600; }}
  .idx-item {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem;
               text-decoration: none; color: var(--text); font-size: 0.8rem;
               transition: background 0.15s; border-left: 2px solid transparent; }}
  .idx-item:hover {{ background: rgba(255,255,255,0.04); }}
  .idx-item.active {{ background: rgba(96,165,250,0.08); border-left-color: #60a5fa; }}
  .idx-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
  .idx-name {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .idx-count {{ font-weight: 700; font-size: 0.72rem; color: var(--muted); }}

  .sidebar-actions {{ padding: 0.75rem 1rem; border-top: 1px solid var(--border); margin-top: 0.5rem; }}
  .btn-sm {{ display: inline-block; padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.72rem;
             font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: var(--card);
             color: var(--text); margin-right: 0.35rem; }}
  .btn-sm:hover {{ border-color: #60a5fa; }}

  /* Main content */
  .main {{ flex: 1; padding: 2rem; max-width: 900px; }}
  h1 {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 0.2rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.88rem; margin-bottom: 1.5rem; }}
  .summary {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 2rem; }}
  .summary-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.1rem; }}
  .summary-card h3 {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em;
                      color: var(--muted); margin-bottom: 0.6rem; }}
  .big-number {{ font-size: 2.2rem; font-weight: 700; }}
  .pill {{ display: inline-block; padding: 0.18rem 0.55rem; border-radius: 9999px;
           font-size: 0.68rem; font-weight: 600; color: white; margin: 0.1rem; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }}
  .bar-label {{ width: 150px; font-size: 0.78rem; text-align: right; color: var(--muted); }}
  .bar-track {{ flex: 1; height: 16px; background: #0f172a; border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; }}
  .bar-count {{ width: 32px; font-size: 0.78rem; font-weight: 600; }}

  /* Component sections (collapsible) */
  .comp-section {{ border: 1px solid var(--border); border-radius: 10px; margin-bottom: 0.75rem;
                   background: var(--card); }}
  .comp-toggle {{ display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem;
                  cursor: pointer; list-style: none; flex-wrap: wrap; gap: 0.5rem; }}
  .comp-toggle::-webkit-details-marker {{ display: none; }}
  .comp-toggle-left {{ display: flex; align-items: center; gap: 0.6rem; }}
  .comp-toggle-right {{ display: flex; flex-wrap: wrap; gap: 0.2rem; }}
  .comp-dot-lg {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
  .comp-title {{ font-size: 0.95rem; font-weight: 700; }}
  .comp-count-badge {{ font-weight: 700; font-size: 0.72rem; padding: 0.1rem 0.4rem;
                       border: 1.5px solid; border-radius: 5px; }}
  .comp-section[open] .comp-toggle {{ border-bottom: 1px solid var(--border); }}
  .comp-body {{ padding: 0.75rem 1rem 1rem; }}
  .comp-cls-row {{ margin-bottom: 0.75rem; }}

  /* Individual failure items (nested collapsible) */
  .failure-item {{ border: 1px solid var(--border); border-radius: 8px; margin-bottom: 0.5rem;
                   background: var(--bg); }}
  .failure-summary {{ display: flex; justify-content: space-between; align-items: flex-start;
                      padding: 0.65rem 0.9rem; cursor: pointer; list-style: none;
                      flex-wrap: wrap; gap: 0.4rem; }}
  .failure-summary::-webkit-details-marker {{ display: none; }}
  .failure-left {{ display: flex; align-items: baseline; gap: 0.4rem; flex: 1; min-width: 200px; }}
  .test-id {{ color: var(--muted); font-size: 0.72rem; font-weight: 600; }}
  .test-name {{ font-weight: 600; font-size: 0.82rem; }}
  .card-badges {{ display: flex; gap: 0.3rem; flex-wrap: wrap; }}
  .badge {{ display: inline-block; padding: 0.12rem 0.45rem; border-radius: 5px;
            font-size: 0.65rem; font-weight: 600; color: white; white-space: nowrap; }}
  .badge.conf {{ background: #475569; }}
  .failure-item[open] .failure-summary {{ border-bottom: 1px solid var(--border); }}
  .failure-body {{ padding: 0.75rem 0.9rem; }}
  .root-cause {{ font-size: 0.82rem; line-height: 1.55; margin-bottom: 0.4rem; }}
  .detail {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.3rem; }}
  .detail code {{ background: var(--card); padding: 0.1rem 0.3rem; border-radius: 4px;
                  font-size: 0.72rem; word-break: break-all; }}

  .footer {{ text-align: center; color: var(--muted); font-size: 0.72rem; margin-top: 2rem;
             padding-top: 0.75rem; border-top: 1px solid var(--border); }}

  /* Chevron indicators */
  .comp-toggle::before {{ content: "\\25B6"; font-size: 0.6rem; color: var(--muted);
                          transition: transform 0.2s; flex-shrink: 0; }}
  .comp-section[open] > .comp-toggle::before {{ transform: rotate(90deg); }}
  .failure-summary::before {{ content: "\\25B6"; font-size: 0.5rem; color: var(--muted);
                              transition: transform 0.2s; flex-shrink: 0; margin-top: 0.2rem; }}
  .failure-item[open] > .failure-summary::before {{ transform: rotate(90deg); }}

  @media (max-width: 800px) {{
    .sidebar {{ display: none; }}
    .summary {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="layout">

  <nav class="sidebar">
    <div class="sidebar-title">Components ({len(suites_sorted)})</div>
    {index_items}
    <div class="sidebar-actions">
      <span class="btn-sm" onclick="toggleAll(true)">Expand All</span>
      <span class="btn-sm" onclick="toggleAll(false)">Collapse All</span>
    </div>
  </nav>

  <div class="main">
    <h1>{title}</h1>
    <div class="subtitle">{subtitle} &mdash; Generated {now}</div>

    <div class="summary">
      <div class="summary-card">
        <h3>Total Failures</h3>
        <div class="big-number">{summary['total']}</div>
        <div style="margin-top:0.4rem">{sev_pills_html}</div>
        <div style="margin-top:0.3rem;font-size:0.78rem;color:var(--muted)">{len(suites_sorted)} components</div>
      </div>
      <div class="summary-card">
        <h3>Classification Breakdown</h3>
        {cls_bars}
      </div>
    </div>

    {comp_sections}

    <div class="footer">
      TFA &mdash; Test Failure Analyzer for RHOAI/ODH &mdash; {now}
    </div>
  </div>

</div>

<script>
function openSection(sid) {{
  const el = document.getElementById('sect-' + sid);
  if (el && !el.open) el.open = true;
  document.querySelectorAll('.idx-item').forEach(a => a.classList.remove('active'));
  event.currentTarget.classList.add('active');
}}

function toggleAll(open) {{
  document.querySelectorAll('.comp-section').forEach(d => d.open = open);
  if (open) document.querySelectorAll('.failure-item').forEach(d => d.open = true);
  else document.querySelectorAll('.failure-item').forEach(d => d.open = false);
}}

const observer = new IntersectionObserver(entries => {{
  entries.forEach(entry => {{
    if (entry.isIntersecting) {{
      const id = entry.target.id;
      document.querySelectorAll('.idx-item').forEach(a => {{
        a.classList.toggle('active', a.getAttribute('href') === '#' + id);
      }});
    }}
  }});
}}, {{ threshold: 0.1, rootMargin: '-80px 0px -60% 0px' }});

document.querySelectorAll('.comp-section').forEach(s => observer.observe(s));
</script>
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
