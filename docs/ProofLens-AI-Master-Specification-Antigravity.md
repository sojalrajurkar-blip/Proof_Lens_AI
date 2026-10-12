# ProofLens AI — Master Project Specification and Phase-Gated Implementation Plan

**Document ID:** PLAI-MASTER-001  
**Version:** 1.0  
**Status:** Proposed execution contract — owner approval required at every phase  
**Product:** ProofLens AI — From Documents to Verifiable Answers  
**Purpose:** This document is the single implementation guide for Antigravity. Follow it phase by phase. Do not treat it as permission to implement every phase automatically.

---

## 1. Mandatory Operating Contract

These rules override any convenience-driven implementation behaviour.

### 1.1 Owner approval is required before every phase

- Work on **one phase only at a time**.
- Before starting a phase, provide a **Phase Proposal** in plain English and wait for explicit approval from the project owner.
- Do not start the next phase until the owner reviews the previous phase's report and explicitly approves the next phase.
- Silence, ambiguous messages, or a request to explain something do **not** count as approval.
- Approval applies only to the named phase and its agreed scope. It is not blanket permission for later phases.
- If an issue requires work outside the approved scope, stop and request permission before making that change.
- If the owner rejects a proposal or asks questions, answer and revise the proposal; do not begin implementation.
- Never claim that a phase is complete merely because files were generated. Completion requires execution and inspection of the relevant checks.

### 1.2 Before asking for approval, explain the phase completely

For each phase, first present a **Phase Proposal** containing:

1. **Purpose:** Why this phase is needed.
2. **Work included:** Exact functionality and tasks planned.
3. **Expected outcome:** What the owner will be able to see or do after it.
4. **Files likely to be created or changed:** Based on repository inspection; do not invent exact existing paths before inspecting.
5. **Dependencies and tools:** Packages, runtimes, services, database extensions, AI-provider accounts/API keys, or other resources required.
6. **How to obtain requirements:** Give beginner-friendly steps for installing or checking tools and obtaining/configuring credentials. Never ask the owner to paste secrets into chat or source code.
7. **Cost and privacy implications:** State likely external API usage, paid/free tier uncertainties, data sent to providers, and local-vs-hosted implications. Do not promise that a service is free unless verified.
8. **Commands and checks:** The commands that will be run and what each checks.
9. **Tests and acceptance criteria:** Observable conditions that must pass to call the phase complete.
10. **Risks and decisions:** Known limitations, assumptions, and questions that genuinely block the phase.
11. **Permission question:** Ask the owner clearly whether they approve this specific phase.

Do not overwhelm the owner with questions that do not affect architecture, cost, privacy, or scope. Recommend conservative defaults, explain them, and ask only for consequential decisions.

### 1.3 Safe execution and tool use

- Start with terminal and repository inspection. **Do not use browser automation or browser navigation unless the owner explicitly authorizes it.**
- Use bounded terminal commands. Do not launch indefinite waits, leave unexplained background processes, or repeatedly retry a failing command. At most one safe retry, then stop and report.
- Never expose, print, commit, or hard-code secret values. Provide `.env.example` with placeholder names only; ensure actual `.env` files are git-ignored.
- Do not delete, reset, clean, overwrite, or reformat unrelated user work.
- Preserve the current Git branch and existing changes. Do not commit, push, deploy, change external services, or perform destructive database operations without separate explicit approval.
- Do not install dependencies or change project configuration during a read-only discovery phase.
- Do not claim a command, test, route, database operation, or feature works unless it was actually executed and its output inspected.
- Label results accurately as **VERIFIED**, **PARTIALLY VERIFIED**, **NOT VERIFIED**, or **BLOCKED**.
- If a command or tool is unavailable, explain the limitation and provide a safe alternative; do not invent results.
- If the repository already contains code, audit and reuse it where appropriate instead of creating duplicates or rebuilding the project blindly.
- Keep changes small and focused. Do not combine multiple phases in one large generation task.

