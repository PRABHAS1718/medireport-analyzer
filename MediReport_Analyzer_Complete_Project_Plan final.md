# MediReport Analyzer

## Complete Project Planning, Requirements, Architecture, Development Roadmap, and Validation Plan

**Document type:** Project master plan and implementation guide\
**Project title:** MediReport Analyzer: AI-Powered Medical Report
Understanding and Comparison System\
**Status:** Planning baseline --- ready to begin Phase 1 after reviewing
open decisions\
**Primary stack:** React.js, Python, FastAPI, MongoDB, PyMuPDF, OCR,
Sentence Transformers, ChromaDB, LangChain, Gemini API, and RAG\
**Target product:** A multilingual application that stores a patient's
medical history, analyzes uploaded and manually entered data, compares
current and historical findings, and produces clear, evidence-grounded
explanations.

------------------------------------------------------------------------

## Table of Contents

1.  Executive Summary
2.  Vision, Objectives, and Success Criteria
3.  Scope and Boundaries
4.  Users and Main Use Cases
5.  Functional Requirements
6.  Non-Functional Requirements
7.  User Workflows
8.  System Architecture
9.  Technology Stack and Responsibilities
10. Data Storage Strategy
11. MongoDB Data Model
12. Data Relationships and Integrity
13. Document Ingestion and Processing Pipeline
14. Chunking, Embeddings, and Vector Retrieval
15. Multilingual NLP Architecture
16. Comparison and Historical Analysis Engine
17. AI Explanation and RAG Design
18. Clinical Risk Assessment and Safety Boundaries
19. User Experience and Screens
20. API Design
21. Security, Privacy, Retention, and Deletion
22. Testing and Validation Plan
23. Observability, Reliability, and Scalability
24. Development Phases and Step-by-Step Tasks
25. Proposed Project Structure
26. Definition of Done and Release Gates
27. Risks, Dependencies, and Mitigations
28. Features to Defer
29. Open Decisions
30. Final Build Checklist
31. Glossary

------------------------------------------------------------------------

# 1. Executive Summary

MediReport Analyzer is an AI-assisted medical report understanding and
comparison system. Users can upload medical reports and can also tell
the system relevant medical information naturally in a conversation;
manual forms remain available as a fallback, not the only way to add
history. The system extracts candidate facts from reports and user
statements, stores them in a persistent, source-traceable patient
history, retrieves relevant history when a later question or report
needs it, compares new results with previous records, and presents a
concise summary and detailed explanation in a supported user-selected
language. Ambiguous or high-impact facts must be confirmed before being
treated as established patient context.

The application will maintain distinct representations of medical
information:

1.  **Original documents:** The uploaded files, retained in controlled
    file storage.
2.  **Structured records:** Measurements, symptoms, conditions,
    medications, dates, units, and provenance stored in MongoDB.
3.  **Searchable text chunks:** Extracted report passages and metadata
    indexed in ChromaDB for semantic retrieval.
4.  **Derived outputs:** Comparisons, summaries, and analyses stored
    with references to their inputs, sources, and processing versions.

The vector database is not the authoritative store for medical
measurements. Exact comparisons must use structured records and
deterministic Python logic. RAG and an LLM can explain findings using
verified data and trusted references, but an LLM must not invent
clinical facts, alter measurements, or manufacture disease-risk
percentages.

The initial scope includes laboratory results, symptoms, medical
history, medications, historical comparisons, a quick report summary,
detailed explanations, and multilingual support for Indian languages
delivered incrementally. The first disease-risk model has deliberately
not been selected. Risk estimates will be exposed only when an
appropriate method has been selected and validated for a defined
clinical purpose and population.

Chest X-ray analysis is a separate optional module. If retained, it
requires its own dataset, model validation, intended-use statement, and
acceptance criteria.

## 1.1 Product principles

-   **Longitudinal record and useful memory:** A new report or a clearly
    attributed medical fact adds to the authorized patient's history; it
    does not silently overwrite older measurements. Relevant saved facts
    are retrieved in future interactions when useful.
-   **Memory is structured, not indiscriminate chat logging:** Store
    relevant medical facts with source, date, confidence/verification
    status, and patient association. Do not treat every chat message or
    an AI-generated inference as a medical fact.
-   **Source traceability:** Important results can be traced to a source
    document, page or location, manual entry, or validated reference.
-   **Separation of facts and interpretation:** Original observations,
    extracted entities, user corrections, AI explanations, and model
    predictions remain distinguishable.
-   **Numerical correctness:** Matching, unit validation, and change
    calculations are deterministic and testable.
-   **Multilingual consistency:** Changing the output language must not
    change the underlying medical values or clinical meaning.
-   **Privacy by design:** Patient records are private by default, and
    every protected operation checks authorization.
-   **Evidence before claims:** Generated explanations must be grounded
    in input records and relevant trusted sources.
-   **Measured quality:** Extraction, retrieval, language quality,
    security, and any clinical model are evaluated separately.

------------------------------------------------------------------------

# 2. Vision, Objectives, and Success Criteria

## 2.1 Vision

Help users understand what their medical reports say, what changed over
time, which findings may need attention, and what remains
uncertain---using clear language and a supported preferred language.

## 2.2 Primary objectives

1.  Accept both manual medical data and document uploads.
2.  Extract and validate structured data from supported medical reports.
3.  Store patient history persistently for future comparison, subject to
    user deletion and applicable obligations.
4.  Compare compatible results across multiple dates.
5.  Generate a quick summary and a detailed report explanation in the
    user's selected language.
6.  Use retrieval-augmented generation for source-grounded explanations.
7.  Provide symptom and medication context without confusing
    patient-reported information with confirmed clinical facts.
8.  Establish a testable foundation for future disease-risk models.
9.  Support secure operation, auditability, recoverable processing, and
    incremental scale.

## 2.3 Success criteria

Success is not defined by how many AI features are present. The project
succeeds when:

-   Extracted values can be reviewed and corrected.
-   Numerical comparisons match expected results on a reviewed test
    suite.
-   Historical records are linked to the correct patient.
-   Users can trace important summary claims to evidence.
-   The quick summary is understandable and faithful to the source.
-   Supported languages pass defined per-language evaluation.
-   Unauthorized access tests fail safely.
-   Data deletion follows the documented lifecycle across active storage
    and derived indexes.
-   Failures, retries, latency, and AI usage can be monitored.
-   No unvalidated disease-risk percentage is presented as a clinical
    fact.

------------------------------------------------------------------------

# 3. Scope and Boundaries

## 3.1 In scope for the planned product

-   User authentication and authorization.
-   Patient profiles and relevant demographics.
-   Natural-language capture of relevant patient-provided information
    during ordinary interactions, with persistent memory across
    sessions.
-   Automatic extraction and storage of report facts after uploads, with
    uncertain extracted values queued for review.
-   Manual entry of laboratory measurements, symptoms, medical history,
    and medications as an optional fallback and correction method.
-   PDF and image upload for supported document types.
-   Digital PDF text extraction and OCR for supported scanned documents.
-   Structured medical entity extraction and user verification.
-   Original document storage and persistent medical history.
-   Structure-aware text chunking and semantic retrieval.
-   Historical report and measurement comparisons.
-   Abnormal finding checks using appropriate reference ranges.
-   Quick summary, detailed analysis, and simple-language explanations.
-   Multilingual user interface and generated explanations for evaluated
    languages.
-   RAG with source references and uncertainty handling.
-   Downloadable summaries and analysis history.
-   Security, audit, deletion, testing, monitoring, and deployment.
-   Research and evaluation of suitable condition-specific risk methods
    for a future release.

## 3.2 Out of scope for the initial release

-   Claiming to diagnose any disease from arbitrary reports.
-   Generating disease probabilities using an LLM's self-reported
    confidence.
-   Recommending or changing medication doses autonomously.
-   Replacing a qualified clinician or emergency services.
-   Claiming that every Indian language and every report layout is
    supported from day one.
-   Broad chest X-ray diagnosis without an independently evaluated model
    and dataset.
-   Autonomous emergency decisions based only on generated
    interpretations.
-   Microservices, Kubernetes, or distributed infrastructure without a
    measured need.

## 3.3 Clinical boundary

The application is a medical-information and decision-support system. It
can explain report findings and may later estimate risk for specifically
defined conditions if suitable methods are validated. A risk estimate is
not the same as a confirmed diagnosis. Clinical claims, intended use,
applicable regulations, and required professional review must be
assessed before real-world deployment.

------------------------------------------------------------------------

# 4. Users and Main Use Cases

## 4.1 Primary users

-   **Patient/user:** Uploads reports, enters medical information,
    reviews extracted data, sees comparisons, and chooses an explanation
    language.
-   **Authorized caregiver or family member:** Optional later
    capability; access requires explicit authorization and suitable
    permissions.
-   **Clinician or reviewer:** Optional later capability for reviewing
    selected records or shared summaries.
-   **Administrator/operator:** Maintains service health and processing
    status without unrestricted access to medical content by default.

## 4.2 Main use cases

### Use case A: Upload a new report

1.  User authenticates and selects a patient profile.
2.  User uploads a supported PDF or image.
3.  Backend validates file type, size, and safety checks.
4.  The file is stored privately and a processing record is created.
5.  Text is extracted and the document language and type are identified.
6.  Medical entities are extracted and validated.
7.  Uncertain values are shown for user review.
8.  Structured data is stored with provenance.
9.  Chunks and embeddings are created for retrieval.
10. The report becomes available for comparison after required
    processing steps finish.

### Use case B: Tell the system relevant medical information naturally

1.  User is interacting with the system about an explicitly selected
    patient profile and says something relevant, for example, "I started
    taking medicine X last month" or "My previous test was done in
    June."
2.  The backend identifies candidate facts and the subject they refer
    to; it does not assume that every statement is about the selected
    patient.
3.  A validation step extracts only supported facts and captures the
    source interaction, date/time, any stated effective date, and
    confidence/verification status.
4.  Clear, low-ambiguity patient-reported facts may be saved as
    `source_type=conversation` / `record_status=patient_reported`, when
    the user has enabled persistent medical memory and the selected
    profile attribution is clear. Ambiguous, conflicting, or high-impact
    facts are shown to the user for confirmation before becoming active
    context.
