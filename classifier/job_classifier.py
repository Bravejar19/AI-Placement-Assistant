import re
import hashlib


NEW_OPPORTUNITY_SIGNALS = {
    "super dream internship": 8,
    "dream internship": 8,
    "dream core internship": 8,
    "campus hiring": 8,
    "campus recruitment": 8,
    "job opportunity": 8,
    "hiring": 5,
    "recruitment": 5,
    "registration": 4,
    "applications are invited": 7,
    "eligible students": 6,
    "eligibility criteria": 7,
    "job description": 7,
    "job details": 5,
    "internship": 6,
    "full time": 4,
    "full-time": 4,
    "ctc": 4,
    "salary": 3,
    "opening": 4,
}


FOLLOW_UP_SIGNALS = {
    "shortlisted students": 10,
    "shortlisted candidates": 10,
    "shortlist": 8,
    "interview schedule": 10,
    "interview scheduled": 10,
    "interview process": 8,
    "online test is scheduled": 10,
    "online test scheduled": 10,
    "assessment results": 10,
    "test results": 9,
    "exam results": 9,
    "selection results": 10,
    "selected students": 10,
    "offer letter": 10,
    "joining date": 8,
    "pre placement talk": 7,
    "pre-placement talk": 7,
    "update": 4,
}


ADMIN_FOLLOW_UP_SIGNALS = {
    "applied students": 10,
    "already applied": 10,
    "application status": 8,
    "applied candidates": 10,
    "students who applied": 10,
}


IRRELEVANT_SIGNALS = {
    "order has shipped": 10,
    "order delivered": 10,
    "your order": 8,
    "shopping": 6,
    "newsletter": 6,
    "invoice": 6,
    "payment received": 6,
    "password reset": 10,
    "new sign-in": 10,
    "sign-in to your": 10,
    "instagram": 8,
    "caterer": 8,
    "student organizers": 5,
}


FORWARD_PATTERNS = [
    "fwd:",
    "fw:",
    "forwarded message",
    "begin forwarded message",
    "---------- forwarded message ----------",
]


def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def find_signals(text, signals):
    matches = []
    score = 0

    for signal, weight in signals.items():
        if signal in text:
            matches.append(signal)
            score += weight

    return score, matches


def detect_forwarded(subject, body):
    subject_lower = normalize_text(subject)
    body_lower = normalize_text(body[:4000])

    for pattern in FORWARD_PATTERNS:
        if pattern in subject_lower:
            return True

        if pattern in body_lower:
            return True

    return False


def detect_jd(subject, body):
    text = normalize_text(
        f"{subject} {body}"
    )

    signals = [
        "job description",
        "job details",
        "job profile",
        "responsibilities",
        "key responsibilities",
        "required skills",
        "requirements",
        "qualifications",
        "technical skills",
        "skills required",
        "what you will do",
        "what we're looking for",
        "what we are looking for",
    ]

    matches = [
        signal
        for signal in signals
        if signal in text
    ]

    return len(matches) > 0, matches


def detect_eligibility(subject, body):
    text = normalize_text(
        f"{subject} {body}"
    )

    signals = [
        "eligibility",
        "eligible",
        "cgpa",
        "minimum cgpa",
        "percentage",
        "minimum percentage",
        "degree",
        "b.tech",
        "b.e",
        "b.e.",
        "batch",
        "graduating",
        "passing year",
    ]

    matches = [
        signal
        for signal in signals
        if signal in text
    ]

    return len(matches) > 0, matches


def detect_application(subject, body):
    text = normalize_text(
        f"{subject} {body}"
    )

    signals = [
        "register",
        "registration",
        "apply",
        "application",
        "apply here",
        "register here",
        "interested students",
        "interested candidates",
        "last date",
        "deadline",
    ]

    matches = [
        signal
        for signal in signals
        if signal in text
    ]

    return len(matches) > 0, matches


def clean_company(company):
    if not company:
        return None

    company = re.sub(r"\s+", " ", company)
    company = company.strip(" -:|,.")

    company = re.sub(
        r"^(urgent|update|kind attention)\s*:?\s*",
        "",
        company,
        flags=re.IGNORECASE
    )

    company = company.strip(" -:|,.")

    if len(company) < 2:
        return None

    return company


