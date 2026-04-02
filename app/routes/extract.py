import io
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse
from PIL import Image

from app.config import LLMProvider, settings
from app.formatters import format_result_html, format_result_text
from app.llm import image_inference
from app.models import BatchResult, ExtractionResult
from app.ocr import extract_text, is_tesseract_available
from app.pipeline import process_path
from app.postprocessing import parse_llm_response
from app.preprocessing import preprocess_image
from app.prompts import (
    IMAGE_PROMPT,
    IMAGE_PROMPT_EN,
    IMAGE_PROMPT_EN_NO_OCR,
    IMAGE_PROMPT_NO_OCR,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/extract")
async def extract_from_image(
    file: UploadFile = File(...),
    format: str = Query("json", description="Output format: json, text, html"),
):
    allowed_types = file.content_type and (
        file.content_type.startswith("image/") or file.content_type == "application/pdf"
    )
    if not allowed_types:
        raise HTTPException(status_code=400, detail="File must be an image or PDF")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        processed = preprocess_image(image)

        ocr_text = ""
        if is_tesseract_available():
            logger.info("Running OCR...")
            ocr_text = extract_text(image) or ""
            if ocr_text:
                logger.info(f"OCR extracted {len(ocr_text)} chars")

        use_en = settings.llm_provider == LLMProvider.GEMINI
        if ocr_text:
            prompt = (IMAGE_PROMPT_EN if use_en else IMAGE_PROMPT).format(ocr_text=ocr_text)
        else:
            prompt = IMAGE_PROMPT_EN_NO_OCR if use_en else IMAGE_PROMPT_NO_OCR

        response = image_inference(processed, prompt)
        result = parse_llm_response(response, file.filename or "uploaded_image")

        if format == "text":
            return PlainTextResponse(format_result_text(result))
        elif format == "html":
            return HTMLResponse(format_result_html(result))
        else:
            return result

    except Exception as e:
        logger.exception("Extraction failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/file", response_model=list[ExtractionResult])
async def extract_from_file(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        results = process_path(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        return results

    except Exception as e:
        logger.exception("Extraction failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/batch", response_model=BatchResult)
async def extract_batch(files: list[UploadFile] = File(...)):
    all_results = []
    failed = 0

    for file in files:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name

            results = process_path(tmp_path)
            all_results.extend(results)
            Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            failed += 1
            all_results.append(ExtractionResult(
                source_file=file.filename or "unknown",
                error=str(e),
            ))

    successful = len([r for r in all_results if not r.error])

    return BatchResult(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=all_results,
    )