5.  The UI tells the user what was saved and lets them review, correct,
    or delete it. A saved fact is not silently promoted to a clinician-
    verified diagnosis or confirmed measurement.
6.  In later interactions, the backend retrieves relevant saved facts
    for the selected patient and includes them in the context used to
    answer questions or compare new reports.
7.  The system uses only relevant, authorized facts and displays their
    origin when they materially affect an answer.

### Use case B2: Enter information manually when needed

1.  User selects a patient profile and enters a measurement or history
    item in a form, or uses a form to correct a saved fact.
2.  The backend validates the input and preserves the source and
    verification status.
3.  The record is stored with `source_type=manual`.
4.  The user can later compare it with compatible measurements or use it
    as relevant patient context.

### Use case C: Compare reports

1.  User chooses the current report and one or more previous reports, or
    requests a historical comparison.
2.  Backend confirms that all records belong to the same authorized
    patient.
3.  Comparison engine matches compatible tests and validates units and
    context.
4.  It calculates changes and identifies missing, new, or incompatible
    values.
5.  Results are saved with input record IDs and algorithm version.
6.  The UI displays a comparison table and relevant trends.

### Use case D: Understand a report

1.  User selects the preferred supported language.
2.  System uses verified structured findings and source passages.
3.  Analysis workflow retrieves relevant trusted references as needed.
4.  A summary is generated and validated.
5.  User sees the quick summary first, with expandable detailed findings
    and source links.

### Use case E: Ask a question with persistent context

1.  User asks a question about authorized records or adds new medical
    information in natural language.
2.  Backend identifies whether the message contains a question, a
    candidate new fact, or both.
3.  For a question, backend retrieves relevant structured history, saved
    patient-context facts, report passages, and approved reference
    material as appropriate.
4.  Retrieved context is checked for patient ownership, relevance, date,
    source, and verification status.
5.  AI generates an answer grounded in that evidence. It must
    distinguish patient-reported information from extracted/verified
    report findings.
6.  The answer shows relevant source references, notes important
    uncertainty, and says when information is insufficient.
7.  If a new fact was captured, the UI indicates what was saved and
    provides review/correction controls.

### Use case F: Delete data

1.  User requests deletion of a patient profile or account.
2.  Backend verifies authorization and explains relevant consequences.
3.  Deletion workflow removes or schedules removal of associated files,
    structured records, chunks, vectors, derived outputs, caches, and
    other in-scope copies.
4.  The operation records its status.
5.  Backup expiry and any legally required retention exceptions follow a
    documented policy.

------------------------------------------------------------------------

# 5. Functional Requirements

Priority labels: - **P0:** Required for the first reliable release. -
**P1:** Important follow-on capability. - **P2:** Later expansion or
optional module.

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-01                   Secure user             P0
                          registration,           
                          authentication, and     
                          session management      

  FR-02                   Patient profile         P0
                          creation and            
                          authorization           

  FR-03                   Manual entry of         P0
                          laboratory values and   
                          supported medical       
                          history                 

  FR-04                   Upload supported PDFs   P0
                          and images              

  FR-05                   Validate files and      P0
                          handle unsupported,     
                          corrupted, oversized,   
                          or unsafe files         

  FR-06                   Extract text from       P0
                          digital PDFs and        
                          supported scanned       
                          documents               

  FR-07                   Extract test names,     P0
                          values, units, dates,   
                          reference ranges, and   
                          flags where available   

  FR-08                   Preserve source text    P0
                          and source location for 
                          extracted entities      

  FR-09                   Show uncertain          P0
                          extracted data for      
                          review and correction   

  FR-10                   Store original          P0
                          documents in controlled 
                          file storage            

  FR-11                   Store structured        P0
                          medical records and     
                          history in MongoDB      

  FR-12                   Generate and store      P0
                          semantic chunks and     
                          embeddings for          
                          retrieval               

  FR-13                   Compare compatible      P0
                          laboratory measurements 
                          across dates            

  FR-14                   Identify new, missing,  P0
                          changed, or             
                          incompatible            
                          measurements            

  FR-15                   Display historical      P0
                          trends and report       
                          summaries               

  FR-16                   Generate quick          P0
                          summaries in the user's 
                          selected supported      
                          language                

  FR-17                   Provide detailed        P0
                          explanations and source 
                          references              

  FR-18                   Record symptoms,        P0/P1 depending on
                          medical conditions, and implementation slice
                          medication history with 
                          provenance              

  FR-19                   Use patient context in  P0
                          explanations without    
                          treating unverified     
                          claims as confirmed     

  FR-20                   Save                    P0
                          analysis/comparison     
                          input references and    
                          processing versions     

  FR-21                   Allow data correction,  P0
                          export, and deletion    
                          under defined           
                          permissions             

  FR-22                   Support Indian          P0 architecture;
                          languages               language rollout
                          incrementally, based on incremental
                          tested capability       

  FR-23                   Provide secure,         P2
                          auditable sharing with  
                          caregivers or           
                          clinicians              

  FR-24                   Implement               Conditional/P2
                          condition-specific risk 
                          estimation after method 
                          selection and           
                          validation              

  FR-25                   Add a separate chest    P2
                          X-ray analysis module   
                          if justified and        
                          validated               

  FR-26                   Provide voice-based     P2
                          multilingual            
                          interaction             

  FR-27                   Provide operational     P1
                          dashboards for quality, 
                          processing, cost, and   
                          latency                 

  FR-28                   Extract and persist     P0
                          relevant patient facts  
                          from natural-language   
                          interactions with       
                          source date, and status 

  FR-29                   Retrieve relevant saved P0
                          patient context in      
                          later interactions,     
                          with patient scoping,   
                          review, correction, and 
                          deletion controls       

  FR-30                   Let users view,         P0
                          correct, and delete     
                          saved context facts and 
                          control persistent      
                          medical memory          
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 6. Non-Functional Requirements

  ---------------------------------------------------------------------
  Area                               Requirement
  ---------------------------------- ----------------------------------
  Security                           Enforce authentication,
                                     authorization, least privilege,
                                     secure transport, secret
                                     management, and appropriate
                                     encryption at rest.

  Privacy                            Minimize personal data, document
                                     consent, limit access, define
                                     retention, and implement deletion
                                     workflows.

  Accuracy                           Never silently treat uncertain OCR
                                     output as verified data.

  Consistency                        Preserve original measurements and
                                     units. Reject or flag incompatible
                                     comparisons.

  Traceability                       Link analysis claims to input
                                     records, source locations, trusted
                                     references, and relevant
                                     model/rule versions.

  Reliability                        Support job status, controlled
                                     retries, idempotent processing,
                                     failure reporting, and recovery.

  Performance                        Measure upload, extraction,
                                     retrieval, and analysis latency
                                     against defined workload targets.

  Scalability                        Scale API requests, file
                                     processing, OCR, embeddings, and
                                     AI calls independently when
                                     justified.

  Maintainability                    Use modular code, validation
                                     schemas, automated tests,
                                     versioned APIs, and documented
                                     configuration.

  Multilingual quality               Evaluate OCR, entity extraction,
                                     retrieval, and generation
                                     separately for every released
                                     language.

  Clinical safety                    Do not fabricate diagnoses,
                                     probabilities, sources, or
                                     treatment instructions.

  Accessibility                      Use clear wording, readable
                                     contrast, keyboard support, and
                                     responsive layouts.

  Cost control                       Track model calls, tokens,
                                     processing costs, and failures;
                                     use quotas and limits where
                                     appropriate.

  Reproducibility                    Save enough input/version metadata
                                     to explain and, where feasible,
                                     reproduce a result.
  ---------------------------------------------------------------------

## 6.1 Proposed quality targets

The team should approve numeric thresholds after a baseline evaluation.
These are targets to define, not measured achievements:

-   Deterministic comparison tests: 100% agreement with expected outputs
    in the defined test suite.
-   Authorization tests: zero unauthorized access in the defined
    cross-user and cross-patient suite.
-   Unit handling: no silent comparison of incompatible units or test
    identities.
-   Extraction: report field-level precision and recall by document and
    language group.
-   Retrieval: measure recall at relevant top-k values and source
    attribution correctness.
-   Generation: measure factual consistency and unsupported claims;
    define blocking thresholds for critical errors.
-   Multilingual quality: define and meet thresholds separately for each
    supported language.
-   Risk prediction: no percentage exposed until the method passes its
    predefined validation and review criteria.

------------------------------------------------------------------------

# 7. User Workflows

## 7.1 New report workflow

1.  User logs in.
2.  User selects an authorized patient profile.
3.  User uploads a report.
4.  Backend validates file type, size, and access.
5.  Original file is stored privately.
6.  Report metadata and processing job are created.
7.  Extraction worker reads text and layout.
8.  Language and document type are detected.
9.  Medical NLP extracts structured entities.
10. Validation checks values, units, dates, and source locations.
11. User reviews uncertain results.
12. Confirmed/corrected entities are stored.
13. Document chunks are created and embedded.
14. ChromaDB index is updated.
15. Processing status becomes complete only when required steps are
    complete.
16. Report becomes available for comparison and analysis.

## 7.2 Historical comparison workflow

1.  Retrieve authorized patient records.
2.  Select the current and previous measurements/reports.
3.  Match test identities using normalized concepts and relevant
    context.
4.  Validate units, specimen, dates, and reference ranges where
    applicable.
5.  Calculate absolute and relative changes where mathematically
    meaningful.
6.  Identify missing tests and incompatible measurements.
7.  Save the comparison with its input record IDs and comparison-engine
    version.
8.  Generate an explanation from the verified comparison results.
9.  Display the comparison in the user's selected language.

## 7.3 Summary workflow

The report summary must be based on verified findings and source
passages, not an unrestricted summary of raw OCR output.

The summary should contain: - Report date and type. - Short
plain-language overview. - Key findings within applicable ranges, where
appropriate. - Findings outside applicable reference ranges. -
Comparison with previous reports when available. - Missing or uncertain
information. - Explanation of important medical terms. - Relevant
limitations and follow-up context. - Source references and a link to the
original wording.

The system must not say that a user is healthy simply because no flagged
result was detected.

------------------------------------------------------------------------

# 8. System Architecture

## 8.1 Logical architecture

