import os
import json
import asyncio
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import streamlit as st
import nest_asyncio

# Apply nest_asyncio to allow asyncio.run() within Streamlit's async loop if needed
nest_asyncio.apply()

from qa_agent.crawler import crawl_sync
from qa_agent.config import QAContext, QAReport
from qa_agent.checks import run_all
from qa_agent.reporter import to_markdown
from qa_agent.asana_client import build_context_from_task, post_results, get_qa_tasks

# --- 1. SETTINGS & CSS ---
st.set_page_config(
    page_title="QA Agent — Social Garden",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stExpander"] {
        border: 1px solid #e9ecef;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- 2. SESSION STATE INIT ---
def init_session_state():
    for key in ["report", "snapshot", "json_data", "md_content", "batch_results", "asana_comment_gid"]:
        if key not in st.session_state:
            st.session_state[key] = None


# --- 3. HELPER FUNCTIONS ---
def build_json(report: QAReport) -> dict:
    return {
        "url": report.context.landing_page_url,
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


def _render_results(report: QAReport, snapshot):
    """Renders the QA Report results into the Streamlit UI."""
    s = report.summary

    # SECTION A — Summary Metrics
    cols = st.columns(5)
    cols[0].metric("Total", s["total"])
    cols[1].metric("✅ Passed", s["passed"])
    cols[2].metric("❌ Failed", s["failed"])
    cols[3].metric("⚠️ Warnings", s["warnings"])
    cols[4].metric("⏭️ Skipped", s["skipped"])

    pass_rate_str = s["pass_rate"]
    pass_rate = float(pass_rate_str.strip('%')) if '%' in pass_rate_str else 0

    if pass_rate >= 80:
        st.success(f"✅ Pass rate: {pass_rate_str} — Looking good!")
    elif pass_rate >= 50:
        st.warning(f"⚠️ Pass rate: {pass_rate_str} — Needs attention")
    else:
        st.error(f"❌ Pass rate: {pass_rate_str} — Significant issues found")

    st.progress(s["passed"] / max(s["total"], 1))
    st.markdown("---")

    # SECTION B — Screenshots
    if snapshot.screenshot_desktop:
        col_d, col_m = st.columns([3, 2])
        with col_d:
            st.subheader("🖥️ Desktop (1440×900)")
            st.image(snapshot.screenshot_desktop, use_container_width=True)
        with col_m:
            st.subheader("📱 Mobile (375×812)")
            if snapshot.screenshot_mobile:
                st.image(snapshot.screenshot_mobile, use_container_width=True)
            else:
                st.info("No mobile screenshot captured.")
        st.markdown("---")

    # SECTION C — Failures
    if report.failed:
        st.subheader(f"❌ {len(report.failed)} Failure(s) — Action Required")
        for r in report.failed:
            with st.expander(f"❌ {r.name}  ·  {r.category}", expanded=True):
                st.markdown(f"**Check ID:** `{r.check_id}`")
                st.markdown(r.message)
                if r.evidence:
                    st.code(r.evidence[:1000], language=None)

    # SECTION D — Warnings
    if report.warnings:
        st.subheader(f"⚠️ {len(report.warnings)} Warning(s) — Review Recommended")
        for r in report.warnings:
            with st.expander(f"⚠️ {r.name}  ·  {r.category}", expanded=False):
                st.markdown(f"**Check ID:** `{r.check_id}`")
                st.markdown(r.message)
                if r.evidence:
                    st.code(r.evidence[:1000], language=None)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION E — Passed Checks
    if report.passed:
        with st.expander(f"✅ {len(report.passed)} Check(s) Passed", expanded=False):
            for r in report.passed:
                st.markdown(f"✅ **{r.name}** ({r.category}) — {r.message[:120]}")

    # SECTION F — Skipped Checks
    if report.skipped:
        with st.expander(f"⏭️ {len(report.skipped)} Check(s) Skipped (Manual/Future Phase)", expanded=False):
            for r in report.skipped:
                st.markdown(f"⏭️ **{r.name}** ({r.category}) — {r.message[:120]}")

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION G — Category Breakdown Tabs
    tab_dev, tab_des, tab_copy = st.tabs([
        f"🔧 Developer ({s['by_category'].get('developer', {}).get('total', 0)})",
        f"🎨 Designer ({s['by_category'].get('designer', {}).get('total', 0)})",
        f"✍️ Copywriter ({s['by_category'].get('copywriter', {}).get('total', 0)})",
    ])

    def render_category_table(category_name):
        cat_results = [r for r in report.results if r.category == category_name]
        if not cat_results:
            st.info(f"No checks in {category_name} category.")
            return

        icon_map = {"pass": "✅", "fail": "❌", "warn": "⚠️", "skip": "⏭️"}
        data = []
        for r in cat_results:
            data.append({
                "Status": icon_map.get(r.status.value, "❓"),
                "Check ID": r.check_id,
                "Name": r.name,
                "Message": r.message
            })
        st.dataframe(data, use_container_width=True, hide_index=True)

    with tab_dev:
        render_category_table("developer")
    with tab_des:
        render_category_table("designer")
    with tab_copy:
        render_category_table("copywriter")

    st.markdown("---")

    # SECTION H — Download Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.md_content:
            st.download_button(
                "📄 Download Markdown",
                data=st.session_state.md_content,
                file_name=f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )
    with col2:
        if st.session_state.json_data:
            st.download_button(
                "📊 Download JSON",
                data=st.session_state.json_data,
                file_name=f"qa_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )
    with col3:
        if st.session_state.asana_comment_gid:
            st.success(f"✅ Posted to Asana (comment {st.session_state.asana_comment_gid})")
            
    # SECTION I — Page Metadata
    with st.expander("🔍 Page Metadata"):
        meta_cols = st.columns(4)
        meta_cols[0].metric("Status Code", snapshot.status_code)
        meta_cols[1].metric("Load Time", f"{snapshot.load_time_ms}ms")
        meta_cols[2].metric("Page Size", f"{snapshot.page_size_bytes / 1024:.0f} KB")
        meta_cols[3].metric("Compression", snapshot.compression or "None")

        st.markdown(f"**Final URL:** `{snapshot.final_url}`")
        st.markdown(f"**Title:** {snapshot.title}")
        st.markdown(f"**Images:** {len(snapshot.images)} · **Forms:** {len(snapshot.forms)} · "
                    f"**Scripts:** {len(snapshot.scripts)} · **Links:** {len(snapshot.links)}")
        st.markdown(f"**Console Errors:** {len(snapshot.console_errors)} · "
                    f"**Console Warnings:** {len(snapshot.console_warnings)}")
        st.markdown(f"**Fonts:** {', '.join(snapshot.fonts_loaded[:10]) if snapshot.fonts_loaded else 'None detected'}")

        if snapshot.redirect_chain and len(snapshot.redirect_chain) > 1:
            st.markdown("**Redirect Chain:**")
            for i, hop in enumerate(snapshot.redirect_chain):
                st.markdown(f"  {i+1}. `{hop}`")


# --- 4. ACTION HANDLERS ---
import re

def extract_asana_gid(url: str) -> str | None:
    if not url: return None
    # Asana GIDs are massive (15+ digits). We ignore '0' and short numbers.
    matches = re.findall(r'\d{10,}', url)
    if matches:
        return matches[-1]
    return None

def run_quick_start_mode(inputs, output_dir):
    if not inputs["url"]:
        st.warning("Please enter a landing page URL.")
        return
    if not (inputs["url"].startswith("http://") or inputs["url"].startswith("https://")):
        st.warning("URL must start with http:// or https://")
        return

    task_gid = extract_asana_gid(inputs.get("asana_url"))
    
    if task_gid and inputs.get("asana_token"):
        os.environ["ASANA_ACCESS_TOKEN"] = inputs["asana_token"]
        import qa_agent.config
        qa_agent.config.ASANA_TOKEN = inputs["asana_token"]

    try:
        with st.status("Running QA scan...", expanded=True) as status:
            st.write(f"🔍 Crawling {inputs['url']}...")
            snapshot = crawl_sync(inputs["url"], output_dir=output_dir, screenshots=True)

            st.write(f"✅ Page loaded in {snapshot.load_time_ms}ms — "
                     f"{len(snapshot.images)} images, {len(snapshot.forms)} forms")
            st.write("🧪 Running checks...")
            context = QAContext(
                landing_page_url=inputs["url"],
                client_name=inputs.get("client"),
                asana_task_id=task_gid,
                expected_form_id="lp-pom-form-42",
            )
            results = run_all(snapshot, context)
            report = QAReport(context=context, results=results)
            report.build_summary()

            if task_gid and inputs.get("asana_token") and inputs.get("post_to_asana", True):
                st.write("📤 Posting results to Asana...")
                try:
                    comment_gid = post_results(report)
                    st.session_state.asana_comment_gid = comment_gid
                except Exception as e:
                    st.warning(f"Failed to post comment to Asana: {type(e).__name__} - {e}")
                    import traceback
                    st.error("Asana Error Traceback:")
                    st.code(traceback.format_exc())

            st.write("📊 Generating report...")
            md_path = to_markdown(report, output_dir)
            json_data = build_json(report)

            st.session_state.report = report
            st.session_state.snapshot = snapshot
            st.session_state.md_content = Path(md_path).read_text()
            st.session_state.json_data = json.dumps(json_data, indent=2)
            st.session_state.batch_results = None
            if not (task_gid and inputs.get("asana_token")):
                st.session_state.asana_comment_gid = None

            status.update(label="✅ Scan complete!", state="complete")
    finally:
        os.environ.pop("ASANA_ACCESS_TOKEN", None)

def run_url_mode(inputs, output_dir):
    if not inputs["url"]:
        st.warning("Please enter a landing page URL.")
        return

    if not (inputs["url"].startswith("http://") or inputs["url"].startswith("https://")):
        st.warning("URL must start with http:// or https://")
        return

    with st.status("Running QA scan...", expanded=True) as status:
        st.write(f"🔍 Crawling {inputs['url']}...")
        snapshot = crawl_sync(inputs["url"], output_dir=output_dir, screenshots=True)

        st.write(f"✅ Page loaded in {snapshot.load_time_ms}ms — "
                 f"{len(snapshot.images)} images, {len(snapshot.forms)} forms")
        st.write("🧪 Running checks...")
        context = QAContext(
            landing_page_url=inputs["url"],
            client_name=inputs.get("client"),
            campaign_name=inputs.get("campaign"),
            expected_form_id=inputs.get("form_id", "lp-pom-form-42"),
            expected_cta_text=inputs.get("cta_text"),
            thank_you_url=inputs.get("thank_you_url"),
            figma_url=inputs.get("figma_url"),
            copy_doc_url=inputs.get("copy_doc_url"),
        )
        results = run_all(snapshot, context)
        report = QAReport(context=context, results=results)
        report.build_summary()

        st.write("📊 Generating report...")
        md_path = to_markdown(report, output_dir)
        json_data = build_json(report)

        st.session_state.report = report
        st.session_state.snapshot = snapshot
        st.session_state.md_content = Path(md_path).read_text()
        st.session_state.json_data = json.dumps(json_data, indent=2)
        st.session_state.batch_results = None  # Clear batch results
        st.session_state.asana_comment_gid = None

        status.update(label="✅ Scan complete!", state="complete")


def run_asana_mode(inputs, output_dir):
    if not inputs["asana_token"]:
        st.warning("Please enter an Asana Access Token.")
        return
    if not inputs["task_gid"]:
        st.warning("Please enter an Asana Task GID.")
        return

    os.environ["ASANA_ACCESS_TOKEN"] = inputs["asana_token"]
    import qa_agent.config
    qa_agent.config.ASANA_TOKEN = inputs["asana_token"]

    try:
        with st.status("Running QA from Asana task...", expanded=True) as status:
            st.write(f"📋 Reading Asana task {inputs['task_gid']}...")
            try:
                ctx = build_context_from_task(inputs["task_gid"])
            except Exception as e:
                st.error(f"Failed to read Asana task. Check your token and Task GID. Error: {e}")
                status.update(label="❌ Failed", state="error")
                return

            if not ctx.landing_page_url:
                st.error("No landing page URL found in Asana task notes.")
                status.update(label="❌ Failed", state="error")
                return

            st.write(f"🔍 Crawling {ctx.landing_page_url}...")
            snapshot = crawl_sync(ctx.landing_page_url, output_dir=output_dir, screenshots=True)

            st.write(f"✅ Page loaded in {snapshot.load_time_ms}ms")
            st.write("🧪 Running checks...")
            results = run_all(snapshot, ctx)
            report = QAReport(context=ctx, results=results)
            report.build_summary()

            if inputs.get("post_to_asana"):
                st.write("📤 Posting results to Asana...")
                try:
                    comment_gid = post_results(report)
                    st.session_state.asana_comment_gid = comment_gid
                except Exception as e:
                    st.warning(f"Failed to post comment to Asana: {e}")

            st.write("📊 Generating report...")
            md_path = to_markdown(report, output_dir)
            json_data = build_json(report)
            
            st.session_state.report = report
            st.session_state.snapshot = snapshot
            st.session_state.md_content = Path(md_path).read_text()
            st.session_state.json_data = json.dumps(json_data, indent=2)
            st.session_state.batch_results = None

            status.update(label="✅ Scan complete!", state="complete")
    finally:
        os.environ.pop("ASANA_ACCESS_TOKEN", None)


def run_batch_mode(inputs):
    if not inputs["asana_token"]:
        st.warning("Please enter an Asana Access Token.")
        return
    if not inputs["project_gid"]:
        st.warning("Please enter an Asana Project GID.")
        return

    os.environ["ASANA_ACCESS_TOKEN"] = inputs["asana_token"]
    import qa_agent.config
    qa_agent.config.ASANA_TOKEN = inputs["asana_token"]

    try:
        try:
            tasks = get_qa_tasks(inputs["project_gid"], inputs.get("section_name", "QA"))
        except Exception as e:
            st.error(f"Failed to load tasks from Asana. Check your token, Project GID, and Section Name. Error: {e}")
            return
            
        st.write(f"Found {len(tasks)} tasks in section '{inputs.get('section_name', 'QA')}'")
        
        if not tasks:
            st.info("No incomplete tasks found in this section.")
            return
            
        batch_results = []
        progress = st.progress(0, text="Starting batch scan...")

        for i, task in enumerate(tasks):
            progress.progress((i + 1) / len(tasks), text=f"Scanning {task['name']} ({i+1}/{len(tasks)})...")
            try:
                ctx = build_context_from_task(task["gid"])
                if not ctx.landing_page_url:
                    st.warning(f"⏭️ Skipped '{task['name']}': No landing page URL in notes.")
                    continue
                
                output_dir = tempfile.mkdtemp(prefix=f"qa_batch_{task['gid']}_")
                snap = crawl_sync(ctx.landing_page_url, output_dir=output_dir, screenshots=True)
                results = run_all(snap, ctx)
                report = QAReport(context=ctx, results=results)
                report.build_summary()
                
                if inputs.get("post_to_asana"):
                    try:
                        post_results(report)
                    except Exception as e:
                        st.warning(f"Failed to post comment for {task['name']}: {e}")
                        
                batch_results.append((task["name"], report, snap))
            except Exception as e:
                st.error(f"Failed to process {task['name']}: {e}")

        progress.progress(1.0, text=f"✅ Batch scan complete! Processed {len(tasks)} tasks.")
        st.session_state.batch_results = batch_results
        st.session_state.report = None  # Clear single report
    finally:
        os.environ.pop("ASANA_ACCESS_TOKEN", None)


# --- 5. MAIN UI ---
def main():
    init_session_state()

    # --- Sidebar ---
    st.sidebar.title("🤖 QA Agent")
    st.sidebar.caption("Landing Page QA Checklist")
    
    mode = st.sidebar.radio("Mode", ["🚀 Quick Start", "🔗 URL Direct", "📋 Asana Task", "📦 Batch (Section)"], index=0)
    st.sidebar.divider()
    
    inputs = {}

    if mode == "🚀 Quick Start":
        inputs["asana_url"] = st.sidebar.text_input("Asana Task URL", placeholder="https://app.asana.com/0/...")
        inputs["url"] = st.sidebar.text_input("Landing Page URL", placeholder="https://your-landing-page.com")
        inputs["client"] = st.sidebar.text_input("Client Name", placeholder="e.g. Berwick Waters")
        st.sidebar.divider()
        inputs["asana_token"] = st.sidebar.text_input("Asana Access Token", type="password")
        inputs["post_to_asana"] = True
        
    elif mode == "🔗 URL Direct":
        inputs["url"] = st.sidebar.text_input("Landing Page URL", placeholder="https://your-landing-page.com")
        inputs["client"] = st.sidebar.text_input("Client Name", placeholder="e.g. Acme Corp")
        inputs["campaign"] = st.sidebar.text_input("Campaign Name", placeholder="e.g. Summer 2025")
        
        with st.sidebar.expander("⚙️ Advanced Options", expanded=False):
            inputs["form_id"] = st.text_input("Expected Form ID", value="lp-pom-form-42")
            inputs["cta_text"] = st.text_input("Expected CTA Text", placeholder="e.g. Get Started")
            inputs["thank_you_url"] = st.text_input("Thank-You Page URL", placeholder="https://...")
            inputs["figma_url"] = st.text_input("Figma Design URL", placeholder="https://figma.com/...")
            inputs["copy_doc_url"] = st.text_input("Copy Doc URL", placeholder="https://docs.google.com/...")

    elif mode == "📋 Asana Task":
        inputs["asana_token"] = st.sidebar.text_input("Asana Access Token", type="password")
        inputs["task_gid"] = st.sidebar.text_input("Task GID", placeholder="1234567890123456")
        inputs["post_to_asana"] = st.sidebar.checkbox("Post results to Asana", value=True)

    elif mode == "📦 Batch (Section)":
        inputs["asana_token"] = st.sidebar.text_input("Asana Access Token", type="password")
        inputs["project_gid"] = st.sidebar.text_input("Project GID", placeholder="9876543210123456")
        inputs["section_name"] = st.sidebar.text_input("Section Name", value="🔁 Final QA")
        inputs["post_to_asana"] = st.sidebar.checkbox("Post results to Asana", value=True)

    st.sidebar.divider()
    run_clicked = st.sidebar.button("🚀 Run QA", type="primary", use_container_width=True)
    st.sidebar.caption("57 automated checks · Developer (37) · Designer (11) · Copywriter (9)")

    # --- Main Content Area ---
    if run_clicked:
        output_dir = tempfile.mkdtemp(prefix="qa_agent_")
        try:
            if mode == "🚀 Quick Start":
                run_quick_start_mode(inputs, output_dir)
            elif mode == "🔗 URL Direct":
                run_url_mode(inputs, output_dir)
            elif mode == "📋 Asana Task":
                run_asana_mode(inputs, output_dir)
            elif mode == "📦 Batch (Section)":
                run_batch_mode(inputs)
        except Exception as e:
            st.error(f"❌ QA scan failed: {str(e)}")
            with st.expander("Full error details"):
                st.code(traceback.format_exc())

    # Render results from session state
    if st.session_state.report is not None:
        _render_results(st.session_state.report, st.session_state.snapshot)

    elif st.session_state.batch_results is not None:
        batch_results = st.session_state.batch_results
        st.subheader(f"📦 Batch Results — {len(batch_results)} Tasks Scanned")

        # Summary table
        summary_data = []
        for task_name, task_report, _ in batch_results:
            task_report.build_summary()
            s = task_report.summary
            summary_data.append({
                "Task": task_name,
                "URL": task_report.context.landing_page_url,
                "Pass Rate": s["pass_rate"],
                "Passed": s["passed"],
                "Failed": s["failed"],
                "Warnings": s["warnings"],
            })
            
        if summary_data:
            st.dataframe(summary_data, use_container_width=True)

            # Per-task expandable detail
            for task_name, task_report, task_snapshot in batch_results:
                task_report.build_summary()
                with st.expander(f"{task_name} — {task_report.summary['pass_rate']} pass rate"):
                    _render_results(task_report, task_snapshot)
        else:
            st.info("No tasks had valid landing page URLs in this batch run.")

    elif not run_clicked:
        # Welcome screen
        st.title("🤖 QA Agent")
        st.markdown("Automated landing page quality checks for Social Garden.")
        st.info("👈 Configure your scan in the sidebar and click **Run QA** to begin.")
        
        st.markdown("""
        | 🔗 URL Direct | 📋 Asana Task | 📦 Batch Mode |
        | :--- | :--- | :--- |
        | Paste any landing page URL and run checks immediately. | Enter a task GID — agent auto-reads URL, Figma, copy doc from task notes. | Scan all tasks in an Asana section. Results posted per task automatically. |
        """)


if __name__ == "__main__":
    main()