---

## 2. Product Definition

ProofLens AI is an evidence-first document intelligence web application. It helps users investigate a defined collection of documents by asking questions, inspecting source passages, and comparing claims across documents.

The product must not present generated text as verified truth. Its distinguishing behaviours are:

- Answers grounded in retrieved document evidence.
- Citations linked to actual source documents and page numbers.
- Inspection of the supporting excerpt.
- Explicit insufficient-evidence responses when support is missing or weak.
- Evidence-backed comparison of findings across multiple documents.
- Repeatable evaluation of retrieval, citation validity, and abstention behaviour.

This is not merely a PDF chatbot. It is a focused document workspace for traceable, testable answers.

### 2.1 Primary users

- College students preparing projects and presentations.
- Researchers reviewing a small collection of papers and reports.
- Developers or project teams comparing technical documents.

### 2.2 First-release goals

1. Build a polished, usable web application suitable for a college presentation and developer portfolio.
2. Upload and process a manageable set of PDF documents.
3. Preserve page-level provenance through parsing, chunking, retrieval, and answers.
4. Perform semantic retrieval using embeddings and vector search.
5. Generate evidence-grounded answers with validated citations.
6. Clearly report insufficient or conflicting evidence.
7. Compare findings across selected documents with supporting citations.
8. Provide a small, repeatable evaluation suite.
9. Keep the code modular and understandable so the underlying RAG pipeline can be learned and tested.

### 2.3 Explicit non-goals for the MVP

Do not add these unless the owner approves a written scope change:

- Autonomous agents or multi-agent orchestration.
- LangGraph, MCP, or LangChain solely for branding.
- Foundation-model training or fine-tuning.
- Claims of infallible truth detection.
- Unrestricted web browsing or live web research.
- General-purpose OCR for all scanned PDFs.
- Enterprise SSO, billing, or multi-tenant SaaS features.
- Support for every file type and language.
- AI replacement of human judgement in high-stakes decisions.

The initial implementation may use direct provider SDK/API calls. Reconsider a framework only after the basic pipeline works and a concrete need is demonstrated.

---

## 3. Target Architecture

This is the target direction, not permission to overwrite a different existing architecture before discovery.

### Frontend

- Next.js.
- A professional, responsive interface for the workspace, document library, upload and processing states, question-and-answer view, citations/evidence viewer, comparison, and evaluation summary.
- Clear loading, empty, success, error, unsupported, and uncertain states.
- Keyboard-accessible controls and readable citation labels.

### Backend

- Python + FastAPI.
- Pydantic request/response schemas.
- Small, clearly separated modules for configuration, document ingestion, PDF parsing, chunking, embeddings, retrieval, answer generation, citation validation, comparison, and evaluation.
- Provider-specific integrations behind small interfaces.
- Typed, validated API inputs and safe error responses.

### Data

- PostgreSQL for application records and document/chunk metadata.
- pgvector for embedding storage and similarity search, after compatibility is checked.
- Database migrations and documented development/test data.
- A storage abstraction for uploaded originals. Use local storage during development if suitable; defer production object storage until deployment requirements are approved.

### AI pipeline

1. Validate the uploaded PDF.
2. Extract text while preserving page identity.
3. Chunk text and preserve document ID, page number, chunk index, and metadata.
4. Generate embeddings using a configurable provider.
5. Persist chunks and vectors.
6. Embed the user's question and retrieve relevant chunks only from the authorized workspace/document scope.
7. Assemble evidence for answer generation.
8. Generate a structured answer from the evidence, not from unsupported outside knowledge.
9. Validate each citation against actual retrieved source records and derive filenames/page numbers server-side.
10. Apply an explicit evidence sufficiency/abstention policy.
11. Return the answer, validated citations, supporting excerpts, and uncertainty/status metadata.

---

## 4. Required MVP Functional Scope

### FR-01 — Workspace and document library

