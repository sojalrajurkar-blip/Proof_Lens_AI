# ProofLens AI — Architecture Decision Record (ADR-001)

**Document ID:** PLAI-ADR-001  
**Status:** Approved for MVP Implementation  
**Date:** October 2026  
**Context:** ProofLens AI is an evidence-first document intelligence web application designed for verifying claims, inspecting source passages, and cross-document comparison with strict provenance.

---

## 1. Summary of Architectural Decisions

### ADR-01: Authentication & Workspace Model
- **Decision:** **Single-User Workspace Mode (with Workspace ID scoping)** for the MVP.
- **Rationale:** The primary target is a college presentation, developer portfolio, and research reviewer demo. Requiring full OAuth/email signup creates friction during demonstrations. Workspaces are isolated by UUID, allowing multiple independent workspaces (e.g., "Research Papers", "Financial Reports") without multi-tenant authentication complexity.
- **Future Extensibility:** The backend database schema will include a `workspace_id` foreign key on all document and chunk tables, ensuring multi-user RBAC can be layered on top later without breaking schema changes.

### ADR-02: AI Provider & Models (Embeddings & Generation)
- **Decision:** **Google Gemini API** via the official `google-genai` Python SDK.
  - **LLM:** `gemini-2.5-flash` (fast, cost-effective, high context window, structured JSON output support).
  - **Embedding Model:** `text-embedding-004` (768 dimensions, high semantic accuracy for RAG).
- **Interface Abstraction:** All LLM calls and embedding requests will sit behind an abstract class `AIProvider` (`BaseEmbeddingProvider`, `BaseCompletionProvider`) in `backend/app/core/ai_provider.py`. This ensures zero vendor lock-in; swapping to local HuggingFace/Ollama models or OpenAI requires changing only the adapter.
- **Cost & Privacy:** Gemini 2.5 Flash has a free tier for development. Document snippets and queries are transmitted to Google's API via TLS. API keys are kept strictly on the backend via environment variables.

### ADR-03: Database & Vector Storage
- **Decision:** **PostgreSQL 18.4 + pgvector**.
- **Rationale:** PostgreSQL is already installed and verified on the local host. `pgvector` provides native vector indexing (`HNSW` / `IVFFlat`) and cosine distance (`<=>`) queries in standard SQL.
- **Fallback / Docker Support:** A `docker-compose.yml` with `pgvector/pgvector:pg16` or `pg18` will also be provided for turnkey reproduction on systems without a local PostgreSQL setup.
- **Migrations:** Alembic will manage all relational and vector table schemas.

### ADR-04: PDF Parsing, Chunking & Provenance
- **Decision:**
  - **PDF Parser:** `pypdf` (lightweight, zero native C-dependency overhead, fast text and page-metadata extraction) with graceful fallback error reporting.
  - **Scope:** Digital text-based PDFs only. Image-only/scanned PDFs will be detected and flagged with a friendly `UNSUPPORTED_SCANNED_PDF` status code instead of failing silently.
  - **Chunking Strategy:** Recursive character chunking (target: 500 tokens / ~1,800 characters, overlap: 50 tokens / ~200 characters) bound strictly to page boundaries. No chunk crosses multiple pages so page numbers remain 100% deterministic and verifiable.
  - **Limits:** Max 10 PDFs per workspace; Max 20MB per file; Max 100 pages per document for the MVP.

### ADR-05: Document Storage
- **Decision:** **Local File System Storage Abstraction** (`LocalStorageProvider`).
- **Storage Location:** `storage/uploads/{workspace_id}/{document_id}.pdf`.
- **Security:** Filenames are sanitized, paths are resolved strictly within the approved root directory to prevent directory traversal (`../`), and files are accessed through UUID identifiers.

### ADR-06: Grounding, Citation Validation & Abstention Policy
- **Decision:** **Two-Stage Verification Pipeline**:
  1. **Retrieval Threshold:** Top-$k$ chunks (default $k=5$) retrieved via cosine similarity. If the maximum similarity score falls below the minimum confidence threshold ($\tau = 0.65$), the system automatically abstains without calling the generation model.
  2. **Generation Prompt:** System prompt enforces: "Answer only using the retrieved excerpts provided in the context. Every factual statement must cite `[chunk_id]`. If the context does not contain sufficient facts to answer the question, state that evidence is insufficient."
  3. **Server-Side Citation Derivation:** The model outputs citation IDs (e.g., `["chunk_1"]`). The backend validates each ID against the actual retrieved list, extracts the verified `filename`, `page_number`, and `exact_excerpt`, and constructs the final response. The model is **never** permitted to hallucinate filenames or page numbers.

