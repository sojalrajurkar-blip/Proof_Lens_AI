# ProofLens AI — From Documents to Verifiable Answers

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4-black.svg)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-3.5_Flash_Lite-4285F4.svg)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-28%2F28_Passing-success.svg)](backend/tests)
[![Evaluation](https://img.shields.io/badge/Benchmark-100%25_Accuracy-brightgreen.svg)](evaluation)

**ProofLens AI** is an evidence-first document intelligence platform. Rather than presenting generative AI outputs as infallible truth, ProofLens AI enforces **strict page-level provenance**, **server-side citation verification**, **explicit abstention on ungrounded claims**, and **side-by-side cross-document comparison**.

---

## 🌟 Key Architecture Invariants

1. **Page-Aware PDF Parsing:** Pure-Python extraction via `pypdf` recording exact page boundaries and character counts. Scanned PDFs without extractable text are immediately flagged with `UNSUPPORTED_SCANNED_PDF`.
2. **Page-Bound Chunking:** Chunks **never cross page boundaries**, ensuring that citations point unambiguously to a single physical page.
3. **Workspace Isolation:** Every document and embedding vector is bound to a specific workspace ID. Semantic search strictly enforces cross-workspace tenant boundaries.
4. **Server-Side Citation Validation Engine:**
   - The LLM does not generate verifiable links directly.
   - The backend cross-references cited chunk IDs against database records.
   - Any hallucinated chunk IDs are **silently dropped**.
   - If an answer loses all valid citations, the system forces an **abstention (`INSUFFICIENT_EVIDENCE`)**.
5. **Cross-Document Comparative Synthesis:**
   - Performs independent retrieval per document.
   - Classifies inter-document relationships: `AGREEMENT`, `DIFFERENCE`, `CONTRADICTION`, or `INSUFFICIENT_EVIDENCE`.
   - Generates scope warnings when documents address different abstraction layers (e.g. network routing vs. REST APIs).
6. **Passage Provenance Inspector:** Clickable citation badges in the UI open a full-fidelity modal displaying the verbatim chunk text, similarity score, and adjacent chunk (`prev`/`next`) navigation.

---

## 🏗️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), SQLite / PostgreSQL 18.4, pypdf |
| **AI Providers** | Google GenAI SDK (`google-genai`), `gemini-3.5-flash-lite`, `gemini-embedding-001` (with deterministic mock fallbacks for offline testing) |
| **Frontend** | Next.js 16 (App Router), TypeScript, Tailwind CSS, Lucide Icons |
| **Evaluation** | Automated benchmark runner (`evaluate_system.py`), pytest async test suite (28 tests) |

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+** and **npm**
- **Google Gemini API Key** (Get free key from [Google AI Studio](https://aistudio.google.com/))

### 2. Clone & Configure Environment
```bash
git clone https://github.com/sojalrajurkar-blip/Proof_Lens_AI.git
cd Proof_Lens_AI

# Copy environment variables
cp .env.example .env
```
Edit `.env` and set your Gemini API key:
```ini
GEMINI_API_KEY="your-gemini-api-key-here"
GEMINI_CHAT_MODEL="gemini-3.5-flash-lite"
GEMINI_EMBEDDING_MODEL="gemini-embedding-001"
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv backend/.venv

# Activate virtual environment
# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 🖥️ Running the Application

### 1. Start the Backend API
From the project root with the virtual environment activated:
```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Start the Next.js Frontend
In a new terminal:
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing & Evaluation

### Run Automated Unit & Integration Tests (28 Tests)
```bash
.\backend\.venv\Scripts\pytest -v
```
All 28 tests run using an in-memory SQLite database and test fixtures. They cover:
- Page-boundary preservation during chunking
- Scanned PDF detection
- Semantic retrieval and workspace scope isolation
- Server-side citation validation and hallucination rejection
- Adversarial prompt injection attacks & abstention enforcement
- Cascading document deletion
- Cross-document comparison classification

### Run End-to-End System Evaluation Benchmark
```bash
.\backend\.venv\Scripts\python backend/scripts/evaluate_system.py
```
This script uploads the sample documents (`sample_docs/Assignment1.pdf` and `sample_docs/Assignment2.pdf`), executes the 11 benchmark test cases via live Gemini models, and outputs a precision/recall report:

```text
===============================================================================================
  BENCHMARK METRICS & ACCEPTANCE SUMMARY
===============================================================================================
Total Benchmark Cases Evaluated:           11
Overall Passed:                            11/11 (100.0%)
  - In-Domain Factual QA Accuracy:         4/4 (100.0%)
  - Out-of-Domain Abstention Recall:       3/3 (100.0%)
  - Adversarial Injection Resistance:      2/2 (100.0%)
  - Cross-Document Comparison Accuracy:    2/2 (100.0%)
===============================================================================================
```
Results are exported to `evaluation/eval_results.json`.

---

## 🛡️ Security & Privacy Guardrails

- **Zero Untrusted Citations:** The server never trusts citation IDs or quotes returned by the LLM. Only chunks physically verified in the database are presented to the user.
- **Prompt Injection Defense:** Reference passages in LLM prompts are wrapped in strict system instruction delimiters stating that passage contents are untrusted data and must never be interpreted as instructions.
- **Tenant Scope Isolation:** Document retrieval, question answering, and comparisons are strictly parameterized by `workspace_id`. Queries in Workspace A can never retrieve or cite data from Workspace B.
- **Secret Hygiene:** All API keys and database credentials reside strictly in local `.env` files and are git-ignored.

---

## 📂 Repository Structure

```text
Proof_Lens_AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI route handlers (workspaces, documents, query, comparison)
│   │   ├── core/                # AI provider abstractions (Gemini + Mock)
│   │   ├── models/              # SQLAlchemy models (Workspace, Document, Page, Chunk)
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── services/            # Business logic (PDF, chunking, retrieval, QA, comparison)
│   ├── scripts/
│   │   └── evaluate_system.py   # Benchmark evaluation runner
│   └── tests/                   # 28 automated pytest test cases
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router (page.tsx, layout.tsx, globals.css)
│   │   ├── components/          # Header, Sidebar, QAView, ComparisonView, PassageModal
│   │   └── lib/                 # API client (api.ts) & TypeScript interfaces (types.ts)
├── evaluation/
│   ├── eval_dataset.json        # Benchmark dataset (11 structured cases)
│   └── eval_results.json        # Quantitative evaluation report
├── sample_docs/                 # Real PDF documents for testing & verification
├── docs/                        # Architecture decisions & master specifications
├── PROGRESS.md                  # Detailed phase-by-phase implementation log
└── README.md                    # Project documentation
```

---

## 📄 License
MIT License.
