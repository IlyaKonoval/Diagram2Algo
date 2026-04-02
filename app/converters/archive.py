import hashlib
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Generator, Optional, Union

logger = logging.getLogger(__name__)


def extract_archive(
    archive_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
) -> Optional[Path]:
    archive_path = Path(archive_path)

    if not archive_path.exists():
        logger.error(f"Archive not found: {archive_path}")
        return None

    suffix = archive_path.suffix.lower()

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(tempfile.mkdtemp(prefix="d2a_"))

    try:
        if suffix == ".zip":
            return _extract_zip(archive_path, output_path)
        elif suffix == ".rar":
            return _extract_rar(archive_path, output_path)
        elif suffix == ".7z":
            return _extract_7z(archive_path, output_path)
        else:
            logger.error(f"Unsupported archive format: {suffix}")
            return None
    except Exception as e:
        logger.error(f"Failed to extract archive {archive_path}: {e}")
        return None


def _extract_zip(archive_path: Path, output_path: Path) -> Path:
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(output_path)
    return output_path


def _extract_rar(archive_path: Path, output_path: Path) -> Path:
    try:
        import rarfile
        with rarfile.RarFile(archive_path, "r") as rf:
            rf.extractall(output_path)
        return output_path
    except ImportError:
        import patoolib
        patoolib.extract_archive(str(archive_path), outdir=str(output_path))
        return output_path


def _extract_7z(archive_path: Path, output_path: Path) -> Path:
    try:
        import py7zr
        with py7zr.SevenZipFile(archive_path, mode="r") as zf:
            zf.extractall(output_path)
        return output_path
    except ImportError:
        import patoolib
        patoolib.extract_archive(str(archive_path), outdir=str(output_path))
        return output_path


def list_archive_contents(archive_path: Union[str, Path]) -> list[str]:
    archive_path = Path(archive_path)
    suffix = archive_path.suffix.lower()

    try:
        if suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                return zf.namelist()
        elif suffix == ".rar":
            import rarfile
            with rarfile.RarFile(archive_path, "r") as rf:
                return rf.namelist()
        elif suffix == ".7z":
            import py7zr
            with py7zr.SevenZipFile(archive_path, mode="r") as zf:
                return zf.getnames()
    except Exception as e:
        logger.error(f"Failed to list archive contents: {e}")

    return []


def compute_file_hash(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def iter_archive_files(
    archive_path: Union[str, Path],
    extensions: Optional[set[str]] = None,
) -> Generator[tuple[str, bytes], None, None]:
    archive_path = Path(archive_path)
    suffix = archive_path.suffix.lower()

    if extensions:
        extensions = {ext.lower().lstrip(".") for ext in extensions}

    try:
        if suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    if extensions:
                        ext = Path(name).suffix.lower().lstrip(".")
                        if ext not in extensions:
                            continue
                    yield name, zf.read(name)
        elif suffix == ".rar":
            import rarfile
            with rarfile.RarFile(archive_path, "r") as rf:
                for name in rf.namelist():
                    if extensions:
                        ext = Path(name).suffix.lower().lstrip(".")
                        if ext not in extensions:
                            continue
                    yield name, rf.read(name)
        elif suffix == ".7z":
            import py7zr
            with py7zr.SevenZipFile(archive_path, mode="r") as zf:
                for name, bio in zf.read().items():
                    if extensions:
                        ext = Path(name).suffix.lower().lstrip(".")
                        if ext not in extensions:
                            continue
                    yield name, bio.read()
    except Exception as e:
        logger.error(f"Failed to iterate archive: {e}")