def extract_company(subject, body):
    original_subject = subject.strip()

    cleaned_subject = re.sub(
        r"^(fwd|fw|re)\s*:\s*",
        "",
        original_subject,
        flags=re.IGNORECASE
    ).strip()

    # --------------------------------------------------------
    # 1. Exact company names that appear in the subject
    # --------------------------------------------------------

    known_companies = [
        "BorgWarner India Pvt Ltd",
        "BorgWarner",
        "Econ Systems",
        "SanDisk",
        "Sandisk",
        "Fastenal",
        "Tredence",
        "Whirlpool",
        "Visteon",
        "Cognizant",
        "Accenture",
        "Amazon",
        "Deloitte",
        "TCS",
        "SAP",
        "Infosys",
        "Wipro",
        "Microsoft",
        "Google",
    ]

    subject_lower = cleaned_subject.lower()

    # Longest company names first
    known_companies.sort(
        key=len,
        reverse=True
    )

    for company in known_companies:
        if company.lower() in subject_lower:
            return company

    # --------------------------------------------------------
    # 2. "Company Dream Core Internship"
    # --------------------------------------------------------

    match = re.search(
        r"^(.+?)\s+"
        r"(?:super\s+dream|dream\s+core|dream)\s+"
        r"internship\b",
        cleaned_subject,
        re.IGNORECASE
    )

    if match:
        company = clean_company(
            match.group(1)
        )

        if company:
            return company

    # --------------------------------------------------------
    # 3. "Congratulations ... Internship Company"
    # --------------------------------------------------------

    match = re.search(
        r"internship\s+(.+?)(?:\s*[-|]|$)",
        cleaned_subject,
        re.IGNORECASE
    )

    if match:
        company = clean_company(
            match.group(1)
        )

        if company:
            return company

    # --------------------------------------------------------
    # 4. "Company campus hiring/recruitment"
    # --------------------------------------------------------

    match = re.search(
        r"^(.+?)\s+"
        r"campus\s+(?:hiring|recruitment)\b",
        cleaned_subject,
        re.IGNORECASE
    )

    if match:
        company = clean_company(
            match.group(1)
        )

        if company:
            return company

    # --------------------------------------------------------
    # 5. "Company online test"
    # --------------------------------------------------------

    match = re.search(
        r"^(.+?)\s+online\s+test\b",
        cleaned_subject,
        re.IGNORECASE
    )

    if match:
        company = clean_company(
            match.group(1)
        )

        if company:
            return company

    # --------------------------------------------------------
    # 6. "Company pre placement talk"
    # --------------------------------------------------------

    match = re.search(
        r"^(.+?)\s+pre[- ]placement\s+talk\b",
        cleaned_subject,
        re.IGNORECASE
    )

    if match:
        company = clean_company(
            match.group(1)
        )

        if company:
            return company

    # --------------------------------------------------------
    # 7. Body fallback
    # --------------------------------------------------------

    body_patterns = [
        r"(?:company|company name)\s*[:\-]\s*"
        r"([A-Za-z0-9&.,'()\- ]{2,80})",

        r"(?:organization|organisation)\s*[:\-]\s*"
        r"([A-Za-z0-9&.,'()\- ]{2,80})",
    ]

    for pattern in body_patterns:
        match = re.search(
            pattern,
            body,
            re.IGNORECASE
        )

        if match:
            company = clean_company(
                match.group(1)
            )

            if company:
                return company

    return None


