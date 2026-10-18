# MediReport Analyzer — Project Learning Guide & Viva Preparation Handbook

This document is your complete companion guide for understanding every file, function, architecture decision, and security rule in the **MediReport Analyzer** project. It is specifically designed to prepare you for your final-year project viva, code reviews, and technical interviews.

---

## 1. Project Overview & Architecture

### What is MediReport Analyzer?
MediReport Analyzer is an AI-assisted medical report understanding, comparison, and persistent medical memory system. It allows users to:
1. Upload medical laboratory reports (PDFs, scanned images).
2. Enter or state medical history and symptoms naturally in conversation.
3. Store verified structured measurements and patient-reported context persistently across sessions.
4. Deterministically compare laboratory results across different dates to track historical health trends.
5. Generate evidence-grounded, plain-language summaries and explanations in preferred languages using Google Gemini API and LangChain.

### Architectural Core Principles
1. **Three Storage Layers:**
   * **Private Storage Disk:** Raw uploaded files (PDFs, images) are stored untouched for legal, audit, and verification integrity.
   * **MongoDB (Authoritative Truth):** Stores structured medical numbers (e.g., `Glucose = 140 mg/dL`), symptoms, medications, dates, user profiles, persistent context facts, and audit records.
   * **ChromaDB (Semantic Search Index):** Stores text chunk embeddings for fast contextual retrieval. ChromaDB is **never** used as the source of truth for numeric values.
2. **Deterministic Calculations vs. AI Explanations:**
   * Pure Python functions calculate all absolute changes, percentage differences, and unit compatibility checks.
   * The LLM (Gemini API) is strictly prohibited from doing math or inventing reference ranges; it is only used for plain-language communication grounded in verified structured data.
3. **Medical Memory vs. Raw Chat Logs:**
   * The system does **not** store arbitrary chat logs as permanent medical records.
   * Only structured candidate facts (e.g., *"started Metformin in June"*) are extracted, linked to a specific patient profile, and tagged with provenance (`source_type=conversation`, `record_status=patient_reported`).
4. **Zero-Trust Patient Isolation:**
   * Every query and mutation checks ownership server-side.
   * Accessing another user's patient profile returns `HTTP 404 Not Found` to prevent profile enumeration and data leakage.

---

## 2. File-by-File Master Index

| File Path | Purpose | Key Functions / Classes | Test File |
| :--- | :--- | :--- | :--- |
| `backend/app/main.py` | FastAPI application entrypoint, CORS, and lifecycle | `create_application()`, `lifespan()` | `tests/test_health.py` |
| `backend/app/core/config.py` | Central typed configuration with Pydantic BaseSettings | `Settings` | N/A (loaded by all) |
| `backend/app/core/security.py` | Bcrypt password hashing & JWT token encoding/decoding | `hash_password()`, `verify_password()`, `create_access_token()`, `decode_access_token()` | `tests/test_auth.py` |
| `backend/app/database/mongodb.py` | Async MongoDB client manager & index initialization | `MongoManager`, `get_database()` | `tests/conftest.py` |
| `backend/app/schemas/user.py` | Pydantic validation schemas for user accounts & tokens | `UserCreate`, `UserLogin`, `UserOut`, `Token` | `tests/test_auth.py` |
| `backend/app/schemas/patient.py` | Pydantic validation schemas for patient profiles | `PatientProfileCreate`, `PatientProfileUpdate`, `PatientProfileOut` | `tests/test_patients.py` |
| `backend/app/api/deps.py` | Authentication & patient authorization dependencies | `get_current_user()`, `verify_patient_access()` | `tests/test_patients.py` |
| `backend/app/api/v1/router.py` | Master aggregator for all v1 API sub-routers | `api_router` | `tests/test_health.py` |
| `backend/app/api/v1/endpoints/health.py` | Operational health probe endpoint | `check_health()` | `tests/test_health.py` |
| `backend/app/api/v1/endpoints/auth.py` | Registration, login, and profile retrieval | `register_user()`, `login_user()`, `get_me()` | `tests/test_auth.py` |
| `backend/app/api/v1/endpoints/patients.py` | CRUD operations on patient profiles with ownership checks | `create_patient()`, `list_patients()`, `get_patient()`, `update_patient()` | `tests/test_patients.py` |
| `backend/tests/conftest.py` | Test fixtures with in-memory Mongo mock | `client()`, `test_db()`, `mock_mongo_client()` | Used by all tests |

