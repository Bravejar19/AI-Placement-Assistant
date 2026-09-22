import os
import sys
import re
import json
import requests


# ============================================================
# PATH
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

from resume.resume_parser import parse_resume

from database.opportunity_db import (
    initialize_database,
    get_opportunity
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "qwen3:4b-instruct-2507-q4_K_M"

REQUEST_TIMEOUT = 120


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text).lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def safe_list(value):

    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [value]


def unique(items):

    result = []
    seen = set()

    for item in items:

        if item is None:
            continue

        item = str(item).strip()

        if not item:
            continue

        key = normalize(item)

        if key in seen:
            continue

        seen.add(key)

        result.append(item)

    return result


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


# ============================================================
# SKILL ALIASES
# ============================================================

ALIASES = {

    "python": [
        "python"
    ],

    "c": [
        "c",
        "embedded c",
        "c programming",
        "c language"
    ],

    "embedded c": [
        "embedded c",
        "embedded-c",
        "c programming"
    ],

    "c++": [
        "c++",
        "cpp"
    ],

    "java": [
        "java"
    ],

    "javascript": [
        "javascript",
        "java script"
    ],

    "sql": [
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "sqlite",
        "database"
    ],

    "mysql": [
        "mysql"
    ],

    "mongodb": [
        "mongodb",
        "mongo db",
        "mongo"
    ],

    "git": [
        "git",
        "github",
        "gitlab",
        "version control"
    ],

    "aws": [
        "aws",
        "amazon web services"
    ],

    "azure": [
        "azure"
    ],

    "gcp": [
        "gcp",
        "google cloud"
    ],

    "cloud": [
        "cloud computing",
        "cloud platform",
        "cloud"
    ],

    "docker": [
        "docker",
        "containerization",
        "containers"
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
        "ml",
        "predictive modelling",
        "predictive modeling"
    ],

    "artificial intelligence": [
        "artificial intelligence",
        "ai"
    ],

    "deep learning": [
        "deep learning",
        "neural network",
        "neural networks",
        "cnn",
        "rnn"
    ],

    "llm": [
        "llm",
        "large language model",
        "large language models"
    ],

    "rag": [
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation"
    ],

    "langchain": [
        "langchain"
    ],

    "langgraph": [
        "langgraph"
    ],

    "openai": [
        "openai"
    ],

    "computer vision": [
        "computer vision",
        "image processing",
        "image recognition"
    ],

    "data analysis": [
        "data analysis",
        "data analytics",
        "data processing"
    ],

    "data interpretation": [
        "data interpretation",
        "data analysis",
        "data analytics"
    ],

    "statistics": [
        "statistics",
        "statistical"
    ],

    "probability": [
        "probability"
    ],

    "mathematics": [
        "mathematics",
        "mathematical",
        "math",
        "algebra",
        "calculus"
    ],

    "logical reasoning": [
        "logical reasoning",
        "logical thinking",
        "reasoning"
    ],

    "problem solving": [
        "problem solving",
        "problem-solving",
        "analytical thinking",
        "analytical problem solving",
        "technical problem solving"
    ],

    "mathematical modelling": [
        "mathematical modelling",
        "mathematical modeling",
        "modelling",
        "modeling"
    ],

    "physics": [
        "physics",
        "physical properties"
    ],

    "electronics": [
        "electronics",
        "electronic systems",
        "electronic circuit",
        "electronic circuits"
    ],

    "analog electronics": [
        "analog electronics",
        "analogue electronics"
    ],

    "digital electronics": [
        "digital electronics",
        "digital logic",
        "logic gates",
        "digital circuits"
    ],

    "circuit theory": [
        "circuit theory",
        "circuit analysis",
        "network theory",
        "network analysis"
    ],

    "network analysis": [
        "network analysis",
        "circuit analysis",
        "circuit theory",
        "network theory"
    ],

    "electrical": [
        "electrical",
        "electrical engineering",
        "electrical systems",
        "electrical fundamentals",
        "electrical circuits"
    ],

    "embedded systems": [
        "embedded systems",
        "embedded system",
        "embedded",
        "microcontroller",
        "microcontrollers",
        "microprocessor"
    ],

    "microprocessor": [
        "microprocessor",
        "microprocessors",
        "8085"
    ],

    "transformers": [
        "transformer",
        "transformers"
    ],

    "matlab": [
        "matlab"
    ],

    "simulink": [
        "simulink"
    ],

    "arduino": [
        "arduino"
    ],

    "system modelling": [
        "system modelling",
        "system modeling",
        "simulation",
        "simulations",
        "modelling",
        "modeling"
    ]
}