def extract_role(subject, body):
    text = f"{subject}\n{body}"

    patterns = [
        r"(?:role|job role|position|designation)\s*[:\-]\s*"
        r"([A-Za-z0-9/&(),.\- ]{2,80})",

        r"(?:hiring for|opening for)\s+(?:the\s+)?"
        r"([A-Za-z0-9/&(),.\- ]{2,80})",

        r"(?:position of)\s+"
        r"([A-Za-z0-9/&(),.\- ]{2,80})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            role = match.group(1).strip()

            role = re.split(
                r"[\n|;]",
                role
            )[0]

            role = re.sub(
                r"\s+",
                " ",
                role
            )

            return role.strip(
                " .,-:"
            )

    if "internship" in normalize_text(subject):
        return "Internship"

    return None


def create_jd_hash(text):
    normalized = normalize_text(text)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def classify_email(subject, body):
    subject_lower = normalize_text(subject)
    body_lower = normalize_text(body)

    combined_text = (
        f"{subject_lower} {body_lower}"
    )

    forwarded = detect_forwarded(
        subject,
        body
    )

    # ========================================================
    # IRRELEVANT
    # ========================================================

    irrelevant_score, irrelevant_matches = find_signals(
        subject_lower,
        IRRELEVANT_SIGNALS
    )

    if irrelevant_score >= 8:
        return {
            "type": "IRRELEVANT",
            "score": 0,
            "company": None,
            "role": None,
            "forwarded": forwarded,
            "has_jd": False,
            "jd_signals": [],
            "has_eligibility": False,
            "eligibility_signals": [],
            "has_application": False,
            "application_signals": [],
            "positive_signals": [],
            "negative_signals": irrelevant_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # APPLIED STUDENTS / ADMINISTRATIVE FOLLOW-UP
    # ========================================================

    admin_score, admin_matches = find_signals(
        subject_lower,
        ADMIN_FOLLOW_UP_SIGNALS
    )

    if admin_score >= 8:
        return {
            "type": "FOLLOW_UP",
            "score": admin_score,
            "company": extract_company(
                subject,
                body
            ),
            "role": extract_role(
                subject,
                body
            ),
            "forwarded": forwarded,
            "has_jd": False,
            "jd_signals": [],
            "has_eligibility": False,
            "eligibility_signals": [],
            "has_application": False,
            "application_signals": [],
            "positive_signals": [],
            "negative_signals": admin_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # FOLLOW-UP
    # ========================================================

    follow_subject_score, follow_subject_matches = find_signals(
        subject_lower,
        FOLLOW_UP_SIGNALS
    )

    follow_body_score, follow_body_matches = find_signals(
        body_lower,
        FOLLOW_UP_SIGNALS
    )

    follow_score = (
            follow_subject_score * 2
            + follow_body_score
    )

    follow_matches = list(
        dict.fromkeys(
            follow_subject_matches
            + follow_body_matches
        )
    )

    # Strong subject-level follow-up
    if follow_subject_score >= 5:

        company = extract_company(
            subject,
            body
        )

        role = extract_role(
            subject,
            body
        )

        if "shortlist" in subject_lower:
            email_type = "SHORTLIST"

        elif (
                "interview" in subject_lower
                or "online test" in subject_lower
        ):
            email_type = "INTERVIEW_UPDATE"

        elif (
                "result" in subject_lower
                or "results" in subject_lower
        ):
            email_type = "ASSESSMENT_RESULT"

        elif "offer" in subject_lower:
            email_type = "OFFER"

        else:
            email_type = "FOLLOW_UP"

        return {
            "type": email_type,
            "score": follow_score,
            "company": company,
            "role": role,
            "forwarded": forwarded,
            "has_jd": False,
            "jd_signals": [],
            "has_eligibility": False,
            "eligibility_signals": [],
            "has_application": False,
            "application_signals": [],
            "positive_signals": [],
            "negative_signals": follow_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # OPPORTUNITY SIGNALS
    # ========================================================

    opportunity_score, opportunity_matches = find_signals(
        combined_text,
        NEW_OPPORTUNITY_SIGNALS
    )

    has_jd, jd_matches = detect_jd(
        subject,
        body
    )

    has_eligibility, eligibility_matches = detect_eligibility(
        subject,
        body
    )

    has_application, application_matches = detect_application(
        subject,
        body
    )

    company = extract_company(
        subject,
        body
    )

    role = extract_role(
        subject,
        body
    )

    # ========================================================
    # NEW OPPORTUNITY
    # ========================================================

    if (
            opportunity_score >= 8
            and company
    ):
        return {
            "type": "NEW_OPPORTUNITY",
            "score": opportunity_score,
            "company": company,
            "role": role,
            "forwarded": forwarded,
            "has_jd": has_jd,
            "jd_signals": jd_matches,
            "has_eligibility": has_eligibility,
            "eligibility_signals": eligibility_matches,
            "has_application": has_application,
            "application_signals": application_matches,
            "positive_signals": opportunity_matches,
            "negative_signals": follow_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # POTENTIAL OPPORTUNITY
    # ========================================================

    if opportunity_score >= 5:
        return {
            "type": "POTENTIAL_OPPORTUNITY",
            "score": opportunity_score,
            "company": company,
            "role": role,
            "forwarded": forwarded,
            "has_jd": has_jd,
            "jd_signals": jd_matches,
            "has_eligibility": has_eligibility,
            "eligibility_signals": eligibility_matches,
            "has_application": has_application,
            "application_signals": application_matches,
            "positive_signals": opportunity_matches,
            "negative_signals": follow_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # FORWARDED
    # ========================================================

    if forwarded:
        return {
            "type": "FORWARDED",
            "score": opportunity_score,
            "company": company,
            "role": role,
            "forwarded": True,
            "has_jd": has_jd,
            "jd_signals": jd_matches,
            "has_eligibility": has_eligibility,
            "eligibility_signals": eligibility_matches,
            "has_application": has_application,
            "application_signals": application_matches,
            "positive_signals": opportunity_matches,
            "negative_signals": follow_matches,
            "jd_hash": create_jd_hash(body),
        }

    # ========================================================
    # IRRELEVANT
    # ========================================================

    return {
        "type": "IRRELEVANT",
        "score": opportunity_score,
        "company": company,
        "role": role,
        "forwarded": forwarded,
        "has_jd": has_jd,
        "jd_signals": jd_matches,
        "has_eligibility": has_eligibility,
        "eligibility_signals": eligibility_matches,
        "has_application": has_application,
        "application_signals": application_matches,
        "positive_signals": opportunity_matches,
        "negative_signals": follow_matches,
        "jd_hash": create_jd_hash(body),
    }


if __name__ == "__main__":

    subject = input("Subject: ")

    print("\nPaste email body.")
    print("Type END when finished.\n")

    lines = []

    while True:
        line = input()

        if line == "END":
            break

        lines.append(line)

    body = "\n".join(lines)

    result = classify_email(
        subject,
        body
    )

    print("\n" + "=" * 60)
    print("CLASSIFICATION")
    print("=" * 60)

    for key, value in result.items():
        print(
            f"{key}: {value}"
        )