import os
import sys
import base64
import hashlib
import re
import time
from html import unescape

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


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
# PROJECT IMPORTS
# ============================================================

print(
    "Loading project modules...",
    flush=True
)

from classifier.job_classifier import classify_email

from gmail.attachments import (
    get_attachments,
    download_attachment
)

from database.opportunity_db import (
    initialize_database,
    find_by_message_id,
    find_by_company_role,
    find_by_jd_hash,
    create_opportunity,
    update_parsed_jd
)

from documents.processor import (
    process_document,
    save_result
)

from documents.jd_parser import parse_jd

print(
    "Project modules loaded.",
    flush=True
)


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

MAX_EMAILS = 50

SUPPORTED_DOCUMENTS = {
    ".pdf",
    ".docx",
    ".txt"
}


# ============================================================
# PRINT HELPER
# ============================================================

def log(message=""):
    print(
        message,
        flush=True
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    return " ".join(
        str(text).split()
    ).strip()


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


def get_header(
        headers,
        name
):

    for header in headers:

        if (
                header.get(
                    "name",
                    ""
                ).lower()
                == name.lower()
        ):

            return header.get(
                "value",
                ""
            )

    return ""


# ============================================================
# COMPANY NORMALIZATION
# ============================================================

def canonical_company_name(company):

    if not company:
        return None

    company = normalize_text(
        company
    )

    if not company:
        return None

    lowered = company.lower()

    aliases = {

        "e-con systems": "e-con Systems",
        "e con systems": "e-con Systems",
        "econ systems": "e-con Systems",
        "econsystems": "e-con Systems",

        "sandisk": "SanDisk",
        "fastenal": "Fastenal",
        "fractal analytics": "Fractal Analytics",

        "chubb": "Chubb",

        "chubb business services india":
            "Chubb Business Services India",

        "mpm infosoft": "MPM Infosoft",

        "super money": "super.money",
        "super.money": "super.money",

        "sima technologies":
            "SiMa Technologies",

        "sima technologies limited":
            "SiMa Technologies",

        "workday":
            "Workday",

        "workday india private limited":
            "Workday India Private Limited",

        "bottomline":
            "Bottomline",

        "exxonmobil":
            "ExxonMobil",

        "accenture":
            "Accenture",

        "flipkart":
            "Flipkart",

        "hitwicket":
            "Hitwicket",

        "ubs":
            "UBS",

        "paypal":
            "PayPal",

        "cisco":
            "Cisco",

        "intel":
            "Intel",

        "microsoft":
            "Microsoft",

        "google":
            "Google",

        "amazon":
            "Amazon",

        "zoho":
            "Zoho",

        "cognizant":
            "Cognizant",

        "wipro":
            "Wipro",

        "infosys":
            "Infosys",

        "tcs":
            "TCS",

        "tata consultancy services":
            "TCS",

        "jpmorgan chase":
            "JPMorgan Chase",

        "palo alto":
            "Palo Alto",

        "visteon":
            "Visteon",

        "spense":
            "Spense",

        "valco melton":
            "Valco Melton",

        "whirlpool":
            "Whirlpool",

        "epsilon":
            "Epsilon",

        "tredence":
            "Tredence",

        "zf group":
            "ZF Group",

        "amd":
            "AMD",

        "societe generale":
            "Societe Generale"
    }

    if lowered in aliases:
        return aliases[lowered]

    return company


def clean_company_name(company):

    if not company:
        return None

    company = normalize_text(
        company
    )

    if not company:
        return None

    company = re.sub(
        r"^(re|fwd|fw)\s*:\s*",
        "",
        company,
        flags=re.IGNORECASE
    )

    prefixes = [

        r"^congratulations\s*!*\s*",
        r"^congrats\s*!*\s*",
        r"^update\s*:?\s*",
        r"^announcement\s*:?\s*",
        r"^urgent\s*:?\s*",
        r"^registration\s*:?\s*",
        r"^placement\s*:?\s*",
        r"^campus\s+hiring\s*:?\s*"
    ]

    for pattern in prefixes:

        company = re.sub(
            pattern,
            "",
            company,
            flags=re.IGNORECASE
        )

    trailing_patterns = [

        r"\s+super\s+dream.*$",
        r"\s+dream\s+internship.*$",
        r"\s+internship\s+registration.*$",
        r"\s+internship\s+drive.*$",
        r"\s+placement\s+drive.*$",
        r"\s+placement\s+offer.*$",
        r"\s+selection\s+list.*$",
        r"\s+online\s+test.*$",
        r"\s+assessment.*$",
        r"\s+next\s+round.*$",
        r"\s+registration.*$"
    ]

    for pattern in trailing_patterns:

        company = re.sub(
            pattern,
            "",
            company,
            flags=re.IGNORECASE
        )

    company = company.strip(
        " :-|.!?"
    )

    invalid_values = {

        "",
        "unknown",
        "unknown company",
        "company",
        "internship",
        "placement",
        "campus hiring",
        "career opportunity",
        "job opportunity"
    }

    if company.lower() in invalid_values:
        return None

    return canonical_company_name(
        company
    )


# ============================================================
# COMPANY FROM SUBJECT
# ============================================================

def extract_company_from_subject(
        subject
):

    if not subject:
        return None

    subject = normalize_text(
        subject
    )

    subject = re.sub(
        r"^(re|fwd|fw)\s*:\s*",
        "",
        subject,
        flags=re.IGNORECASE
    )

    patterns = [

        (r"\be[-\s]?con\s+systems\b", "e-con Systems"),
        (r"\becon\s+systems\b", "e-con Systems"),
        (r"\bsandisk\b", "SanDisk"),
        (r"\bfastenal\b", "Fastenal"),
        (r"\bfractal\s+analytics\b", "Fractal Analytics"),
        (r"\bchubb\b", "Chubb"),
        (r"\bmpm\s+infosoft\b", "MPM Infosoft"),
        (r"\bsuper\.money\b", "super.money"),
        (r"\bsima\s+technologies\b", "SiMa Technologies"),
        (r"\bworkday\b", "Workday"),
        (r"\bbottomline\b", "Bottomline"),
        (r"\bexxonmobil\b", "ExxonMobil"),
        (r"\baccenture\b", "Accenture"),
        (r"\bflipkart\b", "Flipkart"),
        (r"\bhitwicket\b", "Hitwicket"),
        (r"\bubs\b", "UBS"),
        (r"\bpaypal\b", "PayPal"),
        (r"\bcisco\b", "Cisco"),
        (r"\bintel\b", "Intel"),
        (r"\bmicrosoft\b", "Microsoft"),
        (r"\bgoogle\b", "Google"),
        (r"\bamazon\b", "Amazon"),
        (r"\bzoho\b", "Zoho"),
        (r"\bcognizant\b", "Cognizant"),
        (r"\bwipro\b", "Wipro"),
        (r"\binfosys\b", "Infosys"),
        (r"\btcs\b", "TCS"),
        (r"\bjpmorgan\s+chase\b", "JPMorgan Chase"),
        (r"\bvisteon\b", "Visteon"),
        (r"\bspense\b", "Spense"),
        (r"\bvalco\s+melton\b", "Valco Melton"),
        (r"\bwhirlpool\b", "Whirlpool"),
        (r"\bepsilon\b", "Epsilon"),
        (r"\btredence\b", "Tredence"),
        (r"\bzf\s+group\b", "ZF Group"),
        (r"\badm\b", "ADM"),
        (r"\bamd\b", "AMD"),
        (r"\bsociete\s+generale\b", "Societe Generale"),
        (r"\bpalo\s+alto\b", "Palo Alto")
    ]

    for pattern, company in patterns:

        if re.search(
                pattern,
                subject,
                flags=re.IGNORECASE
        ):

            return company

    return None


def resolve_company(
        subject,
        classifier_company
):

    company = extract_company_from_subject(
        subject
    )

    if company:
        return company

    company = clean_company_name(
        classifier_company
    )

    if company:
        return company

    return "Unknown Company"


# ============================================================
# ROLE CLEANING
# ============================================================

def clean_role(role):

    if not role:
        return None

    role = normalize_text(
        role
    )

    if not role:
        return None

    role = re.sub(
        r"^(re|fwd|fw)\s*:\s*",
        "",
        role,
        flags=re.IGNORECASE
    )

    role = role.strip(
        " :-|.!?"
    )

    invalid_roles = {

        "",
        "internship",
        "intern",
        "job opportunity",
        "career opportunity",
        "details",
        "registration",
        "placement",
        "announcement",
        "opportunity"
    }

    if role.lower() in invalid_roles:
        return None

    bad_fragments = [

        "would go through",
        "all the shortlisted students",
        "shortlisted students from",
        "students from the online test",
        "please register",
        "click here",
        "congratulations",
        "you have been selected",
        "registration link",
        "apply here"
    ]

    lowered = role.lower()

    for fragment in bad_fragments:

        if fragment in lowered:
            return None

    if len(role) > 100:
        return None

    return role


def extract_role_from_subject(
        subject
):

    if not subject:
        return None

    subject = normalize_text(
        subject
    )

    subject = re.sub(
        r"^(re|fwd|fw)\s*:\s*",
        "",
        subject,
        flags=re.IGNORECASE
    )

    patterns = [

        r"(?:role|position|job)\s*[:\-]\s*(.+)$",
        r"(?:internship)\s*[:\-]\s*(.+)$",
        r"(?:hiring)\s*[:\-]\s*(.+)$"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            subject,
            flags=re.IGNORECASE
        )

        if match:

            role = clean_role(
                match.group(1)
            )

            if role:
                return role

    return None


def resolve_role(
        subject,
        classifier_role
):

    role = clean_role(
        classifier_role
    )

    if role:
        return role

    role = extract_role_from_subject(
        subject
    )

    if role:
        return role

    return "Internship"


# ============================================================
# HASH
# ============================================================

def generate_body_jd_hash(
        company,
        role,
        body
):

    value = "|".join(
        [
            normalize_text(
                company
            ).lower(),

            normalize_text(
                role
            ).lower(),

            normalize_text(
                body
            ).lower()
        ]
    )

    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def authenticate():

    log()
    log(
        "Starting Gmail authentication..."
    )

    credentials_file = os.path.join(
        BASE_DIR,
        "gmail",
        "credentials.json"
    )

    token_file = os.path.join(
        BASE_DIR,
        "gmail",
        "token.json"
    )

    if not os.path.exists(
            credentials_file
    ):

        raise FileNotFoundError(
            f"Gmail credentials not found: "
            f"{credentials_file}"
        )

    creds = None

    if os.path.exists(
            token_file
    ):

        log(
            "Loading existing Gmail token..."
        )

        creds = Credentials.from_authorized_user_file(
            token_file,
            SCOPES
        )

    if not creds or not creds.valid:

        if (
                creds
                and creds.expired
                and creds.refresh_token
        ):

            log(
                "Refreshing Gmail token..."
            )

            creds.refresh(
                Request()
            )

            log(
                "Gmail token refreshed."
            )

        else:

            log(
                "Gmail authorization required."
            )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

            log(
                "Gmail authorization completed."
            )

        with open(
                token_file,
                "w"
        ) as token:

            token.write(
                creds.to_json()
            )

        log(
            "Gmail token saved."
        )

    log(
        "Building Gmail service..."
    )

    service = build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )

    log(
        "Gmail service ready."
    )

    return service


