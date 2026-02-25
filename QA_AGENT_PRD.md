# Product Requirements Document: QA Checklist Agent
## Social Garden — Advertising Rollout Workflow Automation

**Version:** 1.0  
**Date:** 25 February 2026  
**Owner:** Social Garden — Data & Analytics  
**Platform Target:** Google Cloud Code via Anti-Gravity  
**Status:** Phase 1 MVP Complete → Phase 2 Planning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Strategic Context: The Advertising Rollout Workflow](#2-strategic-context)
3. [Workflow Anatomy: Complete 229-Task Breakdown](#3-workflow-anatomy)
4. [Agent Architecture: Process-Based Agent Framework](#4-agent-architecture)
5. [Phase 1 — QA Checklist Agent: Complete Build Specification](#5-phase-1-qa-checklist-agent)
6. [Phase 2–4 Roadmap: Progressive Agent Expansion](#6-phase-2-4-roadmap)
7. [Deployment Architecture: Google Cloud Code / Anti-Gravity](#7-deployment-architecture)
8. [Integration Layer: Asana MCP + Toolchain](#8-integration-layer)
9. [Success Metrics & Acceptance Criteria](#9-success-metrics)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

### What We're Building

An autonomous QA Checklist Agent that validates landing pages against Social Garden's 62-item quality assurance checklist (42 Developer + 11 Designer + 9 Copywriter checks) using headless browser automation. The agent reads task context from Asana, crawls the target URL at desktop (1440px) and mobile (375px) viewports, runs 53 programmatic checks, and posts structured pass/fail results back to Asana as task comments — with screenshots as evidence.

### Why It Matters

QA & Approvals tasks represent **62 of 229 tasks (27%)** in Social Garden's advertising rollout workflow. Each campaign's QA cycle currently requires a human to manually walk through every checklist item across three role-based checklists (Developer, Designer, Copywriter), consuming approximately 45–60 minutes per campaign. With ~20 campaigns per month, this represents 15–20 hours/month of repetitive manual validation work.

The QA Agent automates ~70% of these checks deterministically (the remaining ~30% are subjective visual/UX judgments that require human review). Net impact: QA time per campaign drops from 45–60 minutes to 10–15 minutes of human review on the agent-flagged items only.

### Where It Fits

The QA Agent is **Phase 1** of a broader agent automation strategy across Social Garden's entire advertising rollout workflow. The 229-task workflow has been analysed, segmented into 9 process buckets, and scored for automation potential. The QA Agent was selected as Phase 1 because it has the highest combination of:

- **Task volume:** 62 tasks (largest single parent-task cluster)
- **Determinism:** Most checks are binary pass/fail with no ambiguity
- **Zero external API dependency:** Headless browser only (no paid API keys needed)
- **Immediate ROI:** Time savings from day one with zero change management friction

### What Exists Today

| Artifact | Status | Description |
|----------|--------|-------------|
| Process Flowchart Tool | ✅ Complete | Interactive HTML visualization of the full 229-task workflow with agent automation planning overlays |
| Workflow Enrichment Engine | ✅ Complete | Deterministic tool detection (14 SaaS platforms), process classification (9 buckets), automation scoring (0.0–5.0), agent candidate flagging |
| QA Agent MVP | ✅ Complete | Functional Python codebase: 53 automated checks, Playwright crawler, CLI interface, Asana integration, 26 passing tests |
| This PRD | ✅ This document | Complete build specification for Cloud Code / Anti-Gravity deployment |

---

## 2. Strategic Context: The Advertising Rollout Workflow

### 2.1 What Is the Advertising Rollout?

Social Garden operates a templated advertising rollout process for new client campaigns. Every new client engagement follows a structured sequence from signed SOW through to monthly reporting. This process is managed entirely in Asana as a project template with 229 tasks organized into sections, parent tasks, and subtasks.

The workflow covers the full lifecycle:

**Intake → Brief → Setup → Creative → Build → QA → Launch → Report → Optimise**

Each campaign follows this process with minor variations depending on channel mix (Google Ads, Meta Ads, TikTok Ads, LinkedIn Ads, optional Display/PMax) and client complexity.

### 2.2 The Asana Project Structure

The workflow is organized in Asana with the following section structure:

| Section | Task Count | Purpose |
|---------|-----------|---------|
| 📂 Agreement & Kick-Off | 12 | SOW confirmation, WIP docs, kickoff meetings |
| 🎨 Campaign Concept Development | 8 | Creative briefs, concept development, Figma designs |
| 🛠️ Build Campaign Architecture | 11 | Campaign shells, platform builds, keyword research |
| 🛠️ Finalise Campaign Deliverables | 6 | Asset refinement, landing page completion |
| 🔁 Final QA, Ad Upload & Client Review | 5 | QA checklists, ad uploads, client sign-off |
| 🚀 Campaign Launch | 4 | Go-live, launch verification |
| 📖 Reporting | 6 | Monthly reports, dashboards |
| 📊 Optimisation & Performance Tracking | 2 | Ongoing optimization cycles |
| 🏁 Close, Reflect & Resign | 6 | Campaign wrap-up, retrospectives |
| (Unassigned subtasks) | 169 | Subtasks nested under parent tasks above |

**Total: 229 tasks** (60 root-level + 169 subtasks under parent tasks)

### 2.3 Role Distribution Across the Workflow

The workflow involves 7 distinct functional roles:

| Role | Task Count | % of Workflow | Primary Activities |
|------|-----------|---------------|-------------------|
| QA / Compliance | 71 | 31% | QA checklists, peer reviews, approval gates |
| Account Management | 68 | 30% | Client comms, kickoffs, sign-offs, documentation |
| Paid Media | 24 | 10% | Campaign builds, ad uploads, platform config |
| Reporting / Analytics | 22 | 10% | Monthly reports, dashboards, performance analysis |
| Design | 19 | 8% | Figma designs, creative assets, visual QA |
| Technical / Development | 13 | 6% | Landing pages, GTM, tracking, integrations |
| Copy | 8 | 3% | Copy docs, messaging, content QA |
| General | 4 | 2% | Administrative, unclassified |

### 2.4 Tool Ecosystem Detected in the Workflow

The enrichment engine scans every task's name, notes, and tags for SaaS tool references. Across all 229 tasks:

| Tool | Tasks Referencing | Primary Process Context |
|------|------------------|----------------------|
| Asana | 41 | Cross-cutting (task management) |
| Google Docs | 24 | Briefing, documentation, reporting |
| Google Ads | 13 | Campaign builds, keyword research |
| Google Drive | 7 | Asset storage, shared folders |
| Figma | 5 | Creative design, design QA |
| Meta Ads | 4 | Campaign builds, ad uploads |
| TikTok Ads | 3 | Campaign builds |
| Whimsical | 3 | Reporting templates |
| Slack | 2 | Communication, access requests |
| WorkflowMax | 2 | Job numbers, billing, SOW |
| Google Sheets | 1 | Data tracking |
| Canva | 1 | Reporting templates |
| Pipedrive | 1 | CRM integration |

### 2.5 Dependency Structure

The workflow contains **174 edges** (5 explicit dependencies + 169 hierarchy edges from parent→subtask relationships). The dependency graph is largely hierarchical — most task sequencing is implied by section ordering rather than explicit Asana dependencies. This is important context: the process flow is convention-driven, which means agents need to understand section-level sequencing, not just follow explicit dependency chains.

---

## 3. Workflow Anatomy: Complete 229-Task Breakdown

### 3.1 Process Segmentation

Every task in the workflow has been classified into one of 9 process buckets using deterministic regex scoring against task names, notes, tags, sections, and detected tools:

| Process Bucket | Task Count | % | Automation Score (Avg) | Agent Candidates |
|---------------|-----------|---|----------------------|-----------------|
| Creative & Assets | 47 | 21% | Low | 1 |
| Campaign Build & Launch | 44 | 19% | Medium-High | 6 |
| Unclassified | 53 | 23% | Low | 0 |
| Briefing & Planning | 20 | 9% | Low | 0 |
| Reporting & Optimisation | 20 | 9% | Medium | 3 |
| Tracking & Integrations | 13 | 6% | Medium | 0 |
| QA & Approvals | 12 | 5% | Low | 0 |
| Intake & Agreements | 11 | 5% | Medium-High | 2 |
| Access & Setup | 9 | 4% | Low | 0 |

**Note on "Unclassified":** The 53 unclassified tasks are predominantly QA checklist subtasks (42 Developer + 11 Designer). They don't match process bucket keywords because their names are procedural check items (e.g., "Font family, colour, alignment and size match the design") rather than process-descriptive names. Despite being classified as "Unclassified" by the enrichment engine, they are definitively QA tasks and are the primary target of the QA Agent.

### 3.2 Agent Candidates (Automation Score ≥ 2.5)

13 tasks across the workflow score above the agent candidate threshold. These are tasks with multiple detected tool integrations, URLs in their notes, and keywords indicating template/checklist/report patterns:

| Score | Task | Process | Tools Detected |
|-------|------|---------|---------------|
| 3.6 | Confirm Signed SOW & Service Agreement Received | Intake & Agreements | Asana, Google Docs, Slack, WorkflowMax |
| 3.4 | Add Campaign to WIP Doc | Intake & Agreements | Asana, Google Docs, WorkflowMax |
| 3.4 | Load Meta Ads | Campaign Build & Launch | Asana, Google Drive, Meta Ads |
| 3.4 | Load RSA Google Ads | Campaign Build & Launch | Asana, Google Ads, Google Drive |
| 3.4 | Optional · Load Performance Max Ads | Campaign Build & Launch | Asana, Google Ads, Google Drive |
| 3.4 | Optional · Google Display Ad Upload | Campaign Build & Launch | Asana, Google Ads, Google Drive |
| 2.9 | Creative Concept Development (Design + Copy) | Creative & Assets | Asana, Figma, Google Docs |
| 2.7 | Keyword Research and Negative Lists | Campaign Build & Launch | Google Ads, Google Docs |
| 2.7 | Optional · Performance Max Shell Build | Campaign Build & Launch | Asana, Google Ads |
| 2.7 | Optional · Google Display Network Shell Build | Campaign Build & Launch | Asana, Google Ads |
| 2.7 | Month 1 Report | Reporting & Optimisation | Asana, Whimsical |
| 2.7 | Month 2 Report | Reporting & Optimisation | Asana, Whimsical |
| 2.7 | Month 3 Report | Reporting & Optimisation | Asana, Whimsical |

### 3.3 The QA Cluster: 62 Tasks in Detail

The QA cluster is the single largest coherent task group in the workflow, organized under three parent tasks:

#### 🔎 Developer QA — Post Dev Checklist (42 subtasks)

These 42 items form the most granular, deterministic checklist in the entire workflow. They cover:

**Page Structure & Configuration (Items 1-2)**
1. Ensure landing page is added to correct Unbounce group
2. For updates, done on new variant unless instructed to update live variant

**Visual Fidelity (Items 3-5)**
3. Font family, colour, alignment and size match the design
4. Images exactly the same as the ones in the design
5. Use PNG for transparent images only, otherwise always JPG

**Mobile Experience (Items 6-7)**
6. Sticky CTA bar added on mobile and functioning
7. Sticky CTA bar has correct CTA text matching main CTA buttons

**Content Accuracy (Items 8-9)**
8. Price updates reflected on all necessary sections (e.g., footer)
9. Copy exactly matches the copy doc

**Interactive Elements (Items 10-13)**
10. CTA button scrolls to correct form location
11. CTA buttons change to correct colour on hover
12. Carousel functioning correctly with correct images
13. Carousel auto-transition speed allows time to read content

**Form Validation (Items 14-23)**
14. Form fields match design and brief
15. Field names maintained or use standardised names (inform MA team if changed)
16. Form uses id `#lp-pom-form-42`
17. Placeholder text lighter than typed text
18. Form validation working on desktop and mobile
19. Form field values do not contain codes
20. Forms tested — submits and redirects to TYP
21. Lead submission works, download functioning
22. SMS Verification client name updated
23. SMS verification showing and functioning on mobile

**Page Flow & Redirects (Items 24-28)**
24. Landing page redirects to thank you / profile page
25. Hover buttons on thank-you page match design
26. Thank-you page redirects to confirmation page (or popup)
27. Thank-you page identical to final design
28. Links carry over ULI parameters

**Quality Assurance (Items 29-35)**
29. UX testing across all pages (click everything clickable)
30. Page loading speed < 4 seconds first paint on Google Speed Test
31. Page titles (LP, TYP, confirmation) correct in metadata
32. GTM implemented and set up correctly
33. No console errors after code edits
34. Cleanup unused scripts
35. URLs do not contain variant letter in redirects

**Performance Optimisation (Items 36-40)**
36. Page load time measured with PageSpeed Insights / Lighthouse
37. Images compressed, modern formats (WebP), lazy loading
38. JS minified, compressed, unused code removed, critical JS async
39. Caching policies verified, CDN for static assets
40. Gzip or Brotli compression enabled for text resources

**Compliance & Final (Items 41-42)**
41. Terms & Conditions, Privacy Policy, Disclaimer links verified in footer
42. Peer review completed

#### 👨🏾‍🎨 Designer QA — Post Dev Check (11 subtasks)

1. Developed page matches initial design as closely as possible
2. Check padding and spacing
3. Double check fonts are correct
4. Click all buttons to check links
5. Check all scroll animations, transitions and hover effects
6. Check mobile design too
7. Sticky CTA on mobile
8. Assign to copywriter
9. Check PageSpeed insights
10. Check logo for link (should not link out)
11. Check image sizes

#### ✍️ Copywriter QA — Post Dev Check (9 subtasks)

1. Check all below for both Desktop and Mobile
2. Consistent spelling and grammar including capitalisation and tense
3. Page flow and hierarchy of information
4. Accessibility: font size on mobile and colour contrast
5. Meta page title
6. General UX: spacing, sticky CTA buttons, interactive elements
7. Check split test set up in Unbounce
8. Add page name and full Unbounce URL to CRO vault landing page list tab
9. Check PageSpeed insights

---

## 4. Agent Architecture: Process-Based Agent Framework

### 4.1 The Agent Model

Each of the 9 process buckets maps to a named agent. The agent label is simply `{Process Bucket} Agent`. The framework is designed so that each agent is:

- **Scoped to a process bucket** — clear ownership boundaries
- **Triggered by Asana task context** — reads task metadata to determine actions
- **Tool-aware** — knows which SaaS tools are relevant to its process
- **Composable** — agents can hand off to each other via Asana task transitions

| Agent | Process Scope | Task Count | Suggested Automation Operations |
|-------|--------------|-----------|-------------------------------|
| **Intake & Agreements Agent** | SOW, billing, kickoff | 11 | Extract SOW metadata → sync WorkflowMax; generate kickoff pack; auto-create Google Docs from templates |
| **Briefing & Planning Agent** | Briefs, strategy, requirements | 20 | Convert brief → structured plan + checklist in Google Doc; summarise requirements + flag missing info |
| **Access & Setup Agent** | Permissions, credentials, platform access | 9 | Track access requests, auto-remind in Slack, validate all accounts present before build |
| **Creative & Assets Agent** | Design, copy, assets | 47 | Validate asset specs (sizes, formats), flag missing creatives, generate copy variants |
| **Tracking & Integrations Agent** | Pixels, UTM, GTM, analytics | 13 | Run tracking checklist: UTMs/pixels/tags present; generate integration test plan |
| **Campaign Build & Launch Agent** | Platform builds, ad uploads, launch | 44 | Pre-launch config QA (naming, targeting, budgets) + proof screenshots; compile launch checklist |
| **QA & Approvals Agent** | QA checklists, peer review, sign-off | 12 + 62 subtasks | **← THIS IS THE QA CHECKLIST AGENT (Phase 1)** |
| **Reporting & Optimisation Agent** | Reports, dashboards, performance | 20 | Auto-generate performance summary + next actions; detect anomalies; propose optimisation experiments |
| **Unclassified Agent** | Administrative, misc | 53 | Varies — most are QA subtasks already covered by QA Agent |

### 4.2 Automation Scoring Methodology

Each task receives a deterministic automation score (0.0–5.0):

- **+0.7 per detected tool** (capped at 3.5) — more tool integrations = more automatable
- **+0.3 if any URL present** in task notes — indicates linked resources
- **+0.5 if keywords match** (template, checklist, report, QA, verify, sync)
- **+0.5 if high-automation process** (Tracking, Campaign Build, Reporting, Intake)
- **Agent candidate threshold: ≥ 2.5**

Current distribution: 13 of 229 tasks (5.7%) score above the candidate threshold. However, this understates automation potential because the scoring doesn't account for checklist subtasks (which are highly automatable despite low individual scores due to minimal tool references in their task names).

### 4.3 Why QA Agent First

| Criterion | QA Agent | Next Best (Campaign Build Agent) |
|-----------|----------|--------------------------------|
| Task volume | 62 tasks (27%) | 44 tasks (19%) |
| Determinism | ~70% fully automatable | ~30% automatable (requires platform APIs) |
| External API needs | None (headless browser only) | Google Ads API, Meta Ads API, etc. |
| Implementation complexity | Medium (Playwright + HTML parsing) | High (multi-platform API auth) |
| Change management | Zero (agent augments, doesn't replace) | Medium (touches live ad platforms) |
| Time to value | Days | Weeks–months |

---

## 5. Phase 1 — QA Checklist Agent: Complete Build Specification

### 5.1 System Overview

The QA Checklist Agent is a Python application that:

1. **Receives a target URL** (either directly via CLI, or extracted from an Asana task's notes/custom fields)
2. **Crawls the page** using Playwright headless browser at two viewports (desktop 1440×900, mobile 375×812)
3. **Runs 53 automated checks** organized into three role-based check modules (Developer, Designer, Copywriter)
4. **Generates a structured report** (terminal output, markdown file, JSON data)
5. **Posts results to Asana** as a formatted comment on the originating task, with pass/fail summary and flagged items

### 5.2 Project Structure

```
qa-agent/
├── qa_agent/
│   ├── __init__.py              # Package init, version
│   ├── config.py                # Configuration constants
│   ├── crawler.py               # Playwright page crawler
│   ├── checks/
│   │   ├── __init__.py          # Check registry
│   │   ├── developer.py         # 33 Developer QA checks
│   │   ├── designer.py          # 11 Designer QA checks
│   │   └── copywriter.py        # 9 Copywriter QA checks
│   ├── reporter.py              # Output formatting (terminal + markdown + JSON)
│   ├── asana_client.py          # Asana API integration
│   └── cli.py                   # CLI entry point (Click)
├── tests/
│   └── test_checks.py           # 26 unit tests
├── run_qa.py                    # Simple runner script
├── requirements.txt             # Dependencies
└── README.md                    # Setup and usage guide
```

### 5.3 Dependencies

```
playwright>=1.40
click>=8.0
requests>=2.28
Pillow>=10.0
```

Playwright requires a one-time browser install: `playwright install chromium`

### 5.4 Core Components — Detailed Specifications

#### 5.4.1 Crawler (`crawler.py`)

The crawler is the foundation. It launches a headless Chromium browser, navigates to the target URL, and extracts a comprehensive `PageSnapshot` data structure.

**PageSnapshot Schema:**

```python
@dataclass
class PageSnapshot:
    url: str
    final_url: str              # After redirects
    status_code: int
    title: str                  # <title> tag content
    meta_tags: dict             # All <meta> tags as key-value
    
    # DOM extraction
    headings: list              # All h1-h6 with text + level
    images: list                # All <img> with src, alt, width, height, format
    links: list                 # All <a> with href, text, target
    forms: list                 # All <form> with id, action, method, fields[]
    scripts: list               # All <script> with src, inline content hash
    stylesheets: list           # All <link rel=stylesheet> with href
    
    # Computed
    fonts_used: set             # CSS font-family values found in computed styles
    colors_used: dict           # CSS color values mapped to selectors
    console_errors: list        # Browser console errors captured during load
    network_requests: list      # All network requests with URL, status, size, type
    
    # Performance
    load_time_ms: int           # DOMContentLoaded timing
    first_paint_ms: int         # First Contentful Paint
    page_size_bytes: int        # Total transfer size
    
    # Screenshots
    desktop_screenshot: bytes   # Full-page screenshot at 1440px
    mobile_screenshot: bytes    # Full-page screenshot at 375px
    
    # Mobile-specific
    has_sticky_cta: bool        # Detected position:fixed/sticky CTA on mobile
    sticky_cta_text: str        # Text content of the sticky CTA
    viewport_meta: str          # <meta name="viewport"> content
```

**Crawl Sequence:**

1. Launch Chromium with `--headless --no-sandbox`
2. Set desktop viewport (1440×900)
3. Navigate to URL, wait for `networkidle`
4. Capture console errors via `page.on('console')`
5. Capture network requests via `page.on('response')`
6. Extract DOM data via `page.evaluate()` JavaScript injection
7. Take full-page desktop screenshot
8. Resize to mobile viewport (375×812)
9. Re-evaluate mobile-specific elements (sticky CTA detection)
10. Take full-page mobile screenshot
11. Compute performance metrics from `performance.timing` API
12. Return assembled `PageSnapshot`

**Critical Implementation Notes:**

- Use `page.wait_for_load_state('networkidle')` with a 30-second timeout
- Capture `page.on('pageerror')` separately from console messages for JavaScript exceptions
- For sticky CTA detection: query `document.querySelectorAll('[style*="position: fixed"], [style*="position: sticky"]')` and filter for elements containing button/anchor tags with CTA-like text
- Network request capture must include response headers for compression detection (Gzip/Brotli check)
- Screenshot format: PNG for evidence, JPEG at 80% quality for Asana upload (size limits)

#### 5.4.2 Developer Checks (`checks/developer.py`)

33 automated checks mapped from the 42-item Asana checklist. Items not automated are flagged as `SKIP` with reason "Requires manual visual review" or "Requires external context."

**Check Result Schema:**

```python
@dataclass
class CheckResult:
    check_id: str               # e.g., "DEV-001"
    name: str                   # Human-readable check name
    status: str                 # PASS | FAIL | WARN | SKIP
    message: str                # Detail message
    evidence: Optional[str]     # Screenshot path, DOM snippet, etc.
    asana_item: str             # Original Asana checklist item text
```

**Complete Developer Check Mapping:**

| ID | Asana Item | Automated? | Check Logic |
|----|-----------|-----------|-------------|
| DEV-001 | Correct Unbounce group | SKIP | Requires Unbounce API (Phase 2) |
| DEV-002 | New variant for updates | SKIP | Requires Unbounce API (Phase 2) |
| DEV-003 | Font family/colour/alignment match design | PARTIAL | Extracts computed fonts; full design comparison requires Figma API (Phase 2) |
| DEV-004 | Images match design | SKIP | Requires Figma API visual diff (Phase 2) |
| DEV-005 | PNG only for transparency | ✅ | Scan all `<img>` → check format: PNG with alpha channel OK, PNG without alpha → WARN, JPG with transparency → FAIL |
| DEV-006 | Sticky CTA on mobile | ✅ | Mobile viewport: query fixed/sticky positioned elements with CTA-like text |
| DEV-007 | Sticky CTA correct text | PARTIAL | Detects sticky CTA text; matching to brief requires copy doc context |
| DEV-008 | Price updates in all sections | SKIP | Requires knowledge of correct price from brief |
| DEV-009 | Copy matches copy doc | SKIP | Requires Google Docs API (Phase 2) |
| DEV-010 | CTA scrolls to form | ✅ | Click CTA → verify form element is in viewport via `isIntersectingViewport()` |
| DEV-011 | CTA hover colour change | ✅ | Get computed color → trigger `:hover` via `page.hover()` → compare computed color |
| DEV-012 | Carousel functioning | ✅ | Detect carousel container → verify navigation works → check slide count |
| DEV-013 | Carousel transition speed | ✅ | Detect auto-transition → measure interval → flag if < 3 seconds |
| DEV-014 | Form fields match design | PARTIAL | Extract form field names/types; full comparison requires design context |
| DEV-015 | Field names standardised | ✅ | Check field names against standardised list: `first_name`, `last_name`, `email`, `phone`, etc. |
| DEV-016 | Form ID `#lp-pom-form-42` | ✅ | Query `document.querySelector('#lp-pom-form-42')` → PASS if exists |
| DEV-017 | Placeholder lighter than text | ✅ | Compare computed color of `::placeholder` vs input text color |
| DEV-018 | Form validation working | ✅ | Submit empty form → verify validation messages appear on required fields |
| DEV-019 | No codes in field values | ✅ | Check all form field `value` attributes for code-like patterns |
| DEV-020 | Form submits to TYP | ✅ | Fill test data → submit → verify redirect to thank-you page URL pattern |
| DEV-021 | Lead submission + download | PARTIAL | Can test submission; download verification requires knowing expected asset |
| DEV-022 | SMS verification client name | SKIP | Requires SMS trigger (external integration) |
| DEV-023 | SMS verification on mobile | SKIP | Requires SMS trigger (external integration) |
| DEV-024 | LP → TYP redirect | ✅ | Submit form → check redirect URL contains "thank" or "thankyou" pattern |
| DEV-025 | TYP hover buttons match design | PARTIAL | Can detect hover state changes; design matching requires Figma |
| DEV-026 | TYP → confirmation redirect | ✅ | Navigate TYP → check for redirect or popup trigger |
| DEV-027 | TYP matches design | SKIP | Requires Figma visual diff (Phase 2) |
| DEV-028 | ULI parameters carried over | ✅ | Add UTM params to LP URL → submit → verify params present in TYP URL |
| DEV-029 | UX testing all clickable | ✅ | Find all interactive elements → click each → verify no dead links/errors |
| DEV-030 | Page speed < 4s | ✅ | Measure First Contentful Paint → FAIL if > 4000ms |
| DEV-031 | Page titles correct | ✅ | Extract `<title>` from LP, TYP, confirmation pages → verify non-empty and reasonable |
| DEV-032 | GTM implemented | ✅ | Check for `googletagmanager.com` in network requests or `<script>` srcs |
| DEV-033 | No console errors | ✅ | Capture `page.on('pageerror')` and `console.error` → FAIL if any present |
| DEV-034 | Cleanup unused scripts | ✅ | Detect scripts that loaded but didn't execute (coverage API) or 404'd |
| DEV-035 | URLs no variant letter | ✅ | Check redirect URLs for patterns like `/a/`, `/b/` variant suffixes |
| DEV-036 | PageSpeed / Lighthouse score | ✅ | Run Lighthouse via `page.evaluate` or subprocess → extract performance score |
| DEV-037 | Images compressed + WebP + lazy | ✅ | Check image sizes > threshold, format (WebP preferred), `loading="lazy"` attribute |
| DEV-038 | JS minified + async | ✅ | Check `<script>` for `async`/`defer` attributes; detect unminified JS (whitespace ratio) |
| DEV-039 | Caching + CDN | ✅ | Check `Cache-Control` and `CDN-Cache-Status` response headers |
| DEV-040 | Gzip/Brotli compression | ✅ | Check `Content-Encoding` response header for `gzip` or `br` |
| DEV-041 | T&C / Privacy / Disclaimer links | ✅ | Find footer links matching "terms", "privacy", "disclaimer" → verify href not empty and not 404 |
| DEV-042 | Peer review | SKIP | Human workflow step — not automatable |

**Automation Summary: 33 of 42 checks automated (79%). 5 SKIP (require external APIs/context). 4 PARTIAL (automated with caveats).**

#### 5.4.3 Designer Checks (`checks/designer.py`)

| ID | Asana Item | Automated? | Check Logic |
|----|-----------|-----------|-------------|
| DES-001 | Page matches design | SKIP | Requires Figma API visual diff (Phase 2) |
| DES-002 | Padding and spacing | PARTIAL | Can extract computed padding/margin; comparison requires design spec |
| DES-003 | Fonts correct | ✅ | Extract all computed font-family values → report unique set |
| DES-004 | Button links work | ✅ | Click all buttons → verify navigation/scroll behavior |
| DES-005 | Scroll animations + hover effects | ✅ | Scroll page → detect CSS transitions/transforms on visible elements |
| DES-006 | Mobile design check | ✅ | Mobile viewport rendering captured in screenshot |
| DES-007 | Sticky CTA mobile | ✅ | Same as DEV-006 |
| DES-008 | Assign to copywriter | SKIP | Asana workflow action (Phase 2: webhook trigger) |
| DES-009 | PageSpeed insights | ✅ | Same as DEV-036 |
| DES-010 | Logo link check | ✅ | Find logo image → check parent `<a>` → verify href is null/empty or same-page (should NOT link out) |
| DES-011 | Image sizes | ✅ | Check all images for dimensions and file size → flag oversized |

**Automation Summary: 11 checks, 8 automated (73%), 1 PARTIAL, 2 SKIP.**

#### 5.4.4 Copywriter Checks (`checks/copywriter.py`)

| ID | Asana Item | Automated? | Check Logic |
|----|-----------|-----------|-------------|
| COPY-001 | Check desktop and mobile | ✅ | Dual viewport crawl provides both |
| COPY-002 | Spelling + grammar | ✅ | Extract all visible text → run basic spell check (can enhance with LLM in Phase 3) |
| COPY-003 | Page flow + hierarchy | PARTIAL | Can detect heading hierarchy (H1 → H2 → H3 order); content flow is subjective |
| COPY-004 | Accessibility: font size + contrast | ✅ | Check computed font sizes on mobile (flag < 14px); calculate WCAG contrast ratios |
| COPY-005 | Meta page title | ✅ | Same as DEV-031 |
| COPY-006 | General UX | PARTIAL | Can check spacing, sticky CTA presence; full UX assessment is subjective |
| COPY-007 | Split test in Unbounce | SKIP | Requires Unbounce API (Phase 2) |
| COPY-008 | CRO vault update | SKIP | Requires Google Sheets API write (Phase 2) |
| COPY-009 | PageSpeed insights | ✅ | Same as DEV-036 |

**Automation Summary: 9 checks, 5 automated (56%), 2 PARTIAL, 2 SKIP.**

### 5.5 CLI Interface

Three commands covering the main usage patterns:

```bash
# Direct URL scan — no Asana context needed
python run_qa.py run https://landing.example.com \
  --checks all \
  --output report.md \
  --screenshots ./shots/

# Single Asana task — reads URL from task notes, posts results back
python run_qa.py asana TASK_ID \
  --post-results \
  --asana-token $ASANA_PAT

# Batch scan — processes all incomplete tasks in an Asana section
python run_qa.py batch \
  --project-id PROJECT_ID \
  --section "🔁 Final QA, Ad Upload & Client Review" \
  --asana-token $ASANA_PAT
```

**CLI Options (all commands):**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--checks` | Choice | `all` | Which check modules: `all`, `developer`, `designer`, `copywriter` |
| `--output` | Path | None | Save markdown report to file |
| `--json` | Path | None | Save JSON results to file |
| `--screenshots` | Path | `./screenshots` | Directory for screenshot evidence |
| `--desktop-width` | Int | 1440 | Desktop viewport width |
| `--mobile-width` | Int | 375 | Mobile viewport width |
| `--timeout` | Int | 30 | Page load timeout in seconds |
| `--verbose` | Flag | False | Show detailed check output |

**Asana-specific options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--asana-token` | String | `$ASANA_PAT` env | Asana Personal Access Token |
| `--post-results` | Flag | False | Post results as Asana task comment |
| `--project-id` | String | None | Asana project GID for batch mode |
| `--section` | String | None | Asana section name to scan |

### 5.6 Report Output Format

#### Terminal Output

```
╔══════════════════════════════════════════════════════════════╗
║  QA CHECKLIST AGENT — Landing Page Validation Report        ║
╠══════════════════════════════════════════════════════════════╣
║  URL:    https://landing.example.com                        ║
║  Date:   2026-02-25 10:30:00 AEST                           ║
║  Checks: 53 total | 38 PASS | 5 FAIL | 3 WARN | 7 SKIP    ║
╚══════════════════════════════════════════════════════════════╝

🔎 DEVELOPER CHECKS (33)
  ✅ DEV-005  Image format compliance         PNG/JPG usage correct
  ✅ DEV-006  Mobile sticky CTA present       Found: "Get Started"
  ❌ DEV-016  Form ID #lp-pom-form-42         Form ID is "#lp-pom-form-37"
  ❌ DEV-033  Console errors                  3 errors found
  ⚠️  DEV-037  Image optimisation              2 images > 500KB, no WebP
  ⏭️  DEV-001  Unbounce group                  Requires Unbounce API
  ...

👨🏾‍🎨 DESIGNER CHECKS (11)
  ✅ DES-003  Fonts detected                  Arial, Inter, system-ui
  ✅ DES-010  Logo link check                 Logo does not link out ✓
  ...

✍️ COPYWRITER CHECKS (9)
  ✅ COPY-004 Mobile font size                Min font: 16px ✓
  ⚠️  COPY-002 Spelling check                  3 potential issues found
  ...

📎 Screenshots saved: ./screenshots/desktop.png, ./screenshots/mobile.png
```

#### Asana Comment Format

```markdown
## 🤖 QA Agent Report — 2026-02-25 10:30 AEST

**38 PASS** · **5 FAIL** · **3 WARN** · **7 SKIP**

### ❌ Failed Checks
- **DEV-016** Form ID: Expected `#lp-pom-form-42`, found `#lp-pom-form-37`
- **DEV-033** Console errors: `TypeError: Cannot read property 'x' of null` (+2 more)
- **DEV-030** Page speed: FCP 5.2s (threshold: 4.0s)
- **DEV-040** No Gzip/Brotli compression detected
- **COPY-004** Contrast ratio 3.2:1 on `.hero-text` (WCAG AA requires 4.5:1)

### ⚠️ Warnings
- **DEV-037** 2 images over 500KB without WebP variant
- **DEV-038** 3 scripts loaded synchronously without `async`/`defer`
- **COPY-002** Potential spelling: "recieve" → "receive" (line 42)

### ⏭️ Skipped (require manual review or external integration)
DEV-001, DEV-002, DEV-004, DEV-008, DEV-009, DEV-022, DEV-023
```

### 5.7 Asana Integration Detail

#### Reading Task Context

The agent extracts the target URL from Asana task context using this priority:

1. **Custom field** named "Landing Page URL" (if configured)
2. **First URL in task notes** matching `*.unbounce*` or common LP domains
3. **First URL in parent task notes** (fallback)
4. **CLI `--url` override** (always takes precedence)

#### Posting Results

Results are posted as a **rich text comment** on the Asana task using the `POST /tasks/{task_gid}/stories` endpoint. The comment includes:

- Summary line with pass/fail/warn/skip counts
- Failed checks section with specific details
- Warning section
- Skipped section (collapsed)
- Timestamp and agent version

#### Batch Processing

In batch mode, the agent:

1. Fetches all tasks in the specified Asana section
2. Filters to incomplete tasks only
3. For each task, extracts the URL and runs the full check suite
4. Posts results to each task individually
5. Logs a summary to terminal

### 5.8 Configuration

All configurable values in `config.py`:

```python
# Viewport dimensions
DESKTOP_WIDTH = 1440
DESKTOP_HEIGHT = 900
MOBILE_WIDTH = 375
MOBILE_HEIGHT = 812

# Performance thresholds
MAX_FCP_MS = 4000              # First Contentful Paint threshold
MAX_IMAGE_SIZE_KB = 500        # Per-image size warning
MIN_FONT_SIZE_PX = 14          # Mobile minimum font size
MIN_CONTRAST_RATIO = 4.5       # WCAG AA contrast ratio

# Form validation
EXPECTED_FORM_ID = "lp-pom-form-42"
STANDARD_FIELD_NAMES = [
    "first_name", "last_name", "email", "phone",
    "postcode", "state", "suburb", "company",
]

# URL patterns
TYP_URL_PATTERNS = ["thank", "thankyou", "thank-you", "confirmation"]
LP_URL_PATTERNS = ["unbounce", "landing"]

# Asana
ASANA_BASE_URL = "https://app.asana.com/api/1.0"

# Screenshots
SCREENSHOT_FORMAT = "png"
SCREENSHOT_QUALITY = 80  # For JPEG compression when uploading
```

### 5.9 Test Suite

26 unit tests covering:

- **Crawler tests:** Mock Playwright page → verify PageSnapshot extraction
- **Developer check tests:** Feed known PageSnapshot → verify correct pass/fail for each check
- **Designer check tests:** Same pattern
- **Copywriter check tests:** Same pattern
- **Reporter tests:** Verify markdown and JSON output format
- **Integration tests:** Full pipeline from URL → report (requires network)

Run with: `python -m pytest tests/ -v`

---

## 6. Phase 2–4 Roadmap: Progressive Agent Expansion

### 6.1 Phase 2: QA Agent Enhancement (Weeks 3–6)

Expand the QA Agent with external integrations to cover the remaining ~30% of checks currently skipped:

| Feature | API/Tool | Unlocks | Effort |
|---------|----------|---------|--------|
| **Figma Visual Comparison** | Figma REST API | DEV-003, DEV-004, DEV-027, DES-001, DES-002 — automated visual diff between Figma design and live page | 2 weeks |
| **Google Docs Copy Validation** | Google Docs API | DEV-009 — automated copy comparison between doc and live page text | 3 days |
| **Lighthouse Integration** | Lighthouse CLI / PageSpeed API | DEV-036, DES-009, COPY-009 — full Lighthouse audit with WCAG accessibility scoring | 3 days |
| **Unbounce API** | Unbounce API | DEV-001, DEV-002, COPY-007 — group validation, variant management | 1 week |
| **Google Sheets CRO Vault** | Google Sheets API | COPY-008 — auto-write page name + URL to CRO vault spreadsheet | 2 days |
| **Live Form Testing** | Enhanced Playwright | DEV-020, DEV-021 — full form submission with test data, verify TYP flow | 1 week |
| **Asana Webhook Trigger** | Asana Events API | Auto-run QA when task moves to QA section | 3 days |

Phase 2 target: **95%+ check automation coverage.**

### 6.2 Phase 3: Campaign Build & Launch Agent (Weeks 7–12)

The second-highest impact agent, targeting the 44 Campaign Build & Launch tasks:

| Capability | Description |
|-----------|-------------|
| Google Ads shell validation | Verify campaign structure, naming conventions, targeting, bid strategies against SG standards |
| Meta Ads config QA | Validate ad set configuration, audience targeting, placement selection |
| Ad creative verification | Cross-reference uploaded ad assets with approved Figma designs |
| Budget verification | Compare configured budgets with approved budget in brief/SOW |
| Launch readiness checklist | Automated pre-flight check across all platforms before go-live |
| Proof screenshots | Automated screenshots of campaign configurations for client records |

**Dependencies:** Google Ads API, Meta Marketing API, (optional) TikTok Ads API, LinkedIn Campaign Manager API.

### 6.3 Phase 4: Reporting & Documentation Agent (Weeks 13–18)

Targeting 20 Reporting & Optimisation tasks + 5 Documentation tasks:

| Capability | Description |
|-----------|-------------|
| Monthly report generation | Pull performance data from ad platforms → populate Whimsical/Google Docs report template |
| Anomaly detection | Flag significant performance changes (CTR drops, CPA spikes, budget pacing issues) |
| Optimisation recommendations | Based on performance data, suggest bid adjustments, audience changes, creative refreshes |
| Campaign documentation | Auto-generate campaign setup docs from live platform configuration |

**Dependencies:** All ad platform APIs + Google Docs API + (optional) Whimsical API.

### 6.4 Future Phases: Remaining Agents

| Agent | Phase | Rationale |
|-------|-------|-----------|
| Tracking & Integrations | Phase 5 | GTM/pixel validation — moderate complexity, 13 tasks |
| Intake & Agreements | Phase 6 | SOW/WorkflowMax sync — high value per task, small task count |
| Access & Setup | Phase 7 | Permission management — low task count, high friction reduction |
| Briefing & Planning | Phase 8 | Brief-to-plan conversion — requires LLM for content generation |
| Creative & Assets | Phase 9 | Asset validation — partially covered by Phase 2 Figma integration |

---

## 7. Deployment Architecture: Google Cloud Code / Anti-Gravity

### 7.1 Environment Setup

The QA Agent runs as a Python application deployed via Google Cloud Code using Anti-Gravity's execution environment. The deployment target is a containerised runtime with:

- **Python 3.11+** runtime
- **Playwright + Chromium** headless browser (installed via `playwright install chromium`)
- **Network access** to target landing pages (Unbounce-hosted URLs)
- **Asana API access** (HTTPS outbound to `app.asana.com`)

### 7.2 Container Configuration

```dockerfile
FROM python:3.11-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy agent code
COPY qa_agent/ /app/qa_agent/
COPY run_qa.py /app/
WORKDIR /app

# Entry point
ENTRYPOINT ["python", "run_qa.py"]
```

### 7.3 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ASANA_PAT` | For Asana modes | Asana Personal Access Token |
| `ASANA_PROJECT_ID` | For batch mode | Default Asana project GID |
| `SCREENSHOT_DIR` | No | Override screenshot output directory |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 7.4 Execution Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| **CLI Direct** | `run_qa.py run <URL>` | Ad-hoc testing during development |
| **Asana Single** | `run_qa.py asana <TASK_ID>` | Run QA on specific task |
| **Asana Batch** | `run_qa.py batch` | Process all QA tasks in a section |
| **Webhook (Phase 2)** | Asana event → HTTP trigger | Auto-run when task enters QA section |

### 7.5 Cloud Code Build Prompt

This is the implementation prompt to provide to Cloud Code / Anti-Gravity for building the agent:

---

**BEGIN CLOUD CODE BUILD PROMPT**

```
You are building a QA Checklist Agent for Social Garden, an advertising agency. 
The agent automates landing page quality assurance checks.

PROJECT: qa-agent
LANGUAGE: Python 3.11+
FRAMEWORK: CLI application using Click
BROWSER: Playwright with headless Chromium

ARCHITECTURE:
- qa_agent/crawler.py — Playwright-based page crawler
  - Crawl at desktop (1440x900) and mobile (375x812) viewports
  - Extract: title, meta tags, all images (src, alt, format, size), all links, 
    all forms (id, fields, validation), all scripts, computed fonts/colors,
    console errors, network requests with response headers, performance timing
  - Take full-page screenshots at both viewports
  - Return a PageSnapshot dataclass with all extracted data

- qa_agent/checks/developer.py — 33 automated checks
  Map each check to the Asana checklist items listed below. Each check returns a 
  CheckResult with: check_id, name, status (PASS/FAIL/WARN/SKIP), message, evidence.
  
  Checks to implement:
  DEV-005: Image format — PNG only for transparent, JPG otherwise
  DEV-006: Mobile sticky CTA present (position:fixed/sticky with CTA text)
  DEV-010: CTA scrolls to form (click CTA → form in viewport)
  DEV-011: CTA hover color change (compare pre/post hover computed color)
  DEV-012: Carousel functioning (detect carousel, verify navigation)
  DEV-013: Carousel transition speed (auto-play interval ≥ 3 seconds)
  DEV-015: Standardised field names (check against: first_name, last_name, 
           email, phone, postcode, state, suburb, company)
  DEV-016: Form ID is #lp-pom-form-42
  DEV-017: Placeholder text lighter than input text color
  DEV-018: Form validation on empty submit
  DEV-019: No codes in form field values
  DEV-020: Form submits and redirects to TYP (URL contains "thank")
  DEV-024: LP → TYP redirect works
  DEV-026: TYP → confirmation redirect/popup
  DEV-028: ULI/UTM parameters preserved through redirects
  DEV-029: All interactive elements clickable (no dead links)
  DEV-030: First Contentful Paint < 4000ms
  DEV-031: Page titles present and non-empty on all pages
  DEV-032: GTM script detected (googletagmanager.com in requests/scripts)
  DEV-033: No console errors
  DEV-034: No unused/404'd scripts
  DEV-035: Redirect URLs don't contain variant letters (/a/, /b/)
  DEV-036: Lighthouse performance score (if available)
  DEV-037: Images < 500KB, WebP preferred, lazy loading attribute
  DEV-038: Scripts have async/defer, JS is minified
  DEV-039: Cache-Control headers present, CDN detected
  DEV-040: Gzip or Brotli Content-Encoding on responses
  DEV-041: Footer links for Terms, Privacy, Disclaimer exist and resolve

  SKIP these with message "Requires external API":
  DEV-001 (Unbounce group), DEV-002 (variant management), DEV-004 (Figma diff),
  DEV-008 (price context), DEV-009 (copy doc), DEV-022/023 (SMS),
  DEV-042 (peer review — human step)

  PARTIAL (extract what's possible, note limitation):
  DEV-003 (fonts extracted, design comparison deferred)
  DEV-007 (CTA text extracted, brief comparison deferred)
  DEV-014 (fields extracted, design comparison deferred)
  DEV-025 (hover states detected, design comparison deferred)

- qa_agent/checks/designer.py — 11 checks
  DES-003: Extract all computed font-family values
  DES-004: Click all buttons, verify navigation/scroll
  DES-005: Detect CSS transitions/transforms on scroll
  DES-006: Mobile viewport screenshot captured
  DES-007: Sticky CTA on mobile (same as DEV-006)
  DES-009: PageSpeed check (same as DEV-036)
  DES-010: Logo image parent <a> href is null/empty/same-page
  DES-011: All images checked for dimension/filesize

  SKIP: DES-001 (Figma diff), DES-008 (Asana action)
  PARTIAL: DES-002 (computed padding/margin extracted)

- qa_agent/checks/copywriter.py — 9 checks
  COPY-001: Dual viewport crawl (built into crawler)
  COPY-002: Extract visible text → basic spell check
  COPY-004: Font sizes ≥ 14px on mobile; WCAG contrast ratio ≥ 4.5:1
  COPY-005: Meta title present (same as DEV-031)
  COPY-009: PageSpeed (same as DEV-036)

  SKIP: COPY-007 (Unbounce), COPY-008 (Google Sheets)
  PARTIAL: COPY-003 (heading hierarchy), COPY-006 (UX subjective)

- qa_agent/reporter.py — Output formatting
  - Terminal: colored pass/fail with details
  - Markdown: structured report with sections per role
  - JSON: machine-readable results
  - Asana comment: condensed markdown for task comments

- qa_agent/asana_client.py — Asana API integration
  - Read task details (GET /tasks/{gid})
  - Extract URL from task notes (regex: https?://...)
  - Post comment (POST /tasks/{gid}/stories)
  - List section tasks (GET /sections/{gid}/tasks)
  - Auth: Bearer token from ASANA_PAT env var

- qa_agent/cli.py — Click CLI
  Three commands: run, asana, batch
  See specification above for full flag details.

- tests/test_checks.py — Unit tests
  Mock PageSnapshot objects with known values → assert correct check results.

CONFIGURATION (config.py):
  DESKTOP_WIDTH = 1440, DESKTOP_HEIGHT = 900
  MOBILE_WIDTH = 375, MOBILE_HEIGHT = 812
  MAX_FCP_MS = 4000
  MAX_IMAGE_SIZE_KB = 500
  MIN_FONT_SIZE_PX = 14
  MIN_CONTRAST_RATIO = 4.5
  EXPECTED_FORM_ID = "lp-pom-form-42"
  STANDARD_FIELD_NAMES = ["first_name", "last_name", "email", "phone",
                           "postcode", "state", "suburb", "company"]
  TYP_URL_PATTERNS = ["thank", "thankyou", "thank-you", "confirmation"]

DEPENDENCIES:
  playwright>=1.40
  click>=8.0
  requests>=2.28
  Pillow>=10.0

After building, run: playwright install chromium
Test with: python -m pytest tests/ -v
```

**END CLOUD CODE BUILD PROMPT**

---

## 8. Integration Layer: Asana MCP + Toolchain

### 8.1 Asana Integration Points

The QA Agent interacts with Asana at three levels:

| Level | API Endpoint | Purpose |
|-------|-------------|---------|
| **Read task** | `GET /tasks/{gid}` | Extract landing page URL, task name, parent task, custom fields |
| **Read section** | `GET /sections/{gid}/tasks` | Batch mode: get all tasks in QA section |
| **Post comment** | `POST /tasks/{gid}/stories` | Write QA results as rich text comment |
| **Update task** (Phase 2) | `PUT /tasks/{gid}` | Set custom field "QA Status" to Pass/Fail |
| **Webhook** (Phase 2) | Asana Events API | Auto-trigger on task section change |

### 8.2 Connected Tools (Available MCP Servers)

The following MCP servers are connected and available for future agent enhancements:

| Service | MCP URL | Agent Use Case |
|---------|---------|---------------|
| Asana | `https://mcp.asana.com/v2/mcp` | Task read/write, section scanning, webhook registration |
| Slack | `https://mcp.slack.com/mcp` | Post QA failure alerts to team channels |
| Gmail | `https://gmail.mcp.claude.com/mcp` | Send QA reports to stakeholders (Phase 3) |
| Coupler.io | `https://mcp.coupler.io/mcp` | Data sync between tools (Phase 4) |

### 8.3 Process Flowchart Integration

The Process Flowchart Tool (`build_process_flowchart.py` + `workflow_enrichment.py`) provides the analytical foundation for the agent framework:

- **Task classification** feeds agent scoping decisions
- **Automation scoring** prioritizes which tasks to automate next
- **Tool detection** identifies which APIs each agent needs
- **Dependency graph** maps agent handoff points
- **View modes** (Process, Agent) visualize the agent architecture

The flowchart tool should be maintained alongside the agent development to track coverage progression as agents come online.

---

## 9. Success Metrics & Acceptance Criteria

### 9.1 Phase 1 MVP Acceptance Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Automated check count | ≥ 53 | Count of implemented checks |
| Check accuracy (true positive rate) | ≥ 95% | Manual validation on 10 test pages |
| Check accuracy (false positive rate) | ≤ 10% | Manual validation on 10 test pages |
| Crawl success rate | ≥ 99% | Pages that load and complete all checks |
| Crawl time per page | < 60 seconds | End-to-end including both viewports |
| Asana comment post success | 100% | API call completion rate |
| Test suite pass rate | 100% | All 26 tests passing |

### 9.2 Operational KPIs

| Metric | Baseline (Manual) | Target (With Agent) | Improvement |
|--------|-------------------|--------------------|----|
| QA time per campaign | 45–60 min | 10–15 min | 70–75% reduction |
| QA consistency | Variable (human error) | Deterministic | Eliminates variance |
| Monthly QA hours | 15–20 hours | 4–5 hours | ~75% reduction |
| Defect escape rate | ~15% (estimated) | < 5% | 67% improvement |
| QA coverage (% of checks automated) | 0% | 70% (Phase 1), 95% (Phase 2) | Step function |

### 9.3 Phase 2+ Success Criteria

| Phase | Key Metric | Target |
|-------|-----------|--------|
| Phase 2 | Automated check coverage | ≥ 95% of all QA items |
| Phase 2 | Figma visual diff accuracy | ≥ 90% match detection |
| Phase 3 | Campaign build validation coverage | ≥ 60% of build checks automated |
| Phase 4 | Report generation time | < 5 minutes per monthly report |

---

## 10. Appendices

### Appendix A: Process Flowchart Tool Reference

The Process Flowchart Tool is the analytical companion to the agent framework. It consists of:

| File | Purpose |
|------|---------|
| `build_process_flowchart.py` | Main generator: Asana CSV → JSON + HTML |
| `workflow_enrichment.py` | Tool detection, process classification, agent ops, automation scoring, node grouping |
| `tests_process_flowchart.py` | 35 tests covering full pipeline |
| `process_scenarios.json` | Scenario definitions (happy path, feedback loops, scope changes) |
| `process_flowchart_data.json` | Generated enriched data for all 229 tasks |
| `process_flowchart.html` | Interactive visualization |

**Rule Edit Locations:**

| What to change | File | Location |
|---------------|------|----------|
| Tool detection rules | `workflow_enrichment.py` | `TOOL_RULES` list |
| Tool → process bias | `workflow_enrichment.py` | `TOOL_BIAS` dict |
| Process classification regex | `workflow_enrichment.py` | `PROCESS_RULES` dict |
| Agent ops suggestions | `workflow_enrichment.py` | `_PROCESS_OPS` dict |
| Automation score formula | `workflow_enrichment.py` | `compute_automation_score()` |
| Candidate threshold | `workflow_enrichment.py` | `AGENT_CANDIDATE_THRESHOLD` (currently 2.5) |

### Appendix B: Complete Task-to-Agent Mapping

**Parent Task Groups by Agent Assignment:**

| Agent | Parent Task | Subtask Count |
|-------|------------|--------------|
| QA & Approvals Agent | 🔎 Developer QA - Post Dev Checklist | 42 |
| QA & Approvals Agent | 👨🏾‍🎨 Designer QA - Post Dev Check | 11 |
| QA & Approvals Agent | ✍️ Copywriter QA - Post Dev Check | 9 |
| Tracking & Integrations Agent | GA4 & GTM Set Up | 8 |
| Campaign Build & Launch Agent | Build Approved Ads in Platforms | 8 |
| Briefing & Planning Agent | Technical Setup | 7 |
| Creative & Assets Agent | Creative Asset Refinement | 7 |
| Creative & Assets Agent | Campaign & Creative Concept Refinement | 6 |
| Campaign Build & Launch Agent | Google Campaign Build | 6 |
| Campaign Build & Launch Agent | Build Campaign Shells | 5 |
| Tracking & Integrations Agent | Complete Integrations | 5 |
| Briefing & Planning Agent | Create Campaign Documentation | 5 |
| Reporting & Optimisation Agent | Build Campaign Docs & Reporting Templates | 4 |
| Campaign Build & Launch Agent | Campaign Optimisations | 4 |
| Campaign Build & Launch Agent | TikTok Account Set Up | 3 |
| Campaign Build & Launch Agent | Meta Campaign Build | 3 |
| Reporting & Optimisation Agent | Create Custom Dashboard & Data Report | 3 |
| Creative & Assets Agent | Present Final Creative Assets | 3 |
| Creative & Assets Agent | Internal QA: Landing Pages & Templates | 3 |

### Appendix C: Automation Score Distribution

```
Score Range    Count    % of Workflow
0.0            138      60.3%
0.1 – 0.9      44      19.2%
1.0 – 1.9      21       9.2%
2.0 – 2.4      13       5.7%
2.5 – 2.9       7       3.1%
3.0 – 3.6       6       2.6%
─────────────────────────────────
Agent candidates (≥2.5): 13 tasks (5.7%)
```

### Appendix D: Glossary

| Term | Definition |
|------|-----------|
| **Anti-Gravity** | Google's Cloud Code execution platform |
| **Agent Candidate** | Task scoring ≥ 2.5 on the automation score (0.0–5.0 scale) |
| **CRO Vault** | Social Garden's Google Sheets repository of landing page records |
| **FCP** | First Contentful Paint — web performance metric |
| **GTM** | Google Tag Manager |
| **LP** | Landing Page |
| **MCP** | Model Context Protocol — Anthropic's tool integration standard |
| **PageSnapshot** | Data structure containing all crawled page data |
| **PAT** | Personal Access Token (Asana authentication) |
| **TYP** | Thank You Page (post-form-submission redirect target) |
| **ULI** | Unique Lead Identifier (tracking parameter) |
| **Unbounce** | Landing page builder platform used by Social Garden |
| **WCAG** | Web Content Accessibility Guidelines |
| **WIP Doc** | Work In Progress Document (campaign tracking spreadsheet) |
| **WorkflowMax** | Job management/billing system |

---

*Document generated from analysis of Social Garden's 229-task Asana advertising rollout workflow, including process segmentation across 9 buckets, tool detection across 14 SaaS platforms, and automation scoring of all tasks. The QA Agent MVP codebase (53 checks, 26 tests) has been built and validated. This PRD provides the complete specification for Cloud Code / Anti-Gravity deployment and the phased roadmap for expanding agent coverage across the full workflow.*