- Create or select a workspace according to the approved authentication/demo decision.
- Upload multiple PDFs within configured file-count and file-size limits.
- Record a stable document ID, original filename, size, upload time, and processing status.
- Handle duplicate uploads and failed ingestion predictably.
- Display processing, success, and failure states.

### FR-02 — PDF extraction and provenance

- Extract text from supported PDFs.
- Preserve page-level source locations.
- Report empty, malformed, unsupported, or unreadable PDFs with useful errors.
- Keep original file identity associated with all extracted content and chunks.
- Scanned PDFs can be reported unsupported in the MVP unless OCR is explicitly approved.

### FR-03 — Chunking and embeddings

- Make chunking settings configurable.
- Preserve document ID, page number, chunk index, and useful metadata for every chunk.
- Integrate a configurable embedding provider.
- Validate embedding dimensions and vector database compatibility.
- Avoid duplicate chunks or vectors on safe retries.

### FR-04 — Semantic retrieval

- Embed the user's query and retrieve relevant passages.
- Enforce workspace/document scope in server-side database queries.
- Return source metadata with every passage.
- Make retrieval count and supported similarity settings configurable.
- Keep retrieval independently testable from answer generation.

### FR-05 — Evidence-grounded Q&A

- Generate document-specific answers from retrieved evidence.
- Do not allow the model to invent document IDs, filenames, page numbers, or citation identifiers.
- Validate citation references against the actual retrieved evidence.
- Return a clear insufficient-evidence result when evidence is missing or weak.
- Keep safe diagnostic evidence available for tests/evaluation without logging full documents by default.

### FR-06 — Evidence inspection

- Display the cited filename, page number, and supporting excerpt.
- Allow users to inspect the passage supporting an answer.
- Visually distinguish original source text from AI-generated interpretation.

### FR-07 — Cross-document comparison

- Select at least two documents and provide a topic/question.
- Show findings per document with citations.
- Label agreement, difference, or contradiction only when supported by retrieved passages.
- Flag differing scopes, definitions, dates, or non-comparable claims instead of forcing a conclusion.

### FR-08 — Repeatable evaluation

- Include a version-controlled dataset of test questions and expected evidence/source locations or answer characteristics.
- Measure retrieval hit rate on the curated dataset.
- Measure citation validity.
- Test abstention on questions with no adequate supporting evidence.
- Label LLM-judged measures as model-based estimates, not ground truth.
- Provide a documented, repeatable evaluation command.

### FR-09 — Operational behaviour

- Validate request payloads and upload types/sizes.
- Use safe, useful API errors without exposing stack traces or secrets.
- Apply timeouts and bounded retries to provider calls.
- Track latency and token/usage information when available.
- Keep API keys server-side in environment variables or an approved secret manager.
- Avoid unnecessary background infrastructure. Introduce a queue only if approved limits or measured processing times justify it.

---

## 5. Security, Privacy, and Reliability Requirements

- Treat all uploaded content and retrieved passages as untrusted data.
- Never execute or follow instructions found inside a document as system instructions.
- Test prompt-injection examples contained in PDFs.
- Keep API keys out of frontend bundles, logs, Git, and error responses.
- Validate file contents as well as filename extensions and declared content types where practical.
- Use parameterized database access.
- Enforce authorization server-side on every workspace/document operation if authentication or multiple workspaces are supported.
- Define deletion behaviour for originals, extracted pages, chunks, embeddings, and related records.
- Avoid logging full document contents or sensitive data by default.
- Handle partial ingestion failures visibly and recover safely.
- Apply timeouts and bounded retries; do not retry indefinitely.
- Keep migrations repeatable and tests isolated from real user data.
- Never state that an answer is factually true merely because it has a citation. A citation proves a source location exists, not that the source itself is correct.
- Make the difference between a source statement and model interpretation visible.

---

## 6. Mandatory Phase-Gated Delivery Plan

