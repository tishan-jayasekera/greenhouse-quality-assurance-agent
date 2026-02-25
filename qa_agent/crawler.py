"""
qa_agent/crawler.py — Playwright-based landing page crawler.

Extracts DOM structure, network activity, console output, fonts, images,
forms, links, scripts, and compression headers for QA validation.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, BrowserContext, Response

from qa_agent.config import PageSnapshot, OUTPUT_DIR


DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 375, "height": 812}
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
NAVIGATION_TIMEOUT = 30_000  # ms
WAIT_AFTER_LOAD = 2_000  # ms — let JS settle


async def _extract_page_data(page: Page, viewport_label: str) -> dict:
    """Extract structured data from the current page state."""

    data = await page.evaluate("""() => {
        const result = {};

        // Title + meta
        result.title = document.title || '';
        const metaTitle = document.querySelector('meta[property="og:title"]')
            || document.querySelector('meta[name="title"]');
        result.meta_title = metaTitle ? metaTitle.getAttribute('content') || '' : '';

        // Fonts — get computed font families from visible elements
        const fontSet = new Set();
        document.querySelectorAll('h1,h2,h3,h4,p,a,span,li,button,label,input').forEach(el => {
            const ff = getComputedStyle(el).fontFamily;
            if (ff) ff.split(',').forEach(f => fontSet.add(f.trim().replace(/['"]/g, '')));
        });
        result.fonts = [...fontSet];

        // Images
        result.images = [...document.querySelectorAll('img')].map(img => ({
            src: img.src || img.dataset.src || '',
            alt: img.alt || '',
            width: img.width,
            height: img.height,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            format: (img.src || '').split('?')[0].split('.').pop().toLowerCase(),
            hasTransparency: (img.src || '').toLowerCase().endsWith('.png'),
        }));

        // Links
        result.links = [...document.querySelectorAll('a, [onclick], [role="link"]')].map(el => ({
            href: el.href || el.getAttribute('onclick') || '',
            text: (el.textContent || '').trim().substring(0, 200),
            target: el.target || '',
            tag: el.tagName.toLowerCase(),
        }));

        // Forms
        result.forms = [...document.querySelectorAll('form')].map(form => ({
            id: form.id || '',
            action: form.action || '',
            method: form.method || '',
            fields: [...form.querySelectorAll('input,select,textarea')].map(f => ({
                name: f.name || '',
                type: f.type || f.tagName.toLowerCase(),
                id: f.id || '',
                placeholder: f.placeholder || '',
                required: f.required,
                value: f.value || '',
                label: f.labels?.[0]?.textContent?.trim() || '',
            })),
        }));

        // Scripts
        result.scripts = [...document.querySelectorAll('script')].map(s => ({
            src: s.src || '',
            inline_length: s.src ? 0 : (s.textContent || '').length,
        }));

        // Sticky / fixed positioned elements (CTA bars)
        const stickyEls = [];
        document.querySelectorAll('*').forEach(el => {
            const pos = getComputedStyle(el).position;
            if (pos === 'fixed' || pos === 'sticky') {
                const text = (el.textContent || '').trim().substring(0, 200);
                if (text.length > 0 && text.length < 500) {
                    stickyEls.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || '',
                        classes: el.className || '',
                        text: text,
                        position: pos,
                    });
                }
            }
        });
        result.sticky_elements = stickyEls;

        // CTA buttons — anything that looks like a call-to-action
        result.cta_buttons = [...document.querySelectorAll(
            'button, a.btn, a.cta, [class*="cta"], [class*="button"], input[type="submit"]'
        )].map(el => ({
            text: (el.textContent || el.value || '').trim().substring(0, 200),
            tag: el.tagName.toLowerCase(),
            href: el.href || '',
            type: el.type || '',
        }));

        // Carousel detection
        result.carousels = [...document.querySelectorAll(
            '[class*="carousel"], [class*="slider"], [class*="swiper"], [class*="slick"]'
        )].map(el => ({
            classes: el.className,
            childCount: el.children.length,
            hasAutoplay: el.getAttribute('data-autoplay') || el.getAttribute('data-auto') || '',
        }));

        // Check for hover color changes on CTA buttons
        // (We can't fully test hover in extraction, but we check if CSS transitions exist)
        result.cta_has_transitions = [...document.querySelectorAll(
            'button, a.btn, [class*="cta"], [class*="button"], input[type="submit"]'
        )].some(el => {
            const t = getComputedStyle(el).transition;
            return t && t !== 'all 0s ease 0s' && t !== 'none';
        });

        // Logo link check
        const logo = document.querySelector('[class*="logo"] a, a [class*="logo"], header a:first-child');
        result.logo_link = logo ? (logo.href || logo.closest('a')?.href || '') : null;

        // Full HTML for deeper checks
        result.dom_html = document.documentElement.outerHTML;

        return result;
    }""")

    return data


async def _capture_network(page: Page) -> tuple[list[dict], str | None]:
    """Returns (network_requests, compression_type)."""
    requests = []
    compression = None

    def on_response(response: Response):
        nonlocal compression
        headers = response.headers
        if response.url == page.url:
            enc = headers.get("content-encoding", "")
            if "br" in enc:
                compression = "br"
            elif "gzip" in enc:
                compression = "gzip"

        requests.append({
            "url": response.url,
            "status": response.status,
            "resource_type": response.request.resource_type,
            "size": int(headers.get("content-length", 0)),
        })

    page.on("response", on_response)
    return requests, compression


async def crawl_page(
    url: str,
    output_dir: Optional[str] = None,
    capture_screenshots: bool = True,
) -> PageSnapshot:
    """
    Crawl a landing page and extract everything needed for QA checks.

    Args:
        url: The landing page URL to crawl.
        output_dir: Where to save screenshots (defaults to QA_OUTPUT_DIR).
        capture_screenshots: Whether to capture desktop/mobile screenshots.

    Returns:
        PageSnapshot with all extracted data.
    """
    out = Path(output_dir or OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ── Desktop crawl ──
        context = await browser.new_context(
            viewport=DESKTOP_VIEWPORT,
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # Collect console messages
        console_errors = []
        console_warnings = []

        def on_console(msg):
            entry = {
                "type": msg.type,
                "text": msg.text,
                "url": msg.location.get("url", "") if msg.location else "",
                "line": msg.location.get("lineNumber", 0) if msg.location else 0,
            }
            if msg.type == "error":
                console_errors.append(entry)
            elif msg.type == "warning":
                console_warnings.append(entry)

        page.on("console", on_console)

        # Collect network
        network_requests = []
        compression = None

        async def on_response(response):
            nonlocal compression
            try:
                headers = response.headers
                if response.url.rstrip("/") == url.rstrip("/"):
                    enc = headers.get("content-encoding", "")
                    if "br" in enc:
                        compression = "br"
                    elif "gzip" in enc:
                        compression = "gzip"
                network_requests.append({
                    "url": response.url,
                    "status": response.status,
                    "resource_type": response.request.resource_type,
                    "size": int(headers.get("content-length", "0") or "0"),
                })
            except Exception:
                pass

        page.on("response", on_response)

        # Navigate
        t0 = time.time()
        redirect_chain = []

        def on_request(request):
            if request.is_navigation_request():
                redirect_chain.append(request.url)

        page.on("request", on_request)

        response = await page.goto(url, wait_until="networkidle", timeout=NAVIGATION_TIMEOUT)
        await page.wait_for_timeout(WAIT_AFTER_LOAD)
        load_time_ms = int((time.time() - t0) * 1000)

        status_code = response.status if response else 0
        final_url = page.url

        # Extract DOM data (desktop)
        desktop_data = await _extract_page_data(page, "desktop")

        # Screenshot desktop
        ss_desktop = None
        if capture_screenshots:
            ss_desktop = str(out / "screenshot_desktop.png")
            await page.screenshot(path=ss_desktop, full_page=True)

        await context.close()

        # ── Mobile crawl ──
        mobile_context = await browser.new_context(
            viewport=MOBILE_VIEWPORT,
            user_agent=MOBILE_UA,
            is_mobile=True,
            ignore_https_errors=True,
        )
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto(url, wait_until="networkidle", timeout=NAVIGATION_TIMEOUT)
        await mobile_page.wait_for_timeout(WAIT_AFTER_LOAD)

        mobile_data = await _extract_page_data(mobile_page, "mobile")

        ss_mobile = None
        if capture_screenshots:
            ss_mobile = str(out / "screenshot_mobile.png")
            await mobile_page.screenshot(path=ss_mobile, full_page=True)

        await mobile_context.close()
        await browser.close()

    # Estimate page size from network
    page_size = sum(r.get("size", 0) for r in network_requests)

    return PageSnapshot(
        url=url,
        final_url=final_url,
        title=desktop_data["title"],
        meta_title=desktop_data["meta_title"],
        status_code=status_code,
        console_errors=console_errors,
        console_warnings=console_warnings,
        network_requests=network_requests,
        fonts_loaded=desktop_data["fonts"],
        images=desktop_data["images"],
        links=desktop_data["links"],
        forms=desktop_data["forms"],
        scripts=desktop_data["scripts"],
        sticky_elements=desktop_data["sticky_elements"],
        dom_html=desktop_data["dom_html"],
        mobile_snapshot={
            "sticky_elements": mobile_data["sticky_elements"],
            "forms": mobile_data["forms"],
            "images": mobile_data["images"],
            "cta_buttons": mobile_data["cta_buttons"],
            "links": mobile_data["links"],
            "fonts": mobile_data["fonts"],
        },
        compression=compression,
        screenshot_desktop=ss_desktop,
        screenshot_mobile=ss_mobile,
        redirect_chain=redirect_chain,
        page_size_bytes=page_size,
        load_time_ms=load_time_ms,
    )


def crawl_sync(url: str, output_dir: str | None = None, screenshots: bool = True) -> PageSnapshot:
    """Synchronous wrapper for crawl_page."""
    return asyncio.run(crawl_page(url, output_dir, screenshots))
