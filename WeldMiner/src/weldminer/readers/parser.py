"""Input parsers for XML, Markdown/Text, and PDF documents."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .multimodal_input import load_raw_input_from_file

SUPPORTED_INPUT_EXTENSIONS = {".xml", ".json", ".pdf", ".md", ".markdown", ".txt"}


def sanitize_name(value: str) -> str:
    """Convert text into a filesystem-safe folder name while preserving Unicode text."""
    unsafe_chars = r'[\\/:|*?"<>|]'
    sanitized = re.sub(unsafe_chars, "-", value.strip())
    sanitized = re.sub(r"-+", "-", sanitized)
    sanitized = sanitized.strip("-")
    return sanitized or "document"


def list_to_text(data_list: Any) -> str:
    """Convert a list/dict table-like structure into plain text."""
    if not data_list:
        return "No information"

    text_items = []
    for item in data_list:
        if isinstance(item, dict):
            text_items.append(", ".join([f"{k} is {v}" for k, v in item.items()]))
        else:
            text_items.append(str(item))
    return ". ".join([x for x in text_items if x])


def _extract_tables_from_xml(xml_path: Path, doi: str) -> Dict[str, Any]:
    """Best-effort table extraction from XML."""
    try:
        from .table_extractor import TableExtractorToAlloy
    except Exception:
        return {}

    try:
        table_extractor = TableExtractorToAlloy(str(xml_path))
        raw_tables = table_extractor.get_xml_tables(doi)
    except Exception:
        return {}

    captions_by_index = {}
    try:
        from lxml import etree

        tree = etree.parse(str(xml_path))
        ns = {
            "ce": "http://www.elsevier.com/xml/common/dtd",
            "tb": "http://www.elsevier.com/xml/common/table/dtd",
        }
        wraps = tree.xpath("//ce:table-wrap", namespaces=ns)
        for i, wrap in enumerate(wraps):
            label_els = wrap.xpath(".//ce:label", namespaces=ns)
            caption_els = wrap.xpath(".//ce:caption", namespaces=ns)
            label_text = ""
            caption_text = ""
            if label_els:
                label_text = "".join(label_els[0].itertext()).strip()
            if caption_els:
                caption_text = "".join(caption_els[0].itertext()).strip()
            if label_text or caption_text:
                captions_by_index[i] = " ".join(p for p in [label_text, caption_text] if p)
    except Exception:
        pass

    processed_tables: Dict[str, Any] = {}
    for idx, (key, table) in enumerate((raw_tables or {}).items()):
        if not isinstance(table, dict):
            continue
        caption = captions_by_index.get(idx, "") or table.get("caption", "")
        if caption:
            caption = re.sub(r"<[^>]+>", " ", str(caption))
            caption = re.sub(r"\s+", " ", caption).strip()
        raw_content = table.get("content", [])
        if not raw_content:
            processed_tables[str(key)] = {"caption": caption, "content": ""}
            continue
        processed_tables[str(key)] = {
            "caption": caption,
            "content": _matrix_to_pipe_text(raw_content),
        }

    return processed_tables


def _matrix_to_pipe_text(matrix: list) -> str:
    """Convert a 2D list to pipe-separated markdown table string."""
    if not matrix:
        return ""
    cleaned = []
    for row in matrix:
        cleaned.append([str(c).strip() if c is not None else "" for c in row])
    max_cols = max((len(r) for r in cleaned), default=0)
    for row in cleaned:
        if len(row) < max_cols:
            row.extend([""] * (max_cols - len(row)))
    lines = ["| " + " | ".join(row) + " |" for row in cleaned]
    sep = "| " + " | ".join(["---"] * max_cols) + " |"
    if lines:
        lines.insert(1, sep)
    return "\n".join(lines)


def parse_xml_document(xml_path: Path) -> dict:
    """Preserve parsed article sections and caption/Markdown table pairs."""
    from .xml_parser import ElsevierXmlReader
    document = ElsevierXmlReader(str(xml_path)).dic()
    if not isinstance(document, dict):
        raise ValueError(f'Invalid XML parser result: {xml_path}')
    document['doi'] = str(document.get('doi') or xml_path.stem).strip()
    document['tables'] = _extract_tables_from_xml(xml_path, document['doi'])
    document['document_type'] = 'weldminer.parsed_xml'
    document['schema_version'] = 1
    if not document_to_text(document)[1]:
        raise ValueError(f'No usable XML content: {xml_path}')
    return document


def process_xml_file(xml_path: Path) -> Optional[Tuple[str, str]]:
    return document_to_text(parse_xml_document(xml_path))


def process_json_file(json_path: Path) -> Tuple[str, str]:
    document = json.loads(json_path.read_text(encoding='utf-8-sig'))
    if not isinstance(document, dict) or document.get('document_type') != 'weldminer.parsed_xml' or document.get('schema_version') != 1:
        raise ValueError('Expected a parsed XML JSON file generated by parse_xml()')
    result = document_to_text(document)
    if not result[1]:
        raise ValueError(f'No usable document content: {json_path}')
    return result


def document_to_text(article_info: dict) -> Tuple[str, str]:
    """Use the same model input for direct XML and saved parsed JSON."""
    extracted_doi = str(article_info.get('doi') or 'document').strip()
    doi_folder = sanitize_name(extracted_doi.replace('/', '-'))
    title = str(article_info.get("title") or "")
    abstract = str(article_info.get("abstract") or "")
    contents = article_info.get("content") or []

    body_parts = []
    for par in contents:
        if not isinstance(par, dict):
            body_parts.append(str(par))
            continue
        tag = par.get("tag")
        text = par.get("text") or ""
        if tag and text:
            body_parts.append(f"{tag}: {text}")
        else:
            body_parts.append(str(text))

    tables_text_parts = []
    tables = article_info.get("tables") or {}
    for _, table in tables.items():
        if not isinstance(table, dict):
            continue
        caption = table.get("caption") or ""
        content = table.get("content") or ""
        if isinstance(content, list):
            content = list_to_text(content)
        tables_text_parts.append(f"{caption}\n{content}".strip())

    figure_text_parts = []
    for fig in article_info.get("figure") or []:
        if not isinstance(fig, dict):
            continue
        label = str(fig.get("label") or "")
        caption = str(fig.get("caption") or "")
        caption = re.sub(r"<[^>]+>", " ", caption)
        caption = re.sub(r"\s+", " ", caption)
        figure_text_parts.append(f"{label} {caption}".strip())

    all_infos = "\n".join(
        [
            title,
            abstract,
            "\n".join(body_parts),
            "\n".join(tables_text_parts),
            "\n".join(figure_text_parts),
        ]
    ).strip()

    return doi_folder, all_infos


def process_markdown_file(markdown_path: Path) -> Optional[Tuple[str, str]]:
    """Parse Markdown/Text file and return document id plus plain text content."""
    try:
        raw_input = load_raw_input_from_file(markdown_path)
    except Exception as e:
        print(f"Failed to parse Markdown/Text {markdown_path.name}: {e}")
        return None

    if raw_input is None or not str(raw_input).strip():
        print(f"No usable Markdown/Text content: {markdown_path.name}")
        return None

    return sanitize_name(markdown_path.stem), str(raw_input)


def process_pdf_file(pdf_path: Path, max_pages: int = 20) -> Optional[Tuple[str, Any]]:
    """Parse PDF file into page image input and return document id plus image payload."""
    try:
        raw_input = load_raw_input_from_file(pdf_path, max_pages=max_pages)
    except Exception as e:
        print(f"Failed to parse PDF {pdf_path.name}: {e}")
        return None

    if raw_input is None:
        print(f"No usable PDF content: {pdf_path.name}")
        return None

    return sanitize_name(pdf_path.stem), raw_input


def load_document_input(file_path: Path, max_pdf_pages: int = 20) -> Optional[Tuple[str, Any]]:
    """
    Return (document_id, raw_input) for a file.
    XML -> document_id from DOI.
    Markdown/Text -> document_id from filename and plain text content.
    PDF -> document_id from filename and rendered page input.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return process_json_file(file_path)

    if suffix == ".xml":
        return process_xml_file(file_path)

    if suffix in {".md", ".markdown", ".txt"}:
        return process_markdown_file(file_path)

    if suffix == ".pdf":
        return process_pdf_file(file_path, max_pages=max_pdf_pages)

    print(f"Unsupported input file type: {file_path.name}")
    return None


def collect_input_files(root_dir: Path) -> list[Path]:
    """Collect supported files from a directory."""
    files = [
        path
        for path in root_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS
    ]
    return sorted(files)


def describe_raw_input(raw_input: Any) -> str:
    if isinstance(raw_input, list):
        return f"{len(raw_input)} page image(s)"
    return f"{len(str(raw_input))} text characters"