### ADR-07: Testing & Evaluation Strategy
- **Backend Tests:** `pytest`, `pytest-asyncio`, `httpx` for unit tests (chunker, parsers, citation validator) and integration tests (API routes, database queries).
- **Frontend Tests:** ESLint, TypeScript `tsc --noEmit`, Next.js production build validation.
- **RAG Evaluation Suite:** A version-controlled dataset `tests/eval_dataset.json` containing 15 test questions (10 answerable across sample PDFs, 5 unanswerable/out-of-scope) with an automated script measuring:
  - Retrieval Hit Rate (%)
  - Citation Precision (%)
  - Abstention Accuracy on out-of-scope questions (%)

---

## 2. Target Project Directory Structure

```text
Proof_Lens_AI/
├── .env.example                     # Placeholder configuration
├── .gitignore                       # Git exclusions for secrets, venvs, builds
├── README.md                        # Project documentation and quickstart
├── docs/                            # Specifications and ADRs
│   ├── ProofLens-AI-Master-Specification-Antigravity.md
│   └── ADR-001-Architecture-Decisions.md
├── storage/                         # Local uploaded PDFs (git-ignored)
│   └── uploads/
├── backend/                         # FastAPI application
│   ├── pyproject.toml / requirements.txt
│   ├── alembic.ini
│   ├── migrations/                  # Alembic database migrations
│   ├── app/
│   │   ├── main.py                  # App entrypoint and CORS setup
│   │   ├── config.py                # Pydantic BaseSettings
│   │   ├── database.py              # Async SQLAlchemy engine and sessionmaker
│   │   ├── models/                  # SQLAlchemy ORM models (Workspace, Document, Chunk)
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── api/                     # API routers
│   │   │   ├── v1/
│   │   │   │   ├── health.py        # Health & readiness probe
│   │   │   │   ├── workspaces.py    # Workspace management
│   │   │   │   ├── documents.py     # PDF upload, status, list, delete
│   │   │   │   ├── query.py         # Retrieval and Grounded Q&A
│   │   │   │   └── comparison.py    # Multi-document comparison
│   │   ├── services/                # Business logic
│   │   │   ├── pdf_service.py       # Page-level text extraction
│   │   │   ├── chunking_service.py  # Page-bound chunker
│   │   │   ├── embedding_service.py # Vector embedding generator
│   │   │   ├── retrieval_service.py # Vector similarity search
│   │   │   ├── qa_service.py        # Prompt assembly & answer synthesis
│   │   │   └── citation_service.py  # Citation ID validation & provenance enrichment
│   │   └── core/                    # Interfaces, exceptions, security
│   │       ├── ai_provider.py       # Abstract AI provider interface
│   │       └── exceptions.py        # Custom domain exceptions
│   └── tests/                       # Unit, integration, and eval tests
│       ├── test_health.py
│       ├── test_pdf_extraction.py
│       ├── test_chunking.py
│       ├── test_citation_validation.py
│       └── eval_dataset.json
└── frontend/                        # Next.js 14+ App Router frontend
    ├── package.json
    ├── next.config.mjs
    ├── tsconfig.json
    ├── src/
    │   ├── app/                     # Next.js routes
    │   ├── components/              # UI components (DocumentViewer, CitationInspector, etc.)
    │   └── lib/                     # API client, types, utilities
```

---

## 3. Dependency Justification

### Backend (Python 3.12+)
- `fastapi` & `uvicorn`: High performance asynchronous API framework with native OpenAPI documentation.
- `pydantic` & `pydantic-settings`: Typed data validation and strictly validated environment settings.
- `sqlalchemy` & `asyncpg`: Async PostgreSQL driver and ORM.
- `pgvector`: Official Python binding for PostgreSQL vector extension.
- `alembic`: Predictable database schema migrations.
- `pypdf`: Clean, fast, pure-Python page-aware text extraction without external binaries.
- `google-genai`: Official Google Gemini SDK for embeddings and LLM calls.
- `pytest` & `pytest-asyncio` & `httpx`: Reliable testing harness.

### Frontend (Node.js 24+, Next.js 14+ with App Router)
- `next`: React production framework with server-side rendering and static optimization.
- `lucide-react`: Lightweight, clean iconography for research workspace UI.
- Standard CSS / Tailwind CSS for editorial research aesthetic.
