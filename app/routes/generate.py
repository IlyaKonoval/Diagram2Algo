import logging

from fastapi import APIRouter

from app.models import GenerateRequest, GenerateResponse
from app.plantuml import generate_activity_diagram, generate_sequence_diagram, render_plantuml

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_diagram(request: GenerateRequest):
    try:
        if request.diagram_type == "sequence":
            plantuml = generate_sequence_diagram(request.steps, request.title)
        elif request.diagram_type == "activity":
            plantuml = generate_activity_diagram(request.steps, request.title)
        else:
            plantuml = generate_sequence_diagram(request.steps, request.title)

        png_base64 = render_plantuml(plantuml)

        return GenerateResponse(
            plantuml_code=plantuml,
            png_base64=png_base64,
        )

    except Exception as e:
        logger.exception("Generation failed")
        return GenerateResponse(
            plantuml_code="",
            error=str(e),
        )
