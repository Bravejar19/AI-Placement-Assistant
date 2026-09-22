from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import json
import os
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
        BASE_DIR
        / "database"
        / "opportunities.db"
)

ANALYSIS_DIR = (
        BASE_DIR
        / "analysis_results"
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Placement Assistant API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REFRESH STATE
# ============================================================

refresh_state = {
    "running": False,
    "last_started": None,
    "last_completed": None,
    "message": "Not run yet",
    "error": None,
}


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# HELPERS
# ============================================================

def load_analysis(opportunity_id):
    """
    Load analysis JSON for a specific opportunity.
    """

    analysis_file = (
            ANALYSIS_DIR
            / f"opportunity_{opportunity_id}_analysis.json"
    )

    if not analysis_file.exists():
        return None

    try:
        with open(
                analysis_file,
                "r",
                encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return None


def get_fit_score(analysis):
    if not analysis:
        return None

    value = analysis.get("fit_score")

    if value is None:
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


def get_recommendation(analysis):
    if not analysis:
        return None

    recommendation = analysis.get(
        "recommendation"
    )

    if recommendation:
        return recommendation

    score = get_fit_score(analysis)

    if score is None:
        return None

    if score >= 70:
        return "STRONG APPLY"

    if score >= 40:
        return "CONSIDER"

    return "LOW MATCH"


def get_best_track(analysis):
    if not analysis:
        return None

    return analysis.get(
        "best_track"
    )


def serialize_opportunity(row):
    """
    Convert SQLite row + analysis JSON
    into the structure consumed by React.
    """

    opportunity = dict(row)

    opportunity_id = opportunity.get(
        "id"
    )

    analysis = load_analysis(
        opportunity_id
    )

    fit_score = get_fit_score(
        analysis
    )

    recommendation = get_recommendation(
        analysis
    )

    best_track = get_best_track(
        analysis
    )

    opportunity["analysis"] = analysis
    opportunity["fit_score"] = fit_score
    opportunity["recommendation"] = recommendation
    opportunity["best_track"] = best_track

    opportunity["resume_analyzed"] = (
        1 if analysis else 0
    )

    return opportunity


def get_all_opportunities():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM opportunities
            ORDER BY id DESC
            """
        )

        rows = cursor.fetchall()

        return [
            serialize_opportunity(row)
            for row in rows
        ]

    finally:
        connection.close()


# ============================================================
# REFRESH PIPELINE
# ============================================================

def run_refresh_pipeline():
    """
    Run the same pipeline used by the automated
    placement assistant:

        Gmail Reader
             ↓
        Decision Engine
             ↓
        Analysis Results
    """

    global refresh_state

    try:

        refresh_state["running"] = True

        refresh_state["last_started"] = (
            datetime.now().isoformat()
        )

        refresh_state["last_completed"] = None

        refresh_state["message"] = (
            "Checking Gmail for new opportunities..."
        )

        refresh_state["error"] = None


        # ====================================================
        # STEP 1: GMAIL READER
        # ====================================================

        reader_result = subprocess.run(
            [
                sys.executable,
                str(
                    BASE_DIR
                    / "gmail"
                    / "reader.py"
                ),
            ],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if reader_result.returncode != 0:

            error_output = (
                    reader_result.stderr
                    or reader_result.stdout
                    or "Unknown Gmail reader error."
            )

            raise RuntimeError(
                "Gmail Reader failed:\n"
                + error_output[-5000:]
            )


        refresh_state["message"] = (
            "Gmail checked. Running AI analysis..."
        )


        # ====================================================
        # STEP 2: DECISION ENGINE
        # ====================================================

        decision_result = subprocess.run(
            [
                sys.executable,
                str(
                    BASE_DIR
                    / "decision"
                    / "decision_engine.py"
                ),
                "--auto",
            ],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=900,
        )

        if decision_result.returncode != 0:

            error_output = (
                    decision_result.stderr
                    or decision_result.stdout
                    or "Unknown decision engine error."
            )

            raise RuntimeError(
                "Decision Engine failed:\n"
                + error_output[-5000:]
            )


        # ====================================================
        # SUCCESS
        # ====================================================

        refresh_state["message"] = (
            "Refresh completed successfully."
        )

        refresh_state["last_completed"] = (
            datetime.now().isoformat()
        )

        refresh_state["error"] = None


    except subprocess.TimeoutExpired as error:

        refresh_state["message"] = (
            "Refresh timed out."
        )

        refresh_state["error"] = (
            str(error)
        )


    except Exception as error:

        refresh_state["message"] = (
            "Refresh failed."
        )

        refresh_state["error"] = (
            str(error)
        )


    finally:

        refresh_state["running"] = False


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "AI Placement Assistant API",
        "status": "online",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "api": "online",
        "database": DATABASE_PATH.exists(),
        "analysis_results": ANALYSIS_DIR.exists(),
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
def dashboard():

    opportunities = (
        get_all_opportunities()
    )

    total_opportunities = (
        len(opportunities)
    )

    analyzed = [
        job
        for job in opportunities
        if job.get("fit_score") is not None
    ]

    strong_matches = [
        job
        for job in analyzed
        if job["fit_score"] >= 70
    ]

    consider_matches = [
        job
        for job in analyzed
        if 40 <= job["fit_score"] < 70
    ]

    low_matches = [
        job
        for job in analyzed
        if job["fit_score"] < 40
    ]

    return {
        "total_opportunities":
            total_opportunities,

        "analyzed_opportunities":
            len(analyzed),

        "strong_matches":
            len(strong_matches),

        "consider_matches":
            len(consider_matches),

        "low_matches":
            len(low_matches),

        "opportunities":
            opportunities,
    }


# ============================================================
# ALL OPPORTUNITIES
# ============================================================

@app.get("/api/opportunities")
def opportunities():

    return {
        "opportunities":
            get_all_opportunities()
    }


# ============================================================
# SINGLE OPPORTUNITY
# ============================================================

@app.get(
    "/api/opportunities/{opportunity_id}"
)
def opportunity(
        opportunity_id: int
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (opportunity_id,)
        )

        row = cursor.fetchone()

    finally:

        connection.close()


    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Opportunity not found."
        )


    return serialize_opportunity(
        row
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.get("/api/status")
def system_status():

    return {
        "api": True,
        "database": DATABASE_PATH.exists(),
        "analysis_results": ANALYSIS_DIR.exists(),
        "refresh_running":
            refresh_state["running"],
        "refresh_message":
            refresh_state["message"],
        "last_refresh_started":
            refresh_state["last_started"],
        "last_refresh_completed":
            refresh_state["last_completed"],
        "refresh_error":
            refresh_state["error"],
    }


# ============================================================
# START REFRESH
# ============================================================

@app.post("/api/refresh")
def refresh():

    if refresh_state["running"]:

        return {
            "status": "already_running",
            "message":
                refresh_state["message"],
        }


    thread = threading.Thread(
        target=run_refresh_pipeline,
        daemon=True,
    )

    thread.start()


    return {
        "status": "started",
        "message":
            "Checking Gmail for new opportunities...",
    }


# ============================================================
# REFRESH STATUS
# ============================================================

@app.get("/api/refresh/status")
def refresh_status():

    return {
        "running":
            refresh_state["running"],

        "last_started":
            refresh_state["last_started"],

        "last_completed":
            refresh_state["last_completed"],

        "message":
            refresh_state["message"],

        "error":
            refresh_state["error"],
    }