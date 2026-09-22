import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "opportunities.db"
ANALYSIS_DIR = BASE_DIR / "analysis_results"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Placement Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.5rem 0 1rem 0;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .hero-subtitle {
        color: #777;
        font-size: 1.05rem;
    }

    .metric-card {
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        background: white;
        min-height: 110px;
    }

    .metric-label {
        color: #777;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }

    .score-large {
        font-size: 3.5rem;
        font-weight: 800;
    }

    .status-strong {
        color: #14833b;
        font-weight: 700;
    }

    .status-apply {
        color: #168aad;
        font-weight: 700;
    }

    .status-consider {
        color: #c77d00;
        font-weight: 700;
    }

    .status-low {
        color: #c45a00;
        font-weight: 700;
    }

    .status-skip {
        color: #b42318;
        font-weight: 700;
    }

    .status-nojd {
        color: #777;
        font-weight: 700;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    .info-box {
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 1rem;
        background: #fafafa;
        margin-bottom: 0.8rem;
    }

    .match-item {
        padding: 0.45rem 0;
        border-bottom: 1px solid #eeeeee;
    }

    .suggestion {
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        background: #f7f7f7;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

@st.cache_data(ttl=30)
def load_opportunities():

    if not DB_PATH.exists():
        return []

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM opportunities
            ORDER BY id DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


# ============================================================
# ANALYSIS FILES
# ============================================================

@st.cache_data(ttl=30)
def load_analysis_files():

    results = {}

    if not ANALYSIS_DIR.exists():
        return results

    for file in ANALYSIS_DIR.glob(
            "opportunity_*_analysis.json"
    ):

        try:

            with open(
                    file,
                    "r",
                    encoding="utf-8"
            ) as f:

                data = json.load(f)

            opportunity_id = data.get(
                "opportunity_id"
            )

            if opportunity_id is None:

                name = file.stem

                parts = name.split("_")

                if len(parts) >= 2:

                    try:
                        opportunity_id = int(
                            parts[1]
                        )
                    except ValueError:
                        continue

            if opportunity_id is not None:

                results[int(opportunity_id)] = data

        except Exception:
            continue

    return results


# ============================================================
# HELPERS
# ============================================================

def get_value(
        data,
        *keys,
        default=None
):

    for key in keys:

        if isinstance(data, dict) and key in data:

            value = data[key]

            if value is not None:

                return value

    return default


def get_score(
        analysis
):

    score = get_value(
        analysis,
        "fit_score",
        "score",
        "overall_score",
        default=None
    )

    if score is None:
        return None

    try:
        return float(score)
    except (ValueError, TypeError):
        return None


def get_decision(
        analysis
):

    return str(
        get_value(
            analysis,
            "decision",
            "recommendation",
            default="UNKNOWN"
        )
    ).upper()


def decision_class(
        decision
):

    decision = decision.upper()

    if "STRONG" in decision:
        return "status-strong"

    if decision == "APPLY":
        return "status-apply"

    if "CONSIDER" in decision:
        return "status-consider"

    if "LOW" in decision:
        return "status-low"

    if "SKIP" in decision:
        return "status-skip"

    return "status-nojd"


def normalize_list(
        value
):

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):

        return [
            value
        ]

    return []


def find_analysis(
        opportunity_id,
        analyses
):

    return analyses.get(
        int(opportunity_id)
    )


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            🎯 AI Placement Assistant
        </div>
        <div class="hero-subtitle">
            Resume ↔ Job Description Evaluation Dashboard
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

opportunities = load_opportunities()
analyses = load_analysis_files()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Dashboard")

    if st.button(
            "↻ Refresh Data",
            use_container_width=True
    ):

        load_opportunities.clear()
        load_analysis_files.clear()

        st.rerun()

    st.divider()

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "Opportunities",
            "Opportunity Details",
            "System Status",
        ]
    )

    st.divider()

    st.caption(
        "Data source"
    )

    st.caption(
        "SQLite database + analysis results"
    )


# ============================================================
# PREPARE STATISTICS
# ============================================================

analyzed = []

for opportunity in opportunities:

    opportunity_id = opportunity.get(
        "id"
    )

    analysis = find_analysis(
        opportunity_id,
        analyses
    )

    if analysis:

        score = get_score(
            analysis
        )

        decision = get_decision(
            analysis
        )

        analyzed.append(
            (
                opportunity,
                analysis,
                score,
                decision
            )
        )


strong_apply = sum(
    1
    for _, _, _, decision in analyzed
    if "STRONG" in decision
)

apply_count = sum(
    1
    for _, _, _, decision in analyzed
    if decision == "APPLY"
)

consider_count = sum(
    1
    for _, _, _, decision in analyzed
    if "CONSIDER" in decision
)