# ============================================================
# TRANSFERABLE RELATIONSHIPS
# ============================================================

RELATED = {

    "analog electronics": [
        "electronics",
        "embedded systems",
        "electrical",
        "arduino"
    ],

    "digital electronics": [
        "electronics",
        "embedded systems",
        "microprocessor",
        "arduino"
    ],

    "circuit theory": [
        "circuit analysis",
        "network analysis",
        "electronics",
        "electrical",
        "embedded systems"
    ],

    "network analysis": [
        "circuit theory",
        "circuit analysis",
        "electrical",
        "electronics"
    ],

    "basic knowledge of electricals": [
        "electrical",
        "electronics",
        "circuit theory",
        "circuit analysis",
        "embedded systems"
    ],

    "embedded c": [
        "embedded systems",
        "embedded",
        "c programming",
        "arduino"
    ],

    "embedded systems": [
        "arduino",
        "microcontroller",
        "microprocessor",
        "embedded c",
        "electronics"
    ],

    "logical reasoning": [
        "problem solving",
        "analytical thinking",
        "mathematics"
    ],

    "geometrical problems": [
        "mathematics",
        "problem solving",
        "analytical thinking"
    ],

    "data interpretation": [
        "data analysis",
        "data analytics",
        "statistics"
    ],

    "algebraic problems": [
        "mathematics",
        "problem solving"
    ],

    "mathematical problem modelling": [
        "mathematics",
        "mathematical modelling",
        "system modelling",
        "matlab",
        "simulink",
        "simulation"
    ],

    "time, speed & distance": [
        "mathematics",
        "problem solving",
        "analytical thinking"
    ],

    "time & work": [
        "mathematics",
        "problem solving",
        "analytical thinking"
    ],

    "practical & analytical puzzles": [
        "problem solving",
        "analytical thinking",
        "logical reasoning"
    ],

    "probability": [
        "mathematics",
        "statistics",
        "data analysis"
    ],

    "combinatorics": [
        "mathematics",
        "probability",
        "logical reasoning"
    ],

    "statistics": [
        "data analysis",
        "mathematics",
        "probability"
    ],

    "physics": [
        "engineering",
        "electronics",
        "electrical",
        "mathematics"
    ],

    "physical properties": [
        "physics",
        "engineering"
    ],

    "machine learning": [
        "python",
        "statistics",
        "mathematics",
        "data analysis"
    ],

    "artificial intelligence": [
        "python",
        "machine learning",
        "data analysis"
    ],

    "data science": [
        "python",
        "data analysis",
        "statistics",
        "mathematics",
        "sql"
    ],

    "backend": [
        "python",
        "sql",
        "database",
        "api"
    ]
}


# ============================================================
# PROJECT / DOMAIN EVIDENCE
# ============================================================

PROJECT_EVIDENCE = {

    "analog electronics": [
        "analog",
        "analogue",
        "sensor",
        "signal",
        "circuit",
        "measurement",
        "angle"
    ],

    "digital electronics": [
        "digital",
        "embedded",
        "arduino",
        "microcontroller",
        "logic"
    ],

    "circuit theory": [
        "circuit",
        "electronics",
        "electrical",
        "sensor",
        "resistor",
        "voltage",
        "current"
    ],

    "network analysis": [
        "circuit",
        "electrical",
        "network",
        "voltage",
        "current"
    ],

    "basic knowledge of electricals": [
        "electrical",
        "electronics",
        "circuit",
        "voltage",
        "current",
        "power"
    ],

    "embedded systems": [
        "embedded",
        "arduino",
        "microcontroller",
        "sensor",
        "hardware",
        "firmware"
    ],

    "embedded c": [
        "embedded c",
        "arduino",
        "microcontroller",
        "embedded",
        "firmware"
    ],

    "logical reasoning": [
        "problem solving",
        "analytical",
        "logic",
        "algorithm"
    ],

    "mathematics": [
        "mathematics",
        "mathematical",
        "modelling",
        "modeling",
        "calculation",
        "analysis"
    ],

    "probability": [
        "probability",
        "statistical",
        "statistics",
        "data analysis"
    ],

    "statistics": [
        "statistics",
        "statistical",
        "data analysis",
        "data analytics"
    ],

    "physics": [
        "physics",
        "engineering",
        "mechanical",
        "electrical",
        "electronics"
    ],

    "mathematical modelling": [
        "matlab",
        "simulink",
        "modelling",
        "modeling",
        "simulation"
    ],

    "system modelling": [
        "matlab",
        "simulink",
        "modelling",
        "modeling",
        "simulation"
    ]
}


