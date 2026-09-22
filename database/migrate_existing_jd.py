import os
import sys

# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# IMPORTS
# ============================================================

from documents.processor import process_document
from database.opportunity_db import (
    initialize_database,
    update_parsed_jd,
    get_opportunity
)


# ============================================================
# EXISTING SANDISK JD
# ============================================================

JD_PATH = os.path.join(
    BASE_DIR,
    "attachments",
    "1a0433c0ea27e37b",
    "Intern_JD.docx"
)

OPPORTUNITY_ID = 1


# ============================================================
# MAIN
# ============================================================

def migrate_jd():

    print(
        "Initializing database..."
    )

    initialize_database()

    print(
        "Database ready!"
    )

    # --------------------------------------------------------
    # Check opportunity
    # --------------------------------------------------------

    opportunity = get_opportunity(
        OPPORTUNITY_ID
    )

    if not opportunity:

        print(
            f"\n❌ Opportunity {OPPORTUNITY_ID} not found."
        )

        return

    print(
        "\nFound opportunity:"
    )

    print(
        "Company:",
        opportunity["company"]
    )

    print(
        "Role:",
        opportunity["role"]
    )

    # --------------------------------------------------------
    # Check JD file
    # --------------------------------------------------------

    if not os.path.exists(JD_PATH):

        print(
            "\n❌ JD file not found:"
        )

        print(
            JD_PATH
        )

        return

    print(
        "\n📄 Processing existing JD..."
    )

    print(
        JD_PATH
    )

    # --------------------------------------------------------
    # Extract + parse
    # --------------------------------------------------------

    result = process_document(
        JD_PATH
    )

    if not result:

        print(
            "\n❌ Document processing failed."
        )

        return

    jd_text = result.get(
        "raw_text"
    )

    parsed_jd = result.get(
        "job_description"
    )

    if not jd_text or not parsed_jd:

        print(
            "\n❌ Parsed JD data is empty."
        )

        return

    # --------------------------------------------------------
    # Store in database
    # --------------------------------------------------------

    updated = update_parsed_jd(
        OPPORTUNITY_ID,
        jd_text,
        parsed_jd
    )

    if not updated:

        print(
            "\n❌ Failed to update opportunity."
        )

        return

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "✅ EXISTING JD MIGRATED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )

    print(
        "Opportunity ID:",
        OPPORTUNITY_ID
    )

    print(
        "Company:",
        opportunity["company"]
    )

    print(
        "Role:",
        parsed_jd.get(
            "role"
        )
    )

    print(
        "Specialization:",
        parsed_jd.get(
            "specialization"
        )
    )

    print(
        "Location:",
        parsed_jd.get(
            "location"
        )
    )

    print(
        "Must-have skills:",
        len(
            parsed_jd.get(
                "must_have",
                []
            )
        )
    )

    print(
        "Required skills:",
        len(
            parsed_jd.get(
                "required_skills",
                []
            )
        )
    )

    print(
        "Preferred qualifications:",
        len(
            parsed_jd.get(
                "preferred_qualifications",
                []
            )
        )
    )

    print(
        "\n✓ Raw JD stored in SQLite"
    )

    print(
        "✓ Parsed JD stored in SQLite"
    )

    print(
        "✓ Opportunity #1 is now ready for resume analysis"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    migrate_jd()