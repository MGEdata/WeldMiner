"""Document parsing implementations, exposed through weldminer.api."""
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile


def _source_file(path: str | Path, suffix: str) -> Path:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() != suffix:
        raise ValueError(f'Expected a {suffix} file: {source}')
    return source


def _save_markdown(source: Path, content: str) -> Path:
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f'Parser produced empty Markdown: {source}')
    # XML uses a simple .md suffix; preserve the existing PDF naming convention.
    target = source.with_suffix(".md") if source.suffix.lower() == ".xml" else source.with_name(source.name + ".md")
    with NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.tmp',
                            dir=source.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def parse_pdf(path: str | Path) -> Path:
    """Convert one PDF via PaddleOCR-VL; return adjacent <filename>.pdf.md.

    Each call parses again and replaces the generated Markdown after success.
    OCR configuration comes from PADDLEOCR_VL_* environment variables.
    """
    source = _source_file(path, '.pdf')
    from .pdf_parser import create_pipeline, process_pdf
    with TemporaryDirectory(prefix='weldminer-ocr-') as temp:
        output_root = Path(temp)
        if not process_pdf(source, output_root, create_pipeline()):
            raise ValueError(f'PDF conversion failed: {source}')
        markdown = output_root / source.stem / f'{source.stem}_extracted_text.md'
        content = markdown.read_text(encoding='utf-8')
    return _save_markdown(source, content)


def parse_xml(path: str | Path) -> Path:
    """Parse XML text, table captions/Markdown, and figure captions into adjacent <stem>.md."""
    source = _source_file(path, '.xml')
    from .parser import process_xml_file
    loaded = process_xml_file(source)
    if loaded is None:
        raise ValueError(f'Parser produced no usable content: {source}')
    return _save_markdown(source, loaded[1])