``` text
React.js frontend
    |
    v
FastAPI application
    |
    +--> Authentication and authorization
    +--> Patient and medical-record APIs
    +--> Upload and processing-job APIs
    |
    v
Private file storage + MongoDB
    |
    v
Background processing workers
    |
    +--> PyMuPDF / OCR
    +--> Language and document detection
    +--> Medical entity extraction
    +--> Validation and normalization
    +--> Structure-aware chunking
    +--> Embedding generation
    |
    +--> MongoDB: structured records
    +--> ChromaDB: vectors and chunk metadata
    |
    v
Analysis orchestration
    |
    +--> Deterministic comparison engine
    +--> Trusted-source retrieval
    +--> RAG and Gemini explanation
    +--> Optional validated risk model
    |
    v
Output validation and saved analysis
    |
    v
React results dashboard
```

## 8.2 Architectural principles

-   Start with a modular FastAPI backend, not a distributed microservice
    system.
-   Run long-running OCR, embedding, and AI jobs in background workers
    when necessary.
-   Keep numerical comparison separate from natural-language generation.
-   Treat ChromaDB as a retrieval index, not the authoritative medical
    database.
-   Use explicit processing states and retries.
-   Ensure every data query enforces patient ownership.
-   Version extraction, normalization, embedding, prompt, and
    clinical-model logic.
-   Design deletion and re-indexing as first-class workflows.
-   Keep uploaded content untrusted; it must not override system
    instructions or access controls.

------------------------------------------------------------------------

# 9. Technology Stack and Responsibilities

  -----------------------------------------------------------------------
  Component               Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React.js                Forms, uploads,
                                                  dashboards, language
                                                  selection, comparison
                                                  UI

  Backend                 Python + FastAPI        APIs, validation,
                                                  authorization,
                                                  orchestration

  Primary database        MongoDB                 Patient profiles,
                                                  structured medical
                                                  records, report
                                                  metadata, analysis
                                                  history

  File storage            Private filesystem or   Original reports and
                          object storage          images

  PDF extraction          PyMuPDF                 Extract digital PDF
                                                  text and layout where
                                                  supported

  OCR                     EasyOCR or an evaluated Extract text from
                          alternative             supported scanned pages

  NLP                     Suitable multilingual   Detect concepts,
                          NLP/medical entity      measurements, symptoms,
                          tools                   medications, dates,
                                                  negation

  Embeddings              Sentence Transformers   Convert chunks to
                          or a validated          vectors for semantic
                          alternative             retrieval

  Vector database         ChromaDB                Searchable chunk
                                                  embeddings and metadata

  RAG orchestration       LangChain or a          Retrieval and
                          controlled equivalent   generation workflow

  LLM                     Gemini API              Grounded explanation
                                                  and multilingual
                                                  natural-language
                                                  generation

  Comparison logic        Python                  Exact calculations,
                                                  matching, unit
                                                  validation, trends

  Background jobs         A durable task queue    Run OCR, embeddings,
                          selected during         and long-running
                          implementation          analyses

  Testing                 Unit, integration,      Verify correctness and
                          security, and           safety
                          evaluation tests        

  Monitoring              Structured logs,        Operational visibility
                          metrics, traces, error  and quality monitoring
                          tracking                
  -----------------------------------------------------------------------

### Technology selection cautions

-   Do not assume EasyOCR supports every Indian script at acceptable
    quality.
-   Select multilingual embeddings based on retrieval evaluation, not
    model name alone.
-   Evaluate LLM language quality and medical factuality separately.
-   Use a queue only when the processing workflow requires it; select
    the implementation after the expected workload is known.
-   Do not add Kubernetes, multiple databases, or microservices without
    measured need.

------------------------------------------------------------------------

# 10. Data Storage Strategy

The system must retain the patient's authorized history for future
comparisons until the user deletes it, subject to applicable legal
obligations and disclosed exceptions.

## 10.1 Three principal storage layers

### A. Original document storage

Store uploaded PDFs and images in controlled private storage. MongoDB
stores a storage key, file hash, ownership, document type, and
processing metadata.

### B. Structured medical data in MongoDB

Store measurements, symptoms, conditions, medications, dates, units,
normalized concepts, source references, verification status, and
historical versions.

### C. Text chunks and vectors in ChromaDB

Store chunk IDs, embeddings, and metadata needed for retrieval. ChromaDB
must not be the only place where medical information exists. The index
should be rebuildable from retained source data and processing records.

## 10.2 Processing states

Suggested report/job states:

-   `queued`
-   `validating`
-   `extracting`
-   `needs_review`
-   `normalizing`
-   `indexing`
-   `completed`
-   `failed`
-   `deletion_pending`
-   `deleted`

A report is not fully processed merely because text or embeddings exist.
Required extraction, validation, and verification states must be tracked
independently.

## 10.3 Provenance

Every extracted, conversation-captured, imported, or manually entered
value should retain: - Source type: `report_ocr`, `report_pdf_text`,
`conversation`, `manual`, `import`, or another defined origin. - Source
report ID or source interaction ID, when applicable. - Page or location,
where available. - Original text/value and normalized representation. -
Date the fact was stated and effective date, if different. -
Verification status and confidence. - Correction history. -
Extraction/normalization version and timestamps.

## 10.4 Persistent patient context (medical memory)

The system should behave like a useful, patient-specific memory across
sessions: when the user provides relevant medical information in a
conversation, the system can save a structured fact and later use it
when it is relevant to a new question or report. This is **not** a
requirement to store every chat message as a permanent medical record.

-   Extract candidate facts such as patient-reported symptoms,
    medication use, known conditions, allergies, relevant dates, and
    user-stated historical test information.
-   Attach every fact to an explicitly selected patient profile and
    record its source, stated/effective dates, status, and correction
    history.
-   Use a distinct status such as `patient_reported`,
    `extracted_unverified`, `user_confirmed`, or `clinician_verified`.
    Never upgrade a fact's verification status merely because an LLM
    repeated it.
-   Save only relevant facts, not the whole conversation by default.
    Keep a source interaction reference and the minimum supporting
    excerpt needed for auditability; apply the same privacy and deletion
    policy to it.
-   Save clear, low-ambiguity facts only when persistent medical memory
    is enabled and the selected patient's identity is clear. Ask for
    confirmation when the subject, meaning, date, medication status, or
    clinical significance is ambiguous or when facts conflict.
-   Notify the user when a fact is saved and provide a memory/history
    screen to inspect, correct, disable future conversation-based
    capture, or delete facts. Disabling capture does not silently delete
    already saved facts; users can separately request deletion.
-   When answering later, retrieve only facts relevant to the current
    task and authorized patient. Prefer structured records for numerical
    comparisons; use semantic retrieval for supporting passages and
    context.
-   If no relevant saved context exists, answer without pretending to
    remember. Never invent a past conversation or infer a diagnosis as a
    stored fact.

The persistent fact store in MongoDB is authoritative. ChromaDB may
index eligible source excerpts for semantic retrieval, but it is only a
retrieval layer and must not be the only copy of a saved fact.

------------------------------------------------------------------------

# 11. MongoDB Data Model

Use separate collections for independently changing records. MongoDB
references are logical relationships; the backend must validate
ownership and existence because MongoDB does not automatically enforce
relational foreign keys.

## 11.1 `users`

Purpose: account and authentication metadata.

Fields: - `_id` - `email` or login identifier - `password_hash` or
identity-provider reference - `status` - `preferred_language` -
`created_at` - `updated_at`

Never store plaintext passwords. Keep authentication data separate from
medical records where feasible.

## 11.2 `patient_profiles`

Fields: - `_id` - `owner_user_id` - `display_name` or pseudonymous
label - `date_of_birth` when needed - `sex` when clinically relevant -
optional height/weight - preferred language - profile status -
created/updated timestamps

Collect only information needed for intended functionality.

## 11.3 `reports`

Fields: - `_id` - `patient_id` - `owner_user_id` - `file_storage_key` -
`file_hash` - `document_type` - `source_language` - `report_date` if
extracted/verified - `uploaded_at` - `extraction_status` -
`verification_status` - `processing_version` - `created_at`

Upload time and medical report date must remain separate.

## 11.4 `lab_results`

Fields: - `_id` - `patient_id` - `report_id` when derived from a
report - `original_test_name` - `normalized_test_code` when recognized -
`value` in an appropriate numeric/string representation - `unit` -
`specimen` - `reference_range` - `collected_at` - `source_type` -
`source_location` - `verification_status` - `version` or correction
history - timestamps

Keep the original result and unit even when a normalized comparison
value is created. Reference ranges must come from the applicable source
and must not be invented.

## 11.5 `symptoms`

Fields: - `_id` - `patient_id` - original and normalized symptom name -
onset/recorded dates - end date where known - severity and scale where
relevant - frequency - associated notes - source type - verification
status - timestamps

Symptoms are patient-reported or extracted observations, not
automatically confirmed diagnoses.

## 11.6 `conditions`

Fields: - `_id` - `patient_id` - condition name and normalized concept -
status - onset date if known - source type - verification status -
source references - timestamps

Distinguish patient-reported conditions from clinician-confirmed
diagnoses.

## 11.7 `medications`

Fields: - `_id` - `patient_id` - medication name and normalized concept
where available - strength, dose, route, frequency - start/end dates
where known - status - source type and source reference - verification
status - timestamps

Do not infer that an old prescription is a currently used medication.

## 11.8 `patient_context_facts` (persistent medical memory)

Purpose: store relevant facts captured from the user's statements across
sessions so they can inform later answers without requiring the user to
re-enter them manually.

Suggested fields:

-   `_id`, `owner_user_id`, and `patient_id`
-   `fact_type` such as symptom, medication use, condition, allergy, or
    historical event
-   `original_statement_excerpt` or a minimally sufficient source
    excerpt
-   `normalized_fact` with structured fields where possible
-   `source_type` (usually `conversation`)
-   `source_interaction_id` or source report ID
-   `stated_at` and `effective_date` when known
-   `record_status` (`patient_reported`, `extracted_unverified`,
    `user_confirmed`, `clinician_verified`, `superseded`, or `deleted`)
-   `confidence`, `needs_confirmation`, and `confirmation_status`
-   `supersedes_fact_id` or conflict references when applicable
-   `created_at`, `updated_at`, and correction/audit history