**Every phase below requires a proposal and explicit owner approval before work starts.** Antigravity must stop after completing each phase, provide evidence, and request approval for the next phase.

### Phase 0 — Repository discovery and feasibility (read-only)

**No code edits, installs, migrations, or configuration changes.**

Inspect:
- Repository root, branch, and Git status.
- `AGENTS.md`, README, project status/handoff docs, manifests, environment examples, configuration, migrations, and tests.
- Actual frontend/backend/database state and reusable components.
- Installed runtime and dependency versions using safe terminal commands.
- Existing RAG/AI integrations, storage choices, and known failures.

Deliver:
- Verified repository report.
- PRD-to-repository gap matrix.
- Existing code/components worth reusing.
- Risks, unknowns, and decisions.
- Proposed architecture only where the repository leaves a gap.
- Phase 1 proposal, file plan, dependencies, setup instructions, costs/privacy, commands, and acceptance criteria.

**Exit criteria:** report is complete, evidence-based, and no repository files have been changed.

Stop and request approval before Phase 1.

### Phase 1 — Architecture decisions and development plan

After approval, finalize only the decisions required for a minimal implementation:
- Whether the demo is single-user or requires authentication.
- LLM and embedding provider/model, including API availability and cost/privacy implications.
- Local PostgreSQL and pgvector compatibility/setup.
- File count/size limits and supported PDF scope.
- Local file storage approach.
- Test strategy and conservative evidence/abstention policy.

Deliver:
- Architecture decision record.
- Minimal directory/module plan adapted to the actual repository.
- Environment-variable reference with placeholders only.
- Dependency justification.
- Updated milestone plan and exact Phase 2 proposal.

Do not build the whole application in this phase. Stop for approval.

### Phase 2 — Minimal backend foundation

Implement only the approved foundation:
- FastAPI application entry point.
- Centralized settings and environment configuration.
- Health endpoint.
- Typed error/response conventions.
- Lint, formatting, type-checking, and test setup where justified.
- Safe `.env.example` and `.gitignore` updates if required.
- Setup/run documentation.

Do not implement full RAG or the frontend yet unless an existing project makes a small prerequisite necessary and the owner approves it.

Validation:
- Run the backend using a bounded terminal command.
- Call the health endpoint using a terminal HTTP client.
- Run the configured lint/type/test commands.
- Inspect the final Git diff and confirm no secrets were added.

Deliver exact commands, actual outputs/results, files changed, known gaps, and Phase 3 proposal. Stop for approval.

### Phase 3 — Database and PDF ingestion/provenance

Implement the approved minimum:
- Database connection and migrations.
- Minimal workspace/document/page/chunk schema as justified by the approved design.
- PDF upload validation and explicit file limits.
- Page-aware text extraction.
- Document processing status and useful failures.
- Safe local storage abstraction.
- Duplicate/retry handling that avoids duplicate persisted content.

Validation:
- Test a valid PDF, empty/malformed/unsupported PDF, and configured size-limit cases.
- Verify extracted text retains correct page provenance.
- Verify database records correspond to the uploaded document.
- Test failure/retry behaviour and deletion semantics that are in scope.
- Use a test database or isolated test fixtures; do not destroy existing data.

Deliver sample run instructions, actual test results, schema/migration summary, and Phase 4 proposal. Stop for approval.

### Phase 4 — Embeddings and semantic retrieval

Implement:
- Configurable embedding-provider adapter.
- Chunking configuration.
- pgvector schema/index only after compatibility checks.
- Embedding persistence with dimensions validation.
- Semantic retrieval endpoint scoped to the selected authorized document/workspace set.
- Retrieval code independently testable from answer generation.

Validation:
- Verify persisted vectors and metadata.
- Test relevant queries against a small curated set.
- Test document/workspace scope isolation.
- Run a basic retrieval hit-rate evaluation.
- Exercise provider timeout/error handling without exposing secrets.

Deliver retrieval evidence, metric definitions/results, limitations, and Phase 5 proposal. Stop for approval.

