"""
qa_agent/config.py — Configuration and data models for the QA agent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import os


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Result of a single QA check."""
    check_id: str
    name: str
    category: str          # "developer" | "designer" | "copywriter"
    status: CheckStatus
    message: str
    evidence: Optional[str] = None   # DOM snippet, URL, or detail
    screenshot: Optional[str] = None # path to screenshot if captured


@dataclass
class PageSnapshot:
    """Everything we extract from a single page crawl."""
    url: str
    final_url: str                           # after redirects
    title: str
    meta_title: str
    status_code: int
    console_errors: list[dict]               # {type, text, url, line}
    console_warnings: list[dict]
    network_requests: list[dict]             # {url, method, status, resource_type, size}
    fonts_loaded: list[str]                  # font family names from CSS
    images: list[dict]                       # {src, format, width, height, naturalWidth, alt}
    links: list[dict]                        # {href, text, target, tag}
    forms: list[dict]                        # {id, action, fields: [{name, type, placeholder, required}]}
    scripts: list[dict]                      # {src, inline_length}
    sticky_elements: list[dict]              # {selector, text, viewport}
    dom_html: str                            # full page HTML for deeper inspection
    mobile_snapshot: Optional[dict] = None   # same structure but at mobile viewport
    compression: Optional[str] = None        # "gzip" | "br" | None
    screenshot_desktop: Optional[str] = None
    screenshot_mobile: Optional[str] = None
    redirect_chain: list[str] = field(default_factory=list)
    page_size_bytes: int = 0
    load_time_ms: int = 0


@dataclass
class QAContext:
    """Context passed to the QA run — what we know about this task."""
    landing_page_url: str
    figma_url: Optional[str] = None
    copy_doc_url: Optional[str] = None
    campaign_name: Optional[str] = None
    client_name: Optional[str] = None
    asana_task_id: Optional[str] = None
    expected_form_id: str = "lp-pom-form-42"  # from the Asana checklist
    expected_cta_text: Optional[str] = None
    thank_you_url: Optional[str] = None


@dataclass
class QAReport:
    """Full QA report across all check categories."""
    context: QAContext
    results: list[CheckResult]
    summary: dict = field(default_factory=dict)  # populated after run

    @property
    def passed(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.PASS]

    @property
    def failed(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.FAIL]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.WARN]

    @property
    def skipped(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.SKIP]

    def build_summary(self):
        self.summary = {
            "total": len(self.results),
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "skipped": len(self.skipped),
            "pass_rate": f"{len(self.passed)/len(self.results)*100:.0f}%" if self.results else "N/A",
            "by_category": {},
        }
        cats = set(r.category for r in self.results)
        for cat in sorted(cats):
            cat_results = [r for r in self.results if r.category == cat]
            self.summary["by_category"][cat] = {
                "total": len(cat_results),
                "passed": sum(1 for r in cat_results if r.status == CheckStatus.PASS),
                "failed": sum(1 for r in cat_results if r.status == CheckStatus.FAIL),
            }


# ── Settings ──

ASANA_TOKEN = os.environ.get("ASANA_ACCESS_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OUTPUT_DIR = os.environ.get("QA_OUTPUT_DIR", "./qa_output")