low_count = sum(
    1
    for _, _, _, decision in analyzed
    if "LOW" in decision
)

skip_count = sum(
    1
    for _, _, _, decision in analyzed
    if "SKIP" in decision
)

no_jd = sum(
    1
    for opportunity in opportunities
    if not opportunity.get(
        "parsed_jd"
    )
)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        '<div class="section-title">Overview</div>',
        unsafe_allow_html=True
    )

    columns = st.columns(6)

    metrics = [
        (
            "Total Opportunities",
            len(opportunities)
        ),
        (
            "Analyzed",
            len(analyzed)
        ),
        (
            "Strong Apply",
            strong_apply
        ),
        (
            "Apply",
            apply_count
        ),
        (
            "Consider",
            consider_count
        ),
        (
            "No JD",
            no_jd
        ),
    ]

    for column, (
            label,
            value
    ) in zip(
        columns,
        metrics
    ):

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        {label}
                    </div>
                    <div class="metric-value">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    st.markdown(
        '<div class="section-title">Top Opportunities</div>',
        unsafe_allow_html=True
    )

    ranked = sorted(
        analyzed,
        key=lambda item: (
            item[2]
            if item[2] is not None
            else -1
        ),
        reverse=True
    )

    if not ranked:

        st.info(
            "No analyzed opportunities available."
        )

    else:

        display_rows = []

        for (
                opportunity,
                analysis,
                score,
                decision
        ) in ranked[:10]:

            display_rows.append(
                {
                    "Company": opportunity.get(
                        "company",
                        "Unknown"
                    ),
                    "Role": opportunity.get(
                        "role",
                        "Unknown"
                    ),
                    "Score": (
                        f"{score:.0f}%"
                        if score is not None
                        else "N/A"
                    ),
                    "Recommendation": decision,
                }
            )

        st.dataframe(
            display_rows,
            use_container_width=True,
            hide_index=True
        )

    st.markdown(
        '<div class="section-title">Recommendation Distribution</div>',
        unsafe_allow_html=True
    )

    distribution = {
        "Strong Apply": strong_apply,
        "Apply": apply_count,
        "Consider": consider_count,
        "Low Match": low_count,
        "Skip": skip_count,
    }

    st.bar_chart(
        distribution
    )


# ============================================================
# OPPORTUNITIES
# ============================================================

elif page == "Opportunities":

    st.markdown(
        '<div class="section-title">All Opportunities</div>',
        unsafe_allow_html=True
    )

    search = st.text_input(
        "Search",
        placeholder="Search by company, role, or specialization..."
    )

    filter_options = [
        "All",
        "Analyzed",
        "No JD",
        "Strong Apply",
        "Apply",
        "Consider",
        "Low Match",
        "Skip",
    ]

    selected_filter = st.selectbox(
        "Filter",
        filter_options
    )

    filtered = []

    for opportunity in opportunities:

        company = str(
            opportunity.get(
                "company",
                ""
            )
        )

        role = str(
            opportunity.get(
                "role",
                ""
            )
        )

        specialization = str(
            opportunity.get(
                "specialization",
                ""
            )
        )

        searchable = (
                company
                + " "
                + role
                + " "
                + specialization
        ).lower()

        if search and search.lower() not in searchable:
            continue

        opportunity_id = opportunity.get(
            "id"
        )

        analysis = find_analysis(
            opportunity_id,
            analyses
        )

        if selected_filter == "Analyzed" and not analysis:
            continue

        if selected_filter == "No JD":

            if opportunity.get(
                    "parsed_jd"
            ):
                continue

        if selected_filter not in {
            "All",
            "Analyzed",
            "No JD"
        }:

            if not analysis:
                continue

            decision = get_decision(
                analysis
            )

            if selected_filter == "Strong Apply":
                if "STRONG" not in decision:
                    continue

            elif selected_filter == "Apply":
                if decision != "APPLY":
                    continue

            elif selected_filter == "Consider":
                if "CONSIDER" not in decision:
                    continue

            elif selected_filter == "Low Match":
                if "LOW" not in decision:
                    continue

            elif selected_filter == "Skip":
                if "SKIP" not in decision:
                    continue

        filtered.append(
            opportunity
        )

    rows = []

    for opportunity in filtered:

        opportunity_id = opportunity.get(
            "id"
        )

        analysis = find_analysis(
            opportunity_id,
            analyses
        )

        score = (
            get_score(analysis)
            if analysis
            else None
        )

        decision = (
            get_decision(analysis)
            if analysis
            else "NO JD"
        )

        rows.append(
            {
                "ID": opportunity_id,
                "Company": opportunity.get(
                    "company",
                    "Unknown"
                ),
                "Role": opportunity.get(
                    "role",
                    "Unknown"
                ),
                "Specialization": opportunity.get(
                    "specialization",
                    ""
                ),
                "Score": (
                    f"{score:.0f}%"
                    if score is not None
                    else "N/A"
                ),
                "Recommendation": decision,
            }
        )

    if rows:

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No opportunities match the selected filters."
        )


