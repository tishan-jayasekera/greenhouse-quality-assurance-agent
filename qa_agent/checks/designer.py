"""
qa_agent/checks/designer.py — Designer QA Post-Dev Checklist.

Maps the 11 Asana checklist items for designer QA to automated checks.
"""
from __future__ import annotations

import re

from qa_agent.config import CheckResult, CheckStatus, PageSnapshot, QAContext


def run(snapshot: PageSnapshot, ctx: QAContext) -> list[CheckResult]:
    """Run all designer QA checks."""
    checks = [
        _check_padding_spacing,
        _check_fonts_correct,
        _check_button_links,
        _check_scroll_animations,
        _check_sticky_cta_mobile,
        _check_logo_no_link,
        _check_desktop_mobile_parity,
        _check_image_quality,
        _check_color_contrast,
        _check_responsive_images,
        _check_visual_hierarchy,
    ]
    results = []
    for fn in checks:
        try:
            results.append(fn(snapshot, ctx))
        except Exception as e:
            results.append(CheckResult(
                check_id=fn.__name__, name=fn.__name__.replace("_check_", "").replace("_", " ").title(),
                category="designer", status=CheckStatus.WARN, message=f"Check error: {e}",
            ))
    return results


def _check_padding_spacing(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check padding and spacing."""
    return CheckResult(
        check_id="padding_spacing",
        name="Padding & spacing consistency",
        category="designer",
        status=CheckStatus.SKIP,
        message="Padding/spacing validation requires Figma design token comparison. "
            "Visual review against Figma spec recommended. (Figma API integration: Phase 2)",
    )


def _check_fonts_correct(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Double check fonts are correct."""
    fonts = snap.fonts_loaded
    # Flag common fallback-only scenarios
    system_only = {"arial", "helvetica", "times new roman", "serif", "sans-serif",
                   "monospace", "system-ui", "-apple-system", "segoe ui"}
    custom = [f for f in fonts if f.lower() not in system_only]
    if not custom:
        return CheckResult(
            check_id="fonts_correct",
            name="Fonts loaded correctly",
            category="designer",
            status=CheckStatus.FAIL,
            message="Only system/fallback fonts detected. Web fonts may not be loading.",
            evidence=f"Detected: {', '.join(fonts[:8])}",
        )
    return CheckResult(
        check_id="fonts_correct",
        name="Fonts loaded correctly",
        category="designer",
        status=CheckStatus.PASS,
        message=f"Web fonts loaded: {', '.join(custom[:5])}",
    )


def _check_button_links(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Click all buttons to check links."""
    links = snap.links
    broken_href = [l for l in links if l.get("href") in ("", "#", "javascript:void(0)", "javascript:;")]
    btn_links = [l for l in links if "btn" in l.get("href", "").lower() or "button" in l.get("tag", "")]
    if broken_href:
        return CheckResult(
            check_id="button_links",
            name="Button links valid",
            category="designer",
            status=CheckStatus.WARN,
            message=f"{len(broken_href)} link(s) with empty/placeholder href. Verify these are intentional scroll triggers.",
            evidence="\n".join(f'"{l["text"][:40]}" → {l["href"]}' for l in broken_href[:5]),
        )
    return CheckResult(
        check_id="button_links",
        name="Button links valid",
        category="designer",
        status=CheckStatus.PASS,
        message=f"All {len(links)} links have non-empty href targets.",
    )


def _check_scroll_animations(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check all scroll animations, transitions and hover effects."""
    html = snap.dom_html
    animation_markers = ["animation", "transition", "@keyframes", "animate", "aos", "wow",
                         "gsap", "scroll-trigger", "intersection-observer"]
    found = [m for m in animation_markers if m.lower() in html.lower()]
    if found:
        return CheckResult(
            check_id="scroll_animations",
            name="Scroll animations & transitions",
            category="designer",
            status=CheckStatus.PASS,
            message=f"Animation/transition code detected: {', '.join(found[:4])}. Visual verification recommended.",
        )
    return CheckResult(
        check_id="scroll_animations",
        name="Scroll animations & transitions",
        category="designer",
        status=CheckStatus.WARN,
        message="No animation libraries or @keyframes detected. If animations are expected, they may be missing.",
    )


def _check_sticky_cta_mobile(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Sticky CTA on mobile."""
    mobile = snap.mobile_snapshot or {}
    sticky = mobile.get("sticky_elements", [])
    if sticky:
        return CheckResult(
            check_id="designer_sticky_cta",
            name="Sticky CTA visible on mobile",
            category="designer",
            status=CheckStatus.PASS,
            message=f"Mobile sticky element(s) found: {len(sticky)}. "
                f"First: \"{sticky[0].get('text', '')[:60]}\"",
        )
    return CheckResult(
        check_id="designer_sticky_cta",
        name="Sticky CTA visible on mobile",
        category="designer",
        status=CheckStatus.FAIL,
        message="No sticky/fixed elements on mobile. Expected a sticky CTA bar.",
    )


def _check_logo_no_link(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check logo for link (Should not link out)."""
    # Look for logo elements
    html = snap.dom_html
    logo_link_match = re.search(
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?(?:logo|brand).*?</a>',
        html, re.IGNORECASE | re.DOTALL
    )
    if logo_link_match:
        href = logo_link_match.group(1)
        if href and href not in ("#", "/", "javascript:void(0)"):
            return CheckResult(
                check_id="logo_no_link",
                name="Logo does not link out",
                category="designer",
                status=CheckStatus.FAIL,
                message=f"Logo links to: {href[:80]}. Should not link away from the landing page.",
            )
    return CheckResult(
        check_id="logo_no_link",
        name="Logo does not link out",
        category="designer",
        status=CheckStatus.PASS,
        message="No outbound logo link detected.",
    )


def _check_desktop_mobile_parity(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check visual parity between desktop and mobile."""
    mobile = snap.mobile_snapshot or {}
    desktop_images = len(snap.images)
    mobile_images = len(mobile.get("images", []))
    desktop_forms = len(snap.forms)
    mobile_forms = len(mobile.get("forms", []))

    issues = []
    if desktop_forms != mobile_forms:
        issues.append(f"Form count differs: desktop={desktop_forms}, mobile={mobile_forms}")
    if abs(desktop_images - mobile_images) > 3:
        issues.append(f"Image count differs significantly: desktop={desktop_images}, mobile={mobile_images}")

    if issues:
        return CheckResult(
            check_id="desktop_mobile_parity",
            name="Desktop/mobile parity",
            category="designer",
            status=CheckStatus.WARN,
            message="Structural differences between desktop and mobile.",
            evidence="\n".join(issues),
        )
    return CheckResult(
        check_id="desktop_mobile_parity",
        name="Desktop/mobile parity",
        category="designer",
        status=CheckStatus.PASS,
        message=f"Desktop and mobile structurally consistent (images: {desktop_images}/{mobile_images}, forms: {desktop_forms}/{mobile_forms}).",
    )


def _check_image_quality(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check images are high quality and not stretched."""
    images = snap.images
    stretched = [
        img for img in images
        if img.get("naturalWidth") and img.get("width")
        and img["width"] > 0
        and abs(img["naturalWidth"] / img["width"] - 1) > 0.5
        and img["naturalWidth"] > 50
    ]
    if stretched:
        return CheckResult(
            check_id="image_quality",
            name="Image quality (no stretching)",
            category="designer",
            status=CheckStatus.WARN,
            message=f"{len(stretched)} image(s) may be stretched or heavily resized.",
            evidence="\n".join(
                f"{img['src'][:60]} — natural:{img['naturalWidth']}px, displayed:{img['width']}px"
                for img in stretched[:5]
            ),
        )
    return CheckResult(
        check_id="image_quality",
        name="Image quality (no stretching)",
        category="designer",
        status=CheckStatus.PASS,
        message=f"All {len(images)} images display at appropriate dimensions.",
    )


def _check_color_contrast(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Accessibility: font size on mobile and colour contrast."""
    mobile = snap.mobile_snapshot or {}
    mobile_fonts = mobile.get("fonts", [])
    return CheckResult(
        check_id="color_contrast",
        name="Colour contrast & mobile font size",
        category="designer",
        status=CheckStatus.SKIP,
        message="Full WCAG contrast analysis requires pixel-level inspection. "
            "Recommend running Lighthouse accessibility audit for automated contrast scoring.",
    )


def _check_responsive_images(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check responsive image handling."""
    html = snap.dom_html
    has_srcset = "srcset" in html
    has_picture = "<picture" in html.lower()
    if has_srcset or has_picture:
        return CheckResult(
            check_id="responsive_images",
            name="Responsive images",
            category="designer",
            status=CheckStatus.PASS,
            message=f"Responsive image handling detected: {'srcset' if has_srcset else ''} {'<picture>' if has_picture else ''}".strip(),
        )
    return CheckResult(
        check_id="responsive_images",
        name="Responsive images",
        category="designer",
        status=CheckStatus.WARN,
        message="No srcset or <picture> elements found. Images may not be optimised for different screen sizes.",
    )


def _check_visual_hierarchy(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """General UX: spacing, sticky CTA buttons and information hierarchy."""
    return CheckResult(
        check_id="visual_hierarchy",
        name="Visual hierarchy & UX flow",
        category="designer",
        status=CheckStatus.SKIP,
        message="Visual hierarchy assessment requires human review against the approved design comp.",
    )