# ============================================================
# PHRASE MATCHING
# ============================================================

def contains_phrase(
        text,
        phrase
):

    text = normalize(text)
    phrase = normalize(phrase)

    if not text or not phrase:
        return False

    pattern = (
            r"(?<![a-z0-9])"
            + re.escape(phrase)
            + r"(?![a-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            text
        )
    )


# ============================================================
# DIRECT MATCH
# ============================================================

def direct_match(
        resume_text,
        requirement
):

    req = normalize(
        requirement
    )

    aliases = ALIASES.get(
        req,
        [req]
    )

    for alias in aliases:

        if contains_phrase(
                resume_text,
                alias
        ):

            return alias

    return None


# ============================================================
# PROJECT MATCH
# ============================================================

def project_match(
        resume_text,
        requirement
):

    req = normalize(
        requirement
    )

    evidence_terms = PROJECT_EVIDENCE.get(
        req,
        []
    )

    for term in evidence_terms:

        if contains_phrase(
                resume_text,
                term
        ):

            return term

    return None


# ============================================================
# RELATED MATCH
# ============================================================

def related_match(
        resume_text,
        requirement
):

    req = normalize(
        requirement
    )

    related_terms = RELATED.get(
        req,
        []
    )

    for term in related_terms:

        if direct_match(
                resume_text,
                term
        ):

            return term

        if project_match(
                resume_text,
                term
        ):

            return term

    return None


# ============================================================
# REQUIREMENT MATCH
# ============================================================

def match_requirement(
        resume_text,
        requirement
):

    direct = direct_match(
        resume_text,
        requirement
    )

    if direct:

        return {
            "type": "direct",
            "evidence": direct
        }

    project = project_match(
        resume_text,
        requirement
    )

    if project:

        return {
            "type": "project",
            "evidence": project
        }

    related = related_match(
        resume_text,
        requirement
    )

    if related:

        return {
            "type": "related",
            "evidence": related
        }

    return {
        "type": "missing",
        "evidence": None
    }


# ============================================================
# TRACK REQUIREMENTS
# ============================================================

def get_track_requirements(
        track
):

    requirements = []

    requirements.extend(
        safe_list(
            track.get(
                "requirements",
                []
            )
        )
    )

    requirements.extend(
        safe_list(
            track.get(
                "technical_keywords",
                []
            )
        )
    )

    return unique(
        requirements
    )


# ============================================================
# MATCH STRENGTH
# ============================================================

def match_value(
        match_type
):

    if match_type == "direct":
        return 1.00

    if match_type == "project":
        return 0.72

    if match_type == "related":
        return 0.42

    return 0.0


# ============================================================
# REQUIREMENT IMPORTANCE
# ============================================================

def requirement_weight(
        requirement,
        track_name=None
):

    req = normalize(
        requirement
    )

    if track_name == "hardware":

        if req in [
            "analog electronics",
            "digital electronics",
            "circuit theory"
        ]:

            return 1.30

        if req in [
            "network analysis",
            "basic knowledge of electricals"
        ]:

            return 1.10

        return 0.75

    if track_name == "software":

        if req == "embedded c":

            return 1.30

        if req in [
            "logical reasoning",
            "mathematical problem modelling",
            "practical & analytical puzzles"
        ]:

            return 1.10

        if req in [
            "mathematics",
            "probability",
            "statistics",
            "data interpretation",
            "algebraic problems",
            "combinatorics"
        ]:

            return 0.95

        if req in [
            "physics",
            "physical properties"
        ]:

            return 0.65

        return 0.60

    return 1.0


# ============================================================
# TRACK ANALYSIS
# ============================================================