# ============================================================
# EMAIL BODY
# ============================================================

def decode_body_data(
        data
):

    if not data:
        return ""

    try:

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


def strip_html(
        text
):

    if not text:
        return ""

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"</p\s*>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    return unescape(
        text
    )


def get_email_body(
        payload
):

    plain_text = []
    html_text = []

    def walk(part):

        mime_type = part.get(
            "mimeType",
            ""
        )

        body = part.get(
            "body",
            {}
        )

        data = body.get(
            "data"
        )

        if data:

            decoded = decode_body_data(
                data
            )

            if mime_type == "text/plain":

                plain_text.append(
                    decoded
                )

            elif mime_type == "text/html":

                html_text.append(
                    decoded
                )

        for child in part.get(
                "parts",
                []
        ):

            walk(child)

    walk(
        payload
    )

    if plain_text:

        return "\n".join(
            plain_text
        ).strip()

    if html_text:

        return strip_html(
            "\n".join(
                html_text
            )
        ).strip()

    return ""


# ============================================================
# ATTACHMENT PROCESSING
# ============================================================

def process_attachment(
        file_path,
        processed_directory
):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_DOCUMENTS:

        log(
            f"    Unsupported document type: {extension}"
        )

        return None

    log(
        "    Processing document..."
    )

    try:

        result = process_document(
            file_path
        )

        if not result:

            log(
                "    No readable content found."
            )

            return None

        saved_path = save_result(
            result,
            processed_directory
        )

        log(
            "    Document processed."
        )

        log(
            f"    Parsed document saved: {saved_path}"
        )

        return result

    except Exception as error:

        log(
            f"    Document processing failed: {error}"
        )

        return None