Store facts, not an unrestricted transcript archive. Do not store a fact
when its subject cannot be reliably associated with a patient profile.
Sensitive facts must remain private, patient-scoped, reviewable, and
deletable. A user's statement is not automatically a clinically verified
fact.

## 11.9 `report_chunks` or vector metadata

Fields: - `chunk_id` - `patient_id` - `report_id` or `source_fact_id` -
`chunk_index` - `page_number` or source location - `section_type` -
`source_language` - `extraction_version` - `content_hash` -
`verification_status`

The vector itself is stored by the vector database. Avoid placing
unnecessary personal identifiers in chunk text or metadata. Index only
the minimum context needed for retrieval, and ensure patient-scoped
filters are enforced server-side.

## 11.10 `analyses`

Fields: - `_id` - `patient_id` - selected input record IDs and
versions - analysis type - structured findings - evidence references -
prompt/model/rule versions - output language - creation timestamp -
validation status

## 11.11 `comparisons`

Fields: - `_id` - `patient_id` - current record/report IDs - previous
record/report IDs - matched test identifiers - changes and compatibility
results - unmatched/missing values - comparison algorithm version -
created timestamp

## 11.12 `risk_assessments`

Use only when a validated risk model is introduced.

Fields: - `_id` - `patient_id` - condition and intended use - prediction
horizon - model/version - input record IDs and versions - estimate and
supported uncertainty information - validation metadata - limitations -
created timestamp

## 11.13 `audit_events` and processing jobs

Record security-relevant actions, state transitions, retries, failures,
and deletion progress. Avoid logging unnecessary report contents or
secrets.

## 11.14 Logical relationships

``` text
users
  └── patient_profiles
       ├── reports
       │    ├── lab_results
       │    └── report_chunks (indexed in ChromaDB)
       ├── lab_results (manual or imported)
       ├── symptoms
       ├── conditions
       ├── medications
       ├── patient_context_facts
       ├── analyses
       │    └── risk_assessments (when implemented)
       └── comparisons
```

Every referenced record must be checked against the authorized patient.
A client-provided patient ID is not proof of access.

## 11.15 Indexes and validation

Consider indexes for: - Owner/user ID and patient ID. - Patient ID plus
collection date. - Patient ID plus report date. - Unique account login
identifier. - Report ID and chunk ID. - Analysis/comparison IDs and
timestamps.

Use schema validation for required fields, types, statuses, dates, and
allowed values. Make processing idempotent so retries do not create
duplicate records.

------------------------------------------------------------------------

# 12. Document Ingestion and Processing Pipeline

## 12.1 Step-by-step pipeline

1.  Authenticate user and verify patient access.
2.  Validate file type, size, extension, and content signature.
3.  Scan or safely process untrusted files using the deployment's
    security controls.
4.  Compute a file hash for duplicate detection.
5.  Store the original file privately.
6.  Create report metadata and a processing job.
7.  Extract digital PDF text and layout with PyMuPDF where possible.
8.  Use OCR for scanned pages or pages without usable text.
9.  Detect language, script, document type, and page layout.
10. Extract structured medical entities.
11. Normalize recognized medical concepts while preserving original
    wording.
12. Validate numeric values, units, dates, and reference ranges.
13. Flag uncertain entities and request user review when needed.
14. Store structured records with source provenance.
15. Split extracted content into structure-aware chunks.
16. Generate embeddings using a selected/evaluated model.
17. Index chunks and metadata in ChromaDB.
18. Mark processing complete only when required stages succeed.
19. Make the report available for comparison and analysis.

## 12.2 Error handling

-   Unsupported file: explain the reason and do not proceed.
-   Corrupted document: mark failure and retain diagnostic metadata.
-   OCR uncertainty: request review rather than guessing.
-   Embedding failure: retry the failed stage without duplicating
    structured records.
-   LLM/API failure: keep stored source data intact and allow a
    controlled retry.
-   Partial processing: display status and prevent misleading claims
    that the report is fully ready.
-   Duplicate upload: identify likely duplicates but do not merge
    records automatically without safe rules.

------------------------------------------------------------------------

# 13. Chunking, Embeddings, and Vector Retrieval

## 13.1 Structure-aware chunking

Avoid arbitrary fixed-length splitting where it separates medical values
from units, headings, or reference ranges.

  ---------------------------------------------------------------------
  Chunk type                         Strategy
  ---------------------------------- ----------------------------------
  Report overview                    Keep document title, type, date,
                                     and relevant headings together

  Laboratory section                 Keep each result with its test
                                     name, unit, reference range, and
                                     flag

  Clinical findings                  Keep each finding with its
                                     heading, negation, and surrounding
                                     context

  Medication section                 Keep medication details and
                                     associated instructions together

  Assessment/discharge section       Keep each assessment with its
                                     evidence and context

  Narrative section                  Split by semantic boundaries, with
                                     limited overlap if useful
  ---------------------------------------------------------------------

Choose chunk size and overlap through retrieval evaluation. Preserve
table headings and row relationships.

## 13.2 Chunk metadata

Each chunk should have: - Unique chunk ID. - Patient and report IDs. -
Page/source location. - Section type. - Source language. - Extraction
version. - Verification status. - Content hash.

Apply patient access checks on every retrieval request. Metadata
filtering in ChromaDB is not a replacement for backend authorization.

## 13.3 Retrieval flow

1.  Receive the question and selected language.
2.  Resolve authorized patient context.
3.  Determine whether the question needs structured records, text
    retrieval, or both.
4.  Query structured data for exact measurements and history.
5.  Retrieve relevant report chunks and trusted medical references.
6.  Apply authorization and relevance checks.
7.  Optionally rerank retrieved passages if evaluation shows a benefit.
8.  Build a bounded context with source references.
9.  Generate an answer.
10. Validate citations, factual consistency, language, and safety.
11. Store the result and input/version references.

Use semantic retrieval for context, not for exact numerical matching.

------------------------------------------------------------------------

# 14. Multilingual NLP Architecture

## 14.1 Language scope

The product goal is support for Indian languages. Launch support
incrementally, using an explicit list of languages that pass evaluation.
Do not claim all Indian languages are supported until that is
demonstrated.

## 14.2 Pipeline

1.  Detect language and script.
2.  Extract text from digital or scanned documents.
3.  Identify medical entities, measurements, units, dates, symptoms,
    medications, and negation.
4.  Normalize recognized concepts to a canonical internal
    representation.
5.  Preserve original text and source language.
6.  Store structured records.
7.  Create multilingual embeddings using a model evaluated for
    cross-lingual retrieval.
8.  Retrieve evidence across supported languages when appropriate.
9.  Perform comparisons using canonical structured values.
10. Generate a response in the preferred supported language.
11. Validate that values, units, negation, uncertainty, and medical
    meaning remain unchanged.

## 14.3 Required multilingual NLP capabilities

-   Medical entity recognition.
-   Negation detection (e.g., "no fever").
-   Temporality detection (past symptom versus current symptom).
-   Uncertainty handling ("possible infection" versus confirmed
    infection).
-   Transliteration and spelling variation where supported.
-   Unit and number normalization.
-   Cross-language concept mapping.
-   Translation fidelity and source-language preservation.
-   Language-specific quality evaluation.

Translation alone is insufficient. OCR, entity extraction, retrieval,
and explanation generation must each be tested separately.

## 14.4 Language rollout

1.  Select initial languages based on user needs and evaluated OCR/NLP
    resources.
2.  Build annotated test cases for each language.
3.  Measure extraction, retrieval, and explanation quality.
4.  Fix critical errors and set release thresholds.
5.  Release only the languages that pass the agreed criteria.
6.  Add further languages through the same evaluation gate.

------------------------------------------------------------------------

# 15. Comparison and Historical Analysis Engine

## 15.1 Responsibilities

The comparison engine should: - Retrieve historical data for the
authorized patient. - Match compatible test concepts. - Check units,
specimen, date, and relevant method context. - Convert units only with
validated conversion rules. - Calculate absolute and relative changes
when meaningful. - Compare values with the applicable reference
ranges. - Identify new, missing, or incompatible measurements. - Show
trends across multiple reports. - Preserve original values and source
references. - Store a reproducible comparison record.

## 15.2 Comparison rules

-   Never compare different tests merely because their names look
    similar.
-   Do not compare incompatible units without a validated conversion.
-   Do not assume different laboratories use identical reference ranges.
-   Do not assume missing values are normal or unchanged.
-   Do not infer clinical improvement solely from an increase/decrease.
-   Do not use the LLM as the calculator.
-   Show the dates and source records for compared values.
-   Flag ambiguous matches for review.

## 15.3 Output structure

A comparison should contain: - Current value and date. - Previous value
and date. - Units and applicable reference ranges. - Absolute change. -
Relative change where meaningful. - Match/compatibility status. - Source
report and page references. - Plain-language explanation. - Uncertainty
or missing context.

------------------------------------------------------------------------

# 16. AI Explanation and RAG Design

## 16.1 Responsibilities

The RAG/LLM layer explains verified structured findings and retrieved
evidence. It should not be responsible for: - Inventing measurements. -
Choosing arbitrary reference ranges. - Performing unverified unit
conversion. - Claiming a diagnosis without sufficient basis. -
Fabricating citations. - Producing a disease probability without a
validated method.

## 16.2 Evidence sources

Use sources that are suitable for the intended question, such as: - The
user's verified report and structured history. - Trusted medical
references selected and versioned by the project. - Validated clinical
guidelines or terminology resources where licensing and access permit.

Record the source, retrieval date/version where possible, and the exact
passages used.

## 16.3 Output validation

Before showing an AI-generated explanation: 1. Confirm it references the
correct patient and records. 2. Check that cited sources exist and
support the associated claims. 3. Check that values and units match
structured inputs. 4. Check for unsupported diagnostic claims. 5. Check
language fidelity and preservation of negation. 6. Include limitations
and missing data where relevant. 7. Block or regenerate outputs that
violate critical safety rules.

Uploaded documents are untrusted input. Instructions embedded inside a
document must not override system rules, access controls, or the
intended task.

------------------------------------------------------------------------

# 17. Clinical Risk Assessment and Safety Boundaries

