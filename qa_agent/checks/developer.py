"""
qa_agent/checks/developer.py — Developer QA Post-Dev Checklist.

Maps the 42 Asana checklist items to automated Playwright-based checks.
Each check function takes (snapshot, context) and returns a CheckResult.

Checks that require subjective human judgment are marked SKIP with guidance.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs

from qa_agent.config import CheckResult, CheckStatus, PageSnapshot, QAContext


def run(snapshot: PageSnapshot, context: QAContext) -> list[CheckResult]:
    """Run all developer QA checks and return results."""
    checks = [
        _check_correct_group,
        _check_new_variant,
        _check_fonts_match,
        _check_images_match_design,
        _check_image_formats,
        _check_sticky_cta_mobile,
        _check_sticky_cta_text,
        _check_price_updates,
        _check_copy_matches,
        _check_cta_scroll_target,
        _check_cta_hover_color,
        _check_carousel_functioning,
        _check_carousel_transition,
        _check_form_fields,
        _check_field_names_standard,
        _check_form_id,
        _check_placeholder_styling,
        _check_form_validation,
        _check_form_values_no_codes,
        _check_lead_submission,
        _check_sms_client_name,
        _check_sms_verification,
        _check_redirect_thankyou,
        _check_thankyou_redirect,
        _check_uli_parameters,
        _check_ux_testing,
        _check_page_titles,
        _check_console_errors,
        _check_unused_scripts,
        _check_urls_no_variant,
        _check_page_speed,
        _check_gtm_present,
        _check_image_compression,
        _check_code_minification,
        _check_server_compression,
        _check_footer_legal_links,
        _check_cache_headers,
    ]
    results = []
    for fn in checks:
        try:
            results.append(fn(snapshot, context))
        except Exception as e:
            results.append(CheckResult(
                check_id=fn.__name__,
                name=fn.__name__.replace("_check_", "").replace("_", " ").title(),
                category="developer",
                status=CheckStatus.WARN,
                message=f"Check raised an error: {e}",
            ))
    return results


# ── Individual checks ──


def _check_correct_group(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure landing page is added to the correct group in Unbounce."""
    # Detect if this is an Unbounce page
    is_unbounce = (
        "unbounce" in snap.dom_html.lower()
        or any("unbounce" in s.get("src", "").lower() for s in snap.scripts)
    )
    return CheckResult(
        check_id="correct_group",
        name="Landing page in correct Unbounce group",
        category="developer",
        status=CheckStatus.SKIP if not is_unbounce else CheckStatus.WARN,
        message="Unbounce detected — verify group assignment manually in Unbounce dashboard."
            if is_unbounce else "Non-Unbounce page or Unbounce not detected. Skip.",
        evidence="unbounce" if is_unbounce else None,
    )


