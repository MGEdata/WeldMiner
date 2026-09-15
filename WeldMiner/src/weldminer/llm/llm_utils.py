"""
LLM validation and retry utilities.

Multimodal prompt construction and file-loading helpers live in
`multimodal_input.py` so this module stays focused on:
- calling the LLM
- parsing JSON
- validating responses
- retrying with error feedback
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Type

from pydantic import BaseModel, TypeAdapter, ValidationError

from ..readers.multimodal_input import (
    PromptInput,
    RawInputContent,
    build_human_message_from_prompt,
    build_prompt_input,
    get_prompt_source_text,
    is_multimodal_raw_input,
    load_raw_input_from_file,
    normalize_prompt_input,
    pdf_to_base64_images,
)

# Dedicated logger for LLM calls (configured by the caller, e.g. example_usage.py)
llm_logger = logging.getLogger("llm_calls")


def _get_prompt_text_for_log(prompt: PromptInput) -> str:
    """Extract plain text prompt content for logging."""
    if isinstance(prompt, dict):
        return str(prompt.get("prompt", prompt.get("prompt_text", "")))
    if isinstance(prompt, str):
        return prompt
    return str(prompt)


def parse_json_response(content: str) -> Any:
    """
    Parse JSON from LLM response, handling markdown code blocks and
    <thinking>/<output> tags introduced by COT+Reflection prompts.
    """
    content = content.strip()

    # If the response uses <think>/<thinking> / <output> tags, extract JSON from <output>
    COT_content = None
    # Support both English <think> and Chinese <thinking> tags
    for cot_tag in [r"<think>(.*?)<\/think>", r"<thinking>(.*?)<\/thinking>"]:
        COT_match = re.search(cot_tag, content, re.DOTALL)
        if COT_match:
            COT_content = COT_match.group(1).strip()
            break

    # Remove COT blocks from content so that <output> examples inside
    # <thinking> do not interfere with extraction of the real JSON.
    content_without_cot = re.sub(r"<think>.*?<\/think>", "", content, flags=re.DOTALL)
    content_without_cot = re.sub(r"<thinking>.*?<\/thinking>", "", content_without_cot, flags=re.DOTALL)

    output_matches = list(re.finditer(r"<output>(.*?)</output>", content_without_cot, re.DOTALL))
    if output_matches:
        content = output_matches[-1].group(1).strip()
    else:
        # Fallback: handle truncated output (model hit token limit before closing tag)
        output_start = content_without_cot.find("<output>")
        if output_start != -1:
            truncated_json = content_without_cot[output_start + len("<output>"):].strip()
            if truncated_json:
                # Try to use the truncated content; json.loads will fail gracefully
                # if it's truly broken, but this gives a better error message
                content = truncated_json

    # Handle markdown code blocks
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    return json.loads(content), COT_content


def create_retry_prompt(
    original_prompt: str, original_response: str, error_message: str
) -> str:
    """
    Create a retry prompt with error feedback.
    """
    return f"""
This is a request to fix an error in the structure of an llm_response.
Here is the original request:
<original_prompt>
{original_prompt}
</original_prompt>

Here is the original llm_response:
<llm_response>
{original_response}
</llm_response>

This response generated an error:
<error_message>
{error_message}
</error_message>

Compare the error message and the llm_response and identify what
needs to be fixed or removed
in the llm_response to resolve this error.

Respond ONLY with valid JSON. Do not include any explanations or
other text or formatting before or after the JSON string.
"""


def _is_chinese(text: str) -> bool:
    """Return True when text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _extract_response_text(response: Any) -> str:
    """Extract plain text from LangChain response objects."""
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    text_parts.append(block["text"])
                elif isinstance(block.get("text"), str):
                    # Tongyi style content block: {"text": "..."}
                    text_parts.append(block["text"])
        return "\n".join(text_parts).strip()

    return str(content)


