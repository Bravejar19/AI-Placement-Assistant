import sqlite3
import json
import os


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "opportunities.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE / MIGRATE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS opportunities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company TEXT,

            role TEXT,

            jd_hash TEXT,

            message_id TEXT UNIQUE,

            thread_id TEXT,

            jd_available INTEGER DEFAULT 0,

            eligibility_available INTEGER DEFAULT 0,

            jd_text TEXT,

            parsed_jd TEXT,

            status TEXT DEFAULT 'NEW',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()

    cursor.execute(
        "PRAGMA table_info(opportunities)"
    )

    columns = cursor.fetchall()

    existing_columns = {
        row["name"]
        for row in columns
    }

    columns_to_add = {

        "company":
            "TEXT",

        "role":
            "TEXT",

        "jd_hash":
            "TEXT",

        "message_id":
            "TEXT",

        "thread_id":
            "TEXT",

        "jd_available":
            "INTEGER DEFAULT 0",

        "eligibility_available":
            "INTEGER DEFAULT 0",

        "jd_text":
            "TEXT",

        "parsed_jd":
            "TEXT",

        "status":
            "TEXT"

    }

    for column, column_type in columns_to_add.items():

        if column not in existing_columns:

            print(
                f"Adding missing database column: {column}",
                flush=True
            )

            cursor.execute(
                f"""
                ALTER TABLE opportunities
                ADD COLUMN {column} {column_type}
                """
            )

    if "created_at" not in existing_columns:

        print(
            "Adding missing database column: created_at",
            flush=True
        )

        cursor.execute(
            """
            ALTER TABLE opportunities
            ADD COLUMN created_at TIMESTAMP
            """
        )

        cursor.execute(
            """
            UPDATE opportunities
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )

    connection.commit()

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_opportunities_message_id
        ON opportunities(message_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_opportunities_jd_hash
        ON opportunities(jd_hash)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_opportunities_company_role
        ON opportunities(company, role)
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# FIND BY MESSAGE ID
# ============================================================

def find_by_message_id(message_id):

    if not message_id:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM opportunities
        WHERE message_id = ?
        """,
        (message_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# FIND BY COMPANY + ROLE
# ============================================================

def find_by_company_role(
        company,
        role
):

    if not company or not role:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM opportunities
        WHERE LOWER(COALESCE(company, '')) = LOWER(?)
        AND LOWER(COALESCE(role, '')) = LOWER(?)
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            company,
            role
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# FIND BY JD HASH
# ============================================================

def find_by_jd_hash(jd_hash):

    if not jd_hash:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM opportunities
        WHERE jd_hash = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (jd_hash,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# CREATE OPPORTUNITY
# ============================================================

def create_opportunity(
        company,
        role,
        jd_hash,
        message_id,
        thread_id=None,
        jd_available=False,
        eligibility_available=False,
        jd_text=None,
        parsed_jd=None,
        status="NEW"
):

    connection = get_connection()
    cursor = connection.cursor()

    parsed_jd_json = None

    if parsed_jd is not None:

        if isinstance(
                parsed_jd,
                str
        ):

            parsed_jd_json = parsed_jd

        else:

            parsed_jd_json = json.dumps(
                parsed_jd,
                ensure_ascii=False
            )

    try:

        cursor.execute(
            """
            INSERT INTO opportunities (

                company,
                role,
                jd_hash,
                message_id,
                thread_id,
                jd_available,
                eligibility_available,
                jd_text,
                parsed_jd,
                status,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,

            (
                company,
                role,
                jd_hash,
                message_id,
                thread_id,
                int(bool(jd_available)),
                int(bool(eligibility_available)),
                jd_text,
                parsed_jd_json,
                status
            )
        )

        connection.commit()

        opportunity_id = cursor.lastrowid

        connection.close()

        return opportunity_id

    except sqlite3.IntegrityError:

        connection.close()

        return None


# ============================================================
# UPDATE PARSED JD
# ============================================================

def update_parsed_jd(
        opportunity_id,
        jd_text,
        parsed_jd
):

    if not opportunity_id:
        return False

    if not parsed_jd:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    if isinstance(
            parsed_jd,
            str
    ):

        parsed_jd_json = parsed_jd

        try:
            parsed_data = json.loads(parsed_jd)
        except Exception:
            parsed_data = {}

    else:

        parsed_data = parsed_jd

        parsed_jd_json = json.dumps(
            parsed_jd,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # Parsed JD becomes authoritative metadata.
    # --------------------------------------------------------

    parsed_company = None
    parsed_role = None

    if isinstance(parsed_data, dict):

        parsed_company = parsed_data.get(
            "company"
        )

        parsed_role = parsed_data.get(
            "role"
        )

    # --------------------------------------------------------
    # Update all JD-related information.
    # Preserve existing company/role if parser does not provide
    # valid values.
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE opportunities

        SET
            company =
                CASE
                    WHEN ? IS NOT NULL
                    AND TRIM(?) != ''
                    THEN ?
                    ELSE company
                END,

            role =
                CASE
                    WHEN ? IS NOT NULL
                    AND TRIM(?) != ''
                    THEN ?
                    ELSE role
                END,

            jd_text = ?,

            parsed_jd = ?,

            jd_available = 1

        WHERE id = ?
        """,

        (
            parsed_company,
            parsed_company,
            parsed_company,

            parsed_role,
            parsed_role,
            parsed_role,

            jd_text,
            parsed_jd_json,

            opportunity_id
        )
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


# ============================================================
# GET OPPORTUNITY
# ============================================================

def get_opportunity(
        opportunity_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM opportunities
        WHERE id = ?
        """,
        (opportunity_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# GET ALL OPPORTUNITIES
# ============================================================

def get_all_opportunities():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM opportunities
        ORDER BY created_at DESC, id DESC
        """
    )

    results = cursor.fetchall()

    connection.close()

    return results


# ============================================================
# UPDATE STATUS
# ============================================================

def update_status(
        opportunity_id,
        status
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE opportunities
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            opportunity_id
        )
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


# ============================================================
# DATABASE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Initializing database..."
    )

    initialize_database()

    print(
        "Database ready!"
    )

    print(
        "\nDatabase location:"
    )

    print(
        DATABASE_PATH
    )