The initial risk-model target is **not selected**. Do not choose a
condition merely to make the project appear more advanced.

Before adding a risk model, define: 1. The clinical question and
intended use. 2. The condition and prediction horizon. 3. The eligible
population and exclusions. 4. The required inputs and acceptable
missingness. 5. The source dataset and data rights. 6. The training,
tuning, and independent test design. 7. Discrimination, calibration, and
subgroup evaluation. 8. Clinical review and release criteria. 9.
Monitoring and model-update policy. 10. Applicable regulatory and
deployment requirements.

A validated model's risk estimate must be distinguished from a current
diagnosis. A model's confidence score or an LLM-generated number is not
a calibrated disease probability.

## 17.1 Output distinctions

-   **Abnormal finding:** A measurement lies outside an applicable
    reference range.
-   **Possible explanation:** A condition may be relevant based on the
    available evidence, but remains uncertain.
-   **Risk estimate:** A defined model estimates a specified risk for an
    eligible population over a defined horizon.
-   **Clinical diagnosis:** A clinical conclusion established using
    appropriate diagnostic criteria and professional assessment.

The system must not collapse these categories into one statement.

## 17.2 Chest X-ray module

If included later, treat it as a separate module with: - Defined
supported findings. - Appropriate, documented dataset provenance and
permissions. - Independent train/validation/test separation. -
Evaluation of sensitivity, specificity, calibration where applicable,
and subgroup behavior. - Explainability limitations clearly
communicated. - Clinical review and appropriate deployment controls.

Do not assume Grad-CAM heatmaps prove a model's reasoning or clinical
correctness.

------------------------------------------------------------------------

# 18. User Experience and Screens

## 18.1 Main screens

1.  **Login and registration:** Secure access and account recovery.
2.  **Patient profile:** Relevant demographics, language preference, and
    medical context.
3.  **Dashboard:** Recent reports, processing status, and historical
    overview.
4.  **Upload page:** Supported formats, upload validation, and progress.
5.  **Review extracted data:** Highlight uncertain values, missing
    units, and editable fields.
6.  **Manual entry:** Structured forms for lab results, symptoms,
    conditions, and medications.
7.  **Report detail:** Original document reference and extracted data.
8.  **Comparison page:** Current versus previous values, trends, and
    source references.
9.  **Quick summary:** Concise summary in the preferred supported
    language.
10. **Detailed analysis:** Findings, explanations, citations,
    uncertainty, and limitations.
11. **History timeline:** Reports, measurements, symptoms, and
    medication changes over time.
12. **Export/share:** Downloadable summary and explicit controlled
    sharing if implemented.
13. **Settings and privacy:** Preferred language, account settings,
    export, and deletion requests.

## 18.2 Three explanation levels

### Level 1: Quick summary

A few clear sentences covering the report's main findings, important
abnormalities, comparison availability, and limitations.

### Level 2: Detailed findings

Test-by-test values, units, reference ranges, historical changes,
explanations, and sources.

### Level 3: Medical context and risk assessment

Relevant symptoms/history, possible explanations, validated risk
estimates if available, missing information, and appropriate follow-up
context.

## 18.3 Quick summary requirements

The summary must: - Be based on verified findings. - Use the selected
supported language. - Preserve values and units. - Explain medical
terminology in plain language. - Highlight important findings without
hiding critical information. - Compare previous reports when
available. - Clearly distinguish facts from interpretation. - State when
data is insufficient. - Link important claims to evidence. - Avoid
saying the user is healthy merely because no abnormal flag was detected.

------------------------------------------------------------------------

# 19. API Design