### Phase 5 — Evidence-grounded Q&A, citation validation, and abstention

Implement:
- Structured answer schema.
- Evidence assembly from retrieved passages.
- Server-derived citation metadata.
- Citation-ID validation against real retrieved records.
- Explicit insufficient-evidence behaviour.
- Safe, bounded provider timeouts/retries.
- Separation of source text and model-generated interpretation.

Validation:
- Answerable question returns citations to real document/page records.
- Unsupported question abstains rather than guessing.
- Invalid/invented citation identifiers are rejected or omitted safely.
- No source metadata is accepted solely because the LLM supplied it.
- Provider failure produces a safe API error.
- Prompt-injection sample does not override application instructions.

Deliver real request/response examples with secrets and sensitive text removed, actual test results, known limitations, and Phase 6 proposal. Stop for approval.

### Phase 6 — Evidence viewer and cross-document comparison API

Implement:
- Source passage inspection.
- Per-document comparison findings.
- Evidence-backed agreement/difference/contradiction classification where justified.
- Warnings for scope or definition mismatch.
- Tests for citation correctness and unsupported comparisons.

Validation:
- A user can inspect a cited excerpt and its page.
- Each comparison finding links to its own source evidence.
- The application does not invent a contradiction when evidence is insufficient.
- Relevant API tests pass.

Deliver API behaviour, actual test results, and Phase 7 proposal. Stop for approval.

### Phase 7 — Next.js frontend

Implement or integrate a responsive interface appropriate to the existing repository:
- Workspace/document library.
- PDF upload and processing states.
- Question-and-answer interface.
- Answer citations and source excerpt inspection.
- Cross-document comparison.
- Evaluation summary.
- Loading, empty, success, error, and insufficient-evidence states.
- Keyboard accessibility and readable labels.

Design direction:
- Polished, restrained, editorial research-workspace aesthetic.
- Clear information hierarchy and visible source provenance.
- Do not create a generic template-heavy interface.
- Do not add customer-facing AI features unrelated to the approved document workflow.
- Avoid decorative animations that obscure evidence or impair accessibility.

Validation:
- Use terminal checks for lint, type checks, tests, and production build.
- Verify frontend API configuration and error handling.
- Do not use browser automation/navigation unless separately authorized by the owner.
- If a UI behaviour cannot be verified without a browser, label it NOT VERIFIED and explain the safe manual check the owner can perform.

Deliver files changed, terminal outputs, UI implementation summary, remaining manual checks, and Phase 8 proposal. Stop for approval.

### Phase 8 — Evaluation, security, reliability, and end-to-end readiness

Implement only approved hardening work:
- Curated evaluation dataset.
- Retrieval hit-rate and citation-validity metrics.
- Abstention tests.
- Prompt-injection test samples.
- Upload validation and workspace isolation tests where applicable.
- Deletion and retry consistency tests.
- Documentation for local setup, environment variables, sample PDFs, evaluation, and troubleshooting.
- A reproducible end-to-end demonstration procedure.

Validation:
- Run all relevant tests and report the exact commands and results.
- Run the documented evaluation command.
- Inspect Git diff/status and scan for accidentally tracked secrets.
- Clearly list any manual checks not executed.
- Do not claim production readiness unless deployment-specific security, storage, monitoring, and operational requirements have actually been verified.

Deliver final acceptance matrix mapping every PRD requirement to evidence, test result, or an explicit outstanding limitation. Stop and request approval for any additional phase.

### Phase 9 — Optional deployment (separate approval required)

Deployment is not automatic. Before any deployment work, provide a separate proposal covering:
- Hosting options and current pricing/limits to verify.
- Database hosting, pgvector availability, backups, network/TLS, and migration plan.
- File/object storage, retention, and deletion.
- Environment secrets and allowed origins.
- Logging, monitoring, quotas, privacy, and provider costs.
- Rollback and recovery approach.

