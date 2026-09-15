"""Convert academic PDF files to Markdown with PaddleOCR-VL.

This parser is not tied to a vendor-specific CNKI format. It can process
ordinary PDF files, including PDFs downloaded through CNKI E-Study, provided
that the configured PaddleOCR-VL service can read them. CAJ files are not
supported.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence


DEFAULT_SERVER_URL = os.getenv("PADDLEOCR_VL_SERVER_URL", "http://localhost:8118/v1")
DEFAULT_BACKEND = os.getenv("PADDLEOCR_VL_BACKEND", "vllm-server")
DEFAULT_MODEL = os.getenv("PADDLEOCR_VL_MODEL", "PaddleOCR-VL-1.5-0.9B")

MODEL_SETTINGS = {
    "use_doc_preprocessor": False,
    "use_layout_detection": True,
    "use_chart_recognition": True,
    "use_seal_recognition": False,
    "use_ocr_for_image_block": False,
    "format_block_content": False,
    "merge_layout_blocks": True,
    "markdown_ignore_labels": [
        "number",
        "footnote",
        "header",
        "header_image",
        "footer",
        "footer_image",
        "aside_text",
        "reference_content",
        "figure_title",
    ],
    "return_layout_polygon_points": True,
}


def create_pipeline(
    server_url: str = DEFAULT_SERVER_URL,
    backend: str = DEFAULT_BACKEND,
    model: str = DEFAULT_MODEL,
):
    """Create the PaddleOCR-VL client lazily so ordinary imports stay lightweight."""
    try:
        from paddleocr import PaddleOCRVL
    except ImportError as exc:
        if getattr(exc, 'name', None) != 'paddleocr':
            raise RuntimeError(
                f'PaddleOCR could not import a dependency ({exc}). '
                'Check PaddleOCR/PaddleX dependency compatibility; '
                'this does not mean PaddleOCR itself is missing.'
            ) from exc
        raise RuntimeError(
            "PaddleOCR is required for OCR PDF parsing. Install the PaddleOCR "
            "dependency before running this module."
        ) from exc

    return PaddleOCRVL(
        vl_rec_server_url=server_url,
        vl_rec_backend=backend,
        vl_rec_api_model_name=model,
    )


def is_reference_title(title: str) -> bool:
    """Return whether a heading marks the beginning of the references section."""
    if not title:
        return False

    raw = title.strip()
    # Keep Chinese-paper support while leaving the source text fully English.
    if re.search("\u53c2\u8003\u6587\u732e", raw):
        return True

    normalized = raw.lower()
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = re.sub(r"[\s\-_,.:;()\[\]/\\]+", "", normalized)
    return normalized in {
        "reference",
        "references",
        "bibliography",
        "literaturecited",
        "workscited",
    }


def build_markdown_from_json(json_output_path: Path, markdown_output_path: Path) -> int:
    """Build Markdown body text from one PaddleOCR-VL JSON result."""
    with json_output_path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    parsing_results = data.get("parsing_res_list", [])
    target_labels = {"paragraph_title", "text", "table"}
    candidate_blocks = []
    first_title_index = None
    last_title_index = None
    last_title_text = ""

    for index, block in enumerate(parsing_results):
        label = block.get("block_label", "")
        content = (block.get("block_content", "") or "").strip()

        if label == "paragraph_title":
            if first_title_index is None:
                first_title_index = index
            last_title_index = index
            last_title_text = content

        if content and label in target_labels:
            candidate_blocks.append((index, label, content))

    if first_title_index is None:
        filtered_blocks = []
    else:
        filtered_blocks = [
            block for block in candidate_blocks if block[0] >= first_title_index
        ]

    if last_title_index is not None and is_reference_title(last_title_text):
        filtered_blocks = [
            block for block in filtered_blocks if block[0] < last_title_index
        ]

    with markdown_output_path.open("w", encoding="utf-8") as stream:
        for _, label, content in filtered_blocks:
            if label == "paragraph_title":
                stream.write(f"## {content}\n\n")
            else:
                stream.write(f"{content}\n\n")

    return len(filtered_blocks)


def process_pdf(pdf_path: Path, output_root: Path, pipeline: Any) -> bool:
    """Parse one PDF and save its JSON and Markdown artifacts."""
    document_output_dir = output_root / pdf_path.stem
    document_output_dir.mkdir(parents=True, exist_ok=True)
    json_output_path = document_output_dir / f"{pdf_path.stem}_res.json"
    markdown_output_path = document_output_dir / f"{pdf_path.stem}_extracted_text.md"

    try:
        result = pipeline.predict(str(pdf_path), model_settings=MODEL_SETTINGS)
        pages = list(result)
        outputs = pipeline.restructure_pages(
            pages,
            merge_tables=True,
            relevel_titles=True,
            concatenate_pages=True,
        )
        for output in outputs:
            output.save_to_json(save_path=str(document_output_dir))
    except RuntimeError as exc:
        print(f"Error processing {pdf_path.name}: {exc}")
        return False

    if not json_output_path.exists():
        print(f"Error processing {pdf_path.name}: expected JSON output was not created")
        return False

    kept_count = build_markdown_from_json(json_output_path, markdown_output_path)
    renamed_count = _rename_images_if_available(json_output_path, document_output_dir / "imgs")

    print(f"Processing completed: {pdf_path.name}")
    print(f"  Output directory: {document_output_dir}")
    print(f"  JSON: {json_output_path}")
    print(f"  Markdown: {markdown_output_path}")
    print(f"  Retained blocks: {kept_count}")
    print(f"  Renamed images: {renamed_count}")
    return True


def process_directory(input_dir: Path, output_dir: Path, pipeline: Any) -> tuple[int, int]:
    """Process every PDF directly contained in ``input_dir``."""
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files: Iterable[Path] = sorted(
        path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"
    )
    processed = 0
    failed = 0
    for pdf_path in pdf_files:
        if process_pdf(pdf_path, output_dir, pipeline):
            processed += 1
        else:
            failed += 1
    return processed, failed


def _rename_images_if_available(json_path: Path, image_dir: Path) -> int:
    """Use the optional image-title postprocessor when it is installed."""
    try:
        from .image_title_postprocess import rename_images_by_titles
    except ImportError:
        return 0

    manifest = rename_images_by_titles(json_path, image_dir)
    return sum(1 for item in manifest if item.get("status") == "renamed")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert academic PDF files to Markdown with PaddleOCR-VL"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing PDF files")
    parser.add_argument("output_dir", type=Path, help="Directory for JSON and Markdown output")
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args(argv)

    pipeline = create_pipeline(args.server_url, args.backend, args.model)
    processed, failed = process_directory(args.input_dir, args.output_dir, pipeline)
    print(f"All processing completed: {processed} succeeded, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