These are proposed API contracts, not implemented endpoints. Use a
versioned prefix such as `/api/v1`.

  ----------------------------------------------------------------------------
  Method and endpoint                                Purpose
  -------------------------------------------------- -------------------------
  `POST /api/v1/patients`                            Create patient profile

  `GET /api/v1/patients/{patient_id}`                Retrieve authorized
                                                     profile

  `PATCH /api/v1/patients/{patient_id}`              Update permitted profile
                                                     fields

  `POST /api/v1/reports/upload`                      Upload and register
                                                     report

  `GET /api/v1/reports/{report_id}`                  Retrieve report metadata
                                                     and status

  `GET /api/v1/reports/{report_id}/extracted-data`   Retrieve extracted
                                                     entities

  `POST /api/v1/reports/{report_id}/verify`          Confirm or correct
                                                     extracted data

  `POST /api/v1/medical-records/labs`                Add lab measurement

  `POST /api/v1/medical-records/symptoms`            Add symptom

  `POST /api/v1/medical-records/conditions`          Add condition history

  `POST /api/v1/medical-records/medications`         Add medication record

  `POST /api/v1/context/capture`                     Extract candidate facts
                                                     from a user interaction

  `GET /api/v1/patients/{patient_id}/context`        List saved context facts

  `POST /api/v1/context/facts/{fact_id}/confirm`     Confirm or correct a
                                                     candidate fact

  `PATCH /api/v1/context/facts/{fact_id}`            Correct a saved fact

  `DELETE /api/v1/context/facts/{fact_id}`           Delete a saved fact

  \`PATCH                                            s\` Update memory/capture
  /api/v1/patients/{patient_id}/memory-setting       preferences

  `GET /api/v1/patients/{patient_id}/history`        Retrieve authorized
                                                     history

  `POST /api/v1/comparisons`                         Create historical
                                                     comparison

  `GET /api/v1/comparisons/{comparison_id}`          Retrieve saved comparison

  `POST /api/v1/analyses`                            Request analysis

  `GET /api/v1/analyses/{analysis_id}`               Retrieve saved analysis

  `DELETE /api/v1/patients/{patient_id}`             Request deletion workflow
  ----------------------------------------------------------------------------

Every protected endpoint must validate authorization and ownership.
Long-running operations should return a job or resource ID and expose
status. Add rate limits, request-size limits, validation errors, and
consistent error responses.

Do not let clients choose arbitrary model versions, file paths, or
patient IDs without backend validation.

------------------------------------------------------------------------

# 20. Security, Privacy, Retention, and Deletion

## Persistent medical memory safeguards

-   Persistent memory must be patient-scoped, private by default, and
    covered by the same retention/deletion policy as other medical data.
-   Tell users what categories of facts can be saved, when facts are
    captured, and how to view, correct, disable future capture, and
    delete saved facts. Do not describe the feature as remembering
    everything.
-   Do not save information about a family member or another person into
    the selected patient's history. Ask which person the fact concerns
    when unclear.
-   Do not persist speculative diagnoses, generated summaries, or model
    guesses as patient facts. Store the user's statement and its status.
-   Send only the minimum relevant context to the LLM for a given
    request. Enforce patient authorization before retrieval, not only
    after it.
-   Include saved facts, source excerpts, embeddings, caches, and
    derived outputs in deletion workflows. Verify deletion across every
    in-scope store and document backup expiry.
-   Do not put raw medical statements into routine logs, analytics, or
    error telemetry. Audit memory access and changes without
    unnecessarily copying the medical content.

## 20.1 Security requirements

-   Authentication and authorization on every protected endpoint.
-   Patient ownership checks for all record retrieval and mutation.
-   Least-privilege database and storage credentials.
-   TLS for network communication.
-   Encryption at rest where supported and appropriate.
-   Secure password hashing or a reputable identity provider.
-   Secret management for API keys.
-   File-type and file-size validation.
-   Private file storage and short-lived access links where appropriate.
-   Rate limiting and abuse controls.
-   Safe error handling without leaking sensitive data.
-   Audit logging for sensitive operations.
-   Prompt-injection defenses for uploaded documents and retrieved text.
-   Backup and recovery procedures.
-   Dependency and vulnerability management.

## 20.2 Retention policy

Default: retain authorized medical history until the user requests
deletion, subject to applicable legal requirements and disclosed
exceptions.

Deletion must address: - Original files. - MongoDB records. - ChromaDB
vectors and metadata. - Derived analyses and comparisons. - Cached
copies and temporary files. - Exported copies where the application
controls them. - Backups according to the documented expiry policy.

The application must communicate where immediate removal is not
technically possible and when backup copies expire. Legal retention
requirements must be assessed before deployment.

## 20.3 Data minimization

Collect only what is necessary. Do not include unnecessary personal
identifiers in embeddings or prompts. Use de-identified or appropriately
consented data for evaluation whenever possible.

------------------------------------------------------------------------

# 21. Testing and Validation Plan

## 21.1 Unit testing

Test: - Schema validation. - Unit conversion. - Numerical differences. -
Reference-range handling. - Date parsing. - Normalized test matching. -
Missing-data behavior. - Provenance and versioning. - Deletion-state
transitions.

## 21.2 Integration testing

Test complete workflows: - Upload to extraction. - Extraction to user
verification. - Verified data to MongoDB. - Chunk generation to
ChromaDB. - Historical retrieval to comparison. - Comparison to summary
generation. - Language selection to localized response. - Deletion
across all storage layers.

## 21.3 Evaluation dataset

Create a reviewed test set containing: - Digital PDFs. - Scanned PDFs. -
Low-quality images. - Multiple report layouts. - Different units and
reference ranges. - Missing values. - Duplicate reports. - Multilingual
and mixed-language documents. - Negated and historical symptoms. -
Incorrect or ambiguous OCR results. - Reports with tables, footnotes,
and unusual formatting.

Use de-identified or appropriately consented data. Record expected
outputs and annotation provenance.

## 21.4 Metrics

  ---------------------------------------------------------------------
  Area                               Evaluation
  ---------------------------------- ----------------------------------
  OCR                                Character/word error measures plus
                                     medical-value extraction accuracy

  Entity extraction                  Precision, recall, and F1 for
                                     medical entities

  Numeric extraction                 Exact value, sign, decimal, unit,
                                     and date accuracy

  Comparison                         Agreement with expected results;
                                     incompatible-match rate

  Retrieval                          Recall@k, precision/relevance, and
                                     source attribution correctness

  Generation                         Factual consistency, citation
                                     support, unsupported-claim rate

  Multilingual                       Meaning preservation, negation
                                     accuracy, terminology and
                                     numerical fidelity

  Security                           Cross-user access, authorization
                                     bypass, prompt injection, and
                                     deletion tests

  Operations                         Failure rate, retry behavior,
                                     latency, throughput, and cost
  ---------------------------------------------------------------------

For clinical models, use patient-level separation across training,
tuning, and test sets; independent validation where possible;
calibration analysis; subgroup evaluation; and qualified clinical
review. A high average score alone does not establish clinical safety.

------------------------------------------------------------------------

# 22. Observability, Reliability, and Scalability

## 22.1 Operational telemetry

Monitor: - Upload and processing job status. - OCR and extraction
failures. - Queue depth and retry counts. - Embedding/indexing
failures. - Retrieval latency. - LLM request latency, failure rate, and
usage cost. - Comparison and validation errors. - Deletion job status. -
System resource utilization. - Security-relevant events.

Logs should avoid unnecessary report text, credentials, and personal
medical details.

## 22.2 Reliability practices

-   Use idempotency keys or equivalent safeguards for repeat requests.
-   Retry transient failures with bounded backoff.
-   Send permanently failed jobs to a review/dead-letter path.
-   Keep processing stages independently recoverable.
-   Record status transitions.
-   Use timeouts and rate limits for external APIs.
-   Avoid duplicate record creation during retries.
-   Test backup restoration and recovery procedures.

## 22.3 Scale-up strategy

Start with a modular monolith and independently runnable background
workers. Scale only after observing bottlenecks.

Potential later additions: - Durable queue such as Celery with an
appropriate broker. - Docker and automated CI/CD. - Centralized metrics,
tracing, and error tracking. - Hybrid keyword/vector retrieval and
reranking. - Separate worker pools for OCR, embeddings, and AI calls. -
Managed object storage or vector infrastructure. - Independently scaled
services if workload and team needs justify them.

Kubernetes and microservices are not initial requirements.

------------------------------------------------------------------------

# 23. Development Phases and Step-by-Step Tasks

The sequence below is the recommended build plan. Each phase has
deliverables, exit criteria, and a mandatory test gate. **Finish one
phase, test it, review the results, fix critical defects, and only then
move to the next phase. Do not build all phases first and postpone
testing until the end.** Keep test cases and results in the repository
so that later changes can rerun the earlier checks. Do not begin
disease-risk modeling before the data, comparison, and evaluation
foundations are reliable.

## Phase 0 --- Freeze the requirements baseline

### Tasks

1.  Review the scope and requirements in this document.
2.  Confirm the initial supported document types.
3.  Select the first language set based on available OCR/NLP evaluation.
4.  Decide whether the initial app supports one patient per account or
    multiple authorized profiles.
5.  Decide deployment target and privacy requirements.
6.  Define file size limits and accepted formats.
7.  Define initial acceptance tests and quality thresholds.
8.  Keep disease-risk target unselected until research establishes
    feasibility.
9.  Write a short architecture decision record for major choices.

### Deliverables

-   Approved requirements baseline.
-   Prioritized backlog.
-   Open-decision register.
-   Acceptance criteria.

### Exit criteria

All required first-release features have owners, dependencies, and
testable acceptance criteria.

### Mandatory phase test gate

Before implementation starts, review the requirements with concrete
examples and run a requirements/acceptance-criteria walkthrough. Confirm
that every in-scope requirement has a testable pass/fail condition, that
critical risks have a planned test, and that the initial test dataset
and quality thresholds are documented. Record unresolved decisions as
blockers or explicitly approved deferrals. **Do not start Phase 1 until
this planning gate is signed off.**

## Phase 1 --- Backend and database foundation

### Tasks

1.  Create the repository and development environment.
2.  Establish frontend/backend configuration and secret handling.
3.  Set up FastAPI and health endpoints.
4.  Configure MongoDB and schema validation.
5.  Define users and patient profiles.
6.  Implement authentication and authorization.
7.  Define report, lab-result, symptom, condition, medication,
    patient-context-fact, analysis, and comparison schemas.
8.  Add indexes and ownership checks for every patient-scoped record.
9.  Define file-storage abstraction.
10. Implement audit events, persistent-memory preferences, and
    processing-job state model.
11. Write unit and integration tests.

### Deliverables

-   Working backend foundation.
-   Initial MongoDB collections and indexes.
-   Authenticated API contracts.
-   Schema and access-control tests.

### Exit criteria

Users can access only authorized profiles and records. Schema and
authorization tests pass.

### Mandatory phase test gate

Run the backend and database tests before moving on:

-   Start the API and verify the health endpoint.
-   Test successful and failed registration/login flows, expired/invalid
    credentials, and protected endpoints.
-   Attempt cross-user and cross-patient access; every unauthorized
    attempt must be rejected.
-   Test schema validation, required fields, indexes, and
    duplicate/conflicting identifiers.
-   Test database-unavailable and configuration/secret-missing behavior.
-   Run unit and integration tests and confirm logs do not expose
    credentials or unnecessary medical data.

**Exit rule:** all critical tests pass; any remaining defect is
documented, severity-rated, and explicitly accepted before the next
phase.

## Phase 2 --- Persistent patient context and optional manual entry

### Tasks

1.  Define allowed categories of persistent medical facts and the
    difference between a fact, an inference, and an AI-generated answer.
2.  Implement extraction of candidate facts from natural-language user
    statements, with patient/profile attribution.
3.  Add a clear persistent-memory preference and explain what is saved.
4.  Save eligible facts to `patient_context_facts` with source, dates,
    status, and correction history; do not save unrestricted chat logs.
5.  Ask for confirmation when the subject, meaning, date, medication
    status, or clinical significance is ambiguous or conflicting.
6.  Build a memory/history screen to view, confirm, correct, and delete
    saved facts, and to disable future conversation-based capture.
7.  Retrieve relevant facts for later interactions using patient-scoped
    structured filters and semantic retrieval where useful.
8.  Keep forms for direct lab-result, symptom, condition, and medication
    entry as a fallback, and use the same validation/provenance
    pipeline.
9.  Preserve `source_type`, record status, and verification level.
10. Add idempotency, correction history, list/history endpoints, and
    unit/integration tests.

### Deliverables

-   Persistent patient-context memory across sessions.
-   Natural-language fact capture and relevant context retrieval.
-   User-visible review, correction, and deletion controls.
-   Manual-entry forms as an optional fallback.
-   Input validation and memory-authorization tests.

### Exit criteria

A clear, user-attributed medical fact can be saved once, reviewed, and
retrieved in a later relevant interaction without re-entry. Ambiguous
facts are held for confirmation. Facts are never mixed between patient
profiles, and the user can correct or delete saved context.

### Mandatory phase test gate

Test the end-to-end memory workflow through the UI and API:

-   Tell the system a clear fact, start a new session, ask a related
    question, and verify the relevant fact is retrieved accurately.
-   Ask an unrelated question and verify irrelevant saved context is not
    injected into the answer.
-   Test ambiguous subjects (for example, user versus family member),
    unclear dates, conflicting statements, and uncertain medication
    status; require confirmation where specified.
-   Verify patient-reported facts are never displayed as clinician-
    verified findings.
-   Confirm memory can be viewed, corrected, disabled for future
    capture, and deleted.
-   Test cross-user/cross-patient access, duplicate capture, retries,
    database failures, and deletion from MongoDB and any vector index.
-   Verify only the intended structured facts are saved, not a complete
    conversation transcript by default.

**Exit rule:** cross-session recall, relevance filtering, provenance,
authorization, and correction/deletion tests pass before proceeding.

## Phase 3 --- Upload and extraction

### Tasks

1.  Implement secure upload endpoint.
2.  Validate file type, size, and content.
3.  Store original files privately.
4.  Create report metadata and processing jobs.
5.  Extract digital PDF text with PyMuPDF.
6.  Add OCR for supported scanned documents.
7.  Detect document language and type.
8.  Extract candidate measurements and metadata.
9.  Preserve page/source locations.
10. Flag uncertain values and missing units.
11. Build the review/correction interface.
12. Save verified structured records.
13. Add duplicate detection and retry handling.

### Deliverables

-   End-to-end upload and extraction workflow.
-   Report status UI.
-   Verified structured records.
-   Extraction evaluation dataset.

### Exit criteria

Representative reports can be processed and reviewed. Unsupported or
uncertain data is handled explicitly rather than silently accepted.

### Mandatory phase test gate

Run a representative extraction test set containing digital PDFs,
scanned PDFs, images, multiple pages, tables, poor-quality scans,
unsupported formats, oversized files, and malformed or malicious files:

-   Compare extracted test names, values, units, dates, reference
    ranges, and flags with manually verified ground truth.
-   Check decimal points, negative signs, OCR confusion, page/source
    locations, and uncertain-value handling.
-   Confirm upload validation rejects unsafe or unsupported files and
    original files remain private.
-   Test processing status, retries, duplicate uploads, partial
    failures, and recovery.
-   Verify uncertain extracted values are not treated as verified
    without review.

**Exit rule:** report extraction metrics against the Phase 0 thresholds;
fix critical numeric/provenance defects and document unsupported cases
before continuing.

## Phase 4 --- Chunking and semantic retrieval

### Tasks

1.  Define structure-aware chunk types.
2.  Preserve headings, tables, units, and source locations.
3.  Select candidate embedding models.
4.  Evaluate models on supported languages and report types.
5.  Generate embeddings.
6.  Store vectors and metadata in ChromaDB.
7.  Implement patient-scoped retrieval over report chunks and eligible
    saved context facts.
8.  Add retrieval tests, fact provenance, and source references.
9.  Implement re-indexing and deletion from the vector index, including
    deletion of indexed context facts.
10. Test duplicate processing and recovery.

### Deliverables

-   Chunking pipeline.
-   Vector index.
-   Retrieval interface and evaluation results.

### Exit criteria

Retrieval returns relevant, authorized passages with correct source
attribution and can be rebuilt from retained source data.

### Mandatory phase test gate

Test chunking and retrieval with known questions and expected source
passages:

-   Confirm chunks preserve report section, test name, value, unit,
    date, page/source location, and related table context.
-   Measure retrieval relevance/recall on the evaluation set and check
    source attribution.
-   Verify one patient's query cannot retrieve another patient's
    content.
-   Test empty results, ambiguous queries, duplicate indexing,
    re-indexing, deletion, and index rebuild from retained source data.
-   Confirm retrieval returns evidence rather than invented passages and
    that metadata filters work.

**Exit rule:** retrieval and authorization tests pass, source links
point to the correct report locations, and measured quality meets the
agreed thresholds.

## Phase 5 --- Historical comparison engine

### Tasks

1.  Define normalized test concepts and matching rules.
2.  Define compatible unit conversions.
3.  Implement exact change calculations.
4.  Handle missing, new, duplicate, and incompatible measurements.
5.  Apply appropriate reference ranges.
6.  Support comparisons across multiple dates.
7.  Store comparison input IDs and algorithm version.
8.  Build tables and trend charts.
9.  Test with known expected outputs.
10. Add source links and uncertainty labels.

### Deliverables

-   Deterministic comparison service.
-   Historical timeline.
-   Comparison dashboard.
-   Regression test suite.

### Exit criteria

All defined comparison tests match expected results. Incompatible
measurements are flagged rather than silently compared.

### Mandatory phase test gate

Run deterministic comparison tests against hand-calculated expected
results:

-   Test unchanged, increased, decreased, newly appearing, missing,
    duplicate, and incompatible measurements.
-   Test valid unit conversions, rounding, reference-range differences,
    and results from different dates.
-   Verify percentages and absolute changes are mathematically correct
    and handle zero/missing baselines safely.
-   Confirm comparisons use the correct patient, test concept, date, and
    source record.
-   Test trend charts and tables against the underlying comparison
    output.
-   Verify incompatible units or concepts are flagged, never silently
    compared.

**Exit rule:** all critical numerical regression tests pass exactly
within documented rounding rules; no LLM is responsible for calculating
comparison values.

## Phase 6 --- RAG and quick summary

### Tasks

1.  Select and document trusted medical knowledge sources.
2.  Implement retrieval over report chunks and approved references.
3.  Pass verified structured findings and only relevant, authorized
    patient-context facts to the explanation workflow, preserving their
    different verification statuses.
4.  Define output schema for summary and detailed findings.
5.  Configure Gemini integration and secret handling.
6.  Generate the quick summary first.
7.  Add detailed explanation and medical terminology clarification.
8.  Add citations and source linking.
9.  Validate numerical consistency and citation support.
10. Add safeguards for unsupported claims and prompt injection.
11. Save analysis with input and model/version metadata.
12. Evaluate output quality against reviewed examples.

### Deliverables

-   Grounded AI explanation service.
-   Quick summary UI.
-   Detailed analysis page.
-   Citation and factuality tests.

### Exit criteria

The summary accurately reflects verified data, includes source
references, and meets the approved critical-error thresholds.

### Mandatory phase test gate

Evaluate the AI explanation pipeline using reviewed reports and
questions with known evidence:

-   Check that every material claim is supported by a cited source or
    clearly identified as general context.
-   Compare all displayed numbers, units, dates, and abnormal flags with
    verified structured data.
-   Test missing evidence, conflicting reports, prompt-injection text
    inside uploaded documents, model/API timeouts, and malformed model
    output.
-   Confirm the quick summary is concise and limitations/uncertainty are
    visible.
-   Measure unsupported-claim rate, citation correctness, numerical
    consistency, latency, and cost.
-   Verify the app fails safely when the model is unavailable and does
    not fabricate a result.

**Exit rule:** the agreed critical-error and factuality thresholds pass;
block release if a critical unsupported medical claim or incorrect
patient value is found.

## Phase 7 --- Multilingual NLP and localization

### Tasks

1.  Approve the initial language list.
2.  Select OCR and language-detection tools for each language.
3.  Build annotated test cases.
4.  Implement medical entity and negation extraction.
5.  Define canonical medical terminology mappings.
6.  Evaluate multilingual embeddings.
7.  Add preferred-language selection.
8.  Generate localized summaries.
9.  Test mixed-language and cross-language report comparisons.
10. Validate medical terminology, units, numbers, and uncertainty.
11. Add languages incrementally after passing evaluation.

### Deliverables

-   Language selection and localized interface.
-   Multilingual summary generation.
-   Per-language evaluation report.

### Exit criteria

Each released language meets its defined extraction, retrieval, and
explanation quality thresholds.

### Mandatory phase test gate

Treat each language as a separate release candidate:

-   Test representative reports and summaries in that language,
    including mixed-language content where in scope.
-   Check medical terminology, negation, dates, decimal values, units,
    abnormal flags, and uncertainty wording.
-   Compare translated/localized summaries with verified source facts;
    ensure translation does not alter the clinical meaning.
-   Test language switching and confirm it does not change the
    underlying analysis or numerical results.
-   Record extraction, retrieval, and explanation metrics separately for
    each language.

**Exit rule:** release a language only after its own documented quality
thresholds pass. Do not infer quality from results in another language.

## Phase 8 --- Expanded patient context

### Tasks

1.  Add structured symptom timelines.
2.  Add condition history and verification status.
3.  Add medication history reconciliation.
4.  Detect cross-report inconsistencies.
5.  Incorporate relevant context into explanations.
6.  Preserve the distinction between patient-reported and verified
    facts.
7.  Add follow-up tracking only when based on an explicit
    user/clinician-entered plan.
8.  Test conflicting and incomplete records.

### Deliverables

-   Unified patient history.
-   Context-aware explanations.
-   Medication and inconsistency review workflows.

### Exit criteria

The system uses context without inventing diagnoses or silently
resolving conflicting data.

### Mandatory phase test gate

Test patient-context integration using synthetic or properly
de-identified cases:

-   Verify symptom, condition, and medication timelines are correctly
    dated and linked to the right patient.
-   Test contradictory, incomplete, stale, and patient-reported
    information.
-   Confirm the system distinguishes patient-reported information from
    verified report findings.
-   Check that medication/history conflicts are surfaced for review
    rather than silently resolved.
-   Confirm context changes are reflected in explanations only when
    relevant and traceable.

**Exit rule:** context is displayed accurately with provenance, and no
test case produces an invented diagnosis or silently resolves a
conflict.

## Phase 9 --- Export, privacy, and production readiness

### Tasks

1.  Generate downloadable summaries.
2.  Implement account/profile data export.
3.  Implement deletion workflows across storage layers.
4.  Add operational metrics and structured logging.
5.  Add rate limits and quotas.
6.  Test failure recovery and retries.
7.  Test backup restoration.
8.  Run security and privacy review.
9.  Containerize if useful for deployment.
10. Establish CI/CD and release procedures.
11. Measure latency and cost under representative workload.
12. Document support and incident-response procedures.

### Deliverables

-   Export and deletion features.
-   Monitoring and operational runbook.
-   Deployment package.
-   Security and release test results.

### Exit criteria

Functional, privacy, recovery, and performance requirements are met for
the target deployment.

### Mandatory phase test gate

Run a release-readiness test cycle in a staging environment:

-   Test export completeness and verify exports contain only the
    authorized user's data.
-   Test deletion across original files, MongoDB records, vector
    indexes, caches, derived outputs, and applicable backup-expiry
    workflows.
-   Test backup restoration, job retries, interrupted processing,
    database/storage outages, and recovery.
-   Run authentication/authorization, upload-security, dependency, and
    privacy checks.
-   Load-test representative workflows and record latency, failure rate,
    and cost against targets.
-   Verify monitoring alerts, incident procedures, deployment rollback,
    and CI/CD release checks.

**Exit rule:** no unresolved critical security/privacy defects;
deletion, recovery, and performance requirements pass before production
release.

## Phase 10 --- Research and validate clinical extensions

### Tasks

1.  Identify candidate conditions based on project goals and available
    evidence.
2.  Define intended use, population, prediction horizon, and exclusions.
3.  Review data availability, licensing, quality, and
    representativeness.
4.  Select a suitable validated model or plan a properly designed model
    study.
5.  Prevent patient-level data leakage.
6.  Evaluate calibration, discrimination, subgroup performance, and
    limitations.
7.  Obtain qualified clinical review.
8.  Establish model versioning and monitoring.
9.  Expose predictions only after passing release criteria.
10. Treat chest X-ray analysis as a separate model pipeline if included.

### Deliverables

-   Clinical-model feasibility report.
-   Evaluation protocol and results.
-   Explicit go/no-go decision.

### Exit criteria

No clinical risk claim is released without appropriate evidence,
validation, and review.

### Mandatory phase test gate

Before exposing any clinical extension, conduct a documented research
and validation review:

-   Verify dataset provenance, consent/licensing, inclusion criteria,
    representativeness, and data quality.
-   Check for patient-level data leakage and use a suitable independent
    evaluation set.
-   Evaluate calibration, discrimination, subgroup performance, failure
    modes, and intended-use limits.
-   Obtain qualified clinical review and document model/data versions
    and limitations.
-   Run a formal go/no-go review; if evidence is insufficient, keep the
    feature disabled.

**Exit rule:** a model is not released merely because it runs or
achieves a single performance score. It requires documented validation
and approval for the defined intended use.

------------------------------------------------------------------------

# 24. Proposed Project Structure

The exact structure can evolve, but responsibilities should remain
separated.

``` text
medireport-analyzer/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── i18n/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── auth/
│   │   ├── database/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   ├── extraction/
│   │   │   ├── normalization/
│   │   │   ├── chunking/
│   │   │   ├── retrieval/
│   │   │   ├── comparison/
│   │   │   ├── analysis/
│   │   │   └── reporting/
│   │   ├── workers/
│   │   └── main.py
│   └── tests/
├── evaluation/
│   ├── extraction/
│   ├── retrieval/
│   ├── multilingual/
│   └── clinical/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── api-contracts.md
│   ├── security-and-privacy.md
│   └── evaluation-plan.md
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