Do not create external resources, change DNS, run production migrations, or deploy without explicit approval for those actions. Local MVP completion does not imply production readiness.

---

## 7. Definition of Done

The project is not considered complete just because the UI looks finished or the server starts.

The approved MVP is complete only when:

1. Multiple supported PDFs can be uploaded and their processing state is accurate.
2. Extracted chunks retain correct document and page provenance.
3. Semantic retrieval finds relevant passages within the intended document/workspace scope.
4. Grounded answers cite only real source locations from retrieved evidence.
5. Unsupported questions receive an explicit insufficient-evidence response.
6. Cited excerpts can be inspected.
7. Cross-document comparisons present evidence per finding and avoid unsupported contradictions.
8. Tests cover ingestion, provenance, retrieval, citations, abstention, and key security behaviours.
9. A documented evaluation command runs repeatably and states its limitations.
10. Setup instructions let another developer run the approved local project.
11. Secrets are not committed or exposed to the frontend.
12. A prepared sample dataset supports an end-to-end demonstration.
13. Each claimed result is backed by executed checks or clearly labelled as unverified.
14. The owner has reviewed the final acceptance matrix.

If any item is incomplete, list it as outstanding. Do not silently downgrade acceptance criteria.

---

## 8. Required Reporting Format After Every Phase

Use this format after the work in each approved phase:

### A. Phase summary
- Phase number and name.
- Approved scope.
- What was actually implemented or inspected.

### B. Files changed
For each file, explain why it was created/changed. Do not list files that were not actually changed as completed work.

### C. Dependencies and setup
- Packages added/removed and justification.
- Required tools/services/accounts.
- Environment variable names only; never include secret values.
- Clear instructions for obtaining/configuring anything the owner must provide.

### D. Verification evidence
A table with:
- Check/command.
- Expected result.
- Actual result.
- Status: VERIFIED / PARTIALLY VERIFIED / NOT VERIFIED / BLOCKED.

Include relevant command output summaries. Never invent results.

### E. What this enables
Explain in beginner-friendly language what the owner can now run, see, or demonstrate.

### F. Remaining issues
List bugs, limitations, technical debt, manual checks, and decisions that remain unresolved.

### G. Next phase proposal
Before the next phase begins, explain:
- Why it is needed.
- Exact scope and expected outcome.
- Expected files and dependencies.
- What the owner needs to install, configure, or provide, with step-by-step instructions.
- Cost/privacy implications.
- Validation plan and acceptance criteria.
- Any decision needed from the owner.

Finish by asking: **“Do you approve Phase N+1 as described? I will not start it until you explicitly approve.”**

Then STOP. Do not continue to the next phase in the same run.

---

## 9. Owner-Friendly Communication Requirements

The owner is learning and must be able to understand the project decisions.

- Explain technical terms briefly when they first matter.
- Before asking the owner to install a tool, explain what it does, why it is needed, how to check whether it is already installed, and the safe installation/configuration path.
- Distinguish local requirements from production/deployment requirements.
- State whether an external service may cost money and what data would be sent to it.
- Give exact commands and identify the directory in which each command should run.
- Explain expected command output and what to do if it differs.
- Do not ask the owner to paste API keys, passwords, tokens, or other secrets into chat.
- Prefer one manageable task at a time.
- When the owner asks a question, answer it without treating the question as phase approval.
- Never imply that a feature is complete if it is only mocked, simulated, stubbed, or untested.

---

## 10. Initial Instruction to Antigravity

When this file is first provided, perform **Phase 0 only**.

Do not begin Phase 1 or any coding.

Read this specification and all applicable repository instructions. Inspect the repository in read-only mode using bounded terminal commands. Then present the Phase 0 discovery report and the full Phase 1 proposal, including what is needed, how to obtain it, what will change, costs/privacy, commands, and acceptance criteria.

End by asking for explicit approval to begin Phase 1, and stop.

**The owner controls phase progression. No approval means no implementation.**
