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
| `backend/app/schemas/medical_record.py` | Provenance enums, lab results, symptoms, conditions, medications & persistent memory schemas | `SourceType`, `RecordStatus`, `FactType`, `PatientContextFactCreate`, `LabResultCreate` | `tests/test_medical_schemas.py` |
| `backend/app/services/context_extractor.py` | Rule-based clinical fact extraction, ambiguity & family member detection | `CandidateFactExtractor`, `context_extractor` | `tests/test_context_memory.py` |
| `backend/app/api/deps.py` | Authentication & patient authorization dependencies | `get_current_user()`, `verify_patient_access()` | `tests/test_patients.py` |
| `backend/app/api/v1/router.py` | Master aggregator for all v1 API sub-routers | `api_router` | `tests/test_health.py` |
| `backend/app/api/v1/endpoints/health.py` | Operational health probe endpoint | `check_health()` | `tests/test_health.py` |
| `backend/app/api/v1/endpoints/auth.py` | Registration, login, and profile retrieval | `register_user()`, `login_user()`, `get_me()` | `tests/test_auth.py` |
| `backend/app/api/v1/endpoints/patients.py` | CRUD operations on patient profiles with ownership checks | `create_patient()`, `list_patients()`, `get_patient()`, `update_patient()` | `tests/test_patients.py` |
| `backend/app/api/v1/endpoints/context.py` | Conversational medical memory capture, review, confirm, update, soft-delete & preference toggles | `capture_context_facts()`, `confirm_context_fact()`, `update_memory_preference()` | `tests/test_context_memory.py` |
| `backend/app/api/v1/endpoints/medical_records.py` | Manual entry fallback for labs, symptoms, conditions, medications & unified history timeline | `create_lab_result()`, `create_symptom()`, `get_patient_history()` | `tests/test_medical_records.py` |
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

### 3.2 Module 2: Persistent Conversational Medical Memory & Structured History

#### 3.2.1 `backend/app/schemas/medical_record.py` (Provenance & Medical Data Models)
* **Purpose:** Defines foundational data contracts for all clinical measurements, symptoms, chronic conditions, medications, persistent context facts, and memory preferences with strict provenance metadata.
* **Key Classes & Enums:**
  * `SourceType(str, Enum)`: `manual`, `conversation`, `report_pdf_text`, `report_ocr`, `import`.
  * `RecordStatus(str, Enum)`: `patient_reported`, `extracted_unverified`, `user_confirmed`, `clinician_verified`, `superseded`, `deleted`.
  * `FactType(str, Enum)`: `symptom`, `medication`, `condition`, `allergy`, `lab_measurement`, `historical_event`.
  * `PatientContextFactCreate`, `PatientContextFactUpdate`, `PatientContextFactOut`: Persistent medical memory contracts.
  * `LabResultCreate`, `LabResultOut`: Laboratory measurement schemas with units, values, and reference ranges.
  * `SymptomCreate`, `ConditionCreate`, `MedicationCreate`: Structured patient-reported health models.
* **Viva Questions & Answers:**
  * **Q1: What is "provenance" in medical informatics and why does our system track `SourceType`?**
    * *Answer:* Provenance is the recorded history of where data originated and how it was obtained. In healthcare, a number entered manually or reported casually in conversation has a very different legal, diagnostic, and evidentiary weight than a measurement extracted directly from an official certified laboratory PDF. Tracking `SourceType` guarantees the system never presents patient-reported statements as certified laboratory findings.
  * **Q2: Why do we allow flexible dates (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) in `MedicationCreate` and `PatientContextFactCreate`?**
    * *Answer:* Patients frequently remember historical context partially (e.g., *"I was diagnosed with hypertension in 2018"* or *"started Metformin in June 2021"*). Forcing an exact day (`YYYY-MM-DD`) would force users to invent fictitious dates or cause validation rejections for valid clinical history.

---

#### 3.2.2 `backend/app/services/context_extractor.py` (Candidate Fact Extraction Engine)
* **Purpose:** Lightweight, rule-based clinical NLP engine that extracts candidate medical facts (medications, symptoms, conditions, allergies) from conversational user statements without depending on an LLM for structured fact identification.
* **Key Class:** `CandidateFactExtractor`, singleton instance `context_extractor`.
* **Safety Mechanisms:**
  * **Family Reference Detection (`FAMILY_INDICATORS`):** Detects third-party mentions (*"my father"*, *"my sister"*), flags `needs_confirmation=True`, degrades confidence to `0.40`, and injects a warning into `normalized_fact`.
  * **Uncertainty Markers (`UNCERTAINTY_INDICATORS`):** Detects speculative phrasing (*"maybe"*, *"I think"*, *"perhaps"*), sets `needs_confirmation=True`, and reduces confidence to `0.60`.
  * **Temporal Scoping:** Extracts years (`YYYY`) and calendar dates (`YYYY-MM-DD`).
* **Viva Questions & Answers:**
  * **Q1: Why use a deterministic rule-based extractor instead of calling an LLM for every sentence?**
    * *Answer:* Speed, cost, and predictability. Rule-based regex extraction runs in microseconds locally without API fees, network latency, or risk of LLM hallucinations. The LLM is reserved for conversational dialogue and plain-language summarization, while candidate fact extraction is deterministic and audit-traceable.
  * **Q2: What is the Section 20 Safety Boundary regarding family medical history?**
    * *Answer:* Medical systems must never mix family medical history with the patient's own direct diagnostic record. If a patient says *"My mother has diabetes"*, the system must never assign diabetes to the patient's active condition profile without explicit user confirmation and clear family-attribution labeling.

