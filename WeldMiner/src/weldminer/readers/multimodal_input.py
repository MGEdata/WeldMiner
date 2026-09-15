"""
Multimodal input helpers.

This module centralizes:
- Raw input loading from Markdown/text/PDF files.
- PDF-to-image conversion.
- Prompt payload normalization for multimodal requests.
- HumanMessage construction for text-only and image-based LLM calls.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import HumanMessage

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


PromptInput = Union[str, Dict[str, Any]]
RawInputContent = Union[str, List[str]]

_PDF_PATH_PATTERN = re.compile(
    r'(?P<path>(?:[A-Za-z]:[\\/]|\.{1,2}[\\/]|[\\/])[^<>"\r\n]+?\.pdf)',
    re.IGNORECASE,
)
_DEFAULT_PDF_DPI = 144
_DEFAULT_MAX_PDF_PAGES = 20
_DEFAULT_IMAGE_MIME_TYPE = "image/png"


def get_intro_prompt(prompt_text: str) -> str:
    """Build the text block used ahead of attached images."""
    return (
        f"{prompt_text}\n\n"
        "The source document is attached below as page images. "
        "Use the images as the primary source when extracting content."
    )


def get_pdf_source_prompt(pdf_name: str, num_pages: int) -> str:
    """Describe an attached PDF source."""
    return f"PDF source: {pdf_name}. Attached pages: {num_pages}."


def is_multimodal_raw_input(raw_input: RawInputContent) -> bool:
    """Return True when raw input is a non-empty list of base64-encoded images."""
    return isinstance(raw_input, list) and len(raw_input) > 0


def get_prompt_source_text(raw_input: RawInputContent) -> str:
    """
    Return the text interpolated into prompt templates.

    Image workflows use a short description instead of embedding the image payload.
    """
    if is_multimodal_raw_input(raw_input):
        return (
            "The source document is attached in this request as page images. "
            "Extract information from the attached images."
        )
    return str(raw_input)


def build_prompt_input(
    prompt_text: str,
    raw_input: RawInputContent,
    image_mime_type: str = _DEFAULT_IMAGE_MIME_TYPE,
) -> PromptInput:
    """Return text prompt for text workflows, or a multimodal prompt payload for image workflows."""
    if is_multimodal_raw_input(raw_input):
        return {
            "prompt": prompt_text,
            "images_base64": raw_input,
            "image_mime_type": image_mime_type,
        }
    return prompt_text


def _extract_pdf_paths_from_text(prompt_text: str) -> List[str]:
    """Extract existing local PDF paths from prompt text."""
    pdf_paths: List[str] = []
    seen = set()

    stripped = prompt_text.strip().strip('"').strip("'")
    if stripped.lower().endswith(".pdf") and Path(stripped).exists():
        resolved = str(Path(stripped).resolve())
        pdf_paths.append(resolved)
        seen.add(resolved)

    for match in _PDF_PATH_PATTERN.finditer(prompt_text):
        raw_path = match.group("path").strip().strip('"').strip("'")
        path = Path(raw_path)
        if path.exists() and path.is_file():
            resolved = str(path.resolve())
            if resolved not in seen:
                pdf_paths.append(resolved)
                seen.add(resolved)

    return pdf_paths


def normalize_prompt_input(prompt: PromptInput) -> Dict[str, Any]:
    """Normalize prompt input into text plus optional local PDF paths or image payloads."""
    if isinstance(prompt, dict):
        prompt_text = str(
            prompt.get("prompt")
            or prompt.get("prompt_text")
            or prompt.get("text")
            or ""
        )

        raw_pdf_paths = prompt.get("pdf_paths") or []
        if isinstance(raw_pdf_paths, (str, Path)):
            raw_pdf_paths = [raw_pdf_paths]

        raw_images_base64 = (
            prompt.get("images_base64")
            or prompt.get("image_base64_list")
            or prompt.get("images")
            or []
        )
        if isinstance(raw_images_base64, str):
            raw_images_base64 = [raw_images_base64]

        image_mime_type = str(prompt.get("image_mime_type") or _DEFAULT_IMAGE_MIME_TYPE)
        pdf_paths: List[str] = []
        seen = set()
        for raw_path in raw_pdf_paths:
            if raw_path is None:
                continue
            resolved = str(Path(raw_path).expanduser().resolve())
            if resolved not in seen:
                pdf_paths.append(resolved)
                seen.add(resolved)

        if not pdf_paths:
            pdf_paths = _extract_pdf_paths_from_text(prompt_text)

        return {
            "prompt_text": prompt_text,
            "pdf_paths": pdf_paths,
            "images_base64": list(raw_images_base64),
            "image_mime_type": image_mime_type,
        }

    prompt_text = str(prompt)
    return {
        "prompt_text": prompt_text,
        "pdf_paths": _extract_pdf_paths_from_text(prompt_text),
        "images_base64": [],
        "image_mime_type": _DEFAULT_IMAGE_MIME_TYPE,
    }


def _render_pdf_to_base64_images(
    pdf_path: str,
    dpi: int = _DEFAULT_PDF_DPI,
    max_pages: int = _DEFAULT_MAX_PDF_PAGES,
) -> List[str]:
    """Render a PDF into base64-encoded PNG images."""
    if fitz is None:
        raise ImportError(
            "PyMuPDF is required for PDF input support. Install it with `pip install pymupdf`."
        )

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_file)
    try:
        total_pages = len(doc)
        page_limit = min(total_pages, max_pages)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        encoded_images: List[str] = []

        for page_index in range(page_limit):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            encoded_images.append(base64.b64encode(pix.tobytes("png")).decode("ascii"))

        return encoded_images
    finally:
        doc.close()


def pdf_to_base64_images(
    pdf_path: str,
    dpi: int = _DEFAULT_PDF_DPI,
    max_pages: Optional[int] = None,
) -> List[str]:
    """Public helper for converting a local PDF into base64-encoded PNG page images."""
    page_limit = max_pages if max_pages is not None else _DEFAULT_MAX_PDF_PAGES
    return _render_pdf_to_base64_images(pdf_path, dpi=dpi, max_pages=page_limit)


def load_raw_input_from_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    dpi: int = _DEFAULT_PDF_DPI,
    max_pages: Optional[int] = None,
) -> RawInputContent:
    """
    Load workflow raw input from a local file.

    - PDF files are converted to base64-encoded PNG page images.
    - Other files are read as text.
    """
    input_path = Path(file_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if input_path.suffix.lower() == ".pdf":
        return pdf_to_base64_images(str(input_path), dpi=dpi, max_pages=max_pages)

    return input_path.read_text(encoding=encoding)


def build_human_message_from_prompt(
    prompt: PromptInput,
    message_format: str = "openai",
) -> HumanMessage:
    """Build a text-only or multimodal human message."""
    normalized_prompt = normalize_prompt_input(prompt)
    prompt_text = normalized_prompt["prompt_text"]
    pdf_paths = normalized_prompt["pdf_paths"]
    images_base64 = normalized_prompt["images_base64"]
    image_mime_type = normalized_prompt["image_mime_type"]

    if not pdf_paths and not images_base64:
        return HumanMessage(content=prompt_text)

    max_pages = int(os.getenv("LLM_UTILS_MAX_PDF_PAGES", _DEFAULT_MAX_PDF_PAGES))
    dpi = int(os.getenv("LLM_UTILS_PDF_DPI", _DEFAULT_PDF_DPI))

    if message_format == "tongyi":
        content_blocks: List[Dict[str, Any]] = [{"text": get_intro_prompt(prompt_text)}]
    else:
        content_blocks = [{"type": "text", "text": get_intro_prompt(prompt_text)}]

    for pdf_path in pdf_paths:
        images = _render_pdf_to_base64_images(pdf_path, dpi=dpi, max_pages=max_pages)
        pdf_name = Path(pdf_path).name
        if message_format == "tongyi":
            content_blocks.append({"text": get_pdf_source_prompt(pdf_name, len(images))})
        else:
            content_blocks.append(
                {"type": "text", "text": get_pdf_source_prompt(pdf_name, len(images))}
            )
        for image_base64 in images:
            image_data_url = f"data:image/png;base64,{image_base64}"
            if message_format == "tongyi":
                content_blocks.append({"image": image_data_url})
            else:
                content_blocks.append(
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                )

    if images_base64:
        if message_format == "tongyi":
            content_blocks.append({"text": f"Attached page images: {len(images_base64)}."})
        else:
            content_blocks.append(
                {"type": "text", "text": f"Attached page images: {len(images_base64)}."}
            )
        for image_base64 in images_base64:
            image_data_url = f"data:{image_mime_type};base64,{image_base64}"
            if message_format == "tongyi":
                content_blocks.append({"image": image_data_url})
            else:
                content_blocks.append(
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                )

    return HumanMessage(content=content_blocks)


__all__ = [
    "PromptInput",
    "RawInputContent",
    "build_human_message_from_prompt",
    "build_prompt_input",
    "get_intro_prompt",
    "get_pdf_source_prompt",
    "get_prompt_source_text",
    "is_multimodal_raw_input",
    "load_raw_input_from_file",
    "normalize_prompt_input",
    "pdf_to_base64_images",
]


def _prepare_prompt_input(prompt_text: str, raw_input: Any):
    """
    Wrap prompt text into a multimodal payload when the workflow input
    is image-based, otherwise keep the original text prompt.
    """
    return build_prompt_input(prompt_text, raw_input)



def _prompt_source_text_or_none(raw_input: Any) -> Optional[str]:
    """Only text/markdown/xml inputs should be injected into prompt text."""
    if is_multimodal_raw_input(raw_input):
        return None
    return str(raw_input)

