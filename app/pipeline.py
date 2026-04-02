import logging
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from app.config import settings
from app.converters import (
    extract_archive,
    parse_bpmn,
    parse_drawio,
    render_pdf_pages,
    render_svg,
)
from app.llm import image_inference, text_inference
from app.models import ExtractionResult, FileInput, FileType
from app.ocr import extract_text, is_tesseract_available
from app.postprocessing import parse_llm_response, validate_steps
from app.preprocessing import load_and_preprocess, preprocess_image, preprocess_rendered
from app.config import LLMProvider
from app.prompts import (
    IMAGE_PROMPT, IMAGE_PROMPT_NO_OCR, SIMPLE_IMAGE_PROMPT, SIMPLE_TEXT_PROMPT, TEXT_PROMPT,
    IMAGE_PROMPT_EN, IMAGE_PROMPT_EN_NO_OCR, TEXT_PROMPT_EN,
)
from app.file_detector import get_file_type
from app.scanner import scan_directory

logger = logging.getLogger(__name__)


def process_image(
    image: Image.Image,
    source_file: str,
    page_or_slide: Optional[int] = None,
    use_simple_prompt: bool = False,
    is_rendered: bool = False,
) -> ExtractionResult:
    try:
        processed = preprocess_rendered(image) if is_rendered else preprocess_image(image)

        ocr_text = ""
        if settings.use_ocr and is_tesseract_available():
            logger.info("Running OCR...")
            ocr_text = extract_text(processed) or ""
            if ocr_text:
                logger.info(f"OCR extracted {len(ocr_text)} chars")

        use_en = settings.llm_provider == LLMProvider.GEMINI
        if use_simple_prompt:
            prompt = SIMPLE_IMAGE_PROMPT
        elif ocr_text:
            prompt = (IMAGE_PROMPT_EN if use_en else IMAGE_PROMPT).format(ocr_text=ocr_text)
        else:
            prompt = IMAGE_PROMPT_EN_NO_OCR if use_en else IMAGE_PROMPT_NO_OCR

        response = image_inference(processed, prompt)
        result = parse_llm_response(response, source_file, page_or_slide)
        result.steps = validate_steps(result.steps)
        return result

    except Exception as e:
        logger.error(f"Failed to process image {source_file}: {e}")
        return ExtractionResult(
            source_file=source_file,
            page_or_slide=page_or_slide,
            error=str(e),
        )


def process_text_diagram(
    text: str,
    source_file: str,
    diagram_type: str,
    use_simple_prompt: bool = False,
) -> ExtractionResult:
    try:
        use_en = settings.llm_provider == LLMProvider.GEMINI
        if use_simple_prompt:
            prompt = SIMPLE_TEXT_PROMPT
        else:
            prompt = TEXT_PROMPT_EN if use_en else TEXT_PROMPT

        response = text_inference(text, prompt)
        result = parse_llm_response(response, source_file)

        if not result.steps and not use_simple_prompt:
            logger.info("Retrying with simple prompt")
            response = text_inference(text, SIMPLE_TEXT_PROMPT)
            result = parse_llm_response(response, source_file)

        result.diagram_type = diagram_type
        result.steps = validate_steps(result.steps)
        return result

    except Exception as e:
        logger.error(f"Failed to process text diagram {source_file}: {e}")
        return ExtractionResult(
            source_file=source_file,
            diagram_type=diagram_type,
            error=str(e),
        )


def process_file(file_input: FileInput) -> list[ExtractionResult]:
    path = file_input.path
    file_type = file_input.file_type
    source = str(path)

    if file_input.parent_archive:
        source = f"{file_input.parent_archive}:{path.name}"

    logger.info(f"Processing {source} (type: {file_type.value})")

    try:
        if file_type == FileType.IMAGE:
            image = load_and_preprocess(str(path))
            if image:
                return [process_image(image, source)]
            return [ExtractionResult(source_file=source, error="Failed to load image")]

        elif file_type == FileType.SVG:
            image = render_svg(path)
            if image:
                return [process_image(image, source, is_rendered=True)]
            return [ExtractionResult(source_file=source, error="Failed to render SVG")]

        elif file_type == FileType.PDF:
            pages = render_pdf_pages(path)
            if not pages:
                return [ExtractionResult(source_file=source, error="Failed to render PDF")]
            results = []
            for page_num, image in enumerate(pages, 1):
                result = process_image(image, source, page_or_slide=page_num, is_rendered=True)
                results.append(result)
            return results

        elif file_type == FileType.DRAWIO:
            text = parse_drawio(path)
            if text:
                return [process_text_diagram(text, source, "drawio")]
            return [ExtractionResult(source_file=source, error="Failed to parse DrawIO")]

        elif file_type == FileType.BPMN:
            text = parse_bpmn(path)
            if text:
                return [process_text_diagram(text, source, "bpmn")]
            return [ExtractionResult(source_file=source, error="Failed to parse BPMN")]

        elif file_type == FileType.ARCHIVE:
            extracted_dir = extract_archive(path)
            if not extracted_dir:
                return [ExtractionResult(source_file=source, error="Failed to extract archive")]

            results = []
            for inner_file in scan_directory(extracted_dir):
                inner_file.parent_archive = source
                inner_results = process_file(inner_file)
                results.extend(inner_results)
            return results

        else:
            return [ExtractionResult(source_file=source, error=f"Unsupported file type: {file_type.value}")]

    except Exception as e:
        logger.exception(f"Error processing {source}")
        return [ExtractionResult(source_file=source, error=str(e))]


def process_path(path: Union[str, Path]) -> list[ExtractionResult]:
    path = Path(path)

    if path.is_file():
        file_type = get_file_type(path)
        file_input = FileInput(path=path, file_type=file_type)
        return process_file(file_input)

    elif path.is_dir():
        results = []
        files = list(scan_directory(path))
        total = len(files)
        for i, file_input in enumerate(files, 1):
            logger.info(f"[{i}/{total}] Processing {file_input.path.name}...")
            file_results = process_file(file_input)
            results.extend(file_results)
            logger.info(f"[{i}/{total}] Done: {file_input.path.name} -> {len(file_results)} result(s)")
        return results

    else:
        return [ExtractionResult(source_file=str(path), error="Path not found")]


def batch_process(
    paths: list[Union[str, Path]],
    progress_callback: Optional[callable] = None,
) -> list[ExtractionResult]:
    all_results = []

    for i, path in enumerate(paths):
        results = process_path(path)
        all_results.extend(results)

        if progress_callback:
            progress_callback(i + 1, len(paths), path, results)

    return all_results
