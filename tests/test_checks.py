"""
tests/test_checks.py — Unit tests for QA checks using mock page data.

Run: python -m pytest tests/ -v
"""
import pytest
from qa_agent.config import PageSnapshot, QAContext, CheckStatus


def _make_snapshot(**overrides) -> PageSnapshot:
    """Create a mock PageSnapshot with sensible defaults."""
    defaults = dict(
        url="https://example.com/landing-page",
        final_url="https://example.com/landing-page",
        title="Acme Corp | Summer Campaign",
        meta_title="Acme Corp - Get Started Today",
        status_code=200,
        console_errors=[],
        console_warnings=[],
        network_requests=[],
        fonts_loaded=["Montserrat", "Open Sans", "sans-serif"],
        images=[
            {"src": "https://example.com/hero.webp", "alt": "Hero", "width": 800,
             "height": 400, "naturalWidth": 800, "naturalHeight": 400,
             "format": "webp", "hasTransparency": False},
        ],
        links=[
            {"href": "https://example.com/landing-page#form", "text": "Get Started", "target": "", "tag": "a"},
            {"href": "https://example.com/privacy", "text": "Privacy Policy", "target": "_blank", "tag": "a"},
        ],
        forms=[
            {
                "id": "lp-pom-form-42",
                "action": "/submit",
                "method": "post",
                "fields": [
                    {"name": "first_name", "type": "text", "id": "fname", "placeholder": "First Name",
                     "required": True, "value": "", "label": "First Name"},
                    {"name": "email", "type": "email", "id": "email", "placeholder": "Email",
                     "required": True, "value": "", "label": "Email"},
                ],
            }
        ],
        scripts=[
            {"src": "https://cdn.example.com/app.min.js", "inline_length": 0},
            {"src": "", "inline_length": 500},
        ],
        sticky_elements=[
            {"tag": "div", "id": "sticky-cta", "classes": "sticky-bar", "text": "Get Started Now", "position": "fixed"},
        ],
        dom_html="<html><head><title>Acme Corp</title></head><body><div>Content</div></body></html>",
        mobile_snapshot={
            "sticky_elements": [
                {"tag": "div", "id": "sticky-cta", "classes": "sticky-bar",
                 "text": "Get Started Now", "position": "fixed"},
            ],
            "forms": [
                {"id": "lp-pom-form-42", "fields": [
                    {"name": "first_name", "type": "text"},
                    {"name": "email", "type": "email"},
                ]},
            ],
            "images": [
                {"src": "https://example.com/hero.webp", "naturalWidth": 800, "width": 375},
            ],
            "cta_buttons": [
                {"text": "Get Started", "tag": "a", "href": "#form", "type": ""},
            ],
            "links": [
                {"href": "#form", "text": "Get Started", "target": "", "tag": "a"},
                {"href": "/privacy", "text": "Privacy", "target": "", "tag": "a"},
            ],
            "fonts": ["Montserrat", "Open Sans"],
        },
        compression="br",
        screenshot_desktop=None,
        screenshot_mobile=None,
        redirect_chain=["https://example.com/landing-page"],
        page_size_bytes=150000,
        load_time_ms=1200,
    )
    defaults.update(overrides)
    return PageSnapshot(**defaults)


def _make_context(**overrides) -> QAContext:
    defaults = dict(
        landing_page_url="https://example.com/landing-page",
        client_name="Acme Corp",
        campaign_name="Summer 2025",
        expected_form_id="lp-pom-form-42",
    )
    defaults.update(overrides)
    return QAContext(**defaults)


# ────────────────────── Developer Checks ──────────────────────

