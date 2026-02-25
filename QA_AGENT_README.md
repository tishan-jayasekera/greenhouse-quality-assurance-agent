# 🤖 QA Checklist Agent

Automated landing page QA for Social Garden's advertising rollout process.

Crawls landing pages with a headless browser and validates against the
Developer (33 checks), Designer (11 checks), and Copywriter (9 checks)
QA checklists from Asana — producing a structured pass/fail report.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Run against a landing page
python -m qa_agent run https://your-landing-page.com

# 3. (Optional) With context for richer checks
python -m qa_agent run https://your-landing-page.com \
  --client "Acme Corp" \
  --campaign "Summer 2025 Lead Gen" \
  --cta-text "Get Started" \
  --form-id "lp-pom-form-42"
```

## Commands

### `run` — Check a URL directly
```bash
python -m qa_agent run <URL> [options]

Options:
  --client TEXT         Client name (enables title/copy checks)
  --campaign TEXT       Campaign name
  --figma URL           Figma design URL (Phase 2: visual comparison)
  --copy-doc URL        Google Doc with approved copy (Phase 2: text diff)
  --cta-text TEXT       Expected CTA button text (enables exact match check)
  --thank-you-url URL   Expected redirect URL after form submission
  --form-id ID          Expected form element ID (default: lp-pom-form-42)
  --output DIR          Output directory (default: ./qa_output)
  --no-screenshots      Skip screenshot capture
```

### `asana` — Run from an Asana task
```bash
# Reads LP URL, Figma, copy doc from task Notes automatically
export ASANA_ACCESS_TOKEN=your_token
python -m qa_agent asana 1234567890123

# Post results back to Asana as a comment
python -m qa_agent asana 1234567890123 --post
```

### `batch` — Run on all tasks in a QA section
```bash
export ASANA_ACCESS_TOKEN=your_token
python -m qa_agent batch 9876543210123 --section "🔁 Final QA" --post
```

## Output

Each run produces:
- **Terminal report** — colour-coded pass/fail summary
- **Markdown report** — `qa_output/qa_report_YYYYMMDD_HHMMSS.md`
- **JSON results** — `qa_output/qa_results_YYYYMMDD_HHMMSS.json` (machine-readable)
- **Screenshots** — `qa_output/screenshot_desktop.png`, `screenshot_mobile.png`

## What Gets Checked

### Developer QA (33 checks)
| Check | Method |
|-------|--------|
| Form ID = `#lp-pom-form-42` | DOM inspection |
| No console errors | Console listener |
| Gzip/Brotli compression | Response headers |
| Sticky CTA on mobile | CSS position check at mobile viewport |
| Image formats (WebP preferred) | File extension + size analysis |
| URL parameter pass-through (UTM/ULI) | Script content scan |
| No variant letter in URL | URL pattern match |
| Form fields present & named | DOM form extraction |
| CTA scroll targets | Anchor href → form ID match |
| Carousel detection & config | DOM class + data attribute scan |
| Code minification | Whitespace ratio heuristic |
| Image compression & sizing | Natural vs displayed dimensions |
| Placeholder styling | CSS rule detection |
| ... and more | |

### Designer QA (11 checks)
| Check | Method |
|-------|--------|
| Web fonts loading | Computed style extraction |
| Button links valid | href inspection |
| Logo not linked out | Anchor analysis |
| Desktop/mobile parity | Element count comparison |
| Image quality (no stretching) | Natural vs display dimension ratio |
| Scroll animations present | Animation library/CSS detection |
| Responsive images | srcset/picture element scan |

### Copywriter QA (9 checks)
| Check | Method |
|-------|--------|
| Spelling (basic) | Regex typo patterns |
| Capitalisation consistency | Heading case classification |
| Meta page title | Title tag analysis |
| CTA copy clarity | Vague-text detection |
| Form field labels | Label/placeholder presence |
| Desktop/mobile copy parity | Link count comparison |

## Check Statuses

- ✅ **PASS** — Check passed, no action needed
- ❌ **FAIL** — Check failed, action required
- ⚠️ **WARN** — Needs manual review (ambiguous or partial signal)
- ⏭️ **SKIP** — Cannot automate yet (needs Figma API, form submission, etc.)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ASANA_ACCESS_TOKEN` | For `asana`/`batch` commands | Asana Personal Access Token |
| `ANTHROPIC_API_KEY` | Future (Phase 2) | For LLM-assisted copy comparison |
| `QA_OUTPUT_DIR` | No | Override default output directory |

## Architecture

```
qa_agent/
├── __init__.py          # Package init
├── __main__.py          # python -m qa_agent entry point
├── cli.py               # CLI commands (run, asana, batch)
├── config.py            # Data models (PageSnapshot, CheckResult, QAReport)
├── crawler.py           # Playwright page crawler
├── reporter.py          # Terminal + Markdown + Asana output formatters
├── asana_client.py      # Asana API integration
└── checks/
    ├── __init__.py      # Check registry
    ├── developer.py     # 33 developer QA checks
    ├── designer.py      # 11 designer QA checks
    └── copywriter.py    # 9 copywriter QA checks
```

## Extending

### Add a new check
1. Add a function to the appropriate `checks/*.py` file
2. Follow the pattern: `def _check_name(snap: PageSnapshot, ctx: QAContext) -> CheckResult`
3. Add it to the `checks` list in the module's `run()` function

### Add a new check category
1. Create `qa_agent/checks/newcategory.py` with a `run(snapshot, context)` function
2. Register it in `qa_agent/checks/__init__.py`

## Roadmap

- **Phase 1 (this):** DOM-based checks, headless browser crawling
- **Phase 2:** Figma API visual comparison, Google Docs copy diff, Lighthouse integration
- **Phase 3:** Live form submission testing, redirect chain validation
- **Phase 4:** Asana webhook trigger (auto-run when task moves to QA section)
