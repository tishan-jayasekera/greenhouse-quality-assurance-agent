"""
qa_agent/checks/copywriter.py — Copywriter QA Post-Dev Checklist.

Maps the 9 Asana checklist items for copywriter QA to automated checks.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

from qa_agent.config import CheckResult, CheckStatus, PageSnapshot, QAContext


class _TextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping script/style."""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


def _extract_visible_text(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return " ".join(parser.text_parts)


def run(snapshot: PageSnapshot, ctx: QAContext) -> list[CheckResult]:
    """Run all copywriter QA checks."""
    checks = [
        _check_desktop_mobile_copy,
        _check_spelling_grammar,
        _check_capitalisation_consistency,
        _check_accessibility_font_contrast,
        _check_meta_page_title,
        _check_general_ux_copy,
        _check_cro_vault_entry,
        _check_cta_copy_clarity,
        _check_form_labels,
    ]
    results = []
    for fn in checks:
        try:
            results.append(fn(snapshot, ctx))
        except Exception as e:
            results.append(CheckResult(
                check_id=fn.__name__, name=fn.__name__.replace("_check_", "").replace("_", " ").title(),
                category="copywriter", status=CheckStatus.WARN, message=f"Check error: {e}",
            ))
    return results


def _check_desktop_mobile_copy(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check all the below for both Desktop and Mobile."""
    mobile = snap.mobile_snapshot or {}
    desktop_text = _extract_visible_text(snap.dom_html)[:2000]
    # We can't extract full mobile HTML from snapshot, but we check structural parity
    mobile_links = len(mobile.get("links", []))
    desktop_links = len(snap.links)
    if abs(mobile_links - desktop_links) > 5:
        return CheckResult(
            check_id="desktop_mobile_copy",
            name="Desktop/mobile copy parity",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"Link count differs between desktop ({desktop_links}) and mobile ({mobile_links}). "
                "Some copy may be hidden on mobile.",
        )
    return CheckResult(
        check_id="desktop_mobile_copy",
        name="Desktop/mobile copy parity",
        category="copywriter",
        status=CheckStatus.PASS,
        message="Desktop and mobile link structures are consistent. Visual copy check recommended for hidden sections.",
    )


def _check_spelling_grammar(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Consistent spelling and grammar including capitalisation."""
    text = _extract_visible_text(snap.dom_html)
    # Basic heuristic checks
    issues = []

    # Check for double spaces
    double_spaces = len(re.findall(r'  +', text))
    if double_spaces > 3:
        issues.append(f"{double_spaces} double-space occurrences")

    # Check for common typos / inconsistencies
    typo_patterns = {
        r'\b(teh|recieve|occured|seperate|definately|accomodate)\b': "common misspelling",
        r'[.!?]\s*[a-z]': "sentence starting with lowercase (may be intentional)",
    }
    for pattern, desc in typo_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE if "misspelling" in desc else 0)
        if matches:
            issues.append(f"{desc}: found {len(matches)}")

    if issues:
        return CheckResult(
            check_id="spelling_grammar",
            name="Spelling & grammar",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"Potential issues found: {'; '.join(issues)}. "
                "Full spell-check recommended with copy doc comparison.",
        )
    return CheckResult(
        check_id="spelling_grammar",
        name="Spelling & grammar",
        category="copywriter",
        status=CheckStatus.PASS,
        message="No obvious spelling/grammar issues detected. Manual proofread recommended.",
    )


def _check_capitalisation_consistency(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Consistent capitalisation across headings and CTAs."""
    # Extract heading text
    heading_pattern = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>', re.DOTALL | re.IGNORECASE)
    headings = heading_pattern.findall(snap.dom_html)
    heading_texts = [re.sub(r'<[^>]+>', '', h).strip() for h in headings if h.strip()]

    if len(heading_texts) < 2:
        return CheckResult(
            check_id="capitalisation",
            name="Capitalisation consistency",
            category="copywriter",
            status=CheckStatus.SKIP,
            message="Fewer than 2 headings found — not enough to check consistency.",
        )

    # Classify: Title Case vs Sentence case
    title_case = sum(1 for h in heading_texts if h == h.title() or h == h.upper())
    sentence_case = len(heading_texts) - title_case
    mixed = min(title_case, sentence_case) > 0

    if mixed and min(title_case, sentence_case) > 1:
        return CheckResult(
            check_id="capitalisation",
            name="Capitalisation consistency",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"Mixed capitalisation: {title_case} Title Case headings, {sentence_case} sentence case. "
                "Pick one style and apply consistently.",
            evidence="\n".join(f"  {h[:60]}" for h in heading_texts[:6]),
        )
    return CheckResult(
        check_id="capitalisation",
        name="Capitalisation consistency",
        category="copywriter",
        status=CheckStatus.PASS,
        message=f"Heading capitalisation appears consistent across {len(heading_texts)} headings.",
    )


def _check_accessibility_font_contrast(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Accessibility such as font size on mobile and colour contrast."""
    return CheckResult(
        check_id="accessibility_copy",
        name="Accessibility (font size & contrast)",
        category="copywriter",
        status=CheckStatus.SKIP,
        message="Full accessibility audit (WCAG AA contrast ratios, min font sizes) "
            "requires Lighthouse or axe-core integration. Recommended for Phase 2.",
    )


def _check_meta_page_title(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Meta page title is set and meaningful."""
    title = snap.title
    meta = snap.meta_title
    if not title:
        return CheckResult(
            check_id="meta_title",
            name="Meta page title",
            category="copywriter",
            status=CheckStatus.FAIL,
            message="No <title> tag found. Page needs a descriptive title for SEO and browser tabs.",
        )
    issues = []
    if len(title) > 60:
        issues.append(f"Title is {len(title)} chars (recommended: ≤60 for search display)")
    if len(title) < 10:
        issues.append("Title appears too short")
    if "untitled" in title.lower() or "landing page" in title.lower():
        issues.append("Title appears to be a placeholder")

    if issues:
        return CheckResult(
            check_id="meta_title",
            name="Meta page title",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"Title: \"{title[:60]}\". Issues: {'; '.join(issues)}",
        )
    return CheckResult(
        check_id="meta_title",
        name="Meta page title",
        category="copywriter",
        status=CheckStatus.PASS,
        message=f"Title: \"{title[:60]}\" ({len(title)} chars). "
            + (f"OG title: \"{meta[:60]}\"" if meta else "No OG meta title set."),
    )


def _check_general_ux_copy(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """General UX looking at spacing, sticky CTA buttons and information hierarchy."""
    # Check if CTA text is clear and action-oriented
    mobile = snap.mobile_snapshot or {}
    ctas = mobile.get("cta_buttons", [])
    if not ctas:
        return CheckResult(
            check_id="ux_copy",
            name="UX copy & CTA clarity",
            category="copywriter",
            status=CheckStatus.WARN,
            message="No CTA buttons detected. Page may lack a clear call-to-action.",
        )
    cta_texts = [c.get("text", "").strip() for c in ctas if c.get("text", "").strip()]
    vague_ctas = [t for t in cta_texts if t.lower() in ("click here", "submit", "click", "go", "ok")]
    if vague_ctas:
        return CheckResult(
            check_id="ux_copy",
            name="UX copy & CTA clarity",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"Vague CTA copy detected: {', '.join(vague_ctas[:3])}. Use action-specific language.",
        )
    return CheckResult(
        check_id="ux_copy",
        name="UX copy & CTA clarity",
        category="copywriter",
        status=CheckStatus.PASS,
        message=f"CTA text appears clear and specific: {', '.join(t[:30] for t in cta_texts[:3])}",
    )


def _check_cro_vault_entry(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Add page name and full unbounce URL to the CRO vault landing page tracker."""
    return CheckResult(
        check_id="cro_vault",
        name="CRO vault entry",
        category="copywriter",
        status=CheckStatus.SKIP,
        message="CRO vault update is a manual process. "
            "Reminder: add this page to the CRO vault landing page tracker spreadsheet.",
    )


def _check_cta_copy_clarity(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """CTA buttons use clear, benefit-driven copy."""
    # Already partially covered in ux_copy, this focuses on desktop
    ctas = []
    for link in snap.links:
        text = link.get("text", "").strip()
        if len(text) > 2 and len(text) < 50 and link.get("tag") in ("a", "button"):
            ctas.append(text)
    unique_ctas = list(set(ctas))
    if len(unique_ctas) > 5:
        return CheckResult(
            check_id="cta_clarity",
            name="CTA copy variety",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"{len(unique_ctas)} distinct CTA texts found — may be too many competing actions.",
            evidence="\n".join(unique_ctas[:8]),
        )
    return CheckResult(
        check_id="cta_clarity",
        name="CTA copy variety",
        category="copywriter",
        status=CheckStatus.PASS,
        message=f"{len(unique_ctas)} distinct CTA text(s) on page.",
    )


def _check_form_labels(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Form field labels are clear and user-friendly."""
    forms = snap.forms
    if not forms:
        return CheckResult(
            check_id="form_labels",
            name="Form field labels",
            category="copywriter",
            status=CheckStatus.SKIP,
            message="No forms on page.",
        )
    all_fields = [f for form in forms for f in form["fields"]]
    unlabelled = [f for f in all_fields if not f.get("label") and not f.get("placeholder")]
    if unlabelled:
        return CheckResult(
            check_id="form_labels",
            name="Form field labels",
            category="copywriter",
            status=CheckStatus.WARN,
            message=f"{len(unlabelled)} field(s) have no label or placeholder text.",
            evidence=", ".join(f.get("name", f.get("id", "unknown")) for f in unlabelled[:5]),
        )
    return CheckResult(
        check_id="form_labels",
        name="Form field labels",
        category="copywriter",
        status=CheckStatus.PASS,
        message=f"All {len(all_fields)} form fields have labels or placeholder text.",
    )