def parsed_jd_is_valid(
        parsed_jd
):

    if not isinstance(
            parsed_jd,
            dict
    ):

        return False

    if not parsed_jd.get(
            "parse_valid",
            False
    ):

        return False

    fields = [

        "role",
        "specialization",
        "company",
        "must_have",
        "responsibilities",
        "required_skills",
        "preferred_qualifications",
        "technical_keywords",
        "eligibility_requirements",
        "tracks"
    ]

    return any(
        parsed_jd.get(
            field
        )
        for field in fields
    )


def extract_attachment_jd(
        service,
        message_id,
        payload,
        processed_directory
):

    try:

        attachments = get_attachments(
            payload
        )

    except Exception as error:

        log(
            f"Could not inspect attachments: {error}"
        )

        return (
            None,
            None,
            0
        )

    if not attachments:

        return (
            None,
            None,
            0
        )

    log(
        f"Attachments found: {len(attachments)}"
    )

    attachment_directory = os.path.join(
        BASE_DIR,
        "attachments",
        message_id
    )

    os.makedirs(
        attachment_directory,
        exist_ok=True
    )

    os.makedirs(
        processed_directory,
        exist_ok=True
    )

    processed_count = 0

    for attachment in attachments:

        filename = attachment.get(
            "filename",
            ""
        )

        if not filename:
            continue

        extension = os.path.splitext(
            filename
        )[1].lower()

        log(
            f"Attachment: {filename}"
        )

        if extension not in SUPPORTED_DOCUMENTS:

            log(
                "    Unsupported attachment. Skipping."
            )

            continue

        try:

            file_path = download_attachment(
                service,
                message_id,
                attachment[
                    "attachment_id"
                ],
                filename,
                attachment_directory
            )

        except Exception as error:

            log(
                f"    Download failed: {error}"
            )

            continue

        if not file_path:

            log(
                "    Download failed."
            )

            continue

        processed = process_attachment(
            file_path,
            processed_directory
        )

        if not processed:
            continue

        processed_count += 1

        raw_text = processed.get(
            "raw_text"
        )

        parsed_jd = processed.get(
            "job_description"
        )

        if parsed_jd_is_valid(
                parsed_jd
        ):

            return (
                raw_text,
                parsed_jd,
                processed_count
            )

        if raw_text:

            try:

                parsed_jd = parse_jd(
                    raw_text
                )

                if parsed_jd_is_valid(
                        parsed_jd
                ):

                    return (
                        raw_text,
                        parsed_jd,
                        processed_count
                    )

            except Exception as error:

                log(
                    f"    Direct JD parsing failed: {error}"
                )

    return (
        None,
        None,
        processed_count
    )


