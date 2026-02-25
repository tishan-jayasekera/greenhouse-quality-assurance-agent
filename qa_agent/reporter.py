"""
qa_agent/reporter.py — Format QA results for terminal + markdown + Asana.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from qa_agent.config import CheckResult, CheckStatus, QAReport, OUTPUT_DIR


STATUS_ICONS = {
    CheckStatus.PASS: "✅",
    CheckStatus.FAIL: "❌",
    CheckStatus.WARN: "⚠️",
    CheckStatus.SKIP: "⏭️",
}

STATUS_COLORS = {
    CheckStatus.PASS: "\033[92m",  # green
    CheckStatus.FAIL: "\033[91m",  # red
    CheckStatus.WARN: "\033[93m",  # yellow
    CheckStatus.SKIP: "\033[90m",  # grey
}
RESET = "\033[0m"


def print_terminal(report: QAReport) -> None:
    """Print a formatted summary to the terminal."""
    report.build_summary()
    s = report.summary

    print()
    print("=" * 70)
    print(f"  QA REPORT — {report.context.landing_page_url}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    print()
    print(f"  TOTAL: {s['total']}  |  "
          f"✅ {s['passed']}  ❌ {s['failed']}  ⚠️ {s['warnings']}  ⏭️ {s['skipped']}")
    print(f"  Pass rate: {s['pass_rate']}")
    print()

    # By category
    for cat, cat_data in s["by_category"].items():
        print(f"  ── {cat.upper()} ({cat_data['total']} checks) ──")
        cat_results = [r for r in report.results if r.category == cat]
        for r in cat_results:
            icon = STATUS_ICONS[r.status]
            color = STATUS_COLORS[r.status]
            print(f"    {icon} {color}{r.name}{RESET}")
            print(f"       {r.message[:120]}")
            if r.evidence and r.status != CheckStatus.PASS:
                for line in r.evidence.split("\n")[:3]:
                    print(f"       → {line[:100]}")
        print()

    # Failures summary
    if report.failed:
        print("  🚨 FAILURES REQUIRING ACTION:")
        for r in report.failed:
            print(f"    ❌ [{r.category}] {r.name}: {r.message[:100]}")
        print()


def to_markdown(report: QAReport, output_dir: str | None = None) -> str:
    """Generate a markdown report file. Returns the file path."""
    report.build_summary()
    s = report.summary
    out = Path(output_dir or OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# QA Report",
        f"",
        f"**URL:** {report.context.landing_page_url}",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Client:** {report.context.client_name or 'N/A'}",
        f"**Campaign:** {report.context.campaign_name or 'N/A'}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total checks | {s['total']} |",
        f"| ✅ Passed | {s['passed']} |",
        f"| ❌ Failed | {s['failed']} |",
        f"| ⚠️ Warnings | {s['warnings']} |",
        f"| ⏭️ Skipped | {s['skipped']} |",
        f"| **Pass rate** | **{s['pass_rate']}** |",
        f"",
    ]

    # Failures first
    if report.failed:
        lines.append("## ❌ Failures (Action Required)")
        lines.append("")
        for r in report.failed:
            lines.append(f"### {r.name}")
            lines.append(f"**Category:** {r.category} | **Check ID:** `{r.check_id}`")
            lines.append(f"")
            lines.append(r.message)
            if r.evidence:
                lines.append(f"```")
                lines.append(r.evidence[:500])
                lines.append(f"```")
            lines.append("")

    # Warnings
    if report.warnings:
        lines.append("## ⚠️ Warnings (Review Recommended)")
        lines.append("")
        for r in report.warnings:
            lines.append(f"- **{r.name}** ({r.category}): {r.message[:150]}")
        lines.append("")

    # Passes
    lines.append("## ✅ Passed")
    lines.append("")
    for r in report.passed:
        lines.append(f"- **{r.name}** ({r.category}): {r.message[:120]}")
    lines.append("")

    # Skipped
    if report.skipped:
        lines.append("## ⏭️ Skipped (Manual or Future Phase)")
        lines.append("")
        for r in report.skipped:
            lines.append(f"- **{r.name}** ({r.category}): {r.message[:120]}")
        lines.append("")

    content = "\n".join(lines)
    filepath = out / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def to_asana_comment(report: QAReport) -> str:
    """Format results as an Asana task comment (plain text, compact)."""
    report.build_summary()
    s = report.summary

    lines = [
        f"🤖 QA Agent Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"URL: {report.context.landing_page_url}",
        f"",
        f"Results: ✅ {s['passed']} | ❌ {s['failed']} | ⚠️ {s['warnings']} | ⏭️ {s['skipped']}",
        f"Pass rate: {s['pass_rate']}",
    ]

    if report.failed:
        lines.append(f"")
        lines.append(f"── FAILURES ──")
        for r in report.failed:
            lines.append(f"❌ [{r.category}] {r.name}")
            lines.append(f"   {r.message[:150]}")

    if report.warnings:
        lines.append(f"")
        lines.append(f"── WARNINGS ({len(report.warnings)}) ──")
        for r in report.warnings[:10]:
            lines.append(f"⚠️ {r.name}: {r.message[:100]}")
        if len(report.warnings) > 10:
            lines.append(f"   ... and {len(report.warnings) - 10} more warnings")

    lines.append(f"")
    lines.append(f"Full report saved. Run `qa-agent report` for details.")

    return "\n".join(lines)
