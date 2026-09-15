"""
Layered Async Workflow - Welding Data Extraction
English prompts and variables
Fix unhashable type: 'dict' issues
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError, Field, TypeAdapter
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import LLM utilities
from ..llm.llm_utils import (
    parse_json_response,
    create_retry_prompt,
    call_llm,
    validate_with_model,
    validate_llm_response,
)

from ..models.data_schemas import (
    ExtractionWorkflowState,
    SkeletonTable,
    SkeletonItemHash,
    SkeletonItem,
    SkeletonCheckItem,
    create_sample_fact_item_model,
    create_deep_result_item_model,
    create_material_dimension_item_model,
    get_sample_user_goal_field_names,
    get_material_user_goal_field_names,
)

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re

# Import prompts
from ..prompts import (
    get_skeleton_prompt,
    get_material_dimension_prompt,
    get_skeleton_check_prompt,
    get_skeleton_correction_prompt,
    get_sample_fact_prompt,
)





from ..exporters.node_results import set_json_output_dir, _save_node_result
from ..readers.multimodal_input import _prepare_prompt_input, _prompt_source_text_or_none
from .materials import _normalize_grade_text, _normalize_grade_texts, _extract_filler_grades
from .state_helpers import (
    _empty_sample_fact, _get_sample_user_goal, _get_sample_direct_goal,
    _get_material_user_goal, _get_material_direct_goal, _item_to_dict, _get_value,
)


# ==================== Node Functions ====================

def detect_language_node(state: ExtractionWorkflowState) -> Dict[str, Any]:
    """
    Node 0: Detect language based on input type and content
    This is the first node in the workflow.
    """
    print("=" * 60)
    print("[Step 0] Detecting Language")
    print("=" * 60)

    # Determine language based on input type
    lang = 'en'  # Default to English
    if isinstance(state.raw_text, list):
        lang = 'zh'  # Image-based (PDF) input defaults to Chinese
        print(f"[DEBUG] Input is image-based (PDF), using Chinese prompts")
    elif isinstance(state.raw_text, str):
        # Check if text contains Chinese characters
        if re.search(r'[\u4e00-\u9fff]', state.raw_text):
            lang = 'zh'
            print(f"[DEBUG] Input text contains Chinese characters, using Chinese prompts")
        else:
            print(f"[DEBUG] Input text is non-Chinese, using English prompts")
    else:
        print(f"[DEBUG] Unknown input type, defaulting to English prompts")

    print(f"[DEBUG] Detected language: {lang.upper()}")
    
    return {"lang": lang}


def extract_skeleton_node(state: ExtractionWorkflowState, llm=None) -> Dict[str, Any]:
    """
    Node 1: Extract skeleton table
    Extract all specimen lists from raw text
    """
    print("=" * 60)
    print("[Step 1] Extracting Skeleton Table - Specimen List")
    print("=" * 60)

    # Get language from state (set by detect_language_node)
    lang = getattr(state, 'lang', 'en')
    print(f"[DEBUG] Using language: {lang.upper()}")

    try:
        if llm is None:
            raise ValueError("LLM is not initialized")
        else:
            # Use prompt from prompts.py with language parameter
            prompt_text = get_skeleton_prompt(
                _prompt_source_text_or_none(state.raw_text),
                lang=lang,
                sample_user_goal=_get_sample_user_goal(state),
                sample_direct_goal=_get_sample_direct_goal(state),
            )
            prompt = _prepare_prompt_input(prompt_text, state.raw_text)

            # Use validate_llm_response with retry mechanism
            print("Calling LLM with validation and retry mechanism...")
            validated_data, COT_content, validation_error = validate_llm_response(
                prompt=prompt,
                data_model=SkeletonTable,
                llm=llm,
                n_retry=5,
                workflow_stage="extract_skeleton",
            )

            if validation_error:
                print(f"LLM validation failed: {validation_error}")
                return {
                    "skeleton": [],
                    "skeleton_cot": COT_content,
                    "error_message": f"Skeleton extraction failed: {validation_error}",
                    "next_step": "terminate"
                }

            # Debug: check validated_data type and content
            print(f"[DEBUG] validated_data type: {type(validated_data)}")
            print(f"[DEBUG] validated_data is list: {isinstance(validated_data, list)}")
            if isinstance(validated_data, list):
                print(f"[DEBUG] validated_data length: {len(validated_data)}")
                for i, item in enumerate(validated_data):
                    print(f"[DEBUG] Item {i}: {type(item)}, base_material={getattr(item, 'base_material', 'N/A')}")

            # validated_data is a SkeletonTable instance (List[SkeletonItem])
            # Convert to list for the new model structure
            skeleton = validated_data if isinstance(validated_data, list) else []
            skeletonhash = []
            for i, item in enumerate(skeleton):
                # Convert list to string before hashing
                factors_str = item.data_features
                specimen_id = str(abs(hash(factors_str)))
                print(f"[DEBUG] Item {i}: specimen_id={specimen_id}, factor={factors_str[:50] if factors_str else 'N/A'}...")
                # Create SkeletonItemHash object
                item_with_hash = SkeletonItemHash(
                    specimen_id=specimen_id,
                    base_material=item.base_material,
                    filler_material=item.filler_material,
                    welding_method=item.welding_method,
                    data_features=item.data_features,
                    source_quote=item.source_quote,
                )
                skeletonhash.append(item_with_hash)

            seen_features = set()
            skeletonhash_dedup = []
            for item in skeletonhash:
                if item.data_features not in seen_features:
                    seen_features.add(item.data_features)
                    skeletonhash_dedup.append(item)
            skeletonhash = skeletonhash_dedup

            print(f"Skeleton extraction complete, {len(skeletonhash)} samples found (after dedup)")
            print(f"[DEBUG] skeletonhash list length: {len(skeletonhash)}")

            # Save skeleton result to JSON
            skeleton_error_message = None
            if len(skeletonhash) == 0:
                skeleton_error_message = (
                    "Skeleton extraction returned an empty list. "
                    "LLM call likely succeeded but did not extract any samples."
                )

            result_dict = {
                "skeleton": [item.model_dump(mode='json') for item in skeletonhash],
                "error_message": skeleton_error_message,
                "skeleton_cot": COT_content,
            }
            if len(skeletonhash) == 0:
                result_dict["next_step"] = "terminate"
            print(f"[DEBUG] result_dict['skeleton'] length: {len(result_dict['skeleton'])}")
            _save_node_result("01_skeleton", result_dict)

            return result_dict

    except Exception as e:
        import traceback
        print(f"Skeleton extraction failed: {str(e)}")
        traceback.print_exc()
        return {
            "skeleton": [],
            "skeleton_cot": None,
            "error_message": f"Skeleton extraction failed: {str(e)}",
            "next_step": "terminate",
        }


def _extract_single_material_dim(grade, differentiation_factors, material_type, raw_text, llm, lang="en", material_user_goal=None, material_direct_goal=None):
    """Extract dimension info for single material in parallel"""
    if llm is None:
        raise ValueError("LLM is not initialized")

    prompt_text = get_material_dimension_prompt(
        grade,
        material_type,
        differentiation_factors,
        raw_text=_prompt_source_text_or_none(raw_text),
        lang=lang,  # Pass language parameter
        material_user_goal=material_user_goal,
        material_direct_goal=material_direct_goal,
    )
    prompt = _prepare_prompt_input(prompt_text, raw_text)
    material_model = create_material_dimension_item_model(material_user_goal, material_direct_goal=material_direct_goal)

    try:
        validated_data, _, validation_error = validate_llm_response(
            prompt=prompt,
            data_model=material_model,
            llm=llm,
            n_retry=5,
            workflow_stage=f"extract_global_dim/material[{material_type}:{grade}]",
        )

        if validation_error:
            print(f"  Validation failed for {grade}: {validation_error}")
            return material_model(grade=grade, material_type=material_type, composition_unit=None, chemical_composition=None)

        # Handle case where LLM returns a list instead of single object
        if isinstance(validated_data, list):
            if len(validated_data) > 0:
                validated_data = validated_data[0]
            else:
                validated_data = None

        if validated_data is None:
            print(f"  No valid data extracted for {grade}")
            return material_model(grade=grade, material_type=material_type, composition_unit=None, chemical_composition=None)

        print(f"  Extraction complete for {grade}, material_type: {material_type}")
        item_payload = _item_to_dict(validated_data)
        item_payload["grade"] = grade
        item_payload["material_type"] = material_type
        return material_model(**item_payload)
    except Exception as e:
        print(f"  Extraction failed for {differentiation_factors}: {str(e)}")
        return material_model(grade=grade, material_type=material_type, composition_unit=None, chemical_composition=None)


def _get_specimen_id_str(factor: Any) -> str:
    """Helper to ensure stable hashing for complex factor types."""
    if isinstance(factor, str):
        return factor
    return json.dumps(factor, sort_keys=True)


def _post_process_skeleton_dicts(item_dicts: List[Dict[str, Any]]) -> List[SkeletonItemHash]:
    """Convert raw dicts into SkeletonItemHash with compatibility fixes, hashing, and dedup."""
    final_skeleton_hashed = []
    for item_dict in item_dicts:
        try:
            # Compatibility fixes from original code
            if 'filler_material' in item_dict and isinstance(item_dict['filler_material'], list):
                new_filler_list = []
                for i, f in enumerate(item_dict['filler_material']):
                    if isinstance(f, str):
                        new_filler_list.append({f"welding_name{i+1}": f})
                    elif isinstance(f, dict):
                        new_filler_list.append(f)
                item_dict['filler_material'] = new_filler_list

            skeleton_item = SkeletonItem(**item_dict)
            specimen_id_str = _get_specimen_id_str(skeleton_item.data_features)
            specimen_id = str(abs(hash(specimen_id_str)))

            item_with_hash = SkeletonItemHash(specimen_id=specimen_id, **skeleton_item.model_dump())
            final_skeleton_hashed.append(item_with_hash)
        except Exception as e:
            print(f"  Failed to process item: {str(e)}, skipping: {item_dict}")
            continue

    # Deduplicate by data_features
    seen_features = set()
    final_skeleton_dedup = []
    for item in final_skeleton_hashed:
        if item.data_features not in seen_features:
            seen_features.add(item.data_features)
            final_skeleton_dedup.append(item)

    return final_skeleton_dedup


def _build_next_skeleton_items(
    correct_items: List[Dict[str, Any]],
    missing_items: List[Dict[str, Any]],
    corrected_full_snapshot: Optional[List[Dict[str, Any]]] = None,
) -> List[SkeletonItemHash]:
    """Build the next skeleton without mixing snapshot and delta semantics.

    The Corrector prompt returns a complete corrected skeleton.  When that
    snapshot is available it must replace the Inspector lists; appending it to
    ``correct_items`` and ``missing_items`` duplicates the same specimens.
    """
    if corrected_full_snapshot:
        source_items = corrected_full_snapshot
    else:
        source_items = correct_items + missing_items
    return _post_process_skeleton_dicts(source_items)


def check_skeleton_node(
    state: ExtractionWorkflowState,
    llm,
    pass_skeleton_cot_to_inspector: bool = True,
    pass_skeleton_cot_to_corrector: bool = True,
) -> Dict[str, Any]:
    """
    Skeleton check node with Inspector-Corrector loop.
    Loop: Inspector checks -> if not passed, Corrector fixes -> re-check.
    Max 3 cycles.
    """
    print("=" * 60)
    print("[Step 1.5] Skeleton Check (Inspector-Corrector Loop)")
    print("=" * 60)

    if len(state.skeleton) == 0:
        return {
            "skeleton": state.skeleton,
            "error_message": "Skeleton is empty, no samples found",
            "extraction_completed": True,
            "next_step": "terminate"
        }

    try:
        if llm is None:
            raise ValueError("LLM is not initialized")

        from ..models.data_schemas import SkeletonCheckItem

        lang = getattr(state, 'lang', 'en')
        max_cycles = 3

        # Current skeleton starts from state.skeleton
        current_skeleton_items = state.skeleton
        skeleton_cot = state.skeleton_cot  # Optional[str]
        inspector_skeleton_cot = skeleton_cot if pass_skeleton_cot_to_inspector else ""
        corrector_skeleton_cot = skeleton_cot if pass_skeleton_cot_to_corrector else ""
        print(
            "[Skeleton COT input] "
            f"Inspector={'ON' if pass_skeleton_cot_to_inspector else 'OFF'}, "
            f"Corrector={'ON' if pass_skeleton_cot_to_corrector else 'OFF'}"
        )
        all_cycles_data = []

        for cycle in range(1, max_cycles + 1):
            print("=" * 60)
            print(f"[Cycle {cycle}/{max_cycles}] Inspector Pass (Lang: {lang.upper()})")
            print("=" * 60)

            # --- INSPECTOR: check current skeleton ---
            skeleton_json = json.dumps(
                [item.model_dump(mode='json') for item in current_skeleton_items],
                ensure_ascii=False, indent=2
            )
            diff_factors_example = json.dumps(
                current_skeleton_items[0].data_features if current_skeleton_items else "",
                ensure_ascii=False
            )

            prompt_text = get_skeleton_check_prompt(
                skeleton_json=skeleton_json,
                skeleton_cot=inspector_skeleton_cot,
                source_text=_prompt_source_text_or_none(state.raw_text),
                diff_factors_example=diff_factors_example,
                lang=lang,
                sample_user_goal=_get_sample_user_goal(state),
                sample_direct_goal=_get_sample_direct_goal(state),
            )
            prompt = _prepare_prompt_input(prompt_text, state.raw_text)

            print(f"Calling Inspector LLM (cycle {cycle})...")
            check_result, _, validation_error = validate_llm_response(
                prompt=prompt,
                data_model=SkeletonCheckItem,
                llm=llm,
                n_retry=3,
                workflow_stage=f"check_skeleton/inspector_cycle_{cycle}",
            )

            if validation_error:
                print(f"Inspector validation failed on cycle {cycle}: {validation_error}")
                # Fall back to returning current skeleton
                break

            cycle_data = {
                "cycle": cycle,
                "check_passed": check_result.check_passed,
                "problem_description": check_result.problem_description,
                "corrected_count": len(check_result.corrected_results or []),
                "false_count": len(check_result.false_results or []),
                "missing_count": len(check_result.missing_items or []),
                "duplicate_count": len(check_result.duplicate_items or []),
            }
            all_cycles_data.append(cycle_data)

            if check_result.check_passed:
                print(f"Inspector check PASSED on cycle {cycle}. No correction needed.")
                final_items_as_dicts = check_result.corrected_results or []
                if not final_items_as_dicts:
                    final_items_as_dicts = [item.model_dump(mode='json') for item in current_skeleton_items]

                final_skeleton_hashed = _post_process_skeleton_dicts(final_items_as_dicts)

                print("=" * 60)
                print(f"Skeleton check PASSED after {cycle} cycle(s). {len(final_skeleton_hashed)} records.")

                result_dict = {
                    "skeleton": [item.model_dump(mode='json') for item in final_skeleton_hashed],
                    "error_message": None,
                    "check_passed": True,
                    "corrected": cycle > 1,
                    "cycles": cycle,
                    "cycle_details": all_cycles_data,
                }
                _save_node_result("02_skeleton_check", result_dict)
                return result_dict

            # --- CHECK FAILED: need correction ---
            problem_desc = check_result.problem_description or "No specific reason provided."
            print(f"Inspector found issues (cycle {cycle}): {problem_desc}")

            correct_items_data = check_result.corrected_results or []
            false_items_data = check_result.false_results or []
            missing_items_data = check_result.missing_items or []

            if not false_items_data:
                print(
                    f"Cycle {cycle}: Check failed but no false results. "
                    f"Applying {len(missing_items_data)} missing item(s) to the current snapshot."
                )
                if correct_items_data or missing_items_data:
                    current_skeleton_items = _build_next_skeleton_items(
                        correct_items_data,
                        missing_items_data,
                    )
                print(
                    f"Cycle {cycle} missing-only update produced "
                    f"{len(current_skeleton_items)} item(s)."
                )
                # Re-run the Inspector so additions are validated instead of
                # returning a stale pre-update snapshot.
                continue

            # --- CORRECTOR: fix false items ---
            print("=" * 60)
            print(f"[Cycle {cycle}] Corrector Pass - fixing {len(false_items_data)} item(s)")
            print("=" * 60)

            _save_node_result(
                f"02_skeleton_false_items_cycle{cycle}",
                {"false_items": false_items_data, "problem_description": problem_desc}
            )

            correction_prompt_text = get_skeleton_correction_prompt(
                source_text=_prompt_source_text_or_none(state.raw_text),
                false_items_data=false_items_data,
                problem_desc=problem_desc,
                skeleton_json=skeleton_json,
                skeleton_cot=corrector_skeleton_cot,
                inspection_data=check_result.model_dump(mode='json'),
                lang=lang
            )
            correction_prompt = _prepare_prompt_input(correction_prompt_text, state.raw_text)

            corrector_result, _, correction_error = validate_llm_response(
                prompt=correction_prompt,
                data_model=SkeletonTable,
                llm=llm,
                n_retry=3,
                workflow_stage=f"check_skeleton/corrector_cycle_{cycle}",
            )

            corrected_full_snapshot = None
            if correction_error:
                print(
                    f"Corrector failed on cycle {cycle}: {correction_error}. "
                    "Falling back to Inspector correct and missing items."
                )
            else:
                # The Corrector contract is a COMPLETE corrected skeleton,
                # not a list of delta items.
                if isinstance(corrector_result, list):
                    corrected_full_snapshot = [
                        item.model_dump(mode='json') if hasattr(item, 'model_dump') else item
                        for item in corrector_result
                    ]
                else:
                    corrected_full_snapshot = (
                        corrector_result.corrected_results
                        if hasattr(corrector_result, 'corrected_results')
                        else []
                    )
                print(
                    f"Corrector returned a full snapshot with "
                    f"{len(corrected_full_snapshot)} item(s)."
                )
                _save_node_result(
                    f"02_skeleton_corrected_items_cycle{cycle}",
                    {"corrected_items": corrected_full_snapshot}
                )

            # A successful Corrector snapshot replaces the Inspector lists.
            # Only the failure path uses correct+missing as a fallback delta.
            current_skeleton_items = _build_next_skeleton_items(
                correct_items_data,
                missing_items_data,
                corrected_full_snapshot=corrected_full_snapshot,
            )
            print(f"Cycle {cycle} complete. Assembled {len(current_skeleton_items)} item(s) for next check.")

        # --- Loop exhausted or broken ---
        print("=" * 60)
        print(f"Skeleton check loop ended. Max cycles={max_cycles}, ran {len(all_cycles_data)} cycle(s).")

        final_skeleton_hashed = current_skeleton_items

        result_dict = {
            "skeleton": [item.model_dump(mode='json') for item in final_skeleton_hashed],
            "error_message": None,
            "check_passed": False,
            "corrected": len(all_cycles_data) > 0,
            "cycles": len(all_cycles_data),
            "cycle_details": all_cycles_data,
        }
        _save_node_result("02_skeleton_check", result_dict)
        return result_dict

    except Exception as e:
        print(f"Skeleton check failed: {str(e)}")
        result_dict = {
            "skeleton": [item.model_dump(mode='json') for item in state.skeleton] if state.skeleton else [],
            "error_message": f"Skeleton check exception: {str(e)}"
        }
        _save_node_result("02_skeleton_check", result_dict)
        return result_dict


def extract_global_dim_node(state: ExtractionWorkflowState, llm) -> Dict[str, Any]:
    """
    Node 2: Extract global dimension table
    Extract chemical composition and mechanical properties for all base and filler materials in parallel
    """
    print("=" * 60)
    print("[Step 2] Extracting Global Dimension Table - Material Properties")
    print("=" * 60)

    # Debug: check if llm is passed
    print(f"[DEBUG] llm is None: {llm is None}")

    # Get language from state (set by extract_skeleton_node)
    lang = getattr(state, 'lang', 'en')
    material_user_goal = _get_material_user_goal(state)
    material_direct_goal = _get_material_direct_goal(state)
    material_hash_model = create_material_dimension_item_model(material_user_goal, include_specimen_id=True, material_direct_goal=material_direct_goal)
    print(f"[DEBUG] Using language: {lang.upper()}")

    if state.skeleton is None:
        return {
            "material_dimensions": [],
            "error_message": "Skeleton is empty, cannot extract dimension table"
        }

    try:
        # Step 1: Identify unique materials to reduce redundant extractions
        unique_materials_to_extract = {}  # Using a dict to store unique materials
        for item in state.skeleton:
            # base_material is now List[str]; iterate each grade
            for base_grade in _normalize_grade_texts(item.base_material):
                key = (base_grade, "base_metal")
                if key not in unique_materials_to_extract:
                    unique_materials_to_extract[key] = item.data_features

            for filler_grade in _extract_filler_grades(item.filler_material):
                key = (filler_grade, "filler")
                if key not in unique_materials_to_extract:
                    unique_materials_to_extract[key] = item.data_features
        
        print(f"Found {len(unique_materials_to_extract)} unique materials to extract.")
        if unique_materials_to_extract:
            preview = list(unique_materials_to_extract.keys())[:20]
            print(f"[DEBUG] Material extraction keys preview: {preview}")

        # Step 2: Extract properties for unique materials in parallel
        total_tasks = len(unique_materials_to_extract)
        if total_tasks == 0:
            return { "material_dimensions": [], "error_message": "No materials found to extract."}

        print(f"Starting {total_tasks} threads for parallel material dimension extraction...")
        
        material_properties_cache = {} # Cache for extracted properties
        max_concurrent = min(10, total_tasks)

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {
                executor.submit(
                    _extract_single_material_dim, 
                    grade, 
                    distinguishing_factor, 
                    material_type, 
                    state.raw_text, 
                    llm,
                    lang,  # Pass language parameter
                    material_user_goal,
                    material_direct_goal,
                ): (grade, material_type)
                for (grade, material_type), distinguishing_factor in unique_materials_to_extract.items()
            }

            for future in as_completed(futures):
                grade, material_type = futures[future]                        
                try:
                    properties = future.result()
                    material_properties_cache[(grade, material_type)] = properties
                    print(f"  Extraction complete for [{material_type}] {grade}")
                except Exception as e:
                    print(f"  Extraction failed for [{material_type}] {grade}: {str(e)}")

        # Step 3: Map cached properties back to each skeleton item to build the final list
        material_dims_hash = []
        for item in state.skeleton:
            # Process base materials (now List[str])
            for base_grade in _normalize_grade_texts(item.base_material):
                if (base_grade, "base_metal") in material_properties_cache:
                    properties = material_properties_cache[(base_grade, "base_metal")]
                    specimen_id_str = item.data_features
                    property_payload = _item_to_dict(properties)
                    property_payload["specimen_id"] = str(abs(hash(specimen_id_str)))
                    item_with_hash = material_hash_model(**property_payload)
                    material_dims_hash.append(item_with_hash)

            # Process filler materials
            for filler_grade in _extract_filler_grades(item.filler_material):
                if (filler_grade, "filler") in material_properties_cache:
                    properties = material_properties_cache[(filler_grade, "filler")]
                    specimen_id_str = item.data_features
                    property_payload = _item_to_dict(properties)
                    property_payload["specimen_id"] = str(abs(hash(specimen_id_str)))
                    item_with_hash = material_hash_model(**property_payload)
                    material_dims_hash.append(item_with_hash)

        print(f"Global dimension mapping complete, total items created: {len(material_dims_hash)}")

        result_dict = {
            "material_dimensions": [item.model_dump(mode='json') for item in material_dims_hash],
            "error_message": None
        }
        _save_node_result("03_material_dimension", result_dict)

        return result_dict

    except Exception as e:
        print(f"Global dimension extraction failed: {str(e)}")
        result_dict = {
            "material_dimensions": [],
            "error_message": f"Global dimension extraction failed: {str(e)}"
        }
        _save_node_result("03_material_dimension", result_dict)
        return result_dict


def _extract_single_sample_fact(
    skeleton_item,
    raw_text,
    llm,
    lang="en",
    sample_user_goal=None,
    sample_direct_goal=None,
    workflow_stage="extract_fact_table/sample",
):
    """Extract welding params and sample-goal performance data for one sample."""
    if llm is None:
        raise ValueError("LLM is not initialized,in _extract_single_sample_fact")

    try:
        base_list = skeleton_item.base_material if isinstance(skeleton_item.base_material, list) else [skeleton_item.base_material]
        base = ", ".join(str(b) for b in base_list if b)
        filler_json = json.dumps(_extract_filler_grades(skeleton_item.filler_material), ensure_ascii=False)
        welding_method = skeleton_item.welding_method
        factors = skeleton_item.data_features

        prompt_text = get_sample_fact_prompt(
            base,
            filler_json,
            welding_method,
            factors,
            _prompt_source_text_or_none(raw_text),
            lang=lang,
            sample_user_goal=sample_user_goal,
            sample_direct_goal=sample_direct_goal,
        )
        prompt = _prepare_prompt_input(prompt_text, raw_text)
        sample_fact_model = create_sample_fact_item_model(sample_user_goal, sample_direct_goal=sample_direct_goal)

        print("  [DEBUG] Prompt created for sample", flush=True)
        print(
            f"  [DEBUG] Skeleton data: base_material={base}, "
            f"filler_material={skeleton_item.filler_material}, data_features={factors}",
            flush=True,
        )
        print("  [DEBUG] Starting extraction for sample", flush=True)

        validated_data, _, validation_error = validate_llm_response(
            prompt=prompt,
            data_model=sample_fact_model,
            llm=llm,
            n_retry=5,
            workflow_stage=workflow_stage,
        )
        if validation_error:
            print(f"  Sample validation failed: {validation_error}")
            return _empty_sample_fact(sample_user_goal, sample_direct_goal)

        if isinstance(validated_data, list):
            validated_data = validated_data[0] if validated_data else None

        return validated_data or _empty_sample_fact(sample_user_goal, sample_direct_goal)

    except Exception as e:
        import traceback

        print(f"  Sample extraction failed: {str(e)}", flush=True)
        traceback.print_exc()
        return _empty_sample_fact(sample_user_goal, sample_direct_goal)


def extract_fact_table_node(state: ExtractionWorkflowState, llm) -> Dict[str, Any]:
    """
    Node 3: Extract sample fact table
    Extract welding params and test performance for all samples in parallel
    """
    print("=" * 60)
    print("[Step 3] Extracting Sample Fact Table - Welding Params and Test Performance")
    print("=" * 60)

    # Get language from state (set by extract_skeleton_node)
    lang = getattr(state, 'lang', 'en')
    sample_user_goal = _get_sample_user_goal(state)
    sample_direct_goal = _get_sample_direct_goal(state)
    sample_hash_model = create_sample_fact_item_model(sample_user_goal, include_specimen_id=True, sample_direct_goal=sample_direct_goal)
    print(f"[DEBUG] Using language: {lang.upper()}")

    if llm is None:
        raise ValueError("LLM is not initialized")
    try:
        # Now skeleton is directly List[SkeletonItem]
        samples_list = state.skeleton
        task_count = len(samples_list)


        print(f"Starting {task_count} threads for parallel sample fact extraction...")
        if task_count == 0:
            result_dict = {
                "sample_facts": [],
                "error_message": (
                    "No skeleton samples available for sample-fact extraction. "
                    "This usually means the skeleton stage returned no samples."
                ),
            }
            _save_node_result("04_sample_fact", result_dict)
            return result_dict

        samples = []

        # Limit max workers to avoid API rate limiting (429 errors)
        max_concurrent = min(5, task_count)  # Max 5 concurrent requests

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}
            for sample_index, item in enumerate(samples_list, start=1):
                # Convert list to string before hashing
                factors_str = item.data_features
                specimen_id_str = abs(hash(factors_str))
                workflow_stage = (
                    f"extract_fact_table/sample_{sample_index}[specimen_id:{specimen_id_str}]"
                )
                future = executor.submit(
                    _extract_single_sample_fact,
                    item,
                    state.raw_text,
                    llm,
                    lang,
                    sample_user_goal,
                    sample_direct_goal,
                    workflow_stage,
                )
                futures[future] = (specimen_id_str, item.data_features)

            # Collect results
            for future in as_completed(futures):
                specimen_id_str, data_diff_factors = futures[future]
                specimen_id = str(specimen_id_str)
                try:
                    single_item = future.result()
                    item_payload = _item_to_dict(single_item)
                    item_payload["specimen_id"] = specimen_id
                    item_with_hash = sample_hash_model(**item_payload)
                    samples.append(item_with_hash)
                    print(f"  - Sample {specimen_id} extraction complete")
                except Exception as e:
                    print(f"  - Sample {specimen_id} extraction failed: {str(e)}")

        # Now sample_facts is directly List[SampleFactItem]
        print(f"Sample fact extraction complete, {len(samples)} samples")

        result_dict = {
            "sample_facts": [item.model_dump(mode='json') for item in samples],
            "error_message": None
        }
        _save_node_result("04_sample_fact", result_dict)

        return result_dict

    except Exception as e:
        print(f"Sample fact extraction failed: {str(e)}")
        result_dict = {
            "sample_facts": [],
            "error_message": f"Sample fact extraction failed: {str(e)}"
        }
        _save_node_result("04_sample_fact", result_dict)
        return result_dict


def join_and_critic_node(state: ExtractionWorkflowState, llm) -> Dict[str, Any]:
    """
    Node 4: Data Merge and Critic Validation
    Merge skeleton, global dimension, sample fact table together, and perform physics logic validation
    """
    print("=" * 60)
    print("[Step 4] Data Merge and Validation")
    print("=" * 60)

    # Updated to use new model structure
    # skeleton is List[SkeletonItem], material_dimensions is List[MaterialDimensionItem], sample_facts is List[SampleFactItem]
    try:
        sample_user_goal = _get_sample_user_goal(state)
        material_user_goal = _get_material_user_goal(state)
        sample_direct_goal = _get_sample_direct_goal(state)
        material_direct_goal = _get_material_direct_goal(state)
        deep_result_model = create_deep_result_item_model(sample_user_goal, sample_direct_goal=sample_direct_goal)
        # Build specimen_id to dimension info mapping
        # MaterialDimensionItemHash has specimen_id, grade, material_type, etc.
        base_dim_map = {}
        filler_dim_map = {}
        for item in state.material_dimensions:
            specimen_id = _get_value(item, "specimen_id")
            material_type = _get_value(item, "material_type")
            if material_type == "base_metal":
                base_dim_map[specimen_id] = item
            elif material_type == "filler":
                filler_dim_map[specimen_id] = item

        # Build specimen_id to fact mapping
        fact_map = {}
        for item in state.sample_facts:
            specimen_id = _get_value(item, "specimen_id")
            fact_map[specimen_id] = item

        # Merge data
        deep_results = []
        errors = []

        # Now skeleton is List[SkeletonItem], each has specimen_id
        for skeleton_item in state.skeleton:
            # Get specimen_id from skeleton_item
            specimen_id = skeleton_item.specimen_id

            # Get corresponding fact item by specimen_id
            fact_item = fact_map.get(specimen_id) if specimen_id else None
            fact_payload = _item_to_dict(fact_item)
            goal_payload = {
                field_name: fact_payload.get(field_name)
                for field_name in get_sample_user_goal_field_names(sample_user_goal, sample_direct_goal)
                if fact_payload.get(field_name) is not None
            }

            # Get base material dimension by specimen_id
            base_dim = base_dim_map.get(specimen_id)

            # Get filler material dimensions by specimen_id
            filler_dim = filler_dim_map.get(specimen_id)

            # Build deep nested result
            # Extract chemical composition and mechanical properties
            base_chemical = _get_value(base_dim, "chemical_composition") if base_dim else None
            # Build mechanical properties dict from individual fields
            base_original_props = None
            if base_dim:
                props_dict = {}
                for goal_field in get_material_user_goal_field_names(material_user_goal, material_direct_goal):
                    value = _get_value(base_dim, goal_field)
                    if value:
                        props_dict[goal_field] = value
                if props_dict:
                    base_original_props = props_dict

            filler_chemical_dict = {}
            filler_original_props_dict = {}
            if filler_dim:
                # Only add if chemical_composition/mechanical_properties is not None
                filler_chemical = _get_value(filler_dim, "chemical_composition")
                filler_grade = _get_value(filler_dim, "grade")
                if filler_chemical is not None:
                    filler_chemical_dict[filler_grade] = filler_chemical


            # Get filler material list - now directly List[Dict[str, Any]]
            filler_material_list = skeleton_item.filler_material if skeleton_item.filler_material else []

            # Get welding params list (from skeleton_item)
            # Now directly List[Dict[str, Any]]
            welding_params_list = fact_payload.get("welding_params", []) if fact_item else []

            deep_payload = {
                "specimen_id": specimen_id,
                "data_features": skeleton_item.data_features if skeleton_item.data_features else "",
                "welding_method": skeleton_item.welding_method,
                "base_material": skeleton_item.base_material,
                "base_chemical_composition": base_chemical,
                "filler_material": filler_material_list,
                "welding_params": welding_params_list,
                "test_method": fact_payload.get("test_method"),
                "testing_area": fact_payload.get("testing_area"),
                "testing_standard": fact_payload.get("testing_standard"),
                "testing_specimen_size": fact_payload.get("testing_specimen_size"),
                "performance_result_source": fact_payload.get("performance_result_source"),
                **goal_payload,
            }
            deep_item = deep_result_model(**deep_payload)

            # Critic validation - physics logic check
            if fact_item and (
                ("tensile_strength_value" in goal_payload and "yield_strength_value" in goal_payload)
                or ("tensile_strength" in goal_payload and "yield_strength" in goal_payload)
            ):
                tensile_str = goal_payload.get("tensile_strength_value") or goal_payload.get("tensile_strength")
                yield_str = goal_payload.get("yield_strength_value") or goal_payload.get("yield_strength")

                # Extract values for comparison
                tensile_val = _extract_numeric_value(tensile_str)
                yield_val = _extract_numeric_value(yield_str)

                if tensile_val is not None and yield_val is not None:
                    if yield_val >= tensile_val:
                        error = f"Sample {specimen_id}: yield strength({yield_str}) >= tensile strength({tensile_str}), violates physics!"
                        errors.append(error)
                        print(f"  Validation warning: {error}")

            deep_results.append(deep_item)

        # Now final_result is directly List[DeepNestedResultItem]
        print(f"\nData merge complete, {len(deep_results)} records")
        if errors:
            print(f"Validation found issues: {len(errors)}")
        else:
            print("Validation passed, no physics logic errors")

        result_dict = {
            "final_result": [_item_to_dict(item) for item in deep_results],
            "error_message": None,
            "validation_errors": errors
        }
        _save_node_result("05_deep_result", result_dict)

        return result_dict

    except Exception as e:
        print(f"Data merge failed: {str(e)}")
        import traceback
        traceback.print_exc()
        result_dict = {
            "final_result": [],
            "error_message": f"Data merge failed: {str(e)}"
        }
        _save_node_result("05_deep_result", result_dict)
        return result_dict
        


def _extract_numeric_value(value_str) -> Optional[float]:
    """Extract numeric value from string"""
    if value_str is None:
        return None
    # If already numeric type, return directly
    if isinstance(value_str, (int, float)):
        return float(value_str)
    # If not string, convert to string
    if not isinstance(value_str, str):
        value_str = str(value_str)
    if not value_str:
        return None
    # Match number (may have units)
    match = re.search(r'([\d.]+)', value_str)
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


# ==================== Workflow Creation ====================

from functools import partial


def create_layered_workflow(
    llm=None,
    json_output_dir: str = None,
    node_llms: Dict[str, Any] = None,
    pass_skeleton_cot_to_inspector: bool = True,
    pass_skeleton_cot_to_corrector: bool = True,
):
    """
    Create layered async workflow

    Args:
        llm: Default large language model instance used when a node-specific
             model is not provided.
        json_output_dir: Optional directory to save JSON files for each node result
        node_llms: Optional mapping for node-specific model instances. Supported
             keys: extract_skeleton, check_skeleton, extract_global_dim,
             extract_fact_table.
        pass_skeleton_cot_to_inspector: Whether the Inspector receives the
             explicit COT produced by skeleton extraction.
        pass_skeleton_cot_to_corrector: Whether the Corrector receives the
             explicit COT produced by skeleton extraction.
    """
    # Set JSON output directory
    if json_output_dir:
        set_json_output_dir(json_output_dir)

    node_llms = node_llms or {}

    def _node_llm(node_name: str):
        return node_llms.get(node_name) or llm

    # Debug: print llm info
    print(f"[DEBUG] create_layered_workflow received llm: {type(llm)}")
    if node_llms:
        node_llm_types = {name: type(model).__name__ for name, model in node_llms.items()}
        print(f"[DEBUG] create_layered_workflow received node_llms: {node_llm_types}")

    # Use partial to bind llm parameter to each node function
    def detect_language_wrapper(state):
        return detect_language_node(state)

    def extract_skeleton_wrapper(state):
        return extract_skeleton_node(state, llm=_node_llm("extract_skeleton"))

    def check_skeleton_wrapper(state):
        return check_skeleton_node(
            state,
            llm=_node_llm("check_skeleton"),
            pass_skeleton_cot_to_inspector=pass_skeleton_cot_to_inspector,
            pass_skeleton_cot_to_corrector=pass_skeleton_cot_to_corrector,
        )

    def extract_global_dim_wrapper(state):
        return extract_global_dim_node(state, llm=_node_llm("extract_global_dim"))

    def extract_fact_table_wrapper(state):
        return extract_fact_table_node(state, llm=_node_llm("extract_fact_table"))

    def join_and_critic_wrapper(state):
        return join_and_critic_node(state, llm=None)

    workflow = StateGraph(ExtractionWorkflowState)

    # Add nodes
    workflow.add_node("detect_language", detect_language_wrapper)        # Step 0: Detect language
    workflow.add_node("extract_skeleton", extract_skeleton_wrapper)      # Step 1: Extract skeleton
    workflow.add_node("check_skeleton", check_skeleton_wrapper)          # Step 1.5: Skeleton check
    workflow.add_node("extract_global_dim", extract_global_dim_wrapper)  # Step 2: Extract global dimension
    workflow.add_node("extract_fact_table", extract_fact_table_wrapper)  # Step 3: Extract sample fact
    workflow.add_node("join_and_critic", join_and_critic_wrapper)        # Step 4: Merge and validate

    def should_continue(state: ExtractionWorkflowState) -> str:
        """Determine whether to continue or terminate based on state"""
        if getattr(state, 'next_step', None) == "terminate":
            return "end"
        return "continue"

    # Set entry point and edges
    workflow.set_entry_point("detect_language")                         # Start with language detection
    workflow.add_edge("detect_language", "extract_skeleton")            # language -> skeleton
    workflow.add_conditional_edges(                                      # skeleton -> check or END
        "extract_skeleton",
        should_continue,
        {
            "continue": "check_skeleton",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "check_skeleton",
        should_continue,
        {
            "continue": "extract_global_dim",
            "end": END
        }
    )
    workflow.add_edge("extract_global_dim", "extract_fact_table")             # global dimension -> sample fact
    workflow.add_edge("extract_fact_table", "join_and_critic")        # sample fact -> merge validation
    workflow.add_edge("join_and_critic", END)

    return workflow.compile()


# Export
__all__ = [
    "create_layered_workflow",
    "detect_language_node",
    "extract_skeleton_node",
    "check_skeleton_node",
    "extract_global_dim_node",
    "extract_fact_table_node",
    "join_and_critic_node",
]
