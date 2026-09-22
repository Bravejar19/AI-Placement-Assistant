AI Placement Assistant

An AI-powered placement assistant that automatically processes placement emails, extracts job descriptions, analyzes opportunities against a candidate's resume, and presents personalized job-fit insights through a React dashboard.


OVERVIEW

The AI Placement Assistant automates the process of tracking placement and internship opportunities received through email.

Instead of manually reading every placement email and comparing each job description with a resume, the system:

- Monitors Gmail for placement-related emails
- Classifies incoming emails
- Identifies relevant job and internship opportunities
- Extracts Job Descriptions (JDs) from emails and attachments
- Parses important JD information
- Stores opportunities in a SQLite database
- Compares JDs with the candidate's resume using a local LLM
- Generates fit scores and recommendations
- Identifies matching and missing skills
- Suggests resume improvements
- Displays all results through a React-based dashboard


FEATURES

Automated Gmail Processing

The system processes placement emails and categorizes them as:

- New opportunities
- Potential opportunities
- Follow-up emails
- Forwarded emails
- Non-job-related emails


Job Description Extraction

The application extracts JDs from email content and supported attachments.

The JD processing pipeline identifies information such as:

- Company
- Job role
- Required skills
- Responsibilities
- Eligibility requirements
- Experience requirements
- Location
- Other relevant job information


AI Resume Analysis

The system uses a locally hosted LLM through Ollama to compare the candidate's resume with job descriptions.

The analysis provides:

- Fit score
- Recommendation
- Best-fit track
- Direct skill matches
- Relevant project/domain experience
- Transferable skills
- Missing or weak skills
- Resume improvement suggestions
- Explanation of the generated score

Running the model locally helps keep resume and job-related information on the local machine.


React Dashboard

The React dashboard provides:

- Placement opportunity overview
- Company and role information
- Fit scores
- AI recommendations
- Detailed opportunity analysis
- System status
- Manual Gmail refresh
- Opportunity-level analysis pages


Automated Processing

A macOS LaunchAgent periodically runs the Gmail reader and decision engine so that new placement opportunities can be processed automatically.


SYSTEM ARCHITECTURE

                    +------------------+
                    |      Gmail       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  Gmail Reader &  |
                    |    Classifier    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | JD Extraction &  |
                    |     Parsing      |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | SQLite Database  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Resume Analyzer  |
                    |   Local LLM      |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Decision Engine  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  FastAPI Backend |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  React Frontend  |
                    +------------------+


PROCESSING PIPELINE

Gmail
|
v
Email Classification
|
v
Job / JD Detection
|
v
Attachment Extraction
|
v
JD Parsing
|
v
SQLite Storage
|
v
Resume + JD Analysis
|
v
Decision Engine
|
v
FastAPI API
|
v
React Dashboard


TECH STACK

Backend

- Python
- FastAPI
- SQLite
- Gmail API
- Ollama
- Local LLM

Frontend

- React.js
- Vite
- Axios
- React Router
- Lucide React

AI / NLP

- Local LLM inference using Ollama
- Resume parsing
- Job description parsing
- Resume-to-JD matching

Automation

- macOS LaunchAgent


PROJECT STRUCTURE

AI-Placement-Assistant/
|
├── api/
│   └── server.py
|
├── brain/
│   └── resume_analyzer_final.py
|
├── classifier/
│   └── job_classifier.py
|
├── database/
│   └── opportunity_db.py
|
├── decision/
│   └── decision_engine.py
|
├── documents/
│   ├── extractor.py
│   ├── jd_parser.py
│   └── processor.py
|
├── gmail/
│   ├── reader.py
│   └── attachments.py
|
├── resume/
│   └── resume_parser.py
|
├── tracker/
│   └── application_tracker.py
|
├── frontend-react/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
|
├── requirements.txt
├── README.md
└── .gitignore


GETTING STARTED

Prerequisites

Make sure the following are installed:

- Python 3
- Node.js
- npm
- Ollama
- A Gmail account with Gmail API access


1. Clone the Repository

git clone https://github.com/Bravejar19/AI-Placement-Assistant.git
cd AI-Placement-Assistant


2. Create a Python Virtual Environment

python3 -m venv venv
source venv/bin/activate


3. Install Python Dependencies

pip install -r requirements.txt


4. Configure Gmail API

Configure Gmail API credentials and place the required credentials inside:

gmail/

Authentication files are intentionally excluded from GitHub.


5. Install and Configure Ollama

Install Ollama and pull the model used by the project:

ollama pull qwen3:4b-instruct-2507-q4_K_M

Make sure Ollama is running before performing AI resume analysis.


6. Install Frontend Dependencies

cd frontend-react
npm install


RUNNING THE APPLICATION

Start the FastAPI Backend

From the project root:

uvicorn api.server:app --reload

The backend will be available at:

http://localhost:8000


Start the React Frontend

Open another terminal:

cd frontend-react
npm run dev

The frontend will be available at:

http://localhost:5173


AI ANALYSIS

The project uses the following local Ollama model:

qwen3:4b-instruct-2507-q4_K_M

The model is used for resume-to-job-description analysis rather than for basic email classification.

The analysis pipeline evaluates:

Resume
+
Job Description
|
v
AI Analysis
|
v
Fit Score
|
v
Skill Matches
|
v
Missing Skills
|
v
Project / Domain Evidence
|
v
Resume Suggestions


DATABASE

The application uses SQLite to store placement opportunities.

The database tracks information such as:

- Opportunity ID
- Company
- Role
- Message ID
- Thread ID
- JD availability
- Eligibility information
- Parsed JD
- Analysis status
- Creation timestamp

The database itself is excluded from the GitHub repository because it contains locally collected placement data.


SECURITY AND PRIVACY

The repository intentionally excludes sensitive and generated files.

Examples include:

gmail/credentials.json
gmail/token.json
database/*.db
resume/*
analysis_results/*
attachments/*
logs/*
processed_documents/*
venv/
node_modules/

The .gitignore file prevents these files from being accidentally committed.

Resume and job-related AI analysis is performed locally using Ollama.


WHY I BUILT THIS

Placement opportunities are often distributed across a large number of emails, making it time-consuming to manually identify relevant roles and compare them with a resume.

This project was built to automate that workflow by combining:

Gmail automation + document processing + database management + local AI + web development

into a single placement management system.


FUTURE IMPROVEMENTS

Potential future improvements include:

- Application status tracking
- Deadline notifications
- Calendar integration
- Interview preparation based on job descriptions
- Additional email provider support
- Improved resume-to-JD matching
- Placement analytics
- Cloud deployment


AUTHOR

Ainessh Kumar

GitHub:
https://github.com/Bravejar19