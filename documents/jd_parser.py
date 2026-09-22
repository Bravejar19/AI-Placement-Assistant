import os
import sys
import re
import json


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = text.replace("\x00", " ")
    text = text.replace("\u00a0", " ")

    # Remove artificial spaces between single characters.
    # Example:
    # P R O J E C T -> PROJECT
    text = re.sub(
        r'(?<!\S)([A-Za-z])(?:\s+([A-Za-z])){2,}(?!\S)',
        lambda m: re.sub(r'\s+', '', m.group(0)),
        text
    )

    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def clean_line(line):
    if not line:
        return ""

    line = line.replace("\u00a0", " ")
    line = re.sub(r'[ \t]+', ' ', line)

    line = re.sub(
        r'^\s*[•●▪◦■□‣*\-–—]+\s*',
        '',
        line
    )

    return line.strip()


def normalize(text):
    text = clean_text(text).lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def unique(items):
    result = []

    for item in items:
        item = clean_text(item)

        if item and item not in result:
            result.append(item)

    return result


# ============================================================
# HEADING DETECTION
# ============================================================

SECTION_ALIASES = {
    "responsibilities": [
        "responsibilities",
        "roles and responsibilities",
        "role and responsibilities",
        "key responsibilities",
        "what you will do",
        "what you'll do",
        "what you will be doing",
        "job responsibilities"
    ],

    "requirements": [
        "requirements",
        "required skills",
        "required qualifications",
        "skills required",
        "technical requirements",
        "qualifications",
        "what we are looking for",
        "what we're looking for",
        "must have",
        "must-have"
    ],

    "preferred": [
        "preferred qualifications",
        "preferred skills",
        "nice to have",
        "nice-to-have",
        "good to have",
        "additional qualifications",
        "bonus"
    ],

    "about": [
        "about the role",
        "about role",
        "role overview",
        "position overview",
        "overview",
        "about us"
    ]
}


def detect_heading(line):
    value = normalize(line).rstrip(":")

    for section, aliases in SECTION_ALIASES.items():

        for alias in aliases:

            if value == alias:
                return section

    return None


def extract_sections(text):

    sections = {
        "general": [],
        "responsibilities": [],
        "requirements": [],
        "preferred": [],
        "about": []
    }

    current = "general"

    for raw_line in text.splitlines():

        line = clean_line(raw_line)

        if not line:
            continue

        heading = detect_heading(line)

        if heading:
            current = heading
            continue

        sections[current].append(line)

    return sections


# ============================================================
# COMPANY
# ============================================================

KNOWN_COMPANIES = [
    "e-con Systems",
    "SanDisk",
    "Sandisk",
    "Fastenal",
    "Fractal Analytics",
    "Chubb",
    "ExxonMobil",
    "Bottomline",
    "SiMa Technologies",
    "Workday",
    "Accenture",
    "MPM Infosoft",
    "Super.money",
    "Hitwicket",
    "Flipkart",
    "UBS"
]


def detect_company(text):

    for company in KNOWN_COMPANIES:

        if company.lower() in text.lower():
            return company

    patterns = [
        r'(?:company|employer|organization)\s*[:\-]\s*(.+)',
        r'^([A-Z][A-Za-z0-9& .\'-]{2,60})\s*\|'
    ]

    for line in text.splitlines():

        line = clean_line(line)

        for pattern in patterns:

            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:

                value = clean_text(
                    match.group(1)
                )

                if len(value) > 2:
                    return value

    return None


# ============================================================
# ROLE
# ============================================================