# ============================================================
# EMAIL BODY JD RECOVERY
# ============================================================

JD_BODY_SIGNALS = [

    "job description",
    "job role",
    "job title",
    "role:",
    "position:",
    "responsibilities",
    "responsibility",
    "requirements",
    "required skills",
    "required skill",
    "technical skills",
    "technical requirements",
    "qualifications",
    "qualification",
    "eligibility",
    "skills required",
    "what you'll do",
    "what you will do",
    "key responsibilities",
    "preferred qualifications",
    "experience required",
    "education",
    "about the role",
    "about the position"
]


def body_has_possible_jd(
        body
):

    if not body:
        return False

    cleaned = normalize_text(
        body
    )

    if len(cleaned) < 150:
        return False

    lowered = cleaned.lower()

    signal_count = sum(
        1
        for signal in JD_BODY_SIGNALS
        if signal in lowered
    )

    return signal_count >= 2


def parse_jd_from_email_body(
        body
):

    if not body:
        return None

    cleaned = normalize_text(
        body
    )

    if len(cleaned) < 150:
        return None

    if not body_has_possible_jd(
            body
    ):

        return None

    log(
        "    Body contains JD indicators."
    )

    try:

        parsed = parse_jd(
            body
        )

        if not parsed_jd_is_valid(
                parsed
        ):

            return None

        return parsed

    except Exception as error:

        log(
            f"    Email JD parsing failed: {error}"
        )

        return None


# ============================================================
# EXISTING OPPORTUNITY SEARCH
# ============================================================

