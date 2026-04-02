from app.routes.extract import router as extract_router
from app.routes.generate import router as generate_router
from app.routes.health import router as health_router
from app.routes.metrics import router as metrics_router

__all__ = ["extract_router", "generate_router", "health_router", "metrics_router"]