def analyze_track(
        resume_text,
        track_name,
        track
):

    requirements = get_track_requirements(
        track
    )

    direct = []
    project = []
    related = []
    missing = []

    weighted_total = 0.0
    weighted_score = 0.0

    for requirement in requirements:

        weight = requirement_weight(
            requirement,
            track_name
        )

        weighted_total += weight

        result = match_requirement(
            resume_text,
            requirement
        )

        value = match_value(
            result["type"]
        )

        weighted_score += (
                weight * value
        )

        item = {
            "skill": requirement,
            "match_type": result["type"],
            "evidence": result["evidence"],
            "weight": weight
        }

        if result["type"] == "direct":

            direct.append(
                item
            )

        elif result["type"] == "project":

            project.append(
                item
            )

        elif result["type"] == "related":

            related.append(
                item
            )

        else:

            missing.append(
                item
            )

    if weighted_total == 0:

        base_score = 0

    else:

        base_score = (
                             weighted_score /
                             weighted_total
                     ) * 100

    # --------------------------------------------------------
    # Evidence bonuses
    # --------------------------------------------------------

    direct_count = len(
        direct
    )

    project_count = len(
        project
    )

    related_count = len(
        related
    )

    missing_count = len(
        missing
    )

    evidence_bonus = 0

    evidence_bonus += min(
        8,
        direct_count * 2
    )

    evidence_bonus += min(
        6,
        project_count * 1.5
    )

    evidence_bonus += min(
        3,
        related_count * 0.75
    )

    score = (
            base_score
            + evidence_bonus
    )

    # --------------------------------------------------------
    # Conservative caps
    # --------------------------------------------------------

    if direct_count == 0:

        score = min(
            score,
            78
        )

    elif direct_count < 2:

        score = min(
            score,
            84
        )

    elif direct_count < 4:

        score = min(
            score,
            91
        )

    if missing_count >= 3:

        score = min(
            score,
            75
        )

    elif missing_count == 2:

        score = min(
            score,
            82
        )

    elif missing_count == 1:

        score = min(
            score,
            88
        )

    score = round(
        max(
            0,
            min(
                100,
                score
            )
        )
    )

    return {
        "track": track_name,

        "title": track.get(
            "title",
            track_name.title()
        ),

        "score": score,

        "direct_matches": direct,

        "project_matches": project,

        "related_matches": related,

        "missing_or_weak": missing
    }


# ============================================================
# SINGLE JD ANALYSIS
# ============================================================

def analyze_single_jd(
        resume_text,
        jd
):

    must_have = unique(
        safe_list(
            jd.get(
                "must_have",
                []
            )
        )
    )

    required = unique(
        safe_list(
            jd.get(
                "required_skills",
                []
            )
        )
    )

    technical = unique(
        safe_list(
            jd.get(
                "technical_keywords",
                []
            )
        )
    )

    preferred = unique(
        safe_list(
            jd.get(
                "preferred_qualifications",
                []
            )
        )
    )

    requirements = unique(
        must_have
        + required
        + technical
    )

    direct = []
    project = []
    related = []
    missing = []

    weighted_total = 0.0
    weighted_score = 0.0

    normalized_must_have = [
        normalize(x)
        for x in must_have
    ]

    normalized_required = [
        normalize(x)
        for x in required
    ]

    for requirement in requirements:

        normalized_requirement = normalize(
            requirement
        )

        if normalized_requirement in normalized_must_have:

            weight = 1.25

        elif normalized_requirement in normalized_required:

            weight = 1.0

        else:

            weight = 0.60

        weighted_total += weight

        result = match_requirement(
            resume_text,
            requirement
        )

        value = match_value(
            result["type"]
        )

        weighted_score += (
                weight * value
        )

        item = {
            "skill": requirement,
            "match_type": result["type"],
            "evidence": result["evidence"],
            "weight": weight
        }

        if result["type"] == "direct":

            direct.append(
                item
            )

        elif result["type"] == "project":

            project.append(
                item
            )

        elif result["type"] == "related":

            related.append(
                item
            )

        else:

            missing.append(
                item
            )

    if weighted_total == 0:

        score = 0

    else:

        score = (
                        weighted_score /
                        weighted_total
                ) * 100

    # Preferred qualifications are bonus only.
    preferred_bonus = 0

    for requirement in preferred:

        result = match_requirement(
            resume_text,
            requirement
        )

        if result["type"] == "direct":

            preferred_bonus += 2

        elif result["type"] == "project":

            preferred_bonus += 1

    score += min(
        5,
        preferred_bonus
    )

    # Small project bonus.
    score += min(
        5,
        len(project) * 1.25
    )

    # Conservative caps.
    if len(direct) == 0:

        score = min(
            score,
            70
        )

    elif len(direct) < 2:

        score = min(
            score,
            80
        )

    elif len(direct) < 4:

        score = min(
            score,
            88
        )

    if len(missing) >= 3:

        score = min(
            score,
            70
        )

    elif len(missing) == 2:

        score = min(
            score,
            78
        )

    elif len(missing) == 1:

        score = min(
            score,
            85
        )

    score = round(
        max(
            0,
            min(
                100,
                score
            )
        )
    )

    return {
        "mode": "single",

        "score": score,

        "best_track": None,

        "tracks": {},

        "direct_matches": direct,

        "project_matches": project,

        "related_matches": related,

        "missing_or_weak": missing
    }