def find_existing_opportunity(
        message_id,
        jd_hash,
        company,
        role
):

    existing = None

    if message_id:

        try:

            existing = find_by_message_id(
                message_id
            )

        except Exception as error:

            log(
                f"Message ID lookup failed: {error}"
            )

        if existing:
            return existing

    if jd_hash:

        try:

            existing = find_by_jd_hash(
                jd_hash
            )

        except Exception as error:

            log(
                f"JD hash lookup failed: {error}"
            )

        if existing:
            return existing

    if (
            company
            and company.lower() != "unknown company"
            and role
    ):

        try:

            existing = find_by_company_role(
                company,
                role
            )

        except Exception as error:

            log(
                f"Company/role lookup failed: {error}"
            )

        if existing:
            return existing

    return None


# ============================================================
# REPAIR EXISTING RECORD
# ============================================================

def repair_existing_opportunity(
        opportunity,
        jd_text,
        parsed_jd
):

    if not opportunity:
        return False

    if not parsed_jd_is_valid(
            parsed_jd
    ):

        return False

    opportunity_id = row_value(
        opportunity,
        "id"
    )

    if not opportunity_id:
        return False

    try:

        updated = update_parsed_jd(
            opportunity_id,
            jd_text,
            parsed_jd
        )

        if not updated:
            return False

        log(
            "Existing opportunity updated."
        )

        log(
            f"Opportunity ID: {opportunity_id}"
        )

        log(
            f"Parsed company: "
            f"{parsed_jd.get('company')}"
        )

        log(
            f"Parsed role: "
            f"{parsed_jd.get('role')}"
        )

        log(
            f"Parsed specialization: "
            f"{parsed_jd.get('specialization')}"
        )

        return True

    except Exception as error:

        log(
            f"Repair failed: {error}"
        )

        return False


# ============================================================
# EMAIL PROCESSING
# ============================================================