Never commit real API keys, passwords, private medical reports, or
production data into source control. Use synthetic fixtures or
appropriately de-identified test data.

------------------------------------------------------------------------

# 25. Definition of Done and Release Gates

A feature or phase is not done merely because its happy path works.

## Mandatory test-after-every-phase rule

At the end of **every phase (Phases 0--10)**:

1.  Run the phase-specific tests listed in Section 23.
2.  Run the full relevant regression suite, including tests from earlier
    phases.
3.  Test normal, invalid, boundary, unauthorized, and failure/recovery
    paths where applicable.
4.  Record the test command, environment, test data/version, pass/fail
    result, and any defect in a test report.
5.  Fix critical and high-severity defects before proceeding. Any
    accepted lower-severity issue must have a documented reason, impact,
    owner, and follow-up task.
6.  Confirm the phase's exit criteria are met and commit/tag the
    known-good state.
7.  If a later change breaks an earlier phase, stop and fix the
    regression before continuing.

Do not mark a phase complete based only on a manual demonstration. Use
automated unit/integration/end-to-end tests wherever practical, plus
manual review for OCR quality, usability, and medical-language
correctness.

For each feature, require: - Acceptance criteria are documented. - Input
validation is implemented. - Authorization is tested. - Failure and
retry behavior is defined. - Unit and integration tests pass. - Logs do
not expose unnecessary sensitive data. - UI error and loading states are
implemented. - Relevant documentation is updated. - Evaluation metrics
are recorded where applicable.