---

## 3. Detailed File Walkthroughs & Viva Preparation

### 3.1 Module 1: `backend/app/core/config.py` (Central Configuration & Settings)

* **Purpose:** Single source of truth for all runtime settings and environment variables. Reads from `.env` and validates data types before the application boots.
* **Key Class:** `Settings(BaseSettings)`
* **Dependencies:** `pathlib`, `pydantic_settings.BaseSettings`, `pydantic_settings.SettingsConfigDict`.
* **Connected Files:**
  * `app/main.py`: Reads `PROJECT_NAME`, `VERSION`, `API_V1_STR`, `CORS_ORIGINS`, `resolved_storage_path`.
  * `app/database/mongodb.py`: Reads `MONGODB_URI` and `MONGODB_DB_NAME`.
  * `app/core/security.py`: Reads `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES`.
  * `app/api/v1/endpoints/health.py`: Reads `PROJECT_NAME`, `VERSION`, `ENVIRONMENT`.
* **Execution Flow:**
  1. Python imports `from app.core.config import settings`.
  2. Pydantic instantiates `Settings()`.
  3. `SettingsConfigDict` opens `.env`.
  4. Variables are parsed and type-checked (e.g. `DEBUG` string `"true"` coerced to `bool True`).
  5. Fallback defaults are applied if any optional variable is omitted in `.env`.
  6. The frozen singleton `settings` instance is cached and used application-wide.
* **Viva Questions & Answers:**
  * **Q1: Why do we use Pydantic `BaseSettings` instead of `os.environ.get()`?**
    * *Answer:* `os.environ.get()` returns unvalidated raw strings and fails silently if a variable is missing or mistyped. `BaseSettings` automatically parses, type-checks (strings to ints, booleans, or lists), and crashes early on startup if critical configuration is malformed, preventing runtime errors.
  * **Q2: What is the 12-Factor App methodology regarding configuration?**
    * *Answer:* It states that configuration should be strictly separated from code. Secrets, database URLs, and port numbers should be stored in environment variables, allowing the same codebase to run in development, testing, and production without code modifications.
  * **Q3: What is a Singleton pattern and how is it used in `config.py`?**
    * *Answer:* A singleton ensures a class has only one active instance. In `config.py`, we instantiate `settings = Settings()` once at module load. Other files import `settings` rather than re-reading the `.env` file from disk repeatedly.
  * **Q4: How does `resolved_storage_path` work?**
    * *Answer:* It is a Python `@property` that resolves relative paths (like `./storage/uploads`) into an absolute OS path and calls `mkdir(parents=True, exist_ok=True)` so the target folder is guaranteed to exist before file writes occur.
  * **Q5: How does Pydantic handle case sensitivity in `.env`?**
    * *Answer:* Via `SettingsConfigDict(case_sensitive=True)`. This enforces that environment variable names in `.env` must exactly match the casing defined in the Python class (e.g., `MONGODB_URI`).
* **Practical Code Challenge:**
  * *Question:* "How would you add a new configuration setting for an external SMTP email server port with a default of 587?"
  * *Answer:* Add `SMTP_PORT: int = 587` to the `Settings` class. Pydantic will ensure any value provided in `.env` is parsed as an integer.

---

## 4. Module 1 Release-Gate Verification Summary

* **Execution Date:** 2026-10-18
* **Release Decision:** **PASS WITH LIMITATIONS** (Backend baseline 100% verified; Frontend deferred to later phase).
* **Test Metrics:**
  * Total Test Cases: 41
  * Passed: 41 (100%)
  * Failed / Blocked: 0
  * Overall Backend Code Coverage: 92%
  * Core Business Logic & Security Coverage: 100%
* **Security Verifications:**
  * Strict cross-user patient isolation verified (User B receives HTTP 404 on User A's patient records).
  * Bcrypt salted password hashing and HMAC-SHA256 JWT tokens verified.
  * Live MongoDB Atlas connectivity verified (`ping: {'ok': 1}`).
  * Git protection confirmed via root `.gitignore` (`.env`, `*.env`, `backend/storage/uploads/*`).
* **Remaining Limitations:**
  * React frontend application not yet built (`frontend/` directory is currently empty).

