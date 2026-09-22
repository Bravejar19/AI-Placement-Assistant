import os
import sys
import json
from datetime import datetime


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# DATABASE
# ============================================================

from database.opportunity_db import (
    initialize_database,
    get_opportunity,
)


# ============================================================
# ANALYSIS DIRECTORY
# ============================================================

ANALYSIS_DIR = os.path.join(
    BASE_DIR,
    "analysis_results"
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=None):

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def row_value(
        row,
        key,
        default=None
):

    if row is None:
        return default

    try:

        value = row[key]

        if value is None:
            return default

        return value

    except (
            KeyError,
            IndexError,
            TypeError
    ):

        return default


def load_analysis(
        opportunity_id
):

    path = os.path.join(
        ANALYSIS_DIR,
        f"opportunity_{opportunity_id}_analysis.json"
    )

    if not os.path.exists(path):

        return None

    try:

        with open(
                path,
                "r",
                encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
                data,
                dict
        ):

            return None

        return data

    except Exception:

        return None


# ============================================================
# SCORE
# ============================================================

def get_score(
        analysis
):

    if not analysis:
        return None

    score = analysis.get(
        "fit_score"
    )

    if score is None:

        score = analysis.get(
            "score"
        )

    return safe_float(
        score
    )


# ============================================================
# DECISION
# ============================================================

def calculate_decision(
        score
):

    if score is None:

        return "NO JD"

    if score >= 75:

        return "STRONG APPLY"

    if score >= 60:

        return "APPLY"

    if score >= 45:

        return "CONSIDER"

    if score >= 30:

        return "LOW MATCH"

    return "SKIP"


# ============================================================
# PRIORITY
# ============================================================

def decision_priority(
        decision
):

    priorities = {

        "STRONG APPLY": 5,

        "APPLY": 4,

        "CONSIDER": 3,

        "LOW MATCH": 2,

        "SKIP": 1,

        "NO JD": 0
    }

    return priorities.get(
        decision,
        0
    )


# ============================================================
# OPPORTUNITY RECORD
# ============================================================

def build_record(
        opportunity
):

    opportunity_id = row_value(
        opportunity,
        "id"
    )

    company = row_value(
        opportunity,
        "company",
        "Unknown Company"
    )

    role = row_value(
        opportunity,
        "role",
        "Unknown Role"
    )

    parsed_jd = row_value(
        opportunity,
        "parsed_jd"
    )

    analysis = load_analysis(
        opportunity_id
    )

    score = get_score(
        analysis
    )

    # If parsed JD exists but analysis doesn't,
    # don't pretend there is a score.
    if score is None:

        decision = "NO JD"

        if parsed_jd:

            decision = "NOT ANALYZED"

    else:

        decision = calculate_decision(
            score
        )

    return {

        "id":
            opportunity_id,

        "company":
            company,

        "role":
            role,

        "parsed_jd":
            bool(parsed_jd),

        "analysis":
            analysis,

        "score":
            score,

        "decision":
            decision
    }


# ============================================================
# GET ALL OPPORTUNITIES
# ============================================================

def get_all_opportunities():

    # Try the most common database APIs used
    # by this project.

    try:

        from database.opportunity_db import (
            get_all_opportunities as getter
        )

        return getter()

    except ImportError:

        pass

    except Exception:

        pass

    try:

        from database.opportunity_db import (
            list_opportunities as getter
        )

        return getter()

    except ImportError:

        pass

    except Exception:

        pass

    # --------------------------------------------------------
    # Last-resort direct SQLite access.
    # --------------------------------------------------------

    import sqlite3

    database_file = os.path.join(
        BASE_DIR,
        "database",
        "opportunities.db"
    )

    connection = sqlite3.connect(
        database_file
    )

    connection.row_factory = sqlite3.Row

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM opportunities ORDER BY id ASC"
        )

        rows = cursor.fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# DISPLAY SINGLE OPPORTUNITY
# ============================================================

