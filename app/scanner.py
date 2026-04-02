import logging
from pathlib import Path
from typing import Generator, Optional, Union

from app.converters.archive import compute_file_hash, extract_archive
from app.models import FileInput, FileType
from app.file_detector import get_file_type

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff",
    ".drawio", ".dio",
    ".bpmn",
    ".zip", ".rar", ".7z",
}


def scan_directory(
    directory: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[set[str]] = None,
) -> Generator[FileInput, None, None]:
    directory = Path(directory)

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return

    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return

    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    extensions = {ext.lower().lstrip(".") for ext in extensions}

    pattern = "**/*" if recursive else "*"

    for path in directory.glob(pattern):
        if not path.is_file():
            continue

        ext = path.suffix.lower().lstrip(".")
        if ext not in extensions:
            continue

        file_type = get_file_type(path)

        yield FileInput(
            path=path,
            file_type=file_type,
        )


def scan_with_deduplication(
    directory: Union[str, Path],
    recursive: bool = True,
) -> list[FileInput]:
    seen_hashes = set()
    unique_files = []

    for file_input in scan_directory(directory, recursive):
        file_hash = compute_file_hash(file_input.path)

        if file_hash in seen_hashes:
            logger.debug(f"Skipping duplicate: {file_input.path}")
            continue

        seen_hashes.add(file_hash)
        unique_files.append(file_input)

    return unique_files


def scan_with_archives(
    directory: Union[str, Path],
    recursive: bool = True,
    temp_dir: Optional[Union[str, Path]] = None,
) -> Generator[FileInput, None, None]:
    seen_hashes = set()

    for file_input in scan_directory(directory, recursive):
        if file_input.file_type == FileType.ARCHIVE:
            extracted_dir = extract_archive(file_input.path, temp_dir)

            if extracted_dir:
                for inner_file in scan_directory(extracted_dir, recursive=True):
                    file_hash = compute_file_hash(inner_file.path)

                    if file_hash in seen_hashes:
                        continue

                    seen_hashes.add(file_hash)

                    yield FileInput(
                        path=inner_file.path,
                        file_type=inner_file.file_type,
                        parent_archive=str(file_input.path),
                    )
        else:
            file_hash = compute_file_hash(file_input.path)

            if file_hash in seen_hashes:
                continue

            seen_hashes.add(file_hash)
            yield file_input


def find_paired_files(files: list[FileInput]) -> dict[str, list[FileInput]]:
    groups = {}

    for file_input in files:
        stem = file_input.path.stem.lower()
        stem = stem.replace("_", "").replace("-", "").replace(" ", "")

        if stem not in groups:
            groups[stem] = []
        groups[stem].append(file_input)

    paired = {k: v for k, v in groups.items() if len(v) > 1}
    return paired


def group_by_type(files: list[FileInput]) -> dict[FileType, list[FileInput]]:
    groups = {}

    for file_input in files:
        if file_input.file_type not in groups:
            groups[file_input.file_type] = []
        groups[file_input.file_type].append(file_input)

    return groups


def count_files(directory: Union[str, Path], recursive: bool = True) -> dict[str, int]:
    counts = {}

    for file_input in scan_directory(directory, recursive):
        ext = file_input.path.suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1

    return counts
