# Glory — Job Search Platform

A production-ready backend for a job search platform built with **FastAPI**, **PostgreSQL**, and an **ML-powered resume-job matching engine**. Designed with real-world engineering practices: role-based access control, JWT authentication, session management, CI/CD pipeline, and a full test suite.

---

## Live Demo

> **Frontend:** `http://localhost:8000`
> **API Docs (Swagger):** `http://localhost:8000/docs`

"Glory is intentionally backend-focused — built to demonstrate production-grade API design, authentication architecture, database modeling, and ML integration rather than UI development. The frontend provides a working interface for the core user journey; the full depth of the platform is best explored through the interactive API documentation at /docs."

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Framework | FastAPI | Async-ready, auto Swagger docs, Pydantic validation |
| Database | PostgreSQL + SQLAlchemy | Relational integrity, ORM for clean query patterns |
| Auth | JWT + passlib | Stateless auth, bcrypt hashing, role enforcement |
| ML | sentence-transformers | Semantic embeddings for resume-JD similarity scoring |
| Testing | pytest + SQLite | Isolated test DB, no real data touched |
| Deployment | Uvicorn | Production ASGI server |

---

## Features

### Authentication & Authorization
- JWT token-based authentication
- Three roles: **Jobseeker**, **Employer**, **Admin**
- Role-based route protection — employers can't apply, jobseekers can't post jobs, only admins can access all data
- Secure password hashing with passlib sha256_crypt

### Job Management
- Employers can create, update, and delete their own job postings
- Jobseekers can browse all listings and apply
- Employers see all applicants per job with **Accept / Reject** controls
- Application status tracked per user

### Resume Management
- Jobseekers create and manage a structured resume (role, experience, skills)
- Full CRUD with ownership enforcement — users can only edit their own resume

### ML Resume–Job Match Scoring
- Paste any resume and job description to get an instant compatibility score
- Uses `sentence-transformers` (`all-MiniLM-L6-v2`) for semantic similarity
- Skill keyword extraction across 90+ tech skills with **synonym normalization** — "ML" and "machine learning" treated as the same skill, "k8s" maps to "kubernetes", etc.
- Blended scoring: 50% semantic similarity + 50% skill keyword overlap for realistic, human-readable results
- Returns matched skills, missing skills, and a Strong / Good / Weak rating

### Frontend
- Dark-themed single-page UI for each core flow — no React, plain HTML/CSS/JS
- Live job search with title, company, and location filtering
- Role-aware dashboard: jobseekers see resume + applications, employers see postings + applicants
- Fully connected to backend API via fetch — no page reloads

---P.S "Glory is a backend-first platform. The frontend demonstrates the core user journey — register, browse jobs, apply, and run ML resume matching. The complete API with all CRUD operations, admin controls, and role-based access is documented and fully interactive at /docs."

## Architecture

```
Glory/
├── app/
│   ├── main.py          # All API routes and endpoint logic
│   ├── models.py        # SQLAlchemy ORM models + Pydantic schemas
│   ├── Database.py      # DB engine and session management
│   ├── security.py      # JWT creation, password hashing, auth dependencies
│   ├── match.py         # ML match endpoint, skill extraction, score calibration
│   └── static/          # Frontend HTML pages
│       ├── index.html   # Login / Register
│       ├── jobs.html    # Job listings with search and filter
│       ├── dashboard.html # Resume manager + applications tracker
│       └── match.html   # ML resume-job match UI
├── tests/
│   ├── conftest.py      # Test DB setup (SQLite), mock psycopg2 and sentence-transformers
│   ├── test_main.py     # Auth, registration, protected route tests
│   └── test_match.py   # ML scoring unit tests
├── .env.example         # Environment variable template
├── requirements.txt
└── pytest.ini
```

---

## API Endpoints

### Users
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/users` | None | Register new user |
| POST | `/login` | None | Login, returns JWT token |
| GET | `/users/me` | Any | Get current user profile |
| GET | `/users` | Admin | Get all users |
| PUT | `/users/{id}` | Owner/Admin | Update user |
| DELETE | `/users/{id}` | Admin | Delete user |

### Jobs
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/jobs` | None | Browse all job listings |
| POST | `/jobs` | Employer | Post a new job |
| PUT | `/jobs/{id}` | Owner/Admin | Update job details |
| DELETE | `/jobs/{id}` | Owner/Admin | Delete job posting |

### Resume
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/resume` | Jobseeker | Create resume |
| GET | `/resume/me` | Jobseeker | Get own resume |
| PUT | `/resume/{id}` | Owner/Admin | Update resume |
| DELETE | `/resume/{id}` | Owner/Admin | Delete resume |

### Applications
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/applications` | Jobseeker | Apply to a job |
| GET | `/applications/me` | Jobseeker | View own applications |
| GET | `/applications/my-jobs` | Employer | View applicants for own jobs |
| PUT | `/applications/{id}` | Employer/Admin | Accept or reject applicant |

### ML
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/match` | None | Score resume vs job description |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/glory.git
cd glory/Glory
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials and a secret key:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/glory
SECRET_KEY=your-long-random-secret-key
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000` in your browser.

---

## Running Tests

Tests use an isolated SQLite database — your real PostgreSQL data is never touched.

```bash
pytest tests/ -v
```

### Test Coverage

| Test | What it verifies |
|---|---|
| `test_register_user_success` | Registration returns correct user data, password never exposed |
| `test_register_duplicate_email` | Duplicate email returns 400 |
| `test_empty_login` | Empty credentials rejected with 400/422 |
| `test_wrong_credentials` | Wrong password rejected with 400 |
| `test_protected_route_requires_valid_token` | Unauthenticated requests get 401 |
| `test_extract_skills_recognizes_common_skills` | Skill extractor identifies Python, FastAPI, SQLAlchemy |
| `test_calibrate_score_is_clamped_to_expected_range` | Score always within 0–100 |
| `test_match_quality` | Matching resume scores higher than mismatched resume |

---

## Design Decisions

**Why FastAPI over Flask** — Native async support, automatic OpenAPI/Swagger generation, and Pydantic validation at the schema level. Flask requires separate libraries for all of this.

**Why JWT over sessions** — Glory's frontend and API are decoupled. Stateless JWT fits a platform where multiple clients (web, mobile, third-party) may consume the same API without sharing server-side session state.

**Why PostgreSQL over SQLite** — Production-grade relational integrity, concurrent write handling, and the ability to scale horizontally. SQLite is used only in the test environment for isolation.

**Why sentence-transformers for matching** — Simple keyword matching misses synonyms and context. Sentence embeddings capture semantic meaning — a resume mentioning "ML" correctly matches a JD requiring "machine learning." The blended scoring (semantic + keyword overlap) gives results that feel intuitively correct to humans.

**Why SQLite for tests** — Tests should never touch production data. SQLite requires zero setup, spins up in memory, and is dropped after every test run. psycopg2 is mocked to prevent import failures in CI environments without PostgreSQL.

---

## Author

**Rakshit Bhardwaj** — Third year CS undergraduate | 
[GitHub](https://github.com/rakshitbhardwaj2986) |
 [LinkedIn](https://www.linkedin.com/in/rakshit-bhardwaj-b49b61325/)
