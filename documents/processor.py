import os
import json

from documents.extractor import extract_text
from documents.jd_parser import parse_jd


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


def process_document(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        print(
            f"Skipping unsupported file: {file_path}"
        )
        return None

    print(
        f"\n📄 Processing document:"
        f"\n   {os.path.basename(file_path)}"
    )

    # --------------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------------

    text = extract_text(
        file_path
    )

    if not text.strip():

        print(
            "⚠️ No readable text found."
        )

        return None

    print(
        f"✓ Extracted {len(text)} characters"
    )

    # --------------------------------------------------------
    # PARSE JD
    # --------------------------------------------------------

    parsed_jd = parse_jd(
        text
    )

    # --------------------------------------------------------
    # BUILD RESULT
    # --------------------------------------------------------

    result = {
        "file_name": os.path.basename(
            file_path
        ),

        "file_path": file_path,

        "file_type": extension,

        "character_count": len(text),

        "raw_text": text,

        "job_description": parsed_jd
    }

    return result


def save_result(
        result,
        output_directory
):

    if not result:
        return None

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    file_name = os.path.splitext(
        result["file_name"]
    )[0]

    output_path = os.path.join(
        output_directory,
        f"{file_name}_parsed.json"
    )

    with open(
            output_path,
            "w",
            encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_path


if __name__ == "__main__":

    file_path = input(
        "Enter document path: "
    ).strip()

    try:

        result = process_document(
            file_path
        )

        if result:

            print(
                "\n" + "=" * 70
            )

            print(
                "📋 PARSED DOCUMENT"
            )

            print(
                "=" * 70
            )

            print(
                json.dumps(
                    result["job_description"],
                    indent=4,
                    ensure_ascii=False
                )
            )

            output_directory = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                ),
                "processed_documents"
            )

            saved_path = save_result(
                result,
                output_directory
            )

            print(
                "\n💾 Saved parsed document:"
            )

            print(
                saved_path
            )

    except Exception as error:

        print(
            "\n❌ Error:",
            error
        )