def get_emails(
        service,
        max_results=MAX_EMAILS
):

    max_results = min(
        int(max_results),
        MAX_EMAILS
    )

    log()
    log(
        "=" * 70
    )
    log(
        "GMAIL EMAIL FETCH"
    )
    log(
        "=" * 70
    )

    log(
        f"Requesting up to {max_results} emails..."
    )

    start_time = time.time()

    try:

        results = service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()

    except Exception as error:

        log(
            f"Gmail list request failed: {error}"
        )

        return

    messages = results.get(
        "messages",
        []
    )

    elapsed = time.time() - start_time

    log(
        f"Gmail list request completed in {elapsed:.2f}s"
    )

    if not messages:

        log(
            "No emails found."
        )

        return

    log(
        f"Emails returned: {len(messages)}"
    )

    processed_directory = os.path.join(
        BASE_DIR,
        "processed_documents"
    )

    os.makedirs(
        processed_directory,
        exist_ok=True
    )

    total = 0
    new_opportunities = 0
    potential_opportunities = 0
    follow_ups = 0
    forwarded_emails = 0
    duplicates = 0
    ignored = 0
    documents_processed = 0
    repaired_opportunities = 0

    for message in messages:

        total += 1

        message_id = message.get(
            "id"
        )

        log()
        log(
            f"[{total}/{len(messages)}] Fetching email..."
        )

        if not message_id:

            log(
                "Missing message ID. Skipping."
            )

            continue

        try:

            msg = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

        except Exception as error:

            log(
                f"Could not fetch email: {error}"
            )

            continue

        payload = msg.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        sender = get_header(
            headers,
            "From"
        )

        subject = get_header(
            headers,
            "Subject"
        )

        thread_id = msg.get(
            "threadId"
        )

        log(
            f"Subject: {subject[:120]}"
        )

        body = get_email_body(
            payload
        )

        # ====================================================
        # CLASSIFICATION
        # ====================================================

        try:

            result = classify_email(
                subject,
                body
            )

        except Exception as error:

            log(
                f"Classification failed: {error}"
            )

            ignored += 1

            continue

        if not isinstance(
                result,
                dict
        ):

            log(
                "Invalid classifier result."
            )

            ignored += 1

            continue

        email_type = result.get(
            "type"
        )

        company = resolve_company(
            subject,
            result.get(
                "company"
            )
        )

        role = resolve_role(
            subject,
            result.get(
                "role"
            )
        )

        log(
            f"Type: {email_type}"
        )

        log(
            f"Initial company: {company}"
        )

        log(
            f"Initial role: {role}"
        )

        # ====================================================
        # IRRELEVANT
        # ====================================================

        if email_type == "IRRELEVANT":

            ignored += 1

            log(
                "Ignored."
            )

            continue

        # ====================================================
        # FOLLOW-UP
        #
        # Important:
        # We normally skip follow-ups, but if the body itself
        # contains a possible JD, allow recovery.
        # ====================================================

        if email_type in [
            "SHORTLIST",
            "ASSESSMENT_RESULT",
            "INTERVIEW_UPDATE",
            "OFFER",
            "FOLLOW_UP"
        ]:

            follow_ups += 1

            log(
                "Follow-up email."
            )

            if not body_has_possible_jd(
                    body
            ):

                continue

            log(
                "Follow-up contains possible JD content."
            )

        # ====================================================
        # FORWARDED
        # ====================================================

        if email_type == "FORWARDED":

            forwarded_emails += 1

            log(
                "Forwarded email."
            )

            if not body_has_possible_jd(
                    body
            ):

                continue

            log(
                "Forwarded email contains possible JD content."
            )

        # ====================================================
        # UNKNOWN CLASSIFICATION
        # ====================================================

        if email_type not in [
            "NEW_OPPORTUNITY",
            "POTENTIAL_OPPORTUNITY",
            "SHORTLIST",
            "ASSESSMENT_RESULT",
            "INTERVIEW_UPDATE",
            "OFFER",
            "FOLLOW_UP",
            "FORWARDED"
        ]:

            ignored += 1

            log(
                "Unknown email type. Skipping."
            )

            continue

        # ====================================================
        # ATTACHMENT JD
        # ====================================================

        jd_text = None
        parsed_jd = None

        (
            jd_text,
            parsed_jd,
            attachment_count
        ) = extract_attachment_jd(
            service,
            message_id,
            payload,
            processed_directory
        )

        documents_processed += attachment_count

        # ====================================================
        # EMAIL BODY JD
        #
        # IMPORTANT:
        # This is intentionally NOT gated by result["has_jd"].
        #
        # This allows old opportunities such as Fastenal,
        # Accenture, ExxonMobil, etc. to be repaired.
        # ====================================================

        if not parsed_jd:

            log(
                "Trying JD from email body..."
            )

            parsed_jd = parse_jd_from_email_body(
                body
            )

            if parsed_jd:

                jd_text = body

                log(
                    "JD parsed from email body."
                )

            else:

                log(
                    "No valid JD found in email body."
                )

        # ====================================================
        # AUTHORITATIVE JD METADATA
        # ====================================================

        if parsed_jd_is_valid(
                parsed_jd
        ):

            parsed_company = clean_company_name(
                parsed_jd.get(
                    "company"
                )
            )

            parsed_role = clean_role(
                parsed_jd.get(
                    "role"
                )
            )

            if parsed_company:

                company = parsed_company

            if parsed_role:

                role = parsed_role

            log()
            log(
                "AUTHORITATIVE JD METADATA"
            )

            log(
                f"Company: {company}"
            )

            log(
                f"Role: {role}"
            )

            log(
                f"Specialization: "
                f"{parsed_jd.get('specialization')}"
            )

        # ====================================================
        # HASH
        # ====================================================

        if parsed_jd_is_valid(
                parsed_jd
        ):

            jd_hash = generate_body_jd_hash(
                company,
                role,
                jd_text or body
            )

        else:

            jd_hash = result.get(
                "jd_hash"
            )

            if not jd_hash:

                jd_hash = generate_body_jd_hash(
                    company,
                    role,
                    body
                )

        # ====================================================
        # DATABASE MATCH
        # ====================================================

        existing = find_existing_opportunity(
            message_id,
            jd_hash,
            company,
            role
        )

        if existing:

            existing_id = row_value(
                existing,
                "id"
            )

            log()
            log(
                f"Existing opportunity found: "
                f"{existing_id}"
            )

            existing_parsed = row_value(
                existing,
                "parsed_jd"
            )

            # ------------------------------------------------
            # REPAIR if the existing record has no parsed JD.
            # ------------------------------------------------

            if (
                    not existing_parsed
                    and parsed_jd_is_valid(
                parsed_jd
            )
            ):

                if repair_existing_opportunity(
                        existing,
                        jd_text,
                        parsed_jd
                ):

                    repaired_opportunities += 1

                else:

                    duplicates += 1

            else:

                duplicates += 1

                if existing_parsed:

                    log(
                        "Existing opportunity already has parsed JD."
                    )

                else:

                    log(
                        "No valid JD available for existing record."
                    )

            continue

        # ====================================================
        # CREATE NEW OPPORTUNITY
        # ====================================================

        if email_type == "NEW_OPPORTUNITY":

            try:

                opportunity_id = create_opportunity(

                    company=company,

                    role=role,

                    jd_hash=jd_hash,

                    message_id=message_id,

                    thread_id=thread_id,

                    jd_available=bool(
                        result.get(
                            "has_jd"
                        )
                        or parsed_jd
                        or attachment_count
                    ),

                    eligibility_available=bool(
                        result.get(
                            "has_eligibility"
                        )
                        or (
                                parsed_jd
                                and parsed_jd.get(
                            "eligibility_requirements"
                        )
                        )
                    ),

                    jd_text=jd_text,

                    parsed_jd=parsed_jd
                )

                if opportunity_id:

                    new_opportunities += 1

                    log()
                    log(
                        "NEW OPPORTUNITY CREATED"
                    )

                    log(
                        f"ID: {opportunity_id}"
                    )

                    log(
                        f"Company: {company}"
                    )

                    log(
                        f"Role: {role}"
                    )

            except Exception as error:

                log(
                    f"Could not create opportunity: {error}"
                )

        # ====================================================
        # POTENTIAL OPPORTUNITY
        # ====================================================

        elif email_type == "POTENTIAL_OPPORTUNITY":

            potential_opportunities += 1

            if not parsed_jd_is_valid(
                    parsed_jd
            ):

                log(
                    "Potential opportunity has no valid JD."
                )

                continue

            try:

                opportunity_id = create_opportunity(

                    company=company,

                    role=role,

                    jd_hash=jd_hash,

                    message_id=message_id,

                    thread_id=thread_id,

                    jd_available=True,

                    eligibility_available=bool(
                        result.get(
                            "has_eligibility"
                        )
                        or parsed_jd.get(
                            "eligibility_requirements"
                        )
                    ),

                    jd_text=jd_text,

                    parsed_jd=parsed_jd
                )

                if opportunity_id:

                    new_opportunities += 1

                    log()
                    log(
                        "POTENTIAL OPPORTUNITY STORED"
                    )

                    log(
                        f"ID: {opportunity_id}"
                    )

                    log(
                        f"Company: {company}"
                    )

                    log(
                        f"Role: {role}"
                    )

            except Exception as error:

                log(
                    f"Could not create potential opportunity: "
                    f"{error}"
                )

    # ========================================================
    # SUMMARY
    # ========================================================

    log()
    log(
        "=" * 70
    )

    log(
        "EMAIL PROCESSING SUMMARY"
    )

    log(
        "=" * 70
    )

    log(
        f"Total emails: {total}"
    )

    log(
        f"New opportunities: {new_opportunities}"
    )

    log(
        f"Potential opportunities: {potential_opportunities}"
    )

    log(
        f"Follow-up emails: {follow_ups}"
    )

    log(
        f"Forwarded emails: {forwarded_emails}"
    )

    log(
        f"Duplicates skipped: {duplicates}"
    )

    log(
        f"Ignored: {ignored}"
    )

    log(
        f"Documents processed: {documents_processed}"
    )

    log(
        f"Existing opportunities repaired: "
        f"{repaired_opportunities}"
    )

    log(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

def main():

    log()
    log(
        "=" * 70
    )

    log(
        "PLACEMENT EMAIL INGESTION"
    )

    log(
        "=" * 70
    )

    log(
        "Initializing database..."
    )

    initialize_database()

    log(
        "Database ready."
    )

    log()
    log(
        "Connecting to Gmail..."
    )

    service = authenticate()

    log()
    log(
        "Successfully connected to Gmail."
    )

    log()
    log(
        "Starting email fetch..."
    )

    get_emails(
        service,
        max_results=MAX_EMAILS
    )

    log()
    log(
        "Email ingestion finished."
    )


if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        log()
        log(
            "Process interrupted by user."
        )

    except Exception as error:

        log()
        log(
            "=" * 70
        )

        log(
            "FATAL ERROR"
        )

        log(
            "=" * 70
        )

        log(
            str(error)
        )

        raise