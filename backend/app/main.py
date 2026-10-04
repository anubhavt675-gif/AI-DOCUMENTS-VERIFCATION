"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, health, ml, advanced_ml, blockchain, ipfs, integrity, demo
from app.config import get_settings
from app.database import create_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Official Government Document Anomaly Detection & Integrity Verification System API.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ml.router)
app.include_router(advanced_ml.router)
app.include_router(advanced_ml.doc_ml_router)
app.include_router(blockchain.router)
app.include_router(ipfs.router)
app.include_router(integrity.router)
app.include_router(demo.router)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc)},
    )


