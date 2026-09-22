import os
import sys
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.opportunity_db import (
    initialize_database,
    get_connection,
    get_opportunity,
    get_all_opportunities,
    update_status
)


STATUSES = [
    "NEW",
    "SHORTLISTED",
    "APPLIED",
    "ONLINE_TEST",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN"
]


def ensure_tracker_columns():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(opportunities)")
    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    columns_to_add = {
        "applied_at": "TEXT",
        "test_at": "TEXT",
        "interview_at": "TEXT",
        "notes": "TEXT"
    }

    for column, column_type in columns_to_add.items():
        if column not in columns:
            cursor.execute(
                f"""
                ALTER TABLE opportunities
                ADD COLUMN {column} {column_type}
                """
            )

    connection.commit()
    connection.close()


def get_status(opportunity_id):
    opportunity = get_opportunity(opportunity_id)

    if not opportunity:
        return None

    return opportunity["status"] or "NEW"


def update_tracker_field(opportunity_id, field, value):
    allowed_fields = {
        "applied_at",
        "test_at",
        "interview_at",
        "notes"
    }

    if field not in allowed_fields:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        UPDATE opportunities
        SET {field} = ?
        WHERE id = ?
        """,
        (value, opportunity_id)
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


def print_opportunity(opportunity):
    print("\n" + "=" * 70)
    print("OPPORTUNITY")
    print("=" * 70)

    print(f"ID:           {opportunity['id']}")
    print(f"Company:      {opportunity['company'] or 'Unknown'}")
    print(f"Role:         {opportunity['role'] or 'Unknown'}")
    print(f"Status:       {opportunity['status'] or 'NEW'}")

    parsed_jd = opportunity["parsed_jd"]

    if parsed_jd:
        try:
            import json

            if isinstance(parsed_jd, str):
                parsed_jd = json.loads(parsed_jd)

            print(
                f"Specialization: "
                f"{parsed_jd.get('specialization', 'Unknown')}"
            )

            print(
                f"Location:       "
                f"{parsed_jd.get('location', 'Unknown')}"
            )

        except Exception:
            pass

    print(
        f"Created:      "
        f"{opportunity['created_at'] or 'Unknown'}"
    )

    print(
        f"Applied:      "
        f"{opportunity['applied_at'] or 'Not recorded'}"
    )

    print(
        f"Online Test:  "
        f"{opportunity['test_at'] or 'Not recorded'}"
    )

    print(
        f"Interview:    "
        f"{opportunity['interview_at'] or 'Not recorded'}"
    )

    notes = opportunity["notes"]

    if notes:
        print(f"Notes:        {notes}")

    print("=" * 70)


def list_opportunities():
    opportunities = get_all_opportunities()

    if not opportunities:
        print("\nNo opportunities found.")
        return

    print("\n" + "=" * 90)
    print("APPLICATION TRACKER")
    print("=" * 90)

    print(
        f"{'ID':<5}"
        f"{'Company':<20}"
        f"{'Role':<32}"
        f"{'Status':<15}"
    )

    print("-" * 90)

    for opportunity in opportunities:
        company = (opportunity["company"] or "Unknown")[:18]
        role = (opportunity["role"] or "Unknown")[:30]
        status = opportunity["status"] or "NEW"

        print(
            f"{opportunity['id']:<5}"
            f"{company:<20}"
            f"{role:<32}"
            f"{status:<15}"
        )

    print("=" * 90)


def choose_opportunity():
    opportunities = get_all_opportunities()

    if not opportunities:
        print("\nNo opportunities found.")
        return None

    list_opportunities()

    while True:
        value = input("\nEnter Opportunity ID: ").strip()

        try:
            opportunity_id = int(value)
        except ValueError:
            print("Enter a valid numeric ID.")
            continue

        opportunity = get_opportunity(opportunity_id)

        if not opportunity:
            print("Opportunity not found.")
            continue

        return opportunity


def choose_status():
    print("\nAvailable statuses:")

    for index, status in enumerate(STATUSES, start=1):
        print(f"{index}. {status}")

    while True:
        value = input("\nSelect status: ").strip()

        try:
            index = int(value)
        except ValueError:
            print("Enter a number.")
            continue

        if 1 <= index <= len(STATUSES):
            return STATUSES[index - 1]

        print("Invalid selection.")


def update_opportunity_status():
    opportunity = choose_opportunity()

    if not opportunity:
        return

    new_status = choose_status()

    updated = update_status(
        opportunity["id"],
        new_status
    )

    if updated:
        print(
            f"\nStatus updated to: {new_status}"
        )

        if new_status == "APPLIED":
            existing = get_opportunity(opportunity["id"])

            if not existing["applied_at"]:
                now = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                update_tracker_field(
                    opportunity["id"],
                    "applied_at",
                    now
                )

                print(
                    f"Applied date recorded: {now}"
                )

    else:
        print("\nFailed to update status.")


def record_date(opportunity_id, field, label):
    print(
        f"\nEnter {label}."
    )

    print(
        "Format: YYYY-MM-DD HH:MM"
    )

    value = input(
        f"{label}: "
    ).strip()

    if not value:
        print("No value entered.")
        return

    try:
        datetime.strptime(
            value,
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        print(
            "Invalid date format."
        )
        return

    updated = update_tracker_field(
        opportunity_id,
        field,
        value
    )

    if updated:
        print(
            f"{label} saved."
        )
    else:
        print(
            f"Could not save {label}."
        )


def add_notes():
    opportunity = choose_opportunity()

    if not opportunity:
        return

    print("\nCurrent notes:")

    print(
        opportunity["notes"]
        or "No notes."
    )

    print(
        "\nEnter new notes."
    )

    notes = input(
        "Notes: "
    ).strip()

    if not notes:
        print("No notes entered.")
        return

    updated = update_tracker_field(
        opportunity["id"],
        "notes",
        notes
    )

    if updated:
        print("\nNotes saved.")
    else:
        print("\nFailed to save notes.")


def view_opportunity():
    opportunity = choose_opportunity()

    if opportunity:
        print_opportunity(opportunity)


def view_by_status():
    print("\nAvailable statuses:")

    for index, status in enumerate(STATUSES, start=1):
        print(f"{index}. {status}")

    while True:
        value = input(
            "\nSelect status: "
        ).strip()

        try:
            index = int(value)
        except ValueError:
            print("Enter a number.")
            continue

        if 1 <= index <= len(STATUSES):
            selected_status = STATUSES[index - 1]
            break

        print("Invalid selection.")

    opportunities = [
        opportunity
        for opportunity in get_all_opportunities()
        if (opportunity["status"] or "NEW")
           == selected_status
    ]

    print(
        f"\n{selected_status} OPPORTUNITIES"
    )

    print("-" * 90)

    if not opportunities:
        print("None.")
        return

    for opportunity in opportunities:
        print(
            f"[{opportunity['id']}] "
            f"{opportunity['company'] or 'Unknown'} "
            f"- "
            f"{opportunity['role'] or 'Unknown'}"
        )


def dashboard():
    opportunities = get_all_opportunities()

    counts = {
        status: 0
        for status in STATUSES
    }

    for opportunity in opportunities:
        status = opportunity["status"] or "NEW"

        if status not in counts:
            counts[status] = 0

        counts[status] += 1

    print("\n" + "=" * 70)
    print("PLACEMENT DASHBOARD")
    print("=" * 70)

    print(
        f"Total opportunities: {len(opportunities)}"
    )

    print()

    for status in STATUSES:
        print(
            f"{status:<15}: "
            f"{counts.get(status, 0)}"
        )

    print("=" * 70)


def tracker_menu():
    while True:
        print("\n" + "=" * 70)
        print("APPLICATION TRACKER")
        print("=" * 70)

        print("1. Dashboard")
        print("2. List opportunities")
        print("3. View opportunity")
        print("4. Update status")
        print("5. Record online test")
        print("6. Record interview")
        print("7. Add notes")
        print("8. Filter by status")
        print("9. Exit")

        choice = input(
            "\nSelect option: "
        ).strip()

        if choice == "1":
            dashboard()

        elif choice == "2":
            list_opportunities()

        elif choice == "3":
            view_opportunity()

        elif choice == "4":
            update_opportunity_status()

        elif choice == "5":
            opportunity = choose_opportunity()

            if opportunity:
                record_date(
                    opportunity["id"],
                    "test_at",
                    "Online test date"
                )

        elif choice == "6":
            opportunity = choose_opportunity()

            if opportunity:
                record_date(
                    opportunity["id"],
                    "interview_at",
                    "Interview date"
                )

        elif choice == "7":
            add_notes()

        elif choice == "8":
            view_by_status()

        elif choice == "9":
            print("\nExiting tracker.")
            break

        else:
            print("\nInvalid option.")


def main():
    print("Initializing database...")

    initialize_database()
    ensure_tracker_columns()

    print("Database ready.")

    tracker_menu()


if __name__ == "__main__":
    main()