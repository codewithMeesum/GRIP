"""GRIP — Green Reporting & Innovation Platform. Run: streamlit run app.py"""
from collections import Counter
from io import BytesIO
import json
import os
import sqlite3
from uuid import uuid4
import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError
import database as db
from ai_service import generate
from prompts import CATEGORIES, STATUSES
from seed_data import seed_demo
from styles import apply_styles
from utils import safe, date_label, prepare_image

st.set_page_config(page_title="GRIP · Community climate action", page_icon="🌱", layout="wide")


_CARD_INDEX = 0


def card():
    """A styled native container; keys provide stable CSS targets."""
    global _CARD_INDEX
    _CARD_INDEX += 1
    return st.container(border=True, key=f"surface_{_CARD_INDEX}")


def setting(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None:
        try:
            value = st.secrets.get(name, default)
        except (FileNotFoundError, KeyError):
            value = default
    return str(value).strip()


def go(page: str, report_id: int | None = None) -> None:
    st.session_state.pending_page = page
    if report_id is not None:
        st.session_state.selected_report = report_id
        st.session_state.pop("detail_picker", None)
        st.session_state.pop("lab_picker", None)
    st.rerun()


def notice(message: str) -> None:
    st.session_state.flash = message


def prose(text: str) -> None:
    # Escape all untrusted text, including AI responses, before using HTML.
    st.html(f'<div class="body-copy">{safe(text)}</div>')


def bullets(items: list[str]) -> None:
    st.html("<ul>" + "".join(f"<li>{safe(item)}</li>" for item in items) + "</ul>")


def heading(kicker: str, title: str, description: str) -> None:
    st.html(f'<div class="eyebrow">{safe(kicker)}</div>')
    st.title(title)
    st.html(f'<div class="intro">{safe(description)}</div>')


def tags(report: dict) -> None:
    demo = '<span class="tag demo">Demo scenario</span>' if report["is_demo"] else ""
    st.html(f'<div class="tags"><span class="tag">{safe(report["category"])}</span>'
            f'<span class="tag status">{safe(report["status"])}</span>{demo}</div>')


def show_image(blob: bytes, caption: str | None = None) -> None:
    try:
        with Image.open(BytesIO(blob)) as image:
            st.image(image.copy(), caption=caption, use_container_width=True)
    except (UnidentifiedImageError, OSError, ValueError):
        st.warning("This image is unavailable. The report text and discussion are still accessible.")


def ai_options() -> dict:
    return dict(key=setting("GEMINI_API_KEY"), model=setting("GEMINI_MODEL", "gemini-2.5-flash"),
                force_demo=st.session_state.get("demo_mode", False))


def source_notice(envelope: dict) -> None:
    if envelope["source"] == "Gemini":
        st.caption(f'Gemini · {date_label(envelope["created_at"])} · advisory only')
    else:
        st.info(envelope["notice"], icon=":material/info:")


def feed_page() -> None:
    heading("Community / Field notes", "Small observations. Shared action.",
            "Find an issue, add local knowledge, and help move the next step forward.")
    top = st.columns([4, 1])
    with top[0]:
        search = st.text_input("Search reports", placeholder="Search issues, locations or observations…", key="feed_search")
    with top[1]:
        st.write("")
        if st.button("Report an issue", type="primary", use_container_width=True, icon=":material/add:"):
            go("Report issue")
    filters = st.columns([2, 2, 2])
    category = filters[0].selectbox("Category", ["All categories"] + CATEGORIES, key="feed_category")
    status = filters[1].selectbox("Status", ["All statuses"] + STATUSES, key="feed_status")
    sort = filters[2].selectbox("Sort by", ["Newest", "Most supported"], key="feed_sort")
    include_demo = st.toggle("Include demo scenarios", value=True, key="feed_demo")
    reports = db.list_reports(search, category, status, sort, include_demo)
    st.caption(f"{len(reports)} reports · Community observations; status labels are not official verification.")
    if not reports:
        st.info("No reports match these filters. Broaden your search or report a new observation.")
        return
    page_count = max(1, (len(reports) + 5) // 6)
    page = st.selectbox("Feed page", range(1, page_count + 1), format_func=lambda n: f"Page {n} of {page_count}") if page_count > 1 else 1
    supported = db.supported_ids(st.session_state.session_id)
    main, rail = st.columns([3, 1], gap="large")
    with main:
        for report in reports[(page - 1) * 6:page * 6]:
            with card():
                tags(report)
                st.html(f'<div class="card-title">{safe(report["title"])}</div>'
                        f'<div class="meta">{safe(report["location"])} · {date_label(report["created_at"])}</div>')
                if report["thumbnail"]:
                    show_image(report["thumbnail"])
                excerpt = report["description"]
                if len(excerpt) > 260:
                    excerpt = excerpt[:257].rsplit(" ", 1)[0] + "…"
                st.html(f'<div class="card-copy">{safe(excerpt)}</div>')
                buttons = st.columns([1.2, 1, 1.5])
                with buttons[0]:
                    voted = report["id"] in supported
                    if st.button(f'{"Supported" if voted else "Support"} · {report["vote_count"]}',
                                 key=f'vote_{report["id"]}', icon=":material/thumb_up:", use_container_width=True):
                        db.toggle_support(report["id"], st.session_state.session_id)
                        st.rerun()
                buttons[1].caption(f'{report["comment_count"]} comments')
                with buttons[2]:
                    if st.button("View report", key=f'open_{report["id"]}', use_container_width=True, icon=":material/arrow_forward:"):
                        go("Issue details", report["id"])
    with rail:
        with card():
            st.subheader("From observation to action")
            st.write("Report a concern. Review the evidence together. Build a practical response.")
            st.html('<div class="rail">REPORT<br>AI ANALYZE<br>DISCUSS<br>TRACK<br>INNOVATE</div>')
            st.caption("Support signals community interest. It does not establish truth or severity.")
        with card():
            st.subheader("Start in Skardu")
            st.write("Explore a stream-litter scenario, add a useful observation, then build a collection pilot.")
            if st.button("Open Innovation Lab", use_container_width=True):
                go("Innovation Lab")


def report_page() -> None:
    heading("01 / Observe", "Give the issue a clear starting point.",
            "Describe what you saw, where it happened, and what the community should investigate next.")
    if st.button("Use Skardu demo example", icon=":material/edit_note:"):
        st.session_state.update(
            report_title="Garbage accumulating beside a stream in Skardu",
            report_description="Plastic bags, bottles and mixed household litter are accumulating on the dry bank beside a stream. Some waste is close to the water. I observed it from the public path and would like help arranging a safe site assessment and collection plan.",
            report_location="Skardu, Gilgit-Baltistan — stream beside a residential lane",
            report_category="Waste & litter",
        )
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        with st.form("report_form"):
            title = st.text_input("Issue title", max_chars=140, key="report_title", placeholder="What did you observe?")
            description = st.text_area("Description", height=160, max_chars=4000, key="report_description",
                                       placeholder="Describe visible conditions, extent and when you noticed the issue.")
            category = st.selectbox("Category", CATEGORIES, key="report_category")
            location = st.text_input("Location", max_chars=180, key="report_location", placeholder="Area, city, and a useful public landmark")
            upload = st.file_uploader("Evidence photo (optional)", type=["jpg", "jpeg", "png", "webp"], key="report_upload",
                                      help="Maximum 8 MB and 24 megapixels. Photos are re-encoded to remove metadata.")
            st.caption("Reports and images are shared in this app. With Gemini enabled, report text and your photo are sent to Google for analysis. Avoid personal or sensitive information.")
            submitted = st.form_submit_button("Publish report & analyze", type="primary", use_container_width=True)
        if submitted:
            try:
                report = db.validate_report(title, description, category, location)
                image, thumbnail = prepare_image(upload.getvalue()) if upload else (None, None)
                with st.spinner("Preparing advisory analysis and publishing your report…"):
                    envelope = generate(report, image=image, **ai_options())
                    report_id = db.create_report(report, envelope, image, thumbnail, st.session_state.report_token)
                st.session_state.report_token = str(uuid4())
                st.session_state.clear_report_form = True
                notice("Report published. Add local knowledge or plan the next step below.")
                go("Issue details", report_id)
            except ValueError as exc:
                st.error(str(exc))
    with right:
        with card():
            st.subheader("A useful report includes")
            bullets(["An observable environmental concern.", "A location others can understand.",
                     "A photo when it is safe and appropriate.", "What remains uncertain or needs checking."])
            st.caption("AI suggests causes and next steps. Community review determines progress; neither is official verification.")


def choose_report(key: str) -> dict | None:
    reports = db.list_reports()
    if not reports:
        st.info("No reports yet. Submit an environmental observation to begin.")
        return None
    ids = [r["id"] for r in reports]
    titles = {r["id"]: r["title"] for r in reports}
    selected = st.session_state.get("selected_report", ids[0])
    if key in st.session_state and st.session_state[key] not in ids:
        del st.session_state[key]
    report_id = st.selectbox("Select a report", ids, index=ids.index(selected) if selected in ids else 0,
                            format_func=lambda value: f"#{value:03d} · {titles[value]}", key=key)
    st.session_state.selected_report = report_id
    return db.get_report(report_id)


def detail_page() -> None:
    heading("02 / Understand & act", "Every issue needs a next step.", "Review the observation, compare perspectives, and record progress.")
    report = choose_report("detail_picker")
    if not report:
        return
    tags(report)
    st.subheader(report["title"])
    st.caption(f'{report["location"]} · Report #{report["id"]:03d} · {date_label(report["created_at"])}')
    if report["is_demo"]:
        st.info("Fictional demonstration scenario. Its discussion and status history illustrate the workflow.")
    current = STATUSES.index(report["status"])
    steps = []
    for index, status in enumerate(STATUSES):
        css = "done current" if index == current else ("done" if index < current else "")
        steps.append(f'<li class="{css}"><span class="step">0{index + 1}</span>{safe(status)}</li>')
    st.html('<ol class="timeline" aria-label="Community status timeline">' + "".join(steps) + "</ol>")
    evidence, discussion, progress = st.tabs(["Evidence & analysis", "Community discussion", "Progress history"])
    with evidence:
        left, right = st.columns([1.25, 1], gap="large")
        with left:
            with card():
                st.subheader("Field observation")
                prose(report["description"])
                if report["image"]:
                    show_image(report["image"], "Community-submitted evidence · not independently verified")
                else:
                    st.caption("Text-only observation · no evidence photo attached.")
        with right:
            with card():
                st.subheader("Environmental analysis", help="Advice cannot establish official verification.")
                envelope = report["analysis"]
                source_notice(envelope)
                data = envelope["data"]
                st.caption(f'Advisory priority: {data["advisory_priority"]} · Suggested category: {data["category"]}')
                prose(data["summary"])
                st.markdown("**Possible causes**")
                bullets(data["possible_causes"])
                st.markdown("**Recommended next actions**")
                bullets(data["recommended_next_actions"])
                st.caption(data["limitations"])
                if st.button("Refresh analysis", key=f'analyze_{report["id"]}', icon=":material/refresh:"):
                    with st.spinner("Reviewing the observation…"):
                        result = generate(report, image=report["image"], **ai_options())
                    if result["source"] != "Gemini" and envelope["source"] == "Gemini":
                        st.warning("Gemini is unavailable or demo mode is enabled. Your saved Gemini analysis has been kept.")
                    else:
                        db.save_analysis(report["id"], result)
                        notice("Analysis updated. The community status is unchanged.")
                        st.rerun()
                st.download_button("Download analysis JSON", json.dumps(envelope, indent=2),
                                   file_name=f'grip-report-{report["id"]}-analysis.json', mime="application/json")
        if st.button("Build a solution in Innovation Lab", type="primary", icon=":material/lightbulb:"):
            go("Innovation Lab", report["id"])
    with discussion:
        st.subheader("Local knowledge makes the difference")
        rows = db.comments(report["id"])
        if not rows:
            st.info("Start the discussion with an observation, a question, or a practical next step.")
        for row in rows:
            with card():
                st.html(f'<div class="meta"><strong>{safe(row["author"])}</strong> · {date_label(row["created_at"])}</div>')
                prose(row["body"])
        with st.form(f'comment_form_{report["id"]}', clear_on_submit=True):
            author = st.text_input("Display name", max_chars=60, key=f'comment_author_{report["id"]}')
            body = st.text_area("Add a useful comment", max_chars=1500, key=f'comment_body_{report["id"]}')
            if st.form_submit_button("Post comment", type="primary"):
                try:
                    db.add_comment(report["id"], author, body, st.session_state.comment_token)
                    st.session_state.comment_token = str(uuid4())
                    notice("Your comment has been added.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with progress:
        st.caption("Shared demo workspace: anyone with access can advance a report. “Verified” means community-reviewed only, never official or AI verification. Display names are self-declared.")
        for event in db.history(report["id"]):
            with card():
                st.html(f'<strong>{safe(event["status"])}</strong><div class="meta">{safe(event["actor"])} · {date_label(event["created_at"])}</div>')
                prose(event["note"])
        if report["status"] != STATUSES[-1]:
            next_status = STATUSES[current + 1]
            with st.form(f'status_form_{report["id"]}_{current}'):
                st.subheader(f"Next step: {next_status}")
                actor = st.text_input("Your display name", max_chars=60)
                note = st.text_area("Evidence or progress note", max_chars=1200,
                                    help="Explain the review or action supporting this change. Minimum 10 characters.")
                acknowledged = st.checkbox("I have recorded the basis for this community status update.")
                if st.form_submit_button(f"Move to {next_status}", type="primary"):
                    try:
                        if not acknowledged:
                            raise ValueError("Confirm that you have recorded the basis for this update.")
                        db.advance_status(report["id"], report["status"], actor, note)
                        notice(f"Community status updated to {next_status}.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        else:
            st.success("Marked resolved by the community. Continue the discussion if new evidence appears.")


def lab_page() -> None:
    heading("03 / Green Innovation Lab", "Turn a local problem into a practical pilot.",
            "Explore an approach your community can test, measure, and improve.")
    report = choose_report("lab_picker")
    if not report:
        return
    with card():
        tags(report)
        prose(report["description"])
    with st.form(f'innovation_form_{report["id"]}'):
        constraints = st.text_area("Local resources & constraints (optional)", max_chars=1000, height=100,
                                   placeholder="For example: a four-week pilot, five volunteers, willing local shops, limited transport.")
        if st.form_submit_button("Generate practical solution", type="primary", use_container_width=True):
            with st.spinner("Developing a small, measurable pilot…"):
                result = generate(report, "innovation", constraints=constraints, **ai_options())
                db.save_innovation(report["id"], result, constraints)
            notice("Your pilot concept is saved with this report.")
            st.rerun()
    plans = db.get_innovations(report["id"])
    if not plans:
        st.info("Your solution will include implementation, environmental benefit, a possible business model and a pilot plan.")
        return
    plan_index = st.selectbox("Saved plan", range(len(plans)),
                              format_func=lambda i: f'{"Latest · " if i == 0 else ""}{date_label(plans[i]["created_at"])} · {plans[i]["content"]["source"]}',
                              key=f'plan_version_{report["id"]}')
    saved = plans[plan_index]
    envelope = saved["content"]
    data = envelope["data"]
    source_notice(envelope)
    st.subheader(data["solution_name"])
    if saved["constraints_text"]:
        st.caption("Constraints used for this plan")
        prose(saved["constraints_text"])
    with card():
        prose(data["practical_solution"])
    left, right = st.columns(2, gap="large")
    with left:
        with card():
            st.subheader("Implementation approach")
            bullets(data["implementation_approach"])
        with card():
            st.subheader("Environmental benefit")
            prose(data["environmental_benefit"])
        with card():
            st.subheader("Possible green-business model")
            prose(data["green_business_model"])
    with right:
        with card():
            st.subheader("Pilot plan")
            bullets(data["pilot_plan"])
        with card():
            st.subheader("What to measure")
            bullets(data["success_metrics"])
    st.caption(data["assumptions_and_risks"])
    st.download_button("Download pilot plan JSON", json.dumps(saved, indent=2),
                       file_name=f'grip-report-{report["id"]}-pilot.json', mime="application/json")


def dashboard_page() -> None:
    heading("Impact / Overview", "See where attention becomes action.",
            "Report activity and community progress — not measured environmental impact.")
    include_demo = st.toggle("Include demo scenarios", value=True, key="dashboard_demo")
    reports = db.list_reports(include_demo=include_demo)
    totals = db.dashboard_data(include_demo)
    resolved = sum(r["status"] == "Resolved" for r in reports)
    metrics = st.columns(4)
    for col, label, value in zip(metrics, ["Reports", "Open issues", "Community resolved", "Saved pilot plans"],
                                  [len(reports), len(reports) - resolved, resolved, totals["innovations"]]):
        col.metric(label, value)
    st.caption(f'{sum(r["is_demo"] for r in reports)} demo scenarios included · {totals["comments"]} comments · {totals["votes"]} support signals')
    if not reports:
        st.info("No reports in this view yet. Publish an observation or include demo scenarios.")
        return
    left, right = st.columns(2, gap="large")
    for column, field, title, order in [(left, "category", "Reports by category", CATEGORIES),
                                        (right, "status", "Community status", STATUSES)]:
        with column, card():
            st.subheader(title)
            counts = Counter(r[field] for r in reports)
            frame = pd.DataFrame({"Group": order, "Reports": [counts[k] for k in order]})
            chart = alt.Chart(frame).mark_bar(color="#27795B", cornerRadiusEnd=5).encode(
                x=alt.X("Reports:Q", axis=alt.Axis(tickMinStep=1), title=None),
                y=alt.Y("Group:N", sort=order, title=None, axis=alt.Axis(labelLimit=210)),
                tooltip=["Group:N", "Reports:Q"],
            ).properties(height=230).configure_view(strokeOpacity=0).configure_axis(
                labelColor="#52685E", titleColor="#52685E", labelFontSize=12, gridColor="#E6ECE8"
            ).configure(background="#FFFFFF")
            st.altair_chart(chart, use_container_width=True, theme=None)
    with card():
        st.subheader("Report activity · last 14 days")
        dates = pd.date_range(pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=13), periods=14)
        counts = Counter(pd.Timestamp(r["created_at"]).normalize() for r in reports)
        frame = pd.DataFrame({"Date": dates, "Reports": [counts[d] for d in dates]})
        chart = alt.Chart(frame).mark_line(color="#27795B", point=alt.OverlayMarkDef(color="#27795B", filled=True)).encode(
            x=alt.X("Date:T", title=None, scale=alt.Scale(type="utc"),
                    axis=alt.Axis(format="%d %b", tickCount=7)),
            y=alt.Y("Reports:Q", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("Date:T", format="%d %b"), "Reports:Q"],
        ).properties(height=200).configure_view(strokeOpacity=0).configure_axis(
            labelColor="#52685E", titleColor="#52685E", labelFontSize=12, gridColor="#E6ECE8"
        ).configure(background="#FFFFFF")
        st.altair_chart(chart, use_container_width=True, theme=None)
    with st.expander("View underlying report data"):
        fields = ["id", "title", "category", "location", "status", "is_demo", "created_at"]
        st.dataframe(pd.DataFrame([{k: r[k] for k in fields} for r in reports]), hide_index=True, use_container_width=True)
    st.subheader("Latest progress")
    for event in totals["activity"]:
        with card():
            st.html(f'<strong>{safe(event["title"])}</strong><div class="meta">{safe(event["status"])} · {date_label(event["created_at"])}</div>')
            prose(event["note"])
    with st.expander("Download a workspace backup"):
        st.caption("The backup contains all reports, images and discussion, including demo scenarios. Streamlit Cloud local data may reset. Save a backup before your demo ends.")
        if st.button("Prepare database backup"):
            st.session_state.backup = db.backup_bytes()
        if "backup" in st.session_state:
            st.download_button("Download SQLite backup", st.session_state.backup, "grip-backup.db", "application/octet-stream")
            st.caption("Snapshot taken when you clicked Prepare. Prepare again to include newer changes.")


def main() -> None:
    apply_styles()
    db.init_db()
    if setting("GRIP_SEED_DEMO", "true").lower() == "true":
        seed_demo()
    for key in ("session_id", "report_token", "comment_token"):
        if key not in st.session_state:
            st.session_state[key] = str(uuid4())
    if st.session_state.pop("clear_report_form", False):
        for key in ("report_title", "report_description", "report_location", "report_category", "report_upload"):
            st.session_state.pop(key, None)
    if "pending_page" in st.session_state:
        st.session_state.route = st.session_state.pop("pending_page")
    with st.sidebar:
        st.html('<div class="brand"><div class="brand-mark">G</div><div><div class="brand-name">GRIP</div><div class="brand-sub">Local insight. Shared progress.</div></div></div>')
        page = st.radio("Workspace", ["Community feed", "Report issue", "Issue details", "Innovation Lab", "Dashboard"], key="route")
        st.divider()
        has_key = bool(setting("GEMINI_API_KEY"))
        st.toggle("Use local demo guidance", value=not has_key, key="demo_mode",
                  help="Bypass Gemini for a predictable demo. Reports and discussion still save normally.")
        st.caption("Gemini key configured" if has_key else "No Gemini key · local guidance available")
        st.html('<div class="rail">A shared environmental workspace.<br>Observe carefully. Act together.</div>')
        st.caption("Demo scenarios are fictional. Community status labels are not official verification.")
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    {"Community feed": feed_page, "Report issue": report_page, "Issue details": detail_page,
     "Innovation Lab": lab_page, "Dashboard": dashboard_page}[page]()
    st.html('<div class="footer">GRIP · Green Reporting &amp; Innovation Platform · Community-led environmental action</div>')


if __name__ == "__main__":
    try:
        main()
    except sqlite3.Error:
        st.error("The workspace could not save or load data right now. Please retry. If this continues, the app owner should check database access and disk space.")
        if st.button("Retry workspace"):
            st.rerun()