# ============================================================
# FULL JD ANALYSIS
# ============================================================

def analyze_jd(
        resume_text,
        jd
):

    tracks = jd.get(
        "tracks",
        {}
    )

    # --------------------------------------------------------
    # Multi-track JD
    # --------------------------------------------------------

    if (
            isinstance(
                tracks,
                dict
            )
            and tracks
    ):

        track_results = {}

        for track_name, track in tracks.items():

            if not isinstance(
                    track,
                    dict
            ):

                continue

            track_results[
                track_name
            ] = analyze_track(
                resume_text,
                track_name,
                track
            )

        if track_results:

            best_track = max(
                track_results.values(),
                key=lambda item: item["score"]
            )

            return {
                "mode": "multi_track",

                "score":
                    best_track["score"],

                "best_track":
                    best_track["track"],

                "tracks":
                    track_results,

                "direct_matches":
                    best_track[
                        "direct_matches"
                    ],

                "project_matches":
                    best_track[
                        "project_matches"
                    ],

                "related_matches":
                    best_track[
                        "related_matches"
                    ],

                "missing_or_weak":
                    best_track[
                        "missing_or_weak"
                    ]
            }

    # --------------------------------------------------------
    # Single-track JD
    # --------------------------------------------------------

    return analyze_single_jd(
        resume_text,
        jd
    )


# ============================================================
# RECOMMENDATION
# ============================================================

def recommendation_for(
        score
):

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
# DECISION
# ============================================================

def decision_for(
        score
):

    if score >= 60:

        return "APPLY"

    if score >= 45:

        return "CONSIDER"

    return "SKIP"


# ============================================================
# REASON
# ============================================================

def build_reason(
        analysis
):

    direct = analysis.get(
        "direct_matches",
        []
    )

    project = analysis.get(
        "project_matches",
        []
    )

    related = analysis.get(
        "related_matches",
        []
    )

    missing = analysis.get(
        "missing_or_weak",
        []
    )

    parts = []

    if direct:

        names = [
            item["skill"]
            for item in direct[:5]
        ]

        parts.append(
            "Direct matches: "
            + ", ".join(names)
        )

    if project:

        names = [
            item["skill"]
            for item in project[:5]
        ]

        parts.append(
            "Project evidence: "
            + ", ".join(names)
        )

    if related:

        names = [
            item["skill"]
            for item in related[:4]
        ]

        parts.append(
            "Transferable evidence: "
            + ", ".join(names)
        )

    if missing:

        names = [
            item["skill"]
            for item in missing[:5]
        ]

        parts.append(
            "Missing/weak: "
            + ", ".join(names)
        )

    if not parts:

        return (
            "Limited relevant evidence was found "
            "between the resume and the JD."
        )

    return ". ".join(
        parts
    ) + "."


# ============================================================
# LOAD RESUME
# ============================================================