def display_single(
        record
):

    print()
    print(
        "=" * 70
    )

    print(
        f"OPPORTUNITY {record['id']}"
    )

    print(
        "=" * 70
    )

    print(
        "Company:",
        record["company"]
    )

    print(
        "Role:",
        record["role"]
    )

    print(
        "Parsed JD:",
        "YES" if record["parsed_jd"] else "NO"
    )

    analysis = record["analysis"]

    if not analysis:

        print()

        if record["parsed_jd"]:

            print(
                "Analysis has not been generated yet."
            )

        else:

            print(
                "No parsed JD available."
            )

        print(
            "Decision:",
            record["decision"]
        )

        return

    score = record["score"]

    print()

    print(
        f"Fit Score: {score:.0f}%"
    )

    print(
        "Recommendation:",
        analysis.get(
            "recommendation",
            calculate_decision(score)
        )
    )

    print(
        "Decision:",
        record["decision"]
    )

    best_track = analysis.get(
        "best_track"
    )

    if best_track:

        print(
            "Best Track:",
            best_track
        )

    track_scores = analysis.get(
        "track_scores",
        {}
    )

    if track_scores:

        print()
        print(
            "Track Scores:"
        )

        for name, value in track_scores.items():

            parsed_score = safe_float(
                value
            )

            if parsed_score is not None:

                print(
                    f"  {name.title():12} "
                    f"{parsed_score:.0f}%"
                )

    reason = analysis.get(
        "reason"
    )

    if reason:

        print()
        print(
            "Reason:"
        )

        print(
            reason
        )


# ============================================================
# ANALYZE OPPORTUNITY
# ============================================================

def analyze_one():

    value = input(
        "\nEnter Opportunity ID: "
    ).strip()

    try:

        opportunity_id = int(
            value
        )

    except ValueError:

        print(
            "Invalid Opportunity ID."
        )

        return

    opportunity = get_opportunity(
        opportunity_id
    )

    if opportunity is None:

        print(
            f"Opportunity {opportunity_id} not found."
        )

        return

    record = build_record(
        opportunity
    )

    display_single(
        record
    )


# ============================================================
# SORT
# ============================================================

def sort_records(
        records
):

    def key(record):

        score = record["score"]

        if score is None:

            score_key = -1

        else:

            score_key = score

        return (
            score_key,
            decision_priority(
                record["decision"]
            ),
            -int(
                record["id"]
            )
        )

    return sorted(
        records,
        key=key,
        reverse=True
    )


# ============================================================
# SUMMARY TABLE
# ============================================================