## Release gates

### Gate A: Data foundation

-   Schema and ownership rules are stable.
-   Cross-patient access tests pass.
-   Provenance and correction history work.

### Gate B: Extraction

-   Supported file types are defined.
-   Uncertain values can be reviewed.
-   Extraction failures do not silently create trusted records.

### Gate C: Comparison

-   Deterministic comparison tests pass.
-   Incompatible measurements are flagged.
-   Historical source references are retained.

### Gate D: AI and multilingual output

-   Claims can be traced to evidence.
-   Numerical values and units remain faithful.
-   Critical unsupported claims are blocked according to agreed
    criteria.
-   Each released language passes its quality gate.

### Gate E: Production

-   Deletion, backup, recovery, monitoring, and security procedures are
    tested.
-   Workload and cost targets are measured.
-   Operational responsibilities are documented.

### Gate F: Clinical extension

-   Intended use and validation are documented.
-   Clinical review and release requirements are met.
-   Risk estimates are not presented outside the validated population or
    use.

------------------------------------------------------------------------

# 26. Risks, Dependencies, and Mitigations

  -----------------------------------------------------------------------
  Risk                    Consequence             Mitigation
  ----------------------- ----------------------- -----------------------
  OCR misreads numbers or Incorrect comparisons   Confidence flags,
  decimals                and explanations        review UI, field-level
                                                  evaluation

  Incorrect test matching False historical change Canonical test
                                                  concepts, compatibility
                                                  rules, manual review

  Inappropriate reference Incorrect abnormal      Preserve laboratory
  ranges                  flags                   ranges and source
                                                  context

  Unsupported LLM claims  Misleading medical      RAG, output validation,
                          explanation             source links,
                                                  critical-error testing

  Poor language coverage  Meaning changes in      Per-language evaluation
                          localized reports       and incremental rollout

  Unauthorized patient    Privacy breach          Backend authorization,
  access                                          ownership checks,
                                                  security tests

  Deletion misses         Residual sensitive data Central deletion
  vector/file copies                              workflow and
                                                  verification

  Duplicate processing    Duplicate measurements  Idempotency, hashes,
                          or analyses             unique constraints
                                                  where appropriate

  External API failure    Incomplete user         Timeouts, retries,
                          workflow                status tracking,
                                                  recoverable jobs

  Unvalidated disease     False reassurance or    No risk percentages
  prediction              alarm                   until validated

  Overengineering         Delayed delivery and    Modular monolith; scale
                          higher maintenance      only on measured need

  Unclear clinical        Unsupported claims or   Define scope and review
  intended use            compliance exposure     obligations before
                                                  deployment
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 27. Features to Defer

Do not add these to the initial build unless a specific requirement
justifies them:

-   Broad disease diagnosis from all available information.
-   Multiple disease-risk models at once.
-   Autonomous medication recommendations.
-   Unvalidated chest X-ray classification.
-   Voice interaction before text-based multilingual output is reliable.
-   Clinician portals and complex multi-role sharing before patient data
    isolation is robust.
-   Microservices and Kubernetes before workload evidence.
-   Automatic clinical alerts without validated rules and appropriate
    safety review.

The purpose of deferring features is to reduce delivery risk, not to
rule out future development.

------------------------------------------------------------------------

# 28. Open Decisions

The architecture is defined, but these decisions must be resolved before
the affected feature is released.

  -----------------------------------------------------------------------
  Decision                Current status          When required
  ----------------------- ----------------------- -----------------------
  Initial Indian-language Open; broad             Before multilingual
  list                    Indian-language support release
                          is the goal             

  Initial supported       Open; define            Before extraction
  document types          representative types    acceptance testing
                          and layouts             

  One or multiple patient Recommended: multiple   Before finalizing
  profiles per account    profiles with strict    ownership model
                          authorization; final    
                          confirmation needed     

  Deployment provider and Open                    Before deployment and
  hosting region                                  privacy review

  File size and retention Open; default retention Before production
  details                 is until user deletion  
                          subject to applicable   
                          obligations             

  Background-job          Select based on         Before asynchronous
  implementation          workload and deployment production processing
                          needs                   

  First disease-risk      Deliberately unselected After feasibility
  model                                           research

  Chest X-ray module      Optional separate       Before any imaging
                          module                  development

  Persistent medical R    ecommended: save only   fore Phase 2
  memory behavior         Be relevant structured  implementation; review
                          facts with source and   privacy UX
                          user controls; do not   
                          store all chat logs     

  Numeric evaluation      Set from baseline and   Before release gates
  thresholds              safety requirements     
  -----------------------------------------------------------------------

Do not let these open items block unrelated work. Record decisions and
their rationale as the project progresses.

------------------------------------------------------------------------

# 29. Final Build Checklist

-   [ ] Every phase (0--10) has passed its specific test gate before the
    next phase begins.
-   [ ] Test results, defects, fixes, and accepted exceptions are
    recorded.
-   [ ] The regression suite is rerun after changes that could affect
    completed phases.
-   [ ] Relevant medical facts can be saved from natural-language
    interactions and recalled in a later session.
-   [ ] Saved context is patient-scoped, source-attributed, reviewable,
    correctable, and deletable.
-   [ ] Unrelated queries do not receive irrelevant saved context, and
    ambiguous facts require confirmation.
-   [ ] Manual forms remain available but are not required for every new
    piece of medical history.

Use this checklist as the overall project tracker.

## Requirements and architecture

-   [ ] Requirements baseline approved.
-   [ ] First-release scope and deferred features agreed.
-   [ ] Architecture and data-flow diagrams reviewed.
-   [ ] API contracts defined.
-   [ ] Open decisions assigned.

## Database and security

-   [ ] MongoDB collections and indexes defined.
-   [ ] Ownership and authorization checks implemented.
-   [ ] Provenance and correction history implemented.
-   [ ] File storage access protected.
-   [ ] Deletion workflow defined and tested.
-   [ ] Secrets and logs handled safely.

## Ingestion and extraction

-   [ ] Upload validation implemented.
-   [ ] Digital PDF extraction tested.
-   [ ] OCR tested for supported document types/languages.
-   [ ] Structured extraction reviewed against reference annotations.
-   [ ] User verification UI implemented.
-   [ ] Retry and duplicate-processing behavior tested.

## Chunking and retrieval

-   [ ] Structure-aware chunking implemented.
-   [ ] Source locations and metadata preserved.
-   [ ] Embedding model evaluated.
-   [ ] ChromaDB retrieval tested.
-   [ ] Patient access filters and backend checks tested.
-   [ ] Re-indexing and deletion tested.

## Comparison and AI

-   [ ] Numerical comparison suite passes.
-   [ ] Incompatible units and tests are flagged.
-   [ ] Historical trends are traceable.
-   [ ] RAG sources are selected and versioned.
-   [ ] Quick summary is implemented.
-   [ ] Detailed explanations include source references.
-   [ ] Unsupported-claim tests pass required thresholds.

## Multilingual support

-   [ ] Initial language list approved.
-   [ ] OCR and NLP evaluated per language.
-   [ ] Medical concept normalization implemented.
-   [ ] Negation, dates, numbers, and units tested.
-   [ ] Output meaning and source fidelity evaluated.

## Release readiness

-   [ ] Security and privacy review completed.
-   [ ] Backup and recovery tested.
-   [ ] Monitoring and failure alerts implemented.
-   [ ] Latency and cost measured.
-   [ ] Documentation and runbook completed.
-   [ ] Release gates passed.

## Clinical extensions

-   [ ] Risk-model intended use defined before development.
-   [ ] Suitable data and validation method identified.
-   [ ] Independent evaluation completed.
-   [ ] Clinical review requirements met.
-   [ ] Imaging module independently validated if included.

------------------------------------------------------------------------

# 30. Glossary

-   **OCR:** Optical Character Recognition; extracts text from images or
    scanned pages.
-   **NLP:** Natural Language Processing; extracts and interprets
    information from human language.
-   **Embedding:** A numerical vector representing text for
    similarity-based retrieval.
-   **Vector database:** A system that stores and searches vectors,
    often for semantic similarity.
-   **Chunk:** A bounded section of a document used for retrieval.
-   **RAG:** Retrieval-Augmented Generation; supplies relevant source
    material to a generative model.
-   **Provenance:** Information describing where a record or claim came
    from.
-   **Canonical concept:** A normalized internal representation of a
    medical term across different wordings or languages.
-   **Calibration:** How closely predicted probabilities correspond to
    observed event frequencies in the relevant population.
-   **Longitudinal analysis:** Analysis of records and observations
    across time.
-   **Idempotency:** A property that makes repeating an operation safe
    without creating unintended duplicate effects.
-   **Acceptance criterion:** A testable condition that must be met
    before a feature is accepted.
-   **Clinical decision support:** Information that assists clinical
    reasoning without automatically establishing a diagnosis.

------------------------------------------------------------------------

# Final Recommendation

Close the planning phase with this document as the project baseline.
Begin with Phase 1: backend foundation, database schema, ownership
rules, and data lifecycle. Then build manual entry and report ingestion,
followed by deterministic comparisons, retrieval, quick summaries, and
multilingual evaluation.

Do not begin with disease prediction. Establish accurate data and
traceable comparisons first. The project's credibility will depend more
on correct measurements, faithful explanations, secure longitudinal
history, and measurable quality than on the number of AI models it uses.
