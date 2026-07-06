from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.config import settings
from app.utils.logger import logger
from app.utils.db import connect_to_mongo, close_mongo_connection

# Import endpoints
from app.routes.qa import router as qa_router
from app.routes.explain import router as explain_router
from app.routes.quiz import router as quiz_router
from app.routes.summarize import router as summarize_router
from app.routes.recommend import router as recommend_router
from app.routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application-wide database connection startup and cleanup events."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# Initialize FastAPI App
app = FastAPI(
    title="EduGenie AI Assistant",
    description="A production-ready educational assistant offering tutoring, explanations, and roadmaps.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Set up CORS policies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist before mounting
settings.STATIC_PATH.mkdir(parents=True, exist_ok=True)
(settings.STATIC_PATH / "css").mkdir(parents=True, exist_ok=True)
(settings.STATIC_PATH / "js").mkdir(parents=True, exist_ok=True)
settings.TEMPLATES_PATH.mkdir(parents=True, exist_ok=True)

# Mount Static Assets and Templates
app.mount("/static", StaticFiles(directory=str(settings.STATIC_PATH)), name="static")
templates = Jinja2Templates(directory=str(settings.TEMPLATES_PATH))

# Mount Routers
app.include_router(auth_router)
app.include_router(qa_router)
app.include_router(explain_router)
app.include_router(quiz_router)
app.include_router(summarize_router)
app.include_router(recommend_router)

# --- Global Middlewares & Error Filters ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs details for incoming requests and measures processing time."""
    logger.info(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Outgoing: Status {response.status_code}")
    return response

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catches any unhandled exceptions to prevent server crashes and yields clean JSON."""
    logger.critical(f"CRITICAL: Unhandled crash on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "A critical system error occurred. Our engineers are investigating."}
    )

# --- Core Routes ---
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders the main EduGenie educational dashboard UI."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"default_model": settings.DEFAULT_MODEL}
    )

@app.get("/health")
async def health_check():
    """Verifies backend system connectivity and configuration status."""
    return {
        "status": "operational",
        "gemini_api_set": settings.is_gemini_configured(),
        "default_provider": settings.DEFAULT_MODEL,
        "lamini_model_name": settings.LAMINI_MODEL_NAME
    }
