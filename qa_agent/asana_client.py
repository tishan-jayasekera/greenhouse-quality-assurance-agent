"""
qa_agent/asana_client.py — Asana integration for reading task context and posting results.

Reads task data (name, notes, custom fields, parent) to build QAContext,
and posts QA results back as task comments.

Requires ASANA_ACCESS_TOKEN environment variable.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from qa_agent.config import QAContext, QAReport


def _get_client():
    """Lazy-load Asana client."""
    try:
        import asana
    except ImportError:
        raise ImportError("Install asana: pip install asana")

    token = os.environ.get("ASANA_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "ASANA_ACCESS_TOKEN not set. "
            "Get a Personal Access Token from: https://app.asana.com/0/my-apps"
        )
    print(f"DEBUG: asana module path: {getattr(asana, '__file__', 'Unknown')}")
    print(f"DEBUG: asana version: {getattr(asana, '__version__', 'Unknown')}")
    print(f"DEBUG: asana dir: {dir(asana)}")
    
    client = asana.Client.access_token(token)
    client.headers = {"asana-enable": "new_memberships,new_goal_memberships"}
    return client


def _extract_urls_from_text(text: str) -> list[str]:
    """Pull all URLs from a text block."""
    return re.findall(r'https?://[^\s<>"\')\]]+', text)


def _find_url_by_pattern(urls: list[str], patterns: list[str]) -> Optional[str]:
    """Find first URL matching any of the given patterns."""
    for url in urls:
        for p in patterns:
            if p in url.lower():
                return url
    return None


def build_context_from_task(task_gid: str) -> QAContext:
    """
    Read an Asana task and extract QAContext.

    Looks for URLs in Notes to identify:
    - Landing page URL (unbounce, instapage, or first non-internal URL)
    - Figma URL
    - Copy doc URL (Google Docs)

    Also reads custom fields if available.
    """
    client = _get_client()
    task = client.tasks.get_task(
        task_gid,
        opt_fields=[
            "name", "notes", "custom_fields", "parent.name",
            "memberships.section.name", "memberships.project.name",
        ],
    )

    name = task.get("name", "")
    notes = task.get("notes", "")
    all_text = f"{name}\n{notes}"
    urls = _extract_urls_from_text(all_text)

    # Identify key URLs
    lp_url = _find_url_by_pattern(urls, [
        "unbounce", "instapage", "leadpages", "landingi",
    ])
    if not lp_url:
        # Fall back to first URL that looks like a landing page (not internal tools)
        internal = ["asana.com", "figma.com", "docs.google", "drive.google",
                     "slack.com", "whimsical.com", "canva.com"]
        for url in urls:
            if not any(i in url.lower() for i in internal):
                lp_url = url
                break

    figma_url = _find_url_by_pattern(urls, ["figma.com"])
    copy_doc_url = _find_url_by_pattern(urls, ["docs.google.com"])

    # Extract client/campaign from parent task or custom fields
    parent_name = ""
    if task.get("parent"):
        parent_name = task["parent"].get("name", "")

    client_name = None
    campaign_name = None
    for cf in task.get("custom_fields", []):
        cf_name = (cf.get("name") or "").lower()
        cf_val = cf.get("display_value") or cf.get("text_value") or ""
        if "client" in cf_name:
            client_name = cf_val
        elif "campaign" in cf_name or "project" in cf_name:
            campaign_name = cf_val

    if not campaign_name:
        campaign_name = parent_name or name

    return QAContext(
        landing_page_url=lp_url or "",
        figma_url=figma_url,
        copy_doc_url=copy_doc_url,
        campaign_name=campaign_name,
        client_name=client_name,
        asana_task_id=task_gid,
    )


def post_results(report: QAReport) -> str:
    """
    Post QA results back to the Asana task as a comment.

    Returns the comment GID.
    """
    if not report.context.asana_task_id:
        raise ValueError("No Asana task ID in report context.")

    from qa_agent.reporter import to_asana_comment
    comment_text = to_asana_comment(report)

    client = _get_client()
    result = client.tasks.add_comment(
        report.context.asana_task_id,
        {"text": comment_text},
    )
    return result.get("gid", "")


def get_qa_tasks(project_gid: str, section_name: str = "QA") -> list[dict]:
    """
    List tasks in a specific section of an Asana project.
    Useful for batch-running QA on all tasks that reach the QA stage.
    """
    client = _get_client()

    # Find the section
    sections = list(client.sections.get_sections_for_project(project_gid))
    target_section = None
    for sec in sections:
        if section_name.lower() in sec["name"].lower():
            target_section = sec
            break

    if not target_section:
        available = [s["name"] for s in sections]
        raise ValueError(f"Section '{section_name}' not found. Available: {available}")

    # Get tasks in section
    tasks = list(client.tasks.get_tasks(
        {"section": target_section["gid"]},
        opt_fields=["name", "completed", "gid"],
    ))
    return [t for t in tasks if not t.get("completed")]