def _stringify_reasoning_value(value: Any) -> str:
    """Convert a provider-specific reasoning payload to readable log text."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [_stringify_reasoning_value(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        for key in ("text", "content", "reasoning_content", "reasoning", "thinking"):
            if key in value:
                text = _stringify_reasoning_value(value[key])
                if text:
                    return text
    return ""


def _extract_reasoning_text(response: Any) -> str:
    """
    Extract model-native reasoning when the provider and LangChain adapter expose it.

    Common OpenAI-compatible adapters place this data in
    ``additional_kwargs.reasoning_content``. Content-block and response-metadata
    variants are supported as fallbacks.
    """
    for container_name in ("additional_kwargs", "response_metadata"):
        container = getattr(response, container_name, None)
        if not isinstance(container, dict):
            continue
        for key in ("reasoning_content", "reasoning", "thinking", "reasoning_details"):
            if key in container:
                text = _stringify_reasoning_value(container[key])
                if text:
                    return text

    content = getattr(response, "content", None)
    if isinstance(content, list):
        reasoning_parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", "")).lower()
            if block_type in {"reasoning", "thinking", "reasoning_content"}:
                text = _stringify_reasoning_value(block)
                if text:
                    reasoning_parts.append(text)
        return "\n".join(reasoning_parts).strip()

    return ""


def _normalize_workflow_stage(workflow_stage: str) -> str:
    """Keep the stage label single-line and reasonably sized for log headers."""
    stage = re.sub(r"\s+", " ", str(workflow_stage or "unlabeled")).strip()
    return stage[:200] or "unlabeled"


def _detect_message_format(llm: Any) -> str:
    """
    Detect message format required by model provider.
    - openai: content blocks with type/image_url
    - tongyi: content blocks like {"text": ...}, {"image": ...}
    """
    class_name = llm.__class__.__name__.lower()
    module_name = llm.__class__.__module__.lower()
    model_name = str(getattr(llm, "model_name", "")).lower()
    base_url = str(getattr(llm, "openai_api_base", "") or getattr(llm, "base_url", "")).lower()

    if "tongyi" in class_name or "tongyi" in module_name:
        return "tongyi"
    if "dashscope.aliyuncs.com" in base_url and model_name.startswith("qwen"):
        return "tongyi"
    return "openai"


def call_llm(
    prompt: PromptInput,
    llm=None,
    call_id: str = "",
    workflow_stage: str = "unlabeled",
) -> str:
    """
    Call LLM with a prompt.
    Logs the full prompt (truncated for brevity) and the complete response
    via the 'llm_calls' logger when it is configured.
    """
    if llm is None:
        raise ValueError("LLM instance is required")

    message_format = _detect_message_format(llm)
    message = build_human_message_from_prompt(prompt, message_format=message_format)

    prompt_text = _get_prompt_text_for_log(prompt)
    model_name = str(getattr(llm, "model_name", "unknown"))
    call_tag = f"[{call_id}]" if call_id else ""
    stage = _normalize_workflow_stage(workflow_stage)

    # Log prompt (first 3000 chars to keep log size reasonable; full text still in node JSON)
    if llm_logger.isEnabledFor(logging.INFO):
        llm_logger.info(
            "\n" + "=" * 60
            + f"\nLLM CALL {call_tag} | Stage: {stage} | Model: {model_name}\n"
            + f"PROMPT:\n{prompt_text[:3000]}"
            + ("\n... [truncated]" if len(prompt_text) > 3000 else "")
            + "\n" + "=" * 60
        )

    response = llm.invoke([message])
    response_text = _extract_response_text(response)
    reasoning_text = _extract_reasoning_text(response)

    # Log full response
    if llm_logger.isEnabledFor(logging.INFO):
        llm_logger.info(
            f"\nLLM RESPONSE {call_tag} | Stage: {stage} | Model: {model_name}\n"
            + "NATIVE REASONING (provider-returned):\n"
            + (reasoning_text if reasoning_text else "[not returned by provider/adapter]")
            + f"\n\nFINAL RESPONSE:\n{response_text}\n"
            + "=" * 60
        )

    return response_text


def validate_with_model(data_model, response_content: str) -> tuple:
    """
    Validate LLM response against a Pydantic model or TypeAdapter.
    Returns (validated_data, COT_content, error_message).
    """
    try:
        try:
            parsed_data, COT_content = parse_json_response(response_content)
        except json.JSONDecodeError as e:
            return None, None, f"JSON parsing error: {str(e)}"

        try:
            if isinstance(data_model, TypeAdapter):
                validated_data = data_model.validate_python(parsed_data)
                return validated_data, COT_content, None

            if isinstance(parsed_data, list):
                if hasattr(data_model, "model_fields") and "samples" in data_model.model_fields:
                    validated_data = data_model.model_validate({"samples": parsed_data})
                    return validated_data, COT_content, None

                validated_items = []
                for item in parsed_data:
                    validated_items.append(data_model.model_validate(item))
                return validated_items, COT_content, None

            validated_data = data_model.model_validate(parsed_data)
            return validated_data, COT_content, None
        except ValidationError as e:
            return None, COT_content, f"Validation error: {str(e)}"

    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"


def validate_llm_response(
    prompt: PromptInput,
    data_model: Type[BaseModel],
    llm=None,
    n_retry: int = 5,
    workflow_stage: str = "unlabeled",
) -> tuple:
    """
    Call LLM and validate response with retry mechanism.
    Logs full prompt/response via the 'llm_calls' logger.
    Returns (validated_data, COT_content, error_message).
    """
    import uuid

    normalized_prompt = normalize_prompt_input(prompt)
    current_prompt: PromptInput = normalized_prompt
    call_id = str(uuid.uuid4())[:8]
    model_name = str(getattr(llm, "model_name", "unknown")) if llm else "unknown"
    stage = _normalize_workflow_stage(workflow_stage)

    try:
        response_content = call_llm(
            current_prompt,
            llm=llm,
            call_id=f"{call_id}-init",
            workflow_stage=stage,
        )
        preview = response_content[:200].replace("\n", " ")
        print(f"[LLM DEBUG] Initial response preview: {preview}")
    except Exception as e:
        llm_logger.warning(
            f"\nLLM CALL FAILED [{call_id}] | Stage: {stage} | Model: {model_name}\n"
            f"Error: {str(e)}\n"
            + "=" * 60
        )
        return None, None, f"LLM call failed: {str(e)}"

    for attempt in range(n_retry + 1):
        validated_data, COT_content, validation_error = validate_with_model(
            data_model, response_content
        )

        if validation_error:
            is_empty_response = not response_content.strip()
            llm_logger.warning(
                f"\nVALIDATION FAILED [{call_id}] | Stage: {stage} | Model: {model_name} | "
                f"Attempt: {attempt + 1}/{n_retry + 1}\n"
                f"Error: {validation_error}\n"
                + "=" * 60
            )

            if attempt < n_retry:
                print(f"  Retry {attempt} of {n_retry} failed, trying again...")
            else:
                print(f"  Max retries reached. Last error: {validation_error}")
                llm_logger.error(
                    f"\nMAX RETRIES REACHED [{call_id}] | Stage: {stage} | Model: {model_name}\n"
                    f"Final error: {validation_error}\n"
                    + "=" * 60
                )
                return None, COT_content, f"Max retries reached. Last error: {validation_error}"

            if is_empty_response:
                current_prompt = normalized_prompt
                llm_logger.warning(
                    f"\nEMPTY LLM RESPONSE [{call_id}] | Stage: {stage} | Model: {model_name}\n"
                    "Retrying with the original prompt instead of a structure-fix prompt.\n"
                    + "=" * 60
                )
            else:
                validation_retry_prompt = create_retry_prompt(
                    original_prompt=normalized_prompt["prompt_text"],
                    original_response=response_content,
                    error_message=validation_error,
                )
                current_prompt = {
                    "prompt": validation_retry_prompt,
                    "pdf_paths": normalized_prompt["pdf_paths"],
                    "images_base64": normalized_prompt["images_base64"],
                    "image_mime_type": normalized_prompt["image_mime_type"],
                }
            try:
                response_content = call_llm(
                    current_prompt,
                    llm=llm,
                    call_id=f"{call_id}-retry-{attempt + 1}",
                    workflow_stage=stage,
                )
            except Exception as e:
                llm_logger.error(
                    f"\nLLM RETRY CALL FAILED [{call_id}] | Stage: {stage} | Model: {model_name} | "
                    f"Retry: {attempt + 1}\n"
                    f"Error: {str(e)}\n"
                    + "=" * 60
                )
                return None, None, f"LLM retry call failed: {str(e)}"
            continue

        # Success
        llm_logger.info(
            f"\nVALIDATION PASSED [{call_id}] | Stage: {stage} | Model: {model_name} | "
            f"Attempts: {attempt + 1}/{n_retry + 1}\n"
            + "=" * 60
        )
        return validated_data, COT_content, None

    return None, None, "Unexpected error in validation loop"


__all__ = [
    "PromptInput",
    "RawInputContent",
    "build_prompt_input",
    "call_llm",
    "create_retry_prompt",
    "get_prompt_source_text",
    "is_multimodal_raw_input",
    "load_raw_input_from_file",
    "parse_json_response",
    "pdf_to_base64_images",
    "_is_chinese",
    "validate_llm_response",
    "validate_with_model",
]
