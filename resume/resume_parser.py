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
# IMPORT DOCUMENT EXTRACTOR
# ============================================================

from documents.extractor import extract_text


# ============================================================
# FIND RESUME
# ============================================================

RESUME_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


def find_resume():

    supported_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    files = []

    for filename in os.listdir(
            RESUME_DIR
    ):

        file_path = os.path.join(
            RESUME_DIR,
            filename
        )

        if not os.path.isfile(
                file_path
        ):
            continue

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension in supported_extensions:

            files.append(
                file_path
            )

    if not files:

        return None

    # Prefer resume.pdf if present
    preferred = os.path.join(
        RESUME_DIR,
        "resume.pdf"
    )

    if os.path.exists(
            preferred
    ):

        return preferred

    return files[0]


# ============================================================
# PARSE RESUME
# ============================================================

def parse_resume():

    resume_path = find_resume()

    if not resume_path:

        print(
            "❌ No resume found."
        )

        print(
            "\nPlace your resume inside:"
        )

        print(
            RESUME_DIR
        )

        return None

    print(
        "\n📄 Resume found:"
    )

    print(
        resume_path
    )

    print(
        "\n📄 Extracting resume text..."
    )

    try:

        text = extract_text(
            resume_path
        )

    except Exception as error:

        print(
            "\n❌ Resume extraction failed:"
        )

        print(
            error
        )

        return None

    if not text.strip():

        print(
            "\n❌ No readable text found in resume."
        )

        return None

    print(
        f"✓ Extracted {len(text)} characters"
    )

    return {
        "file_name": os.path.basename(
            resume_path
        ),

        "file_path": resume_path,

        "text": text,

        "character_count": len(text)
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = parse_resume()

    if result:

        print(
            "\n" + "=" * 70
        )

        print(
            "📋 EXTRACTED RESUME"
        )

        print(
            "=" * 70
        )

        print(
            result["text"]
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "Resume extraction complete."
        )

        print(
            "=" * 70
        )