def print_summary(
        records
):

    print()
    print(
        "=" * 100
    )

    print(
        "PLACEMENT DECISION SUMMARY"
    )

    print(
        "=" * 100
    )

    print(
        f"{'ID':<5}"
        f"{'Company':<25}"
        f"{'Role':<32}"
        f"{'Score':<8}"
        f"{'Decision':<18}"
    )

    print(
        "-" * 100
    )

    for record in records:

        opportunity_id = str(
            record["id"]
        )

        company = str(
            record["company"]
        )

        role = str(
            record["role"]
        )

        decision = record[
            "decision"
        ]

        score = record[
            "score"
        ]

        if score is None:

            score_text = "N/A"

        else:

            score_text = (
                f"{score:.0f}"
            )

        company = company[:23]

        role = role[:30]

        print(
            f"{opportunity_id:<5}"
            f"{company:<25}"
            f"{role:<32}"
            f"{score_text:<8}"
            f"{decision:<18}"
        )

    print(
        "=" * 100
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

def print_recommendations(
        records
):

    strong = [
        r for r in records
        if r["decision"] == "STRONG APPLY"
    ]

    apply = [
        r for r in records
        if r["decision"] == "APPLY"
    ]

    consider = [
        r for r in records
        if r["decision"] == "CONSIDER"
    ]

    low = [
        r for r in records
        if r["decision"] == "LOW MATCH"
    ]

    skip = [
        r for r in records
        if r["decision"] == "SKIP"
    ]

    no_jd = [
        r for r in records
        if r["decision"] == "NO JD"
    ]

    not_analyzed = [
        r for r in records
        if r["decision"] == "NOT ANALYZED"
    ]

    analyzed = [
        r for r in records
        if r["score"] is not None
    ]

    print()
    print(
        "RECOMMENDATIONS"
    )

    print(
        "-" * 70
    )

    print(
        f"Strong apply: {len(strong)}"
    )

    print(
        f"Apply:        {len(apply)}"
    )

    print(
        f"Consider:     {len(consider)}"
    )

    print(
        f"Low match:    {len(low)}"
    )

    print(
        f"Skip:         {len(skip)}"
    )

    print(
        f"Total analyzed: {len(analyzed)}"
    )

    print(
        f"No JD:          {len(no_jd)}"
    )

    print(
        f"Not analyzed:   {len(not_analyzed)}"
    )

    # --------------------------------------------------------
    # Best opportunities
    # --------------------------------------------------------

    best = [
        r for r in records
        if r["score"] is not None
    ]

    best = sorted(
        best,
        key=lambda r: r["score"],
        reverse=True
    )

    if best:

        print()
        print(
            "TOP OPPORTUNITIES"
        )

        print(
            "-" * 70
        )

        for index, record in enumerate(
                best[:10],
                start=1
        ):

            print(
                f"{index}. "
                f"{record['company']} — "
                f"{record['role']} — "
                f"{record['score']:.0f}% "
                f"({record['decision']})"
            )

    # --------------------------------------------------------
    # No JD opportunities
    # --------------------------------------------------------

    if no_jd:

        print()
        print(
            "OPPORTUNITIES WITHOUT PARSED JD"
        )

        print(
            "-" * 70
        )

        for record in no_jd:

            print(
                f"{record['id']}. "
                f"{record['company']} — "
                f"{record['role']}"
            )

        print()
        print(
            "These cannot receive a reliable fit score "
            "until their JD is parsed."
        )

    # --------------------------------------------------------
    # Not analyzed
    # --------------------------------------------------------

    if not_analyzed:

        print()
        print(
            "PARSED JDs NOT YET ANALYZED"
        )

        print(
            "-" * 70
        )

        for record in not_analyzed:

            print(
                f"{record['id']}. "
                f"{record['company']} — "
                f"{record['role']}"
            )


# ============================================================
# ANALYZE ALL
# ============================================================

def analyze_all():

    print()
    print(
        "Analyzing all opportunities..."
    )

    opportunities = get_all_opportunities()

    if not opportunities:

        print(
            "No opportunities found."
        )

        return

    print(
        f"Total opportunities: "
        f"{len(opportunities)}"
    )

    records = []

    for opportunity in opportunities:

        try:

            record = build_record(
                opportunity
            )

            records.append(
                record
            )

        except Exception as error:

            opportunity_id = row_value(
                opportunity,
                "id",
                "?"
            )

            company = row_value(
                opportunity,
                "company",
                "Unknown Company"
            )

            role = row_value(
                opportunity,
                "role",
                "Unknown Role"
            )

            records.append({

                "id":
                    opportunity_id,

                "company":
                    company,

                "role":
                    role,

                "parsed_jd":
                    False,

                "analysis":
                    None,

                "score":
                    None,

                "decision":
                    "NO JD",

                "error":
                    str(error)
            })

    records = sort_records(
        records
    )

    print_summary(
        records
    )

    print_recommendations(
        records
    )


# ============================================================
# MENU
# ============================================================

def menu():

    while True:

        print()
        print(
            "=" * 70
        )

        print(
            "PLACEMENT DECISION ENGINE"
        )

        print(
            "=" * 70
        )

        print(
            "1. Analyze opportunity"
        )

        print(
            "2. Analyze all opportunities"
        )

        print(
            "3. Exit"
        )

        choice = input(
            "\nSelect option: "
        ).strip()

        if choice == "1":

            analyze_one()

        elif choice == "2":

            analyze_all()

        elif choice == "3":

            print(
                "Exiting."
            )

            break

        else:

            print(
                "Invalid option."
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Initializing database..."
    )

    initialize_database()

    print(
        "Database ready."
    )

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":

        print()
        print(
            "AUTOMATIC MODE"
        )

        print(
            "Analyzing all opportunities..."
        )

        analyze_all()

        print()
        print(
            "Automatic analysis complete."
        )

        return

    menu()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