def detect_role(text):

    # Multi-track e-con format.
    if re.search(
            r'project\s+engineering\s+trainee\s*[-–—]\s*hardware',
            text,
            re.IGNORECASE
    ) and re.search(
        r'project\s+engineering\s+trainee\s*[-–—]\s*software',
        text,
        re.IGNORECASE
    ):

        return "Project Engineering Trainee"

    patterns = [
        r'project\s+engineering\s+trainee',
        r'AI Engineer Intern',
        r'AI Engineer',
        r'Machine Learning Engineer Intern',
        r'Data Scientist Intern',
        r'Data Analyst Intern',
        r'Software Engineer Intern',
        r'Software Engineer Trainee',
        r'Software Trainee',
        r'Hardware Trainee',
        r'Backend Engineer Intern',
        r'Backend Developer Intern',
        r'Cloud Engineer Intern',
        r'Cloud Trainee',
        r'DevOps Intern',
        r'Cybersecurity Intern'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = clean_text(
                match.group(0)
            )

            if value:
                return value

    return None


# ============================================================
# TRACK DETECTION
# ============================================================

def detect_tracks(text):

    normalized = normalize(text)

    tracks = []

    hardware_patterns = [
        "project engineering trainee - hardware",
        "hardware trainee",
        "hardware track"
    ]

    software_patterns = [
        "project engineering trainee - software",
        "software trainee",
        "software track"
    ]

    if any(
            pattern in normalized
            for pattern in hardware_patterns
    ):

        tracks.append("hardware")

    if any(
            pattern in normalized
            for pattern in software_patterns
    ):

        tracks.append("software")

    return tracks


# ============================================================
# EXACT E-CON TRACK EXTRACTION
# ============================================================

def extract_econ_tracks(text):

    normalized_text = normalize(text)

    hardware_start = normalized_text.find(
        "project engineering trainee - hardware"
    )

    software_start = normalized_text.find(
        "project engineering trainee - software"
    )

    if (
            hardware_start == -1
            or software_start == -1
    ):
        return {}


    # Hardware section ends when Software track begins.
    hardware_text = normalized_text[
                    hardware_start:
                    software_start
                    ]

    # Software section ends before the Hardware track section
    # that starts later in the document, if present.
    software_text = normalized_text[
                    software_start:
                    ]

    software_end_markers = [
        "hardware track",
        "before you walk in"
    ]

    positions = []

    for marker in software_end_markers:

        position = software_text.find(
            marker
        )

        if position > 0:
            positions.append(position)

    if positions:

        software_text = software_text[
                        :min(positions)
                        ]


    hardware_keywords = [
        "Analog Electronics",
        "Digital Electronics",
        "Circuit Theory",
        "Network Analysis",
        "Basic Knowledge of Electricals",
        "BJT Biasing",
        "MOSFET Biasing",
        "Operational Amplifier",
        "Zener Diode",
        "Clipper Circuit",
        "Clamper Circuit",
        "Rectifier",
        "Low Frequency BJT Amplifier",
        "Logic Gates",
        "Combinational Circuits",
        "Number Systems",
        "Binary Codes",
        "Sequential Circuits",
        "DAC",
        "ADC",
        "Microprocessor 8085",
        "Logic Family",
        "Boolean Algebra",
        "Ohm's Law",
        "Kirchhoff's Laws",
        "KVL",
        "KCL",
        "Voltage Division",
        "Current Division",
        "Equivalent Resistance",
        "Nodal Analysis",
        "Star to Delta Conversion",
        "Thevenin's Theorem",
        "Norton's Theorem",
        "Superposition Theorem",
        "Maximum Power Transfer Theorem",
        "DC Transient Analysis",
        "Resonance Circuits",
        "Transformer Basics",
        "Working Principle",
        "EMF Equation",
        "Turns Ratio",
        "Losses and Efficiency"
    ]


    software_keywords = [
        "Logical Reasoning",
        "Geometrical Problems",
        "Data Interpretation",
        "Algebraic Problems",
        "Mathematical Problem Modelling",
        "Mathematical Problem Modeling",
        "Time, Speed & Distance",
        "Time & Work",
        "Practical & Analytical Puzzles",
        "Probability",
        "Combinatorics",
        "Statistics",
        "Physics",
        "Physical Properties",
        "Embedded C"
    ]


    def find_keywords(
            source,
            keywords
    ):

        found = []

        for keyword in keywords:

            if normalize(keyword) in source:

                found.append(
                    keyword
                )

        return unique(found)


    hardware_found = find_keywords(
        hardware_text,
        hardware_keywords
    )

    software_found = find_keywords(
        software_text,
        software_keywords
    )


    return {

        "hardware": {

            "title":
                "Project Engineering Trainee - Hardware",

            "requirements":
                hardware_found,

            "technical_keywords":
                hardware_found,

            "about":
                "Hardware track covering analog electronics, digital electronics, circuit theory, and electrical fundamentals."
        },

        "software": {

            "title":
                "Project Engineering Trainee - Software",

            "requirements":
                software_found,

            "technical_keywords":
                software_found,

            "about":
                "Software track focused on logical reasoning, mathematics, analytical problem solving, and project depth."
        }
    }


# ============================================================
# GENERAL TECHNICAL SKILLS
# ============================================================

TECHNICAL_SKILLS = {

    "Python": [
        "python"
    ],

    "Java": [
        "java"
    ],

    "C": [
        "embedded c",
        "c programming",
        "c language"
    ],

    "C++": [
        "c++",
        "cpp"
    ],

    "JavaScript": [
        "javascript"
    ],

    "TypeScript": [
        "typescript"
    ],

    "React.js": [
        "react.js",
        "reactjs"
    ],

    "Next.js": [
        "next.js",
        "nextjs"
    ],

    "Node.js": [
        "node.js",
        "nodejs"
    ],

    "SQL": [
        "sql",
        "mysql",
        "postgresql"
    ],

    "MySQL": [
        "mysql"
    ],

    "MongoDB": [
        "mongodb",
        "mongo db"
    ],

    "Git": [
        "git",
        "github",
        "gitlab"
    ],

    "AWS": [
        "aws",
        "amazon web services"
    ],

    "Azure": [
        "azure"
    ],

    "GCP": [
        "gcp",
        "google cloud"
    ],

    "Docker": [
        "docker"
    ],

    "Kubernetes": [
        "kubernetes",
        "k8s"
    ],

    "LangChain": [
        "langchain"
    ],

    "LangGraph": [
        "langgraph"
    ],

    "RAG": [
        "retrieval augmented generation",
        "retrieval-augmented generation"
    ],

    "MCP": [
        "model context protocol"
    ],

    "LLM": [
        "llm",
        "large language model"
    ],

    "REST API": [
        "rest api",
        "restful api"
    ],

    "Power BI": [
        "power bi",
        "powerbi"
    ],

    "Tableau": [
        "tableau"
    ],

    "MATLAB": [
        "matlab"
    ],

    "Simulink": [
        "simulink"
    ],

    "Embedded Systems": [
        "embedded systems",
        "microcontroller",
        "firmware"
    ],

    "Electronics": [
        "electronics"
    ],

    "Circuit Theory": [
        "circuit theory",
        "network analysis"
    ],

    "Probability": [
        "probability"
    ],

    "Statistics": [
        "statistics"
    ],

    "Mathematics": [
        "mathematics",
        "algebra"
    ],

    "Logical Reasoning": [
        "logical reasoning",
        "analytical reasoning"
    ],

    "Data Interpretation": [
        "data interpretation"
    ],

    "Physics": [
        "physics",
        "physical properties"
    ],

    "Digital Electronics": [
        "digital electronics"
    ],

    "Analog Electronics": [
        "analog electronics"
    ],

    "Microprocessor 8085": [
        "8085"
    ],

    "Boolean Algebra": [
        "boolean algebra"
    ],

    "Karnaugh Map": [
        "k-map",
        "k map",
        "karnaugh map"
    ],

    "Transformers": [
        "transformer basics",
        "transformer theory",
        "transformers"
    ]
}


def extract_technical_keywords(text):

    normalized = normalize(text)

    found = []

    for skill, aliases in TECHNICAL_SKILLS.items():

        for alias in aliases:

            if normalize(alias) in normalized:

                if skill not in found:
                    found.append(skill)

                break

    return found


# ============================================================
# SPECIALIZATION
# ============================================================

def detect_specialization(
        text,
        role,
        tracks
):

    if (
            "hardware" in tracks
            and "software" in tracks
    ):

        return "Hardware + Software"

    if "hardware" in tracks:
        return "Hardware / Electronics"

    if "software" in tracks:
        return "Software"

    combined = normalize(
        text + " " + (role or "")
    )

    rules = {

        "AI / Machine Learning": [
            "artificial intelligence",
            "machine learning",
            "generative ai",
            "langchain",
            "langgraph",
            "rag",
            "llm"
        ],

        "Full-Stack": [
            "full-stack",
            "full stack",
            "react",
            "next.js",
            "node.js"
        ],

        "Backend": [
            "backend",
            "back-end",
            "rest api"
        ],

        "Data / Analytics": [
            "data science",
            "data scientist",
            "data analytics",
            "power bi",
            "tableau"
        ],

        "Cloud": [
            "cloud",
            "aws",
            "azure",
            "gcp"
        ],

        "Embedded Systems": [
            "embedded",
            "firmware",
            "microcontroller"
        ],

        "Cybersecurity": [
            "cybersecurity",
            "cyber security"
        ],

        "DevOps": [
            "devops",
            "docker",
            "kubernetes",
            "ci/cd"
        ]
    }

    scores = {}

    for specialization, keywords in rules.items():

        score = 0

        for keyword in keywords:

            if normalize(keyword) in combined:
                score += 1

        if score:
            scores[
                specialization
            ] = score

    if not scores:
        return None

    return max(
        scores,
        key=scores.get
    )


# ============================================================
# DURATION / LOCATION
# ============================================================

def detect_duration(text):

    patterns = [
        r'\b\d+\s*(?:-|to)?\s*\d*\s*(?:months?|weeks?)\b',
        r'\bsummer internship\b',
        r'\bwinter internship\b'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return clean_text(
                match.group(0)
            )

    return None


def detect_location(text):

    patterns = [
        r'(?:location|work location|job location)\s*[:\-]\s*(.+)',
        r'\b(Bangalore|Bengaluru|Chennai|Hyderabad|Pune|Mumbai|Delhi|Noida|Gurgaon|Gurugram|Kolkata|Coimbatore|Mysore|Mysuru)\b',
        r'\b(Remote|Hybrid|On-site|Onsite)\b'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = clean_text(
                match.group(0)
            )

            if len(value) <= 100:
                return value

    return None


# ============================================================
# RESPONSIBILITIES / ELIGIBILITY
# ============================================================

def extract_responsibilities(
        sections
):

    result = []

    for line in sections.get(
            "responsibilities",
            []
    ):

        line = clean_line(line)

        if len(line) >= 10:
            result.append(line)

    return unique(result)[:40]


def extract_preferred(
        sections
):

    result = []

    for line in sections.get(
            "preferred",
            []
    ):

        line = clean_line(line)

        if len(line) >= 3:
            result.append(line)

    return unique(result)[:30]


def extract_eligibility(text):

    result = []

    for line in text.splitlines():

        line = clean_line(line)

        if not line:
            continue

        lower = line.lower()

        if (
                "eligib" in lower
                or "degree required" in lower
                or "qualification required" in lower
                or "students from" in lower
        ):

            if len(line) >= 10:
                result.append(line)

    return unique(result)[:20]


# ============================================================
# JD SIGNALS
# ============================================================

def detect_signals(
        text,
        role,
        responsibilities,
        requirements,
        keywords,
        tracks
):

    normalized = normalize(
        text
    )

    return {

        "job_title":
            bool(role),

        "responsibilities":
            bool(
                responsibilities
                or "responsibilities" in normalized
            ),

        "requirements":
            bool(
                requirements
                or "requirements" in normalized
            ),

        "skills":
            bool(keywords),

        "employment":
            bool(
                "internship" in normalized
                or "intern" in normalized
                or "trainee" in normalized
            ),

        "multi_track":
            len(tracks) > 1,

        "hardware_track":
            "hardware" in tracks,

        "software_track":
            "software" in tracks
    }


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
        role,
        specialization,
        requirements,
        keywords,
        company,
        tracks
):

    score = 0.0

    if role:
        score += 0.20

    if specialization:
        score += 0.15

    if company:
        score += 0.10

    if requirements:
        score += 0.20

    if keywords:
        score += 0.20

    if tracks:
        score += 0.15

    return round(
        min(
            score,
            1.0
        ),
        2
    )


# ============================================================
# MAIN PARSER
# ============================================================

def parse_jd(text):

    text = clean_text(text)

    if not text:

        return {
            "role": None,
            "specialization": None,
            "duration": None,
            "location": None,
            "company": None,
            "about_role": "",
            "must_have": [],
            "responsibilities": [],
            "required_skills": [],
            "preferred_qualifications": [],
            "technical_keywords": [],
            "eligibility_requirements": [],
            "tracks": {},
            "parse_valid": False,
            "parse_confidence": 0.0
        }


    role = detect_role(
        text
    )

    tracks = detect_tracks(
        text
    )

    company = detect_company(
        text
    )

    specialization = detect_specialization(
        text,
        role,
        tracks
    )

    duration = detect_duration(
        text
    )

    location = detect_location(
        text
    )

    sections = extract_sections(
        text
    )

    responsibilities = extract_responsibilities(
        sections
    )

    preferred = extract_preferred(
        sections
    )

    eligibility = extract_eligibility(
        text
    )


    # ========================================================
    # MULTI-TRACK DOCUMENT
    # ========================================================

    track_data = {}

    if (
            "hardware" in tracks
            and "software" in tracks
    ):

        track_data = extract_econ_tracks(
            text
        )


    if track_data:

        technical_keywords = []

        required_skills = []

        for track_name, data in track_data.items():

            for keyword in data.get(
                    "technical_keywords",
                    []
            ):

                if keyword not in technical_keywords:
                    technical_keywords.append(
                        keyword
                    )

            for requirement in data.get(
                    "requirements",
                    []
            ):

                if requirement not in required_skills:
                    required_skills.append(
                        requirement
                    )

        must_have = list(
            required_skills
        )

    else:

        # Normal single-track JD.
        #
        # IMPORTANT:
        # We only extract technical keywords globally when
        # the document is NOT a known multi-track prep guide.

        technical_keywords = extract_technical_keywords(
            "\n".join(
                sections.get(
                    "requirements",
                    []
                )
            )
        )

        required_skills = list(
            technical_keywords
        )

        must_have = list(
            required_skills
        )


    signals = detect_signals(
        text,
        role,
        responsibilities,
        required_skills,
        technical_keywords,
        tracks
    )

    confidence = calculate_confidence(
        role,
        specialization,
        required_skills,
        technical_keywords,
        company,
        tracks
    )


    parse_valid = bool(
        role
        and (
                technical_keywords
                or required_skills
                or track_data
        )
    )


    about_role = ""

    if track_data:

        about_role = (
            "Multi-track Project Engineering Trainee "
            "opportunity with Hardware and Software tracks."
        )

    elif sections.get("about"):

        about_role = " ".join(
            sections["about"]
        )[:2500]


    return {

        "role":
            role,

        "specialization":
            specialization,

        "duration":
            duration,

        "location":
            location,

        "company":
            company,

        "about_role":
            about_role,

        "must_have":
            unique(must_have)[:60],

        "responsibilities":
            unique(responsibilities)[:40],

        "required_skills":
            unique(required_skills)[:60],

        "preferred_qualifications":
            unique(preferred)[:30],

        "technical_keywords":
            unique(technical_keywords)[:60],

        "eligibility_requirements":
            unique(eligibility)[:20],

        "tracks":
            track_data,

        "parse_valid":
            parse_valid,

        "parse_confidence":
            confidence,

        "jd_signals":
            signals
    }


# ============================================================
# FILE PROCESSING
# ============================================================

def parse_document(
        file_path
):

    from documents.extractor import extract_text

    if not os.path.exists(
            file_path
    ):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    print(
        "Reading:",
        file_path
    )

    text = extract_text(
        file_path
    )

    if not text:

        raise ValueError(
            "No text could be extracted."
        )

    print(
        "Extracted characters:",
        len(text)
    )

    parsed = parse_jd(
        text
    )

    return text, parsed


# ============================================================
# DISPLAY
# ============================================================

def display_result(
        parsed
):

    print()
    print("=" * 70)
    print("STRUCTURED JOB DESCRIPTION")
    print("=" * 70)

    print(
        "Role:",
        parsed.get("role")
    )

    print(
        "Specialization:",
        parsed.get("specialization")
    )

    print(
        "Duration:",
        parsed.get("duration")
    )

    print(
        "Location:",
        parsed.get("location")
    )

    print(
        "Company:",
        parsed.get("company")
    )

    print(
        "Parse valid:",
        parsed.get("parse_valid")
    )

    print(
        "Parse confidence:",
        parsed.get("parse_confidence")
    )

    print()

    print("Must-have:")

    for item in parsed.get(
            "must_have",
            []
    ):

        print(
            "-",
            item
        )

    print()

    print("Responsibilities:")

    for item in parsed.get(
            "responsibilities",
            []
    ):

        print(
            "-",
            item
        )

    print()

    print("Required skills:")

    for item in parsed.get(
            "required_skills",
            []
    ):

        print(
            "-",
            item
        )

    print()

    print("Preferred qualifications:")

    for item in parsed.get(
            "preferred_qualifications",
            []
    ):

        print(
            "-",
            item
        )

    print()

    print("Technical keywords:")

    print(
        ", ".join(
            parsed.get(
                "technical_keywords",
                []
            )
        )
    )

    print()

    print("Eligibility:")

    for item in parsed.get(
            "eligibility_requirements",
            []
    ):

        print(
            "-",
            item
        )


    # ========================================================
    # TRACK DISPLAY
    # ========================================================

    tracks = parsed.get(
        "tracks",
        {}
    )

    if tracks:

        print()
        print("=" * 70)
        print("TRACKS")
        print("=" * 70)

        for name, data in tracks.items():

            print()
            print(
                name.upper()
            )

            print(
                "Title:",
                data.get("title")
            )

            print(
                "Requirements:"
            )

            for item in data.get(
                    "requirements",
                    []
            ):

                print(
                    "-",
                    item
                )

            print(
                "Technical keywords:"
            )

            print(
                ", ".join(
                    data.get(
                        "technical_keywords",
                        []
                    )
                )
            )


    print()

    print("JD signals:")

    for key, value in parsed.get(
            "jd_signals",
            {}
    ).items():

        print(
            f"- {key}: {value}"
        )

    print()

    print("Full JSON:")

    print(
        json.dumps(
            parsed,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "=" * 70
    )


# ============================================================
# CLI
# ============================================================

def main():

    if len(sys.argv) < 2:

        print(
            'Usage: python documents/jd_parser.py "file.pdf"'
        )

        sys.exit(1)

    file_path = sys.argv[1]

    try:

        _, parsed = parse_document(
            file_path
        )

        display_result(
            parsed
        )

    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(
            error
        )

        sys.exit(1)


if __name__ == "__main__":

    main()