def load_resume():

    print()
    print(
        "📄 Loading resume..."
    )

    try:

        resume = parse_resume()

    except Exception as error:

        print(
            f"❌ Resume parser failed: {error}"
        )

        return None

    if not resume:

        print(
            "❌ Resume could not be loaded."
        )

        return None

    if isinstance(
            resume,
            dict
    ):

        text = (
                resume.get("text")
                or resume.get("raw_text")
                or resume.get("resume_text")
                or ""
        )

    else:

        text = str(
            resume
        )

    if not text:

        print(
            "❌ Resume text is empty."
        )

        return None

    print(
        f"✓ Resume extracted: {len(text)} characters"
    )

    return text


# ============================================================
# LOAD JD
# ============================================================

def load_jd(
        opportunity_id
):

    opportunity = get_opportunity(
        opportunity_id
    )

    if opportunity is None:

        print(
            f"❌ Opportunity {opportunity_id} not found."
        )

        return None

    parsed = row_value(
        opportunity,
        "parsed_jd"
    )

    if not parsed:

        print(
            "❌ No parsed JD available."
        )

        return None

    if isinstance(
            parsed,
            dict
    ):

        return parsed

    try:

        parsed = json.loads(
            parsed
        )

    except Exception as error:

        print(
            f"❌ Could not decode parsed JD: {error}"
        )

        return None

    if not isinstance(
            parsed,
            dict
    ):

        return None

    return parsed


# ============================================================
# OLLAMA PROMPT
# ============================================================

def build_ai_prompt(
        resume_text,
        jd,
        analysis
):

    company = jd.get(
        "company",
        "Unknown Company"
    )

    role = jd.get(
        "role",
        "Unknown Role"
    )

    specialization = jd.get(
        "specialization",
        ""
    )

    direct = [
        item["skill"]
        for item in analysis.get(
            "direct_matches",
            []
        )
    ]

    project = [
        item["skill"]
        for item in analysis.get(
            "project_matches",
            []
        )
    ]

    related = [
        item["skill"]
        for item in analysis.get(
            "related_matches",
            []
        )
    ]

    missing = [
        item["skill"]
        for item in analysis.get(
            "missing_or_weak",
            []
        )
    ]

    track_scores = {
        name: value.get("score")
        for name, value
        in analysis.get(
            "tracks",
            {}
        ).items()
    }

    return f"""
You are a conservative placement assistant evaluating a student's resume.

COMPANY:
{company}

ROLE:
{role}

SPECIALIZATION:
{specialization}

FIT SCORE:
{analysis.get("score", 0)}/100

BEST TRACK:
{analysis.get("best_track")}

TRACK SCORES:
{json.dumps(track_scores)}

DIRECT MATCHES:
{json.dumps(direct)}

PROJECT / DOMAIN EVIDENCE:
{json.dumps(project)}

TRANSFERABLE MATCHES:
{json.dumps(related)}

MISSING / WEAK:
{json.dumps(missing)}

RESUME:
{resume_text[:10000]}

RULES:

1. Only use evidence actually present in the resume.
2. Never invent experience.
3. Do not tell the student to add a skill they do not demonstrate.
4. Resume suggestions should improve wording or presentation of existing evidence.
5. Distinguish direct evidence from project evidence and transferable evidence.
6. Do not describe a transferable skill as a direct skill.
7. Do not call the candidate a perfect fit unless the evidence genuinely supports it.
8. If multiple tracks exist, mention the best track and briefly acknowledge the alternative when relevant.
9. Give realistic application advice.

Return ONLY valid JSON:

{{
    "summary": "Short realistic assessment",
    "application_advice": "One of STRONG APPLY, APPLY, CONSIDER, LOW MATCH, SKIP",
    "resume_suggestions": [
        "Suggestion based on existing evidence",
        "Suggestion based on existing evidence",
        "Suggestion based on existing evidence"
    ]
}}
"""


# ============================================================
# ASK QWEN
# ============================================================

