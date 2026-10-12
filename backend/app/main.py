import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.api.v1.health import router as health_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.documents import router as documents_router
from app.api.v1.query import router as query_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prooflens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables if connected
    logger.info("Initializing ProofLens AI application...")
    await init_db()
    yield
    logger.info("Shutting down ProofLens AI application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ProofLens AI — From Documents to Verifiable Answers",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safe global exception handler avoiding internal stack trace exposure."""
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "path": request.url.path,
        },
    )


# Include API Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