class TestDeveloperChecks:

    def test_form_id_pass(self):
        from qa_agent.checks.developer import _check_form_id
        result = _check_form_id(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_form_id_fail(self):
        from qa_agent.checks.developer import _check_form_id
        snap = _make_snapshot(forms=[{"id": "wrong-form", "action": "/", "method": "post", "fields": []}])
        result = _check_form_id(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_console_errors_pass(self):
        from qa_agent.checks.developer import _check_console_errors
        result = _check_console_errors(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_console_errors_fail(self):
        from qa_agent.checks.developer import _check_console_errors
        snap = _make_snapshot(console_errors=[
            {"type": "error", "text": "Uncaught TypeError: null is not an object", "url": "app.js", "line": 42}
        ])
        result = _check_console_errors(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_server_compression_brotli(self):
        from qa_agent.checks.developer import _check_server_compression
        result = _check_server_compression(_make_snapshot(compression="br"), _make_context())
        assert result.status == CheckStatus.PASS

    def test_server_compression_none(self):
        from qa_agent.checks.developer import _check_server_compression
        result = _check_server_compression(_make_snapshot(compression=None), _make_context())
        assert result.status == CheckStatus.FAIL

    def test_sticky_cta_mobile_pass(self):
        from qa_agent.checks.developer import _check_sticky_cta_mobile
        result = _check_sticky_cta_mobile(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_sticky_cta_mobile_fail(self):
        from qa_agent.checks.developer import _check_sticky_cta_mobile
        snap = _make_snapshot(mobile_snapshot={"sticky_elements": [], "forms": [], "images": [],
                                                "cta_buttons": [], "links": [], "fonts": []})
        result = _check_sticky_cta_mobile(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_image_formats_modern(self):
        from qa_agent.checks.developer import _check_image_formats
        result = _check_image_formats(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_url_no_variant_pass(self):
        from qa_agent.checks.developer import _check_urls_no_variant
        result = _check_urls_no_variant(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_url_variant_fail(self):
        from qa_agent.checks.developer import _check_urls_no_variant
        snap = _make_snapshot(final_url="https://example.com/landing-page/a")
        result = _check_urls_no_variant(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_form_values_clean(self):
        from qa_agent.checks.developer import _check_form_values_no_codes
        result = _check_form_values_no_codes(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_form_values_with_codes(self):
        from qa_agent.checks.developer import _check_form_values_no_codes
        snap = _make_snapshot(forms=[{
            "id": "form1", "action": "/", "method": "post",
            "fields": [{"name": "hidden", "type": "hidden", "id": "h1",
                        "placeholder": "", "required": False,
                        "value": "{{campaign_id}}", "label": ""}],
        }])
        result = _check_form_values_no_codes(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_page_speed_pass(self):
        from qa_agent.checks.developer import _check_page_speed
        result = _check_page_speed(_make_snapshot(load_time_ms=1200), _make_context())
        assert result.status == CheckStatus.PASS

    def test_page_speed_fail(self):
        from qa_agent.checks.developer import _check_page_speed
        result = _check_page_speed(_make_snapshot(load_time_ms=5000), _make_context())
        assert result.status == CheckStatus.FAIL

    def test_gtm_present_pass(self):
        from qa_agent.checks.developer import _check_gtm_present
        snap = _make_snapshot(
            scripts=[{"src": "https://www.googletagmanager.com/gtm.js?id=GTM-ABCD1234", "inline_length": 0}]
        )
        result = _check_gtm_present(snap, _make_context())
        assert result.status == CheckStatus.PASS

    def test_gtm_present_fail(self):
        from qa_agent.checks.developer import _check_gtm_present
        result = _check_gtm_present(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.FAIL

    def test_footer_legal_links_pass(self):
        from qa_agent.checks.developer import _check_footer_legal_links
        snap = _make_snapshot(links=[
            {"href": "https://example.com/terms", "text": "Terms & Conditions", "target": "_blank", "tag": "a"},
            {"href": "https://example.com/privacy", "text": "Privacy Policy", "target": "_blank", "tag": "a"},
            {"href": "https://example.com/disclaimer", "text": "Disclaimer", "target": "_blank", "tag": "a"},
        ])
        result = _check_footer_legal_links(snap, _make_context())
        assert result.status == CheckStatus.PASS

    def test_footer_legal_links_missing_privacy(self):
        from qa_agent.checks.developer import _check_footer_legal_links
        snap = _make_snapshot(links=[
            {"href": "https://example.com/terms", "text": "Terms", "target": "_blank", "tag": "a"},
        ])
        result = _check_footer_legal_links(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_cache_headers_with_cdn(self):
        from qa_agent.checks.developer import _check_cache_headers
        snap = _make_snapshot(network_requests=[
            {"url": "https://cdn.example.com/app.js", "status": 200, "resource_type": "script", "size": 5000},
        ])
        result = _check_cache_headers(snap, _make_context())
        assert result.status == CheckStatus.PASS

    def test_cache_headers_no_cdn(self):
        from qa_agent.checks.developer import _check_cache_headers
        result = _check_cache_headers(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.WARN

    def test_full_developer_run(self):
        from qa_agent.checks.developer import run
        results = run(_make_snapshot(), _make_context())
        assert len(results) == 37
        statuses = [r.status for r in results]
        # With good defaults, we should get mostly PASS/WARN/SKIP, no unexpected errors
        assert CheckStatus.FAIL not in statuses or all(
            r.check_id in ("correct_group", "gtm_present", "footer_legal_links")
            for r in results if r.status == CheckStatus.FAIL
        )


# ────────────────────── Designer Checks ──────────────────────

class TestDesignerChecks:

    def test_fonts_loaded(self):
        from qa_agent.checks.designer import _check_fonts_correct
        result = _check_fonts_correct(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_fonts_system_only(self):
        from qa_agent.checks.designer import _check_fonts_correct
        snap = _make_snapshot(fonts_loaded=["Arial", "Helvetica", "sans-serif"])
        result = _check_fonts_correct(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_logo_no_link(self):
        from qa_agent.checks.designer import _check_logo_no_link
        result = _check_logo_no_link(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_full_designer_run(self):
        from qa_agent.checks.designer import run
        results = run(_make_snapshot(), _make_context())
        assert len(results) == 11


# ────────────────────── Copywriter Checks ──────────────────────

class TestCopywriterChecks:

    def test_meta_title_pass(self):
        from qa_agent.checks.copywriter import _check_meta_page_title
        result = _check_meta_page_title(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_meta_title_missing(self):
        from qa_agent.checks.copywriter import _check_meta_page_title
        snap = _make_snapshot(title="")
        result = _check_meta_page_title(snap, _make_context())
        assert result.status == CheckStatus.FAIL

    def test_form_labels_present(self):
        from qa_agent.checks.copywriter import _check_form_labels
        result = _check_form_labels(_make_snapshot(), _make_context())
        assert result.status == CheckStatus.PASS

    def test_full_copywriter_run(self):
        from qa_agent.checks.copywriter import run
        results = run(_make_snapshot(), _make_context())
        assert len(results) == 9


# ────────────────────── Full Pipeline ──────────────────────

class TestFullPipeline:

    def test_run_all(self):
        from qa_agent.checks import run_all
        results = run_all(_make_snapshot(), _make_context())
        # 37 dev + 11 designer + 9 copywriter = 57
        assert len(results) == 57

    def test_report_summary(self):
        from qa_agent.checks import run_all
        from qa_agent.config import QAReport
        results = run_all(_make_snapshot(), _make_context())
        report = QAReport(context=_make_context(), results=results)
        report.build_summary()
        assert report.summary["total"] == 57
        assert "developer" in report.summary["by_category"]
        assert "designer" in report.summary["by_category"]
        assert "copywriter" in report.summary["by_category"]

    def test_markdown_output(self, tmp_path):
        from qa_agent.checks import run_all
        from qa_agent.config import QAReport
        from qa_agent.reporter import to_markdown
        results = run_all(_make_snapshot(), _make_context())
        report = QAReport(context=_make_context(), results=results)
        path = to_markdown(report, str(tmp_path))
        assert path.endswith(".md")
        content = open(path).read()
        assert "QA Report" in content
        assert "Passed" in content

    def test_asana_comment_format(self):
        from qa_agent.checks import run_all
        from qa_agent.config import QAReport
        from qa_agent.reporter import to_asana_comment
        results = run_all(_make_snapshot(), _make_context())
        report = QAReport(context=_make_context(), results=results)
        comment = to_asana_comment(report)
        assert "QA Agent Report" in comment
        assert "Pass rate" in comment