def ask_qwen(
        prompt
):

    print()
    print(
        "🤖 Asking local Qwen for assessment..."
    )

    payload = {

        "model": MODEL_NAME,

        "prompt": prompt,

        "stream": False,

        "format": "json",

        "think": False,

        "options": {

            "temperature": 0,

            "num_predict": 500,

            "num_ctx": 8192
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

    except requests.exceptions.Timeout:

        print(
            "⚠ Qwen request timed out."
        )

        return None

    except requests.exceptions.ConnectionError:

        print(
            "⚠ Ollama is not running."
        )

        return None

    except Exception as error:

        print(
            f"⚠ Ollama error: {error}"
        )

        return None

    if response.status_code != 200:

        print(
            f"⚠ Ollama returned HTTP {response.status_code}"
        )

        return None

    try:

        data = response.json()

    except Exception:

        print(
            "⚠ Invalid response from Ollama."
        )

        return None

    output = data.get(
        "response",
        ""
    )

    if not output:

        return None

    try:

        return json.loads(
            output
        )

    except Exception:

        start = output.find(
            "{"
        )

        end = output.rfind(
            "}"
        )

        if (
                start >= 0
                and end > start
        ):

            try:

                return json.loads(
                    output[
                    start:end + 1
                    ]
                )

            except Exception:

                pass

    return None


# ============================================================
# DISPLAY
# ============================================================

def display_analysis(
        jd,
        analysis
):

    score = analysis[
        "score"
    ]

    recommendation = recommendation_for(
        score
    )

    decision = decision_for(
        score
    )

    print()
    print(
        "=" * 70
    )

    print(
        "RESUME ↔ JD ANALYSIS"
    )

    print(
        "=" * 70
    )

    print()
    print(
        f"Company: {jd.get('company')}"
    )

    print(
        f"Role: {jd.get('role')}"
    )

    print(
        f"Specialization: {jd.get('specialization')}"
    )

    print()
    print(
        f"Fit Score: {score}%"
    )

    print(
        f"Recommendation: {recommendation}"
    )

    print(
        f"Decision: {decision}"
    )

    if analysis.get(
            "best_track"
    ):

        print(
            f"Best Track: {analysis['best_track']}"
        )

    # --------------------------------------------------------
    # TRACK COMPARISON
    # --------------------------------------------------------

    tracks = analysis.get(
        "tracks",
        {}
    )

    if tracks:

        print()
        print(
            "-" * 70
        )

        print(
            "TRACK COMPARISON"
        )

        print(
            "-" * 70
        )

        for name, track in tracks.items():

            print(
                f"{name.title():15} : "
                f"{track['score']}%"
            )

        best_name = analysis.get(
            "best_track"
        )

        if best_name:

            alternatives = [
                name
                for name in tracks
                if name != best_name
            ]

            if alternatives:

                print()
                print(
                    f"Best fit: {best_name.title()}"
                )

                print(
                    "Alternative track(s): "
                    + ", ".join(
                        x.title()
                        for x in alternatives
                    )
                )

    # --------------------------------------------------------
    # DIRECT
    # --------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        "DIRECT MATCHES"
    )

    print(
        "-" * 70
    )

    direct = analysis.get(
        "direct_matches",
        []
    )

    if not direct:

        print(
            "None."
        )

    for item in direct:

        evidence = item.get(
            "evidence"
        )

        if evidence:

            print(
                f"✓ {item['skill']} "
                f"(resume evidence: {evidence})"
            )

        else:

            print(
                f"✓ {item['skill']}"
            )

    # --------------------------------------------------------
    # PROJECT
    # --------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        "PROJECT / DOMAIN EVIDENCE"
    )

    print(
        "-" * 70
    )

    project = analysis.get(
        "project_matches",
        []
    )

    if not project:

        print(
            "None."
        )

    for item in project:

        print(
            f"✓ {item['skill']} "
            f"(project/domain evidence: "
            f"{item.get('evidence')})"
        )

    # --------------------------------------------------------
    # RELATED
    # --------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        "TRANSFERABLE MATCHES"
    )

    print(
        "-" * 70
    )

    related = analysis.get(
        "related_matches",
        []
    )

    if not related:

        print(
            "None."
        )

    for item in related:

        print(
            f"~ {item['skill']} "
            f"(related evidence: "
            f"{item.get('evidence')})"
        )

    # --------------------------------------------------------
    # MISSING
    # --------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        "MISSING / WEAK"
    )

    print(
        "-" * 70
    )

    missing = analysis.get(
        "missing_or_weak",
        []
    )

    if not missing:

        print(
            "None."
        )

    for item in missing:

        print(
            f"✗ {item['skill']}"
        )


# ============================================================
# SAVE RESULT
# ============================================================