---

#### 3.2.3 `backend/app/api/v1/endpoints/context.py` (Conversational Medical Memory Endpoints)
* **Purpose:** REST API managing persistent conversational facts across sessions. Provides capture, review, user confirmation, correction (PATCH), soft deletion (DELETE), and memory preference toggling (`/memory-settings`).
* **Endpoints:**
  * `POST /{patient_id}/context/capture`: Extracts and saves candidate facts from statements.
  * `POST /{patient_id}/context`: Manual creation of context facts.
  * `GET /{patient_id}/context`: Lists active facts with filtering by `fact_type` and `needs_confirmation`.
  * `POST /{patient_id}/context/{fact_id}/confirm`: Promotes fact to `user_confirmed` with `needs_confirmation=False`.
  * `PATCH /{patient_id}/context/{fact_id}`: Allows patient to correct dates, confidence, or structured content.
  * `DELETE /{patient_id}/context/{fact_id}`: Soft-deletes fact (`record_status="deleted"`).
  * `GET` & `PATCH /{patient_id}/memory-settings`: Retrieves and toggles `memory_enabled`.
* **Viva Questions & Answers:**
  * **Q1: Why do we store structured facts instead of raw conversation chat logs?**
    * *Answer:* Storing uncurated chat logs introduces severe privacy liabilities, creates noisy context windows for RAG retrieval, and mixes casual remarks with clinical data. Storing atomic, structured facts (`patient_context_facts`) ensures deterministic retrieval, easy user correction, auditability, and right-to-erasure compliance.
  * **Q2: Why do we use soft deletion (`record_status="deleted"`) instead of `db.collection.delete_one()`?**
    * *Answer:* Medical data requires audit trails. Soft deletion immediately removes the item from all user queries and downstream RAG contexts while preserving provenance timestamps and preventing historical data corruption.

---

#### 3.2.4 `backend/app/api/v1/endpoints/medical_records.py` (Direct Entry & Unified History)
* **Purpose:** Provides direct manual entry fallback for labs, symptoms, conditions, and medications, as well as an aggregated chronological history timeline endpoint (`/{patient_id}/history`).
* **Endpoints:**
  * `POST` & `GET /{patient_id}/labs`: Record & list lab measurements.
  * `POST` & `GET /{patient_id}/symptoms`: Record & list symptoms.
  * `POST` & `GET /{patient_id}/conditions`: Record & list diagnosed conditions.
  * `POST` & `GET /{patient_id}/medications`: Record & list active medications.
  * `GET /{patient_id}/history`: Unified patient timeline aggregating all labs, symptoms, conditions, medications, and confirmed memory facts.
* **Viva Questions & Answers:**
  * **Q1: How does the system prevent cross-user data leakage and horizontal privilege escalation?**
    * *Answer:* Through the centralized FastAPI dependency `verify_patient_access()` in `app/api/deps.py`. It decodes the JWT token from the `Authorization` header, retrieves the user's `user_id`, queries the `patient_profiles` collection with both `_id=patient_id` AND `owner_user_id=user_id`. If no matching record is found, it immediately raises an `HTTP 404 Not Found` (rather than a 403 Forbidden), completely concealing whether the requested patient ID exists to prevent enumeration attacks.
  * **Q2: Why do we provide manual entry forms if we already have PDF extraction and natural language memory?**
    * *Answer:* Robustness and accessibility. Medical reports can have illegible handwriting, degraded scan quality, or unsupported formats. Providing structured manual entry ensures the patient or clinician always has a guaranteed fallback to record vital information regardless of OCR or parsing limitations.
* **Practical Code Challenge:**
  * *Question:* "How would you add a new category for `SURGICAL_PROCEDURE` to the system?"
  * *Answer:* 
    1. Add `SURGICAL_PROCEDURE = "surgical_procedure"` to `FactType` enum in `schemas/medical_record.py`.
    2. Add surgery regex patterns (e.g. `r"(?:underwent|had|surgery for)\s+([a-zA-Z\s]+)"`) to `context_extractor.py`.
    3. Add a dedicated MongoDB collection `surgeries` with an index on `patient_id` in `mongodb.py`.
    4. Mount `POST` and `GET /{patient_id}/surgeries` in `medical_records.py` and include them in the unified `/history` aggregator.

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

---

## 5. Module 2 Release-Gate Verification Summary

* **Execution Date:** 2026-10-18
* **Release Decision:** **PASS WITH LIMITATIONS** (Module 2 backend baseline 100% verified; Frontend deferred to later phase).
* **Test Metrics:**
  * Total Test Cases: 64 (23 new Module 2 tests added)
  * Passed: 64 (100%)
  * Failed / Blocked: 0
  * Overall Backend Code Coverage: **97%**
  * Module 2 Components Coverage: **100%** on `medical_record.py`, `context_extractor.py`, `context.py`, and `medical_records.py`.
* **Security & Business Logic Verifications:**
  * Cross-user patient isolation strictly verified across all context and medical record endpoints (HTTP 404 on unauthorized access).
  * Automatic ambiguity detection and family member reference guard verified.
  * Memory toggle disabling new fact captures verified.
  * Confirmation flow promoting unverified candidate facts to `user_confirmed` verified.
  * Soft-deletion and exclusion of deleted facts from active contexts verified.
  * Live MongoDB Atlas database connectivity verified (`ping: {'ok': 1}`).
* **Remaining Limitations:**
  * React frontend UI for memory review and history timeline deferred to frontend integration phase.


