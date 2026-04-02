import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.exceptions import CVUMLException, LLMProviderError, UnsupportedFileError
from app.llm import warmup
from app.logging_config import RequestLoggingMiddleware, setup_logging
from app.routes import extract_router, generate_router, health_router, metrics_router

setup_logging(json_format=settings.log_json, level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Warming up LLM...")
    if warmup():
        logger.info("LLM ready")
    else:
        logger.warning("LLM warmup failed - will initialize on first request")
    yield


app = FastAPI(
    title="Diagram2Algo",
    description="Extract algorithms from diagram images and documents",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(extract_router)
app.include_router(generate_router)
app.include_router(metrics_router)



@app.exception_handler(UnsupportedFileError)
async def unsupported_file_handler(request: Request, exc: UnsupportedFileError):
    return JSONResponse(status_code=400, content={"error": exc.message, "detail": exc.detail})


@app.exception_handler(LLMProviderError)
async def llm_provider_handler(request: Request, exc: LLMProviderError):
    return JSONResponse(status_code=503, content={"error": exc.message, "detail": exc.detail})


@app.exception_handler(CVUMLException)
async def cvuml_handler(request: Request, exc: CVUMLException):
    return JSONResponse(status_code=500, content={"error": exc.message, "detail": exc.detail})


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