def save_result(
        opportunity_id,
        jd,
        analysis,
        ai_result
):

    directory = os.path.join(
        BASE_DIR,
        "analysis_results"
    )

    os.makedirs(
        directory,
        exist_ok=True
    )

    result = {

        "opportunity_id":
            opportunity_id,

        "company":
            jd.get(
                "company"
            ),

        "role":
            jd.get(
                "role"
            ),

        "specialization":
            jd.get(
                "specialization"
            ),

        "fit_score":
            analysis.get(
                "score"
            ),

        "recommendation":
            recommendation_for(
                analysis.get(
                    "score",
                    0
                )
            ),

        "decision":
            decision_for(
                analysis.get(
                    "score",
                    0
                )
            ),

        "best_track":
            analysis.get(
                "best_track"
            ),

        "track_scores": {

            name:
                value.get(
                    "score"
                )

            for name, value
            in analysis.get(
                "tracks",
                {}
            ).items()
        },

        "direct_matches":
            analysis.get(
                "direct_matches",
                []
            ),

        "project_matches":
            analysis.get(
                "project_matches",
                []
            ),

        "related_matches":
            analysis.get(
                "related_matches",
                []
            ),

        "missing_or_weak":
            analysis.get(
                "missing_or_weak",
                []
            ),

        "reason":
            build_reason(
                analysis
            ),

        "ai_assessment":
            ai_result
    }

    output_file = os.path.join(
        directory,
        f"opportunity_{opportunity_id}_analysis.json"
    )

    try:

        with open(
                output_file,
                "w",
                encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

        print()
        print(
            f"✓ Analysis saved: {output_file}"
        )

    except Exception as error:

        print(
            f"⚠ Could not save analysis: {error}"
        )


# ============================================================
# ANALYZE OPPORTUNITY
# ============================================================

def analyze_opportunity(
        opportunity_id
):

    jd = load_jd(
        opportunity_id
    )

    if not jd:

        return None

    print()
    print(
        "JD loaded"
    )

    print(
        "Company:",
        jd.get(
            "company"
        )
    )

    print(
        "Role:",
        jd.get(
            "role"
        )
    )

    print(
        "Specialization:",
        jd.get(
            "specialization"
        )
    )

    resume_text = load_resume()

    if not resume_text:

        return None

    print()
    print(
        "Running calibrated resume-to-JD matching..."
    )

    analysis = analyze_jd(
        resume_text,
        jd
    )

    display_analysis(
        jd,
        analysis
    )

    # --------------------------------------------------------
    # REASON
    # --------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        "WHY THIS SCORE?"
    )

    print(
        "-" * 70
    )

    print(
        build_reason(
            analysis
        )
    )

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    prompt = build_ai_prompt(
        resume_text,
        jd,
        analysis
    )

    ai_result = ask_qwen(
        prompt
    )

    print()
    print(
        "-" * 70
    )

    print(
        "AI ASSESSMENT"
    )

    print(
        "-" * 70
    )

    if ai_result:

        print(
            ai_result.get(
                "summary",
                "No summary returned."
            )
        )

        print()
        print(
            "APPLICATION ADVICE:"
        )

        print(
            ai_result.get(
                "application_advice",
                recommendation_for(
                    analysis["score"]
                )
            )
        )

        suggestions = ai_result.get(
            "resume_suggestions",
            []
        )

        if suggestions:

            print()
            print(
                "RESUME SUGGESTIONS:"
            )

            for suggestion in suggestions:

                print(
                    f"• {suggestion}"
                )

    else:

        print(
            "AI assessment unavailable."
        )

    save_result(
        opportunity_id,
        jd,
        analysis,
        ai_result
    )

    return analysis


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Initializing database..."
    )

    initialize_database()

    print(
        "Database ready!"
    )

    while True:

        value = input(
            "\nEnter Opportunity ID "
            "(or Q to quit): "
        ).strip()

        if value.lower() == "q":

            print(
                "Exiting."
            )

            break

        try:

            opportunity_id = int(
                value
            )

        except ValueError:

            print(
                "Invalid Opportunity ID."
            )

            continue

        try:

            analyze_opportunity(
                opportunity_id
            )

        except Exception as error:

            print()
            print(
                "=" * 70
            )

            print(
                "ANALYSIS ERROR"
            )

            print(
                "=" * 70
            )

            print(
                str(error)
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()