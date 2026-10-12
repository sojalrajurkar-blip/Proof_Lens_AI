# ProofLens AI — Backend Service

FastAPI-powered document intelligence and grounded Q&A engine.

## Prerequisites

- Python 3.12+
- Local PostgreSQL 18+ with `pgvector` extension

## Local Setup

1. **Activate the Virtual Environment:**
   - On Windows (PowerShell):
     ```powershell
     .\backend\.venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     source backend/.venv/bin/activate
     ```

2. **Environment Variables:**
   Copy `.env.example` at the repository root to `.env` and fill in any customized values.

3. **Run the Development Server:**
   ```powershell
   backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Verify:**
   - Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Health Probe: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

## Running Tests

From the `backend` folder:
```powershell
backend\.venv\Scripts\pytest.exe -v
```
