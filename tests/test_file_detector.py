import tempfile
from pathlib import Path

import pytest

from app.file_detector import get_file_type, get_supported_extensions, is_supported
from app.models import FileType


class TestGetFileType:
    def test_png(self, tmp_path):
        f = tmp_path / "diagram.png"
        f.touch()
        assert get_file_type(f) == FileType.IMAGE

    def test_jpg(self, tmp_path):
        f = tmp_path / "diagram.jpg"
        f.touch()
        assert get_file_type(f) == FileType.IMAGE

    def test_jpeg(self, tmp_path):
        f = tmp_path / "diagram.jpeg"
        f.touch()
        assert get_file_type(f) == FileType.IMAGE

    def test_svg(self, tmp_path):
        f = tmp_path / "diagram.svg"
        f.touch()
        assert get_file_type(f) == FileType.SVG

    def test_pdf(self, tmp_path):
        f = tmp_path / "document.pdf"
        f.touch()
        assert get_file_type(f) == FileType.PDF

    def test_drawio(self, tmp_path):
        f = tmp_path / "diagram.drawio"
        f.touch()
        assert get_file_type(f) == FileType.DRAWIO

    def test_bpmn(self, tmp_path):
        f = tmp_path / "process.bpmn"
        f.touch()
        assert get_file_type(f) == FileType.BPMN

    def test_zip(self, tmp_path):
        f = tmp_path / "archive.zip"
        f.touch()
        assert get_file_type(f) == FileType.ARCHIVE

    def test_unknown_extension(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.touch()
        assert get_file_type(f) == FileType.UNKNOWN

    def test_xml_with_mxfile(self, tmp_path):
        f = tmp_path / "diagram.xml"
        f.write_text('<mxfile><diagram></diagram></mxfile>')
        assert get_file_type(f) == FileType.DRAWIO

    def test_xml_with_bpmn(self, tmp_path):
        f = tmp_path / "process.xml"
        f.write_text('<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"></definitions>')
        assert get_file_type(f) == FileType.BPMN

    def test_xml_without_markers(self, tmp_path):
        f = tmp_path / "data.xml"
        f.write_text('<root><item>test</item></root>')
        assert get_file_type(f) == FileType.UNKNOWN

    def test_case_insensitive_extension(self, tmp_path):
        f = tmp_path / "DIAGRAM.PNG"
        f.touch()
        assert get_file_type(f) == FileType.IMAGE


class TestIsSupportedAndExtensions:
    def test_supported_file(self, tmp_path):
        f = tmp_path / "test.png"
        f.touch()
        assert is_supported(f) is True

    def test_unsupported_file(self, tmp_path):
        f = tmp_path / "test.mp3"
        f.touch()
        assert is_supported(f) is False

    def test_supported_extensions_contains_png(self):
        exts = get_supported_extensions()
        assert ".png" in exts
        assert ".jpg" in exts
        assert ".svg" in exts
        assert ".pdf" in exts
