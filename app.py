import streamlit as st

from database import (
    init_db,
    seed_demo_data,
    create_report,
    list_reports,
    get_report,
    add_comment,
    list_comments,
    update_status,
)
from ai_service import analyze_environmental_report, generate_green_innovation


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="GRIP — Green Reporting & Innovation Platform",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CONSTANTS
# =========================================================
STATUSES = [
    "Reported",
    "Under Review",
    "Verified",
    "Action Required",
    "Resolved",
]

CATEGORIES = [
    "Water",
    "Waste",
    "Air",
    "Climate",
    "Biodiversity",
    "Other",
]


# =========================================================
# PREMIUM UI
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #11241a;
        --muted: #68786e;
        --line: #dbe8df;
        --soft: #f2f8f4;
        --accent: #16804f;
        --accent2: #0d613d;
        --white: #ffffff;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--ink);
        letter-spacing: -0.035em;
    }

    .block-container {
        max-width: 1240px;
        padding: 1.15rem 2rem 3rem;
    }

    [data-testid="stSidebar"] {
        background: #f7fbf8;
        border-right: 1px solid var(--line);
    }

    .brand {
        font: 700 2.2rem 'Space Grotesk', sans-serif;
        letter-spacing: -0.06em;
        color: var(--ink);
    }

    .subbrand {
        font-size: 0.82rem;
        color: var(--muted);
        margin-top: -0.2rem;
    }

    .hero {
        padding: 1.7rem 1.8rem;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: linear-gradient(
            135deg,
            #edf8f0 0%,
            #ffffff 57%,
            #f6fbf8 100%
        );
        box-shadow: 0 12px 30px rgba(17, 36, 26, 0.04);
    }

    .kicker {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: var(--accent2);
    }

    .hero-title {
        font: 700 2.85rem 'Space Grotesk', sans-serif;
        letter-spacing: -0.065em;
        color: var(--ink);
        margin: 0.15rem 0 0.3rem;
    }

    .hero-copy {
        max-width: 820px;
        color: #506259;
        line-height: 1.55;
    }

    .flow {
        margin-top: 0.9rem;
        font-weight: 700;
        font-size: 0.88rem;
        color: #315247;
    }

    .metric {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 17px;
        padding: 1rem 1.05rem;
        box-shadow: 0 7px 20px rgba(17, 36, 26, 0.03);
    }

    .metric-num {
        font: 700 1.7rem 'Space Grotesk', sans-serif;
        color: var(--ink);
    }

    .metric-label {
        font-size: 0.78rem;
        color: var(--muted);
    }

    .card {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem 1.05rem;
        margin: 0.7rem 0;
        box-shadow: 0 5px 18px rgba(17, 36, 26, 0.025);
    }

    .issue-title {
        font: 700 1.08rem 'Space Grotesk', sans-serif;
        color: var(--ink);
    }

    .meta {
        font-size: 0.8rem;
        color: var(--muted);
    }

    .pill,
    .status {
        display: inline-block;
        padding: 0.27rem 0.62rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
    }

    .pill {
        background: #eaf6ee;
        color: #166a43;
        border: 1px solid #cfe7d7;
    }

    .status {
        background: #f4f7f5;
        color: #526158;
        border: 1px solid var(--line);
    }

    .callout {
        border-left: 4px solid var(--accent);
        background: var(--soft);
        padding: 0.85rem 1rem;
        border-radius: 0 13px 13px 0;
        color: #385248;
    }

    .timeline {
        display: flex;
        gap: 0.42rem;
        align-items: center;
        flex-wrap: wrap;
        margin: 0.55rem 0 1rem;
    }

    .step {
        padding: 0.34rem 0.56rem;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: #fff;
        color: #77847d;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .step.active {
        background: #e5f4ea;
        color: #11633c;
        border-color: #c7e3d0;
    }

    .section-label {
        font-size: 0.76rem;
        color: var(--muted);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .footer {
        font-size: 0.73rem;
        color: #859189;
        margin-top: 2rem;
    }

    button[kind="primary"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================
init_db()
seed_demo_data()


# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "selected_report" not in st.session_state:
    st.session_state.selected_report = None

if "innovation_result" not in st.session_state:
    st.session_state.innovation_result = None


# =========================================================
# HELPERS
# =========================================================
def go(page: str):
    st.session_state.page = page

    if page != "Innovation Lab":
        st.session_state.innovation_result = None

    st.rerun()


def status_badge(value: str) -> str:
    return f'<span class="status">{value}</span>'


def render_timeline(current: str):
    current_idx = STATUSES.index(current) if current in STATUSES else 0

    html = '<div class="timeline">'

    for i, status in enumerate(STATUSES):
        active = " active" if i <= current_idx else ""

        html += f'<span class="step{active}">{status}</span>'

        if i < len(STATUSES) - 1:
            html += '<span style="color:#a4b0aa">→</span>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def render_report_card(report: dict):
    with st.container(border=True):

        left, right = st.columns([5, 1])

        with left:
            st.markdown(
                f'<div class="issue-title">{report["title"]}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'''
                <div style="margin:.4rem 0">
                    <span class="pill">{report["category"]}</span>
                    &nbsp;
                    {status_badge(report["status"])}
                </div>
                ''',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'''
                <div class="meta">
                    📍 {report["location"]}
                    &nbsp;•&nbsp;
                    Report #{report["id"]}
                    &nbsp;•&nbsp;
                    {report["created_at"]}
                </div>
                ''',
                unsafe_allow_html=True,
            )

            st.write(report["description"])

        with right:
            if st.button(
                "View issue",
                key=f"view_{report['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_report = report["id"]
                go("Issue")


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown('<div class="brand">GRIP</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="subbrand">Green Reporting & Innovation Platform</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    pages = [
        "Home",
        "Report an Issue",
        "Innovation Lab",
        "Dashboard",
    ]

    selected_page = st.radio(
        "Navigate",
        pages,
        index=pages.index(st.session_state.page)
        if st.session_state.page in pages
        else 0,
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.session_state.innovation_result = None
        st.rerun()

    st.divider()

    st.markdown(
        '<div class="section-label">Core flow</div>',
        unsafe_allow_html=True,
    )

    st.caption("Report → Analyze → Discuss → Track → Innovate")
    st.caption(
        "AI assistance is advisory. Reports require human verification."
    )


# =========================================================
# HOME
# =========================================================
if st.session_state.page == "Home":

    st.markdown(
        """
        <div class="hero">
            <div class="kicker">Community + AI for environmental action</div>

            <div class="hero-title">
                Turn environmental problems into action.
            </div>

            <div class="hero-copy">
                GRIP gives people one focused place to report environmental
                issues, discuss evidence, track progress, and generate
                practical green innovation ideas.
            </div>

            <div class="flow">
                REPORT → ANALYZE → DISCUSS → TRACK → INNOVATE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    reports = list_reports()

    metrics = [
        (len(reports), "Reports"),
        (
            sum(r["status"] == "Verified" for r in reports),
            "Verified",
        ),
        (
            sum(r["status"] == "Action Required" for r in reports),
            "Action Required",
        ),
        (
            sum(r["status"] == "Resolved" for r in reports),
            "Resolved",
        ),
    ]

    cols = st.columns(4)

    for col, (value, label) in zip(cols, metrics):
        col.markdown(
            f'''
            <div class="metric">
                <div class="metric-num">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    st.write("")

    a, b = st.columns([4, 1])

    with a:
        st.markdown(
            '<div class="section-label">Community feed</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Latest environmental reports")

    with b:
        if st.button(
            "＋ Report issue",
            type="primary",
            use_container_width=True,
        ):
            go("Report an Issue")

    f1, f2 = st.columns([2, 1])

    with f1:
        query = st.text_input(
            "Search",
            placeholder="Search issues, places, or categories…",
            label_visibility="collapsed",
        )

    with f2:
        category_filter = st.selectbox(
            "Category",
            ["All"] + CATEGORIES,
            label_visibility="collapsed",
        )

    q = query.strip().lower()

    filtered = [
        report
        for report in reports
        if (
            not q
            or q
            in (
                f'{report["title"]} '
                f'{report["description"]} '
                f'{report["location"]} '
                f'{report["category"]}'
            ).lower()
        )
        and (
            category_filter == "All"
            or report["category"] == category_filter
        )
    ]

    if not filtered:
        st.info("No matching environmental reports.")

    else:
        for report in filtered[:10]:
            render_report_card(report)


# =========================================================
# REPORT ISSUE
# =========================================================
elif st.session_state.page == "Report an Issue":

    st.title("Report an environmental issue")

    st.caption(
        "Submit useful evidence and context. AI assists with triage; "
        "it does not officially verify a report."
    )

    with st.form("report_form", clear_on_submit=True):

        title = st.text_input(
            "Issue title",
            placeholder="e.g. Waste dumped beside a stream",
        )

        c1, c2 = st.columns(2)

        with c1:
            category = st.selectbox(
                "Category",
                CATEGORIES,
            )

        with c2:
            location = st.text_input(
                "Location",
                placeholder="e.g. Skardu, Gilgit-Baltistan",
            )

        description = st.text_area(
            "What did you observe?",
            placeholder=(
                "Describe what happened, where it happened, "
                "and why it matters."
            ),
            height=150,
        )

        image = st.file_uploader(
            "Evidence photo (optional)",
            type=["jpg", "jpeg", "png", "webp"],
        )

        submitted = st.form_submit_button(
            "Analyze & Submit",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if (
            not title.strip()
            or not location.strip()
            or not description.strip()
        ):
            st.error(
                "Please complete the title, location, and description."
            )

        else:

            image_bytes = image.getvalue() if image else None
            image_type = image.type if image else None

            with st.spinner("Analyzing the report…"):

                ai = analyze_environmental_report(
                    title=title.strip(),
                    category=category,
                    location=location.strip(),
                    description=description.strip(),
                    image_bytes=image_bytes,
                    mime_type=image_type,
                )

                report_id = create_report(
                    title=title.strip(),
                    category=ai.get("category", category),
                    location=location.strip(),
                    description=description.strip(),
                    image_bytes=image_bytes,
                    mime_type=image_type,
                    ai_analysis=ai,
                )

            st.session_state.selected_report = report_id
            st.session_state.page = "Issue"

            st.success("Report created successfully.")
            st.rerun()


# =========================================================
# ISSUE DETAILS
# =========================================================
elif st.session_state.page == "Issue":

    report_id = st.session_state.selected_report

    report = get_report(report_id) if report_id else None

    if not report:

        st.warning("Select an issue from the Home feed first.")

        if st.button("Back to Home"):
            go("Home")

        st.stop()

    if st.button("← Back to feed"):
        go("Home")

    st.title(report["title"])

    st.markdown(
        f'''
        <span class="pill">{report["category"]}</span>
        &nbsp;
        {status_badge(report["status"])}
        ''',
        unsafe_allow_html=True,
    )

    st.caption(
        f'📍 {report["location"]} · '
        f'Report #{report["id"]} · '
        f'{report["created_at"]}'
    )

    left, right = st.columns([1.05, 1])

    with left:

        if report.get("image_bytes"):
            st.image(
                report["image_bytes"],
                use_container_width=True,
            )

        else:
            st.info("No evidence image attached.")

        st.markdown("### Observation")
        st.write(report["description"])

    with right:

        st.markdown("### AI-assisted analysis")

        ai = report.get("ai_analysis") or {}

        st.markdown(
            f'''
            <div class="callout">
                <b>Summary:</b>
                {ai.get("summary", "Not available")}
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.write("")

        st.write(
            f'**Priority:** {ai.get("priority", "Medium")}'
        )

        st.write("**Possible causes**")

        for item in ai.get("possible_causes", []):
            st.write(f"• {item}")

        st.write("**Suggested next actions**")

        for item in ai.get("next_actions", []):
            st.write(f"• {item}")

        st.caption(
            "AI output is advisory and does not establish official verification."
        )

    st.divider()

    st.markdown("### Issue progress")

    render_timeline(report["status"])

    update_choice = st.selectbox(
        "Update status (demo/admin)",
        STATUSES,
        index=(
            STATUSES.index(report["status"])
            if report["status"] in STATUSES
            else 0
        ),
    )

    if st.button(
        "Save status",
        type="primary",
    ):
        update_status(
            report["id"],
            update_choice,
        )

        st.success("Issue status updated.")
        st.rerun()

    st.divider()

    st.markdown("### Community discussion")

    comments = list_comments(report["id"])

    if not comments:
        st.caption(
            "No comments yet. Add the first useful observation."
        )

    for comment in comments:

        st.markdown(
            f'''
            **{comment["author"]}**
            <span class="meta">· {comment["created_at"]}</span>
            ''',
            unsafe_allow_html=True,
        )

        st.write(comment["comment"])

    with st.form("comment_form", clear_on_submit=True):

        author = st.text_input(
            "Your name",
            value="Demo User",
        )

        comment_text = st.text_area(
            "Add a comment",
            placeholder="Add useful context or evidence.",
        )

        ok = st.form_submit_button(
            "Post comment",
            use_container_width=True,
        )

        if ok:

            if not comment_text.strip():
                st.error(
                    "Write a comment before posting."
                )

            else:

                add_comment(
                    report["id"],
                    author.strip() or "Anonymous",
                    comment_text.strip(),
                )

                st.success("Comment added.")
                st.rerun()


# =========================================================
# INNOVATION LAB
# =========================================================
elif st.session_state.page == "Innovation Lab":

    st.title("Green Innovation Lab")

    st.caption(
        "Turn an environmental problem into a practical solution "
        "and possible green-business opportunity."
    )

    reports = list_reports()

    if not reports:

        st.info(
            "Create an environmental report first."
        )

        st.stop()

    options = {
        (
            f'#{report["id"]} — '
            f'{report["title"]} · '
            f'{report["location"]}'
        ): report["id"]
        for report in reports
    }

    selected_label = st.selectbox(
        "Choose a problem",
        list(options.keys()),
    )

    report = get_report(
        options[selected_label]
    )

    st.markdown(
        f'''
        <div class="card">
            <div class="issue-title">
                {report["title"]}
            </div>

            <div class="meta">
                {report["category"]} · {report["location"]}
            </div>

            <p>
                {report["description"]}
            </p>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if st.button(
        "Generate Green Solution",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Generating a practical innovation pathway…"
        ):

            st.session_state.innovation_result = (
                generate_green_innovation(report)
            )

    if st.session_state.innovation_result:

        idea = st.session_state.innovation_result

        st.divider()

        st.markdown(
            '<div class="section-label">AI innovation brief</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("#### Proposed solution")
            st.write(idea.get("solution", ""))

            st.markdown("#### How it could work")
            st.write(idea.get("implementation", ""))

            st.markdown("#### First pilot")
            st.write(idea.get("pilot", ""))

        with c2:

            st.markdown("#### Environmental benefit")
            st.write(idea.get("environmental_benefit", ""))

            st.markdown("#### Possible green-business model")
            st.write(idea.get("business_model", ""))

            st.markdown("#### Problem addressed")
            st.write(idea.get("problem", ""))

        st.caption(
            "AI-generated ideas are starting points and require local validation."
        )


# =========================================================
# DASHBOARD
# =========================================================
else:

    st.title("GRIP Dashboard")

    reports = list_reports()

    if not reports:

        st.info("No reports yet.")

    else:

        categories = {}
        statuses = {}

        for report in reports:

            categories[report["category"]] = (
                categories.get(report["category"], 0) + 1
            )

            statuses[report["status"]] = (
                statuses.get(report["status"], 0) + 1
            )

        a, b = st.columns(2)

        with a:

            st.markdown(
                '<div class="section-label">Issues by category</div>',
                unsafe_allow_html=True,
            )

            st.bar_chart(categories)

        with b:

            st.markdown(
                '<div class="section-label">Issues by status</div>',
                unsafe_allow_html=True,
            )

            st.bar_chart(statuses)

        st.divider()

        st.markdown(
            '<div class="section-label">Recent reports</div>',
            unsafe_allow_html=True,
        )

        for report in reports[:15]:

            st.write(
                f'**#{report["id"]} {report["title"]}** — '
                f'{report["category"]} — '
                f'{report["status"]} — '
                f'{report["location"]}'
            )


# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
    <div class="footer">
        GRIP MVP · Pak Angels / iCode Guru Hackathon ·
        AI assistance is advisory and requires human verification.
    </div>
    """,
    unsafe_allow_html=True,
)
