"""
qa_agent/cli.py — Command-line interface for the QA agent.

Usage:
    # Run against a URL directly
    python -m qa_agent.cli run https://example.com/landing-page

    # Run against an Asana task (extracts URL from task Notes)
    python -m qa_agent.cli asana TASK_GID

    # Run against all tasks in a project's QA section
    python -m qa_agent.cli batch PROJECT_GID --section "QA"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from qa_agent.config import QAContext, QAReport, OUTPUT_DIR
from qa_agent.crawler import crawl_page
from qa_agent.checks import run_all
from qa_agent.reporter import print_terminal, to_markdown, to_asana_comment


def run_qa(
    url: str,
    client_name: str | None = None,
    campaign_name: str | None = None,
    figma_url: str | None = None,
    copy_doc_url: str | None = None,
    expected_cta_text: str | None = None,
    thank_you_url: str | None = None,
    form_id: str = "lp-pom-form-42",
    output_dir: str | None = None,
    screenshots: bool = True,
    post_to_asana: bool = False,
    asana_task_id: str | None = None,
) -> QAReport:
    """
    Core QA run: crawl a page, run all checks, generate report.
    This is the function to call programmatically.
    """
    context = QAContext(
        landing_page_url=url,
        figma_url=figma_url,
        copy_doc_url=copy_doc_url,
        campaign_name=campaign_name,
        client_name=client_name,
        asana_task_id=asana_task_id,
        expected_form_id=form_id,
        expected_cta_text=expected_cta_text,
        thank_you_url=thank_you_url,
    )

    out_dir = output_dir or OUTPUT_DIR
    print(f"\n🔍 Crawling {url} ...")
    snapshot = asyncio.run(crawl_page(url, output_dir=out_dir, capture_screenshots=screenshots))
    print(f"   Page loaded in {snapshot.load_time_ms}ms | Status: {snapshot.status_code}")
    print(f"   Images: {len(snapshot.images)} | Forms: {len(snapshot.forms)} | "
          f"Scripts: {len(snapshot.scripts)} | Console errors: {len(snapshot.console_errors)}")

    print(f"\n🧪 Running checks ...")
    results = run_all(snapshot, context)

    report = QAReport(context=context, results=results)
    report.build_summary()

    # Terminal output
    print_terminal(report)

    # Save markdown report
    md_path = to_markdown(report, out_dir)
    print(f"📄 Report saved: {md_path}")

    # Save JSON (machine-readable)
    json_path = Path(out_dir) / f"qa_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_data = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "summary": report.summary,
        "results": [
            {
                "check_id": r.check_id,
                "name": r.name,
                "category": r.category,
                "status": r.status.value,
                "message": r.message,
                "evidence": r.evidence,
            }
            for r in report.results
        ],
    }
    json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    print(f"📊 JSON results: {json_path}")

    # Post to Asana if requested
    if post_to_asana and asana_task_id:
        try:
            from qa_agent.asana_client import post_results
            gid = post_results(report)
            print(f"✅ Posted to Asana task comment: {gid}")
        except Exception as e:
            print(f"⚠️  Failed to post to Asana: {e}")

    return report


def cmd_run(args):
    """Handle the 'run' subcommand."""
    report = run_qa(
        url=args.url,
        client_name=args.client,
        campaign_name=args.campaign,
        figma_url=args.figma,
        copy_doc_url=args.copy_doc,
        expected_cta_text=args.cta_text,
        thank_you_url=args.thank_you_url,
        form_id=args.form_id,
        output_dir=args.output,
        screenshots=not args.no_screenshots,
        post_to_asana=args.post,
        asana_task_id=args.asana_task_id,
    )

    # Exit code based on failures
    if report.failed:
        sys.exit(1)
    sys.exit(0)


def cmd_asana(args):
    """Handle the 'asana' subcommand — run QA from an Asana task."""
    from qa_agent.asana_client import build_context_from_task
    ctx = build_context_from_task(args.task_gid)

    if not ctx.landing_page_url:
        print(f"❌ No landing page URL found in Asana task {args.task_gid}.")
        print("   Add the LP URL to the task Notes or use `run` with an explicit URL.")
        sys.exit(1)

    print(f"📋 Asana task: {ctx.campaign_name or args.task_gid}")
    print(f"   LP: {ctx.landing_page_url}")
    if ctx.figma_url:
        print(f"   Figma: {ctx.figma_url[:60]}")
    if ctx.copy_doc_url:
        print(f"   Copy doc: {ctx.copy_doc_url[:60]}")

    report = run_qa(
        url=ctx.landing_page_url,
        client_name=ctx.client_name,
        campaign_name=ctx.campaign_name,
        figma_url=ctx.figma_url,
        copy_doc_url=ctx.copy_doc_url,
        asana_task_id=args.task_gid,
        output_dir=args.output,
        post_to_asana=args.post,
    )

    if report.failed:
        sys.exit(1)
    sys.exit(0)


def cmd_batch(args):
    """Handle the 'batch' subcommand — run QA on all tasks in a section."""
    from qa_agent.asana_client import get_qa_tasks, build_context_from_task

    print(f"🔎 Finding tasks in section '{args.section}' of project {args.project_gid}...")
    tasks = get_qa_tasks(args.project_gid, args.section)
    print(f"   Found {len(tasks)} incomplete tasks.")

    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*60}")
        print(f"  Task {i}/{len(tasks)}: {task['name']}")
        print(f"{'='*60}")
        try:
            ctx = build_context_from_task(task["gid"])
            if not ctx.landing_page_url:
                print(f"   ⏭️ No LP URL found, skipping.")
                continue
            run_qa(
                url=ctx.landing_page_url,
                client_name=ctx.client_name,
                campaign_name=ctx.campaign_name,
                figma_url=ctx.figma_url,
                copy_doc_url=ctx.copy_doc_url,
                asana_task_id=task["gid"],
                output_dir=args.output,
                post_to_asana=args.post,
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Social Garden QA Checklist Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run https://example.com/landing-page
  %(prog)s run https://example.com/lp --client "Acme Corp" --campaign "Summer 2025"
  %(prog)s asana 1234567890 --post
  %(prog)s batch 9876543210 --section "🔁 Final QA"
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── run ──
    p_run = subparsers.add_parser("run", help="Run QA against a URL")
    p_run.add_argument("url", help="Landing page URL to check")
    p_run.add_argument("--client", help="Client name")
    p_run.add_argument("--campaign", help="Campaign name")
    p_run.add_argument("--figma", help="Figma design URL for comparison")
    p_run.add_argument("--copy-doc", help="Google Doc URL with approved copy")
    p_run.add_argument("--cta-text", help="Expected CTA button text")
    p_run.add_argument("--thank-you-url", help="Expected thank-you page URL")
    p_run.add_argument("--form-id", default="lp-pom-form-42", help="Expected form element ID")
    p_run.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory")
    p_run.add_argument("--no-screenshots", action="store_true", help="Skip screenshot capture")
    p_run.add_argument("--post", action="store_true", help="Post results back to Asana")
    p_run.add_argument("--asana-task-id", help="Asana task GID to post results to")
    p_run.set_defaults(func=cmd_run)

    # ── asana ──
    p_asana = subparsers.add_parser("asana", help="Run QA from an Asana task")
    p_asana.add_argument("task_gid", help="Asana task GID")
    p_asana.add_argument("--client", help="Override client name")
    p_asana.add_argument("--campaign", help="Override campaign name")
    p_asana.add_argument("--cta-text", help="Expected CTA button text")
    p_asana.add_argument("--form-id", default="lp-pom-form-42", help="Expected form element ID")
    p_asana.add_argument("--post", action="store_true", help="Post results back to Asana")
    p_asana.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory")
    p_asana.set_defaults(func=cmd_asana)

    # ── batch ──
    p_batch = subparsers.add_parser("batch", help="Run QA on all tasks in a project section")
    p_batch.add_argument("project_gid", help="Asana project GID")
    p_batch.add_argument("--section", default="QA", help="Section name to scan (default: QA)")
    p_batch.add_argument("--post", action="store_true", help="Post results back to Asana")
    p_batch.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory")
    p_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