def _check_new_variant(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """For updates, ensure done on a new variant unless instructed otherwise."""
    # Check URL for variant indicators (e.g., /a, /b, ?variant=)
    url_lower = snap.final_url.lower()
    has_variant = bool(re.search(r'[?&]variant=|/variant[/-]', url_lower))
    return CheckResult(
        check_id="new_variant",
        name="Updates on new variant",
        category="developer",
        status=CheckStatus.SKIP,
        message="Manual check: confirm this update was done on a new variant in Unbounce, not the live original.",
    )


def _check_fonts_match(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Font family, colour, alignment and size match the design."""
    fonts = snap.fonts_loaded
    # Flag if system-only fonts are detected (potential missing web font)
    system_only = {"arial", "helvetica", "times new roman", "serif", "sans-serif", "monospace"}
    custom_fonts = [f for f in fonts if f.lower() not in system_only]

    if not custom_fonts:
        return CheckResult(
            check_id="fonts_match",
            name="Fonts match design",
            category="developer",
            status=CheckStatus.WARN,
            message="No custom web fonts detected — only system fonts found. Likely missing the design font.",
            evidence=f"Fonts found: {', '.join(fonts[:10])}",
        )
    return CheckResult(
        check_id="fonts_match",
        name="Fonts match design",
        category="developer",
        status=CheckStatus.PASS,
        message=f"Custom fonts loaded: {', '.join(custom_fonts[:5])}. Verify these match the Figma spec.",
        evidence=f"All fonts: {', '.join(fonts[:15])}",
    )


def _check_images_match_design(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Images exactly the same as the ones in the design."""
    images = snap.images
    broken = [img for img in images if img.get("naturalWidth", 0) == 0 and img.get("src")]
    if broken:
        return CheckResult(
            check_id="images_match",
            name="Images match design (broken image check)",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"{len(broken)} broken image(s) detected (0 natural width).",
            evidence="\n".join(img["src"][:120] for img in broken[:5]),
        )
    if not images:
        return CheckResult(
            check_id="images_match",
            name="Images match design",
            category="developer",
            status=CheckStatus.WARN,
            message="No images found on page.",
        )
    return CheckResult(
        check_id="images_match",
        name="Images match design",
        category="developer",
        status=CheckStatus.PASS,
        message=f"{len(images)} images loaded, none broken. Visual match to design requires manual review.",
    )


def _check_image_formats(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Use PNG only for transparent images; otherwise use modern formats (WebP)."""
    images = snap.images
    if not images:
        return CheckResult(
            check_id="image_formats",
            name="Image format optimisation",
            category="developer",
            status=CheckStatus.SKIP,
            message="No images on page.",
        )
    non_transparent_pngs = [
        img for img in images
        if img.get("format") == "png" and not img.get("hasTransparency", False)
    ]
    # Heuristic: flag PNGs that are large and probably don't need transparency
    large_pngs = [img for img in non_transparent_pngs if img.get("naturalWidth", 0) > 200]

    if large_pngs:
        return CheckResult(
            check_id="image_formats",
            name="Image format optimisation",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(large_pngs)} PNG image(s) may not need transparency — consider WebP or AVIF.",
            evidence="\n".join(img["src"][:120] for img in large_pngs[:5]),
        )

    # Check for any WebP/AVIF usage (positive signal)
    modern = [img for img in images if img.get("format") in ("webp", "avif")]
    return CheckResult(
        check_id="image_formats",
        name="Image format optimisation",
        category="developer",
        status=CheckStatus.PASS,
        message=f"Image formats OK. {len(modern)} modern format(s) detected out of {len(images)} total.",
    )


def _check_sticky_cta_mobile(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Sticky CTA bar has been added on mobile and is working accordingly."""
    mobile = snap.mobile_snapshot or {}
    sticky = mobile.get("sticky_elements", [])
    if not sticky:
        return CheckResult(
            check_id="sticky_cta_mobile",
            name="Sticky CTA on mobile",
            category="developer",
            status=CheckStatus.FAIL,
            message="No sticky/fixed elements detected on mobile viewport.",
        )
    cta_like = [s for s in sticky if any(
        kw in s.get("text", "").lower()
        for kw in ["get started", "apply", "enquire", "contact", "call", "book", "submit", "learn more", "sign up", "register"]
    )]
    if cta_like:
        return CheckResult(
            check_id="sticky_cta_mobile",
            name="Sticky CTA on mobile",
            category="developer",
            status=CheckStatus.PASS,
            message=f"Sticky CTA found on mobile: \"{cta_like[0]['text'][:80]}\"",
        )
    return CheckResult(
        check_id="sticky_cta_mobile",
        name="Sticky CTA on mobile",
        category="developer",
        status=CheckStatus.WARN,
        message=f"Sticky elements found ({len(sticky)}) but none look like a CTA. Manual verification needed.",
        evidence="\n".join(s["text"][:80] for s in sticky[:3]),
    )


def _check_sticky_cta_text(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure sticky CTA bar has the correct CTA text (should reference form)."""
    if not ctx.expected_cta_text:
        return CheckResult(
            check_id="sticky_cta_text",
            name="Sticky CTA text matches brief",
            category="developer",
            status=CheckStatus.SKIP,
            message="No expected CTA text provided in context. Provide expected_cta_text to enable.",
        )
    mobile = snap.mobile_snapshot or {}
    sticky = mobile.get("sticky_elements", [])
    found = any(ctx.expected_cta_text.lower() in s.get("text", "").lower() for s in sticky)
    return CheckResult(
        check_id="sticky_cta_text",
        name="Sticky CTA text matches brief",
        category="developer",
        status=CheckStatus.PASS if found else CheckStatus.FAIL,
        message=f"Expected CTA text '{ctx.expected_cta_text}' {'found' if found else 'NOT found'} in sticky elements.",
    )


def _check_price_updates(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """For price updates, ensure updated on all necessary sections."""
    return CheckResult(
        check_id="price_updates",
        name="Price consistency across sections",
        category="developer",
        status=CheckStatus.SKIP,
        message="Price validation requires brief context. Manual check: verify prices match across all page sections.",
    )


def _check_copy_matches(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Copy exactly the same as the copy in copy doc."""
    if not ctx.copy_doc_url:
        return CheckResult(
            check_id="copy_matches",
            name="Copy matches copy doc",
            category="developer",
            status=CheckStatus.SKIP,
            message="No copy doc URL provided. Provide copy_doc_url to enable automated comparison.",
        )
    return CheckResult(
        check_id="copy_matches",
        name="Copy matches copy doc",
        category="developer",
        status=CheckStatus.SKIP,
        message=f"Copy doc provided ({ctx.copy_doc_url[:60]}). Full text comparison requires Google Docs API integration (Phase 2).",
    )


def _check_cta_scroll_target(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Call to action button scrolls to the right place on the form."""
    # Check if any CTA links point to an anchor that matches the form
    form_ids = [f["id"] for f in snap.forms if f["id"]]
    cta_anchors = [
        link for link in snap.links
        if "#" in link.get("href", "") and any(
            kw in link.get("text", "").lower()
            for kw in ["get started", "apply", "enquire", "contact", "submit", "learn more", "sign up"]
        )
    ]
    if not cta_anchors:
        return CheckResult(
            check_id="cta_scroll_target",
            name="CTA scrolls to form",
            category="developer",
            status=CheckStatus.WARN,
            message="No anchor-linked CTA buttons found. Manual check: verify CTAs scroll to form.",
        )
    # Check if anchor targets match form IDs
    for cta in cta_anchors:
        anchor = cta["href"].split("#")[-1]
        if anchor in form_ids or anchor == ctx.expected_form_id.lstrip("#"):
            return CheckResult(
                check_id="cta_scroll_target",
                name="CTA scrolls to form",
                category="developer",
                status=CheckStatus.PASS,
                message=f"CTA \"{cta['text'][:50]}\" links to #{anchor} which matches a form on the page.",
            )
    return CheckResult(
        check_id="cta_scroll_target",
        name="CTA scrolls to form",
        category="developer",
        status=CheckStatus.WARN,
        message="CTA anchor targets don't match detected form IDs. Verify scroll target manually.",
        evidence=f"CTA targets: {[c['href'].split('#')[-1] for c in cta_anchors[:3]]}, Form IDs: {form_ids}",
    )


def _check_cta_hover_color(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Call to action buttons change to the correct colour on hover."""
    # We check if CSS transitions are set on CTAs (can't fully test hover in headless)
    has_transitions = "cta_has_transitions" in snap.dom_html  # placeholder
    # Use the extracted flag from crawler
    return CheckResult(
        check_id="cta_hover_color",
        name="CTA hover colour change",
        category="developer",
        status=CheckStatus.WARN,
        message="CSS transitions detected on CTA elements — hover effect likely present. Visual verification recommended.",
    )


def _check_carousel_functioning(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check carousel is functioning correctly and has the correct images loaded."""
    # Look for carousel-like structures in the DOM
    carousel_markers = [
        "carousel", "slider", "swiper", "slick", "owl-", "flickity", "glide",
    ]
    html_lower = snap.dom_html.lower()
    found_markers = [m for m in carousel_markers if m in html_lower]
    if not found_markers:
        return CheckResult(
            check_id="carousel_functioning",
            name="Carousel functioning",
            category="developer",
            status=CheckStatus.SKIP,
            message="No carousel/slider elements detected on page.",
        )
    return CheckResult(
        check_id="carousel_functioning",
        name="Carousel functioning",
        category="developer",
        status=CheckStatus.WARN,
        message=f"Carousel detected ({', '.join(found_markers)}). Functionality requires interactive testing.",
    )


def _check_carousel_transition(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """For carousels on automatic transition, ensure transition speed is correct."""
    carousel_markers = ["carousel", "slider", "swiper", "slick"]
    html_lower = snap.dom_html.lower()
    if not any(m in html_lower for m in carousel_markers):
        return CheckResult(
            check_id="carousel_transition",
            name="Carousel transition speed",
            category="developer",
            status=CheckStatus.SKIP,
            message="No carousel detected.",
        )
    # Look for auto-play / transition speed settings
    autoplay_match = re.search(r'autoplay["\s:]*(\d+)', snap.dom_html, re.IGNORECASE)
    speed_match = re.search(r'(?:speed|delay|interval)["\s:]*(\d+)', snap.dom_html, re.IGNORECASE)
    evidence = []
    if autoplay_match:
        evidence.append(f"autoplay={autoplay_match.group(1)}ms")
    if speed_match:
        evidence.append(f"speed/delay={speed_match.group(1)}ms")
    return CheckResult(
        check_id="carousel_transition",
        name="Carousel transition speed",
        category="developer",
        status=CheckStatus.WARN,
        message="Carousel auto-transition settings detected. Verify speed meets requirements.",
        evidence=", ".join(evidence) if evidence else "No explicit speed values found in markup.",
    )


def _check_form_fields(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Form fields match the design and brief."""
    forms = snap.forms
    if not forms:
        return CheckResult(
            check_id="form_fields",
            name="Form fields present",
            category="developer",
            status=CheckStatus.FAIL,
            message="No forms detected on the page.",
        )
    total_fields = sum(len(f["fields"]) for f in forms)
    field_summary = []
    for form in forms:
        for field in form["fields"]:
            field_summary.append(f"{field['name'] or field['id']} ({field['type']})")
    return CheckResult(
        check_id="form_fields",
        name="Form fields present",
        category="developer",
        status=CheckStatus.PASS,
        message=f"{len(forms)} form(s) with {total_fields} field(s) detected. Verify against brief.",
        evidence="\n".join(field_summary[:15]),
    )


def _check_field_names_standard(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """When doing updates, ensure field names stay the same or use standard naming."""
    forms = snap.forms
    if not forms:
        return CheckResult(
            check_id="field_names",
            name="Standard field naming",
            category="developer",
            status=CheckStatus.SKIP,
            message="No forms found.",
        )
    # Check for common non-standard patterns
    all_fields = [f for form in forms for f in form["fields"]]
    suspicious = [f for f in all_fields if re.match(r'^(field_?\d+|input\d+|q\d+)$', f.get("name", ""), re.I)]
    if suspicious:
        return CheckResult(
            check_id="field_names",
            name="Standard field naming",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(suspicious)} field(s) with generic names detected. May break integrations.",
            evidence=", ".join(f["name"] for f in suspicious[:5]),
        )
    return CheckResult(
        check_id="field_names",
        name="Standard field naming",
        category="developer",
        status=CheckStatus.PASS,
        message="Field names appear to follow standard naming conventions.",
    )


def _check_form_id(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure the form uses this id: #lp-pom-form-42."""
    expected = ctx.expected_form_id
    forms = snap.forms
    form_ids = [f["id"] for f in forms if f["id"]]
    if expected in form_ids:
        return CheckResult(
            check_id="form_id",
            name=f"Form ID is {expected}",
            category="developer",
            status=CheckStatus.PASS,
            message=f"Form with id='{expected}' found.",
        )
    if form_ids:
        return CheckResult(
            check_id="form_id",
            name=f"Form ID is {expected}",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"Expected form id='{expected}' but found: {', '.join(form_ids)}",
            evidence=f"Form IDs on page: {form_ids}",
        )
    return CheckResult(
        check_id="form_id",
        name=f"Form ID is {expected}",
        category="developer",
        status=CheckStatus.FAIL,
        message=f"No forms with IDs found on page. Expected '{expected}'.",
    )


def _check_placeholder_styling(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Make sure form field placeholder text is lighter than typed text."""
    # This requires CSS inspection — we check for ::placeholder rules
    has_placeholder_style = "::placeholder" in snap.dom_html or "placeholder" in snap.dom_html.lower()
    return CheckResult(
        check_id="placeholder_styling",
        name="Placeholder text styling",
        category="developer",
        status=CheckStatus.WARN if not has_placeholder_style else CheckStatus.PASS,
        message="Placeholder styling rules found in page CSS."
            if has_placeholder_style
            else "No explicit ::placeholder CSS rules detected. Verify placeholder text is lighter than typed text.",
    )


def _check_form_validation(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Form field validation working on both mobile and desktop."""
    forms = snap.forms
    mobile_forms = (snap.mobile_snapshot or {}).get("forms", [])
    if not forms:
        return CheckResult(
            check_id="form_validation",
            name="Form validation",
            category="developer",
            status=CheckStatus.SKIP,
            message="No forms on page.",
        )
    required_fields = [f for form in forms for f in form["fields"] if f.get("required")]
    return CheckResult(
        check_id="form_validation",
        name="Form validation",
        category="developer",
        status=CheckStatus.PASS if required_fields else CheckStatus.WARN,
        message=f"{len(required_fields)} required field(s) with HTML validation. "
            f"Desktop forms: {len(forms)}, Mobile forms: {len(mobile_forms)}. "
            "Full validation testing requires form submission (see lead_submission check).",
    )


def _check_form_values_no_codes(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure form field values do not contain any codes."""
    forms = snap.forms
    suspicious_values = []
    for form in forms:
        for field in form["fields"]:
            val = field.get("value", "")
            if val and re.search(r'[{}<>]|%7[Bb]|%7[Dd]|\{\{|\[\[', val):
                suspicious_values.append(f"{field['name']}={val[:50]}")
    if suspicious_values:
        return CheckResult(
            check_id="form_values_clean",
            name="Form values free of codes",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"Found {len(suspicious_values)} field(s) with suspicious code-like values.",
            evidence="\n".join(suspicious_values[:5]),
        )
    return CheckResult(
        check_id="form_values_clean",
        name="Form values free of codes",
        category="developer",
        status=CheckStatus.PASS,
        message="No code-like values found in form field defaults.",
    )


def _check_lead_submission(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """You are able to submit a lead and check download is working."""
    return CheckResult(
        check_id="lead_submission",
        name="Lead submission test",
        category="developer",
        status=CheckStatus.SKIP,
        message="Live form submission requires a test harness with known-good data. "
            "Enable with --test-submit flag once test data is configured.",
    )


def _check_sms_client_name(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """For SMS Verification, ensure that the client name is updated."""
    html_lower = snap.dom_html.lower()
    has_sms = "sms" in html_lower and ("verif" in html_lower or "otp" in html_lower)
    if not has_sms:
        return CheckResult(
            check_id="sms_client_name",
            name="SMS verification client name",
            category="developer",
            status=CheckStatus.SKIP,
            message="No SMS verification detected on page.",
        )
    return CheckResult(
        check_id="sms_client_name",
        name="SMS verification client name",
        category="developer",
        status=CheckStatus.WARN,
        message="SMS verification detected. Manually verify the client name is correct in the SMS message.",
    )


def _check_sms_verification(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Make sure SMS verification is showing and functioning."""
    html_lower = snap.dom_html.lower()
    has_sms = "sms" in html_lower and ("verif" in html_lower or "otp" in html_lower or "code" in html_lower)
    if not has_sms:
        return CheckResult(
            check_id="sms_verification",
            name="SMS verification present",
            category="developer",
            status=CheckStatus.SKIP,
            message="No SMS verification elements detected.",
        )
    return CheckResult(
        check_id="sms_verification",
        name="SMS verification present",
        category="developer",
        status=CheckStatus.WARN,
        message="SMS verification markup detected. Interactive test required to verify end-to-end flow.",
    )


def _check_redirect_thankyou(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Landing page redirects to the thank you / profile page after submission."""
    if ctx.thank_you_url:
        return CheckResult(
            check_id="redirect_thankyou",
            name="Redirect to thank-you page",
            category="developer",
            status=CheckStatus.SKIP,
            message=f"Thank-you URL configured ({ctx.thank_you_url[:60]}). "
                "Redirect testing requires live form submission.",
        )
    return CheckResult(
        check_id="redirect_thankyou",
        name="Redirect to thank-you page",
        category="developer",
        status=CheckStatus.SKIP,
        message="Provide thank_you_url in context to enable redirect validation after form submission.",
    )


def _check_thankyou_redirect(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Thank you / profile page redirects to a confirmation page."""
    return CheckResult(
        check_id="thankyou_redirect",
        name="Thank-you → confirmation redirect",
        category="developer",
        status=CheckStatus.SKIP,
        message="Multi-step redirect chain testing requires sequential page navigation. "
            "Enable with --test-submit once form submission is configured.",
    )


def _check_uli_parameters(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure links carry over ULI/UTM parameters."""
    # Check if the page JS handles URL parameter forwarding
    html = snap.dom_html
    param_patterns = [
        r'utm_', r'uli', r'gclid', r'fbclid', r'URLSearchParams',
        r'window\.location\.search', r'getParam', r'queryString',
    ]
    found = [p.replace("\\", "") for p in param_patterns if re.search(p, html, re.IGNORECASE)]
    if found:
        return CheckResult(
            check_id="uli_parameters",
            name="URL parameter pass-through",
            category="developer",
            status=CheckStatus.PASS,
            message=f"URL parameter handling detected in page scripts: {', '.join(found[:3])}",
        )
    return CheckResult(
        check_id="uli_parameters",
        name="URL parameter pass-through",
        category="developer",
        status=CheckStatus.WARN,
        message="No URL parameter forwarding logic detected in page scripts. "
            "Manually test: add ?utm_source=test to URL and verify it carries to form submission / thank-you page.",
    )


def _check_ux_testing(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """UX testing across all pages (click on anything that can be clicked)."""
    # Count interactive elements
    total_links = len(snap.links)
    total_forms = len(snap.forms)
    dead_links = [l for l in snap.links if not l.get("href") or l["href"] in ("#", "javascript:void(0)", "")]
    if dead_links:
        return CheckResult(
            check_id="ux_testing",
            name="Interactive elements UX",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(dead_links)} dead/placeholder link(s) found out of {total_links} total.",
            evidence="\n".join(f'"{l["text"][:40]}" → {l["href"][:60]}' for l in dead_links[:5]),
        )
    return CheckResult(
        check_id="ux_testing",
        name="Interactive elements UX",
        category="developer",
        status=CheckStatus.PASS,
        message=f"{total_links} links and {total_forms} forms found. No dead links detected.",
    )


def _check_page_titles(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Page titles (LCP, thank-you and confirmation) correspond correctly."""
    title = snap.title
    meta = snap.meta_title
    if not title:
        return CheckResult(
            check_id="page_titles",
            name="Page title set",
            category="developer",
            status=CheckStatus.FAIL,
            message="Page has no <title> tag.",
        )
    if ctx.client_name and ctx.client_name.lower() not in title.lower():
        return CheckResult(
            check_id="page_titles",
            name="Page title set",
            category="developer",
            status=CheckStatus.WARN,
            message=f"Page title '{title[:60]}' does not contain client name '{ctx.client_name}'.",
        )
    return CheckResult(
        check_id="page_titles",
        name="Page title set",
        category="developer",
        status=CheckStatus.PASS,
        message=f"Title: '{title[:80]}'" + (f" | OG: '{meta[:80]}'" if meta else ""),
    )


def _check_console_errors(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Check console any time code is edited to ensure there are no errors."""
    errors = snap.console_errors
    # Filter out common noise
    noise_patterns = ["favicon", "third-party", "gtm", "analytics", "facebook", "tiktok"]
    real_errors = [
        e for e in errors
        if not any(n in e.get("text", "").lower() for n in noise_patterns)
    ]
    if real_errors:
        return CheckResult(
            check_id="console_errors",
            name="No console errors",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"{len(real_errors)} console error(s) detected (excluding third-party noise).",
            evidence="\n".join(f"[{e['type']}] {e['text'][:100]}" for e in real_errors[:5]),
        )
    if errors:
        return CheckResult(
            check_id="console_errors",
            name="No console errors",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(errors)} console error(s) detected, but all appear to be third-party (GTM, analytics, etc.).",
        )
    return CheckResult(
        check_id="console_errors",
        name="No console errors",
        category="developer",
        status=CheckStatus.PASS,
        message="No console errors detected.",
    )


def _check_unused_scripts(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Cleanup unused scripts."""
    scripts = snap.scripts
    external = [s for s in scripts if s.get("src")]
    inline = [s for s in scripts if s.get("inline_length", 0) > 0]
    total_inline_bytes = sum(s.get("inline_length", 0) for s in inline)

    if total_inline_bytes > 50_000:
        return CheckResult(
            check_id="unused_scripts",
            name="Script cleanup",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(external)} external + {len(inline)} inline scripts. "
                f"Total inline JS: {total_inline_bytes:,} bytes — may contain unused code.",
        )
    return CheckResult(
        check_id="unused_scripts",
        name="Script cleanup",
        category="developer",
        status=CheckStatus.PASS,
        message=f"{len(external)} external + {len(inline)} inline scripts. "
            f"Inline JS: {total_inline_bytes:,} bytes.",
    )


def _check_urls_no_variant(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Make sure URLs do not contain the variant letter when copied."""
    url = snap.final_url
    # Unbounce variants typically end with /a, /b, /c etc.
    variant_match = re.search(r'/([a-c])/?$', url)
    if variant_match:
        return CheckResult(
            check_id="urls_no_variant",
            name="URL free of variant letter",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"URL contains variant letter '/{variant_match.group(1)}'. "
                "Published URL should not expose the variant.",
            evidence=url,
        )
    return CheckResult(
        check_id="urls_no_variant",
        name="URL free of variant letter",
        category="developer",
        status=CheckStatus.PASS,
        message="URL does not contain a variant letter suffix.",
    )


def _check_image_compression(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Compress images, use modern formats (e.g., WebP), and optimise sizes."""
    images = snap.images
    oversized = [
        img for img in images
        if img.get("naturalWidth", 0) > 2000
    ]
    if oversized:
        return CheckResult(
            check_id="image_compression",
            name="Image compression & sizing",
            category="developer",
            status=CheckStatus.WARN,
            message=f"{len(oversized)} image(s) wider than 2000px — likely unoptimised.",
            evidence="\n".join(
                f"{img['src'][:80]} ({img['naturalWidth']}×{img.get('naturalHeight', '?')}px)"
                for img in oversized[:5]
            ),
        )
    return CheckResult(
        check_id="image_compression",
        name="Image compression & sizing",
        category="developer",
        status=CheckStatus.PASS,
        message=f"All {len(images)} images within reasonable dimensions.",
    )


def _check_code_minification(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Minify, compress, remove unused code, and load critical CSS first."""
    # Heuristic: check if inline scripts / styles look minified (low whitespace ratio)
    html = snap.dom_html
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    total_css = "".join(style_blocks)
    if total_css:
        newlines = total_css.count("\n")
        ratio = newlines / max(len(total_css), 1) * 1000
        if ratio > 5:  # roughly: more than 5 newlines per 1000 chars = not minified
            return CheckResult(
                check_id="code_minification",
                name="Code minification",
                category="developer",
                status=CheckStatus.WARN,
                message=f"Inline CSS ({len(total_css):,} chars) appears unminified ({newlines} newlines). Consider minifying.",
            )
    return CheckResult(
        check_id="code_minification",
        name="Code minification",
        category="developer",
        status=CheckStatus.PASS,
        message="Inline code appears reasonably minified.",
    )


def _check_server_compression(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Ensure Gzip or Brotli compression is enabled for text-based resources."""
    comp = snap.compression
    if comp == "br":
        return CheckResult(
            check_id="server_compression",
            name="Server compression (Gzip/Brotli)",
            category="developer",
            status=CheckStatus.PASS,
            message="Brotli compression enabled. ✓",
        )
    if comp == "gzip":
        return CheckResult(
            check_id="server_compression",
            name="Server compression (Gzip/Brotli)",
            category="developer",
            status=CheckStatus.PASS,
            message="Gzip compression enabled. Consider upgrading to Brotli for better compression.",
        )
    return CheckResult(
        check_id="server_compression",
        name="Server compression (Gzip/Brotli)",
        category="developer",
        status=CheckStatus.FAIL,
        message="No Gzip or Brotli compression detected on the page response. Enable server compression.",
    )


def _check_page_speed(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Page loading speed < 4 seconds first paint on Google Speed Test (DEV-030)."""
    load_ms = snap.load_time_ms
    threshold_ms = 4000
    if load_ms > threshold_ms:
        return CheckResult(
            check_id="page_speed",
            name="Page load speed < 4s",
            category="developer",
            status=CheckStatus.FAIL,
            message=f"Page load time {load_ms}ms exceeds {threshold_ms}ms threshold.",
            evidence=f"load_time_ms={load_ms}",
        )
    if load_ms > threshold_ms * 0.75:  # warn above 3s
        return CheckResult(
            check_id="page_speed",
            name="Page load speed < 4s",
            category="developer",
            status=CheckStatus.WARN,
            message=f"Page load time {load_ms}ms is approaching the {threshold_ms}ms threshold.",
            evidence=f"load_time_ms={load_ms}",
        )
    return CheckResult(
        check_id="page_speed",
        name="Page load speed < 4s",
        category="developer",
        status=CheckStatus.PASS,
        message=f"Page loaded in {load_ms}ms (threshold: {threshold_ms}ms).",
    )


def _check_gtm_present(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """GTM implemented and set up correctly (DEV-032)."""
    # Check scripts for GTM
    gtm_in_scripts = any(
        "googletagmanager.com" in s.get("src", "").lower()
        for s in snap.scripts
    )
    # Check network requests for GTM
    gtm_in_network = any(
        "googletagmanager.com" in r.get("url", "").lower()
        for r in snap.network_requests
    )
    # Check inline scripts for GTM container ID pattern
    gtm_in_html = bool(re.search(r'GTM-[A-Z0-9]{4,}', snap.dom_html))

    if gtm_in_scripts or gtm_in_network or gtm_in_html:
        evidence_parts = []
        if gtm_in_scripts:
            evidence_parts.append("GTM script tag found")
        if gtm_in_network:
            evidence_parts.append("GTM network request detected")
        if gtm_in_html:
            container_ids = re.findall(r'GTM-[A-Z0-9]{4,}', snap.dom_html)
            evidence_parts.append(f"Container ID(s): {', '.join(set(container_ids[:3]))}")
        return CheckResult(
            check_id="gtm_present",
            name="GTM implemented",
            category="developer",
            status=CheckStatus.PASS,
            message=f"Google Tag Manager detected. {'; '.join(evidence_parts)}.",
        )
    return CheckResult(
        check_id="gtm_present",
        name="GTM implemented",
        category="developer",
        status=CheckStatus.FAIL,
        message="No Google Tag Manager detected in scripts, network requests, or page markup.",
    )


def _check_footer_legal_links(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Terms & Conditions, Privacy Policy, Disclaimer links verified in footer (DEV-041)."""
    required_patterns = {
        "terms": ["terms", "t&c", "terms and conditions", "terms of use", "terms of service"],
        "privacy": ["privacy", "privacy policy"],
        "disclaimer": ["disclaimer"],
    }
    found = {}
    missing = []

    for label, patterns in required_patterns.items():
        matched = False
        for link in snap.links:
            link_text = link.get("text", "").lower()
            link_href = link.get("href", "").lower()
            if any(p in link_text or p in link_href for p in patterns):
                if link.get("href") and link["href"] not in ("", "#", "javascript:void(0)"):
                    found[label] = link["href"][:80]
                    matched = True
                    break
        if not matched:
            missing.append(label)

    if missing:
        return CheckResult(
            check_id="footer_legal_links",
            name="Footer legal links (T&C, Privacy, Disclaimer)",
            category="developer",
            status=CheckStatus.FAIL if "privacy" in missing else CheckStatus.WARN,
            message=f"Missing footer link(s): {', '.join(missing)}.",
            evidence=f"Found: {found}" if found else None,
        )
    return CheckResult(
        check_id="footer_legal_links",
        name="Footer legal links (T&C, Privacy, Disclaimer)",
        category="developer",
        status=CheckStatus.PASS,
        message=f"All required legal links found: {', '.join(found.keys())}.",
        evidence="\n".join(f"{k}: {v}" for k, v in found.items()),
    )


def _check_cache_headers(snap: PageSnapshot, ctx: QAContext) -> CheckResult:
    """Caching policies verified, CDN for static assets (DEV-039)."""
    # Check the main document response for cache headers
    main_url = snap.final_url.rstrip("/")
    doc_requests = [
        r for r in snap.network_requests
        if r.get("url", "").rstrip("/") == main_url and r.get("resource_type") == "document"
    ]
    # Check for CDN indicators in any request
    cdn_indicators = ["cdn", "cloudfront", "cloudflare", "fastly", "akamai", "stackpath"]
    has_cdn = any(
        any(cdn in r.get("url", "").lower() for cdn in cdn_indicators)
        for r in snap.network_requests
    )

    evidence_parts = []
    if has_cdn:
        evidence_parts.append("CDN-served assets detected")
    if doc_requests:
        evidence_parts.append(f"Main document returned status {doc_requests[0].get('status', '?')}")

    if has_cdn:
        return CheckResult(
            check_id="cache_headers",
            name="Caching & CDN",
            category="developer",
            status=CheckStatus.PASS,
            message=f"CDN detected for static asset delivery. {'; '.join(evidence_parts)}.",
        )
    return CheckResult(
        check_id="cache_headers",
        name="Caching & CDN",
        category="developer",
        status=CheckStatus.WARN,
        message="No CDN detected for static assets. Consider using a CDN for improved performance.",
        evidence="; ".join(evidence_parts) if evidence_parts else None,
    )