# ============================================================
# OPPORTUNITY DETAILS
# ============================================================

elif page == "Opportunity Details":

    st.markdown(
        '<div class="section-title">Opportunity Details</div>',
        unsafe_allow_html=True
    )

    if not opportunities:

        st.warning(
            "No opportunities found."
        )

    else:

        options = {}

        for opportunity in opportunities:

            opportunity_id = opportunity.get(
                "id"
            )

            company = opportunity.get(
                "company",
                "Unknown"
            )

            role = opportunity.get(
                "role",
                "Unknown"
            )

            options[
                f"{opportunity_id} — {company} — {role}"
            ] = opportunity_id

        selected_label = st.selectbox(
            "Select opportunity",
            list(options.keys())
        )

        selected_id = options[
            selected_label
        ]

        opportunity = next(
            (
                item
                for item in opportunities
                if item.get("id") == selected_id
            ),
            None
        )

        analysis = find_analysis(
            selected_id,
            analyses
        )

        if opportunity is None:

            st.error(
                "Opportunity not found."
            )

        else:

            company = opportunity.get(
                "company",
                "Unknown"
            )

            role = opportunity.get(
                "role",
                "Unknown"
            )

            specialization = opportunity.get(
                "specialization",
                ""
            )

            st.markdown(
                f"## {company}"
            )

            st.write(
                f"### {role}"
            )

            if specialization:

                st.caption(
                    specialization
                )

            st.divider()

            if not analysis:

                st.warning(
                    "This opportunity has not been analyzed yet."
                )

                if not opportunity.get(
                        "parsed_jd"
                ):

                    st.info(
                        "No parsed JD is available for this opportunity."
                    )

            else:

                score = get_score(
                    analysis
                )

                decision = get_decision(
                    analysis
                )

                best_track = get_value(
                    analysis,
                    "best_track",
                    "best_fit_track",
                    default=None
                )

                columns = st.columns(3)

                with columns[0]:

                    st.markdown(
                        "### Fit Score"
                    )

                    if score is not None:

                        st.markdown(
                            f'<div class="score-large">{score:.0f}%</div>',
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown(
                            '<div class="score-large">N/A</div>',
                            unsafe_allow_html=True
                        )

                with columns[1]:

                    st.markdown(
                        "### Recommendation"
                    )

                    st.markdown(
                        f'<div class="{decision_class(decision)}">{decision}</div>',
                        unsafe_allow_html=True
                    )

                with columns[2]:

                    st.markdown(
                        "### Best Track"
                    )

                    st.write(
                        best_track
                        if best_track
                        else "Not specified"
                    )

                st.divider()

                # --------------------------------------------
                # MATCHES
                # --------------------------------------------

                direct_matches = normalize_list(
                    get_value(
                        analysis,
                        "direct_matches",
                        "matches",
                        default=[]
                    )
                )

                project_matches = normalize_list(
                    get_value(
                        analysis,
                        "project_domain_evidence",
                        "project_matches",
                        "domain_matches",
                        default=[]
                    )
                )

                transferable = normalize_list(
                    get_value(
                        analysis,
                        "transferable_matches",
                        "related_matches",
                        default=[]
                    )
                )

                missing = normalize_list(
                    get_value(
                        analysis,
                        "missing_weak",
                        "missing",
                        "missing_skills",
                        default=[]
                    )
                )

                if direct_matches:

                    st.markdown(
                        "### Direct Matches"
                    )

                    for item in direct_matches:

                        if isinstance(
                                item,
                                dict
                        ):

                            text = (
                                    item.get(
                                        "skill"
                                    )
                                    or item.get(
                                "name"
                            )
                                    or str(item)
                            )

                        else:

                            text = str(
                                item
                            )

                        st.markdown(
                            f"✓ {text}"
                        )

                if project_matches:

                    st.markdown(
                        "### Project / Domain Evidence"
                    )

                    for item in project_matches:

                        if isinstance(
                                item,
                                dict
                        ):

                            text = (
                                    item.get(
                                        "skill"
                                    )
                                    or item.get(
                                "name"
                            )
                                    or str(item)
                            )

                        else:

                            text = str(
                                item
                            )

                        st.markdown(
                            f"✓ {text}"
                        )

                if transferable:

                    st.markdown(
                        "### Transferable / Related Matches"
                    )

                    for item in transferable:

                        if isinstance(
                                item,
                                dict
                        ):

                            text = (
                                    item.get(
                                        "skill"
                                    )
                                    or item.get(
                                "name"
                            )
                                    or str(item)
                            )

                        else:

                            text = str(
                                item
                            )

                        st.markdown(
                            f"~ {text}"
                        )

                if missing:

                    st.markdown(
                        "### Missing / Weak"
                    )

                    for item in missing:

                        if isinstance(
                                item,
                                dict
                        ):

                            text = (
                                    item.get(
                                        "skill"
                                    )
                                    or item.get(
                                "name"
                            )
                                    or str(item)
                            )

                        else:

                            text = str(
                                item
                            )

                        st.markdown(
                            f"✗ {text}"
                        )

                # --------------------------------------------
                # WHY SCORE
                # --------------------------------------------

                why = get_value(
                    analysis,
                    "why_this_score",
                    "score_explanation",
                    "explanation",
                    default=None
                )

                if why:

                    st.markdown(
                        "### Why This Score?"
                    )

                    st.markdown(
                        f'<div class="info-box">{why}</div>',
                        unsafe_allow_html=True
                    )

                # --------------------------------------------
                # AI ASSESSMENT
                # --------------------------------------------

                ai_assessment = get_value(
                    analysis,
                    "ai_assessment",
                    "assessment",
                    default=None
                )

                if isinstance(
                        ai_assessment,
                        dict
                ):

                    assessment_text = (
                            ai_assessment.get(
                                "assessment"
                            )
                            or ai_assessment.get(
                        "summary"
                    )
                            or ai_assessment.get(
                        "text"
                    )
                    )

                else:

                    assessment_text = ai_assessment

                if assessment_text:

                    st.markdown(
                        "### AI Assessment"
                    )

                    st.markdown(
                        f'<div class="info-box">{assessment_text}</div>',
                        unsafe_allow_html=True
                    )

                # --------------------------------------------
                # RESUME SUGGESTIONS
                # --------------------------------------------

                suggestions = get_value(
                    analysis,
                    "resume_suggestions",
                    "suggestions",
                    "improvement_suggestions",
                    default=[]
                )

                suggestions = normalize_list(
                    suggestions
                )

                if suggestions:

                    st.markdown(
                        "### Resume Improvements"
                    )

                    for suggestion in suggestions:

                        if isinstance(
                                suggestion,
                                dict
                        ):

                            text = (
                                    suggestion.get(
                                        "suggestion"
                                    )
                                    or suggestion.get(
                                "text"
                            )
                                    or str(suggestion)
                            )

                        else:

                            text = str(
                                suggestion
                            )

                        st.markdown(
                            f"""
                            <div class="suggestion">
                                • {text}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                # --------------------------------------------
                # TRACK COMPARISON
                # --------------------------------------------

                track_comparison = get_value(
                    analysis,
                    "track_comparison",
                    "tracks",
                    default=None
                )

                if track_comparison:

                    st.markdown(
                        "### Track Comparison"
                    )

                    if isinstance(
                            track_comparison,
                            dict
                    ):

                        track_rows = []

                        for name, value in track_comparison.items():

                            if isinstance(
                                    value,
                                    dict
                            ):

                                track_score = (
                                        value.get(
                                            "score"
                                        )
                                        or value.get(
                                    "fit_score"
                                )
                                )

                            else:

                                track_score = value

                            track_rows.append(
                                {
                                    "Track": name,
                                    "Score": track_score,
                                }
                            )

                        if track_rows:

                            st.dataframe(
                                track_rows,
                                use_container_width=True,
                                hide_index=True
                            )


# ============================================================
# SYSTEM STATUS
# ============================================================

elif page == "System Status":

    st.markdown(
        '<div class="section-title">System Status</div>',
        unsafe_allow_html=True
    )

    columns = st.columns(4)

    status_data = [
        (
            "Database",
            "Connected"
            if DB_PATH.exists()
            else "Not Found"
        ),
        (
            "Opportunities",
            len(opportunities)
        ),
        (
            "Analysis Files",
            len(analyses)
        ),
        (
            "Parsed JDs",
            len(
                [
                    item
                    for item in opportunities
                    if item.get(
                    "parsed_jd"
                )
                ]
            )
        ),
    ]

    for column, (
            label,
            value
    ) in zip(
        columns,
        status_data
    ):

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        {label}
                    </div>
                    <div class="metric-value">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    st.markdown(
        "### Paths"
    )

    st.code(
        f"""
Project:
{BASE_DIR}

Database:
{DB_PATH}

Analysis Results:
{ANALYSIS_DIR}
""".strip()
    )

    st.markdown(
        "### Last Data Refresh"
    )

    st.write(
        datetime.now().strftime(
            "%d %B %Y, %I:%M:%S %p"
        )
    )

    st.info(
        "The backend automatically updates Gmail data and "
        "analysis results in the background. Use Refresh Data "
        "to load the latest results into the dashboard."
    )