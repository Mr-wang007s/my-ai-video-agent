#!/usr/bin/env python3
"""
Validate pipeline JSON outputs against their schemas.

Usage:
    python scripts/validate_schema.py --target characters --project PROJECT_ID
    python scripts/validate_schema.py --target script_breakdown --project PROJECT_ID
    python scripts/validate_schema.py --target all --project PROJECT_ID

Outputs JSON: {"status": "success/failed", "errors": [...], "warnings": [...]}
"""

import argparse
import json
import sys
import os

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print(json.dumps({
        "status": "failed",
        "error": "jsonschema not installed. Run: pip install jsonschema"
    }))
    sys.exit(1)


SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")
PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects")

# Map targets to their schema and data file paths
TARGETS = {
    "characters": {
        "schema": os.path.join(SCHEMA_DIR, "character_list.schema.json"),
        "data_file": "characters.json",
        "description": "Character list validation"
    },
    "script_breakdown": {
        "schema": os.path.join(SCHEMA_DIR, "script_breakdown.schema.json"),
        "data_file": "script_breakdown.json",
        "description": "Script breakdown (3-layer) validation"
    }
}


def load_json(path):
    """Load a JSON file with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"


def validate_target(target_name, project_id):
    """Validate a single target and return results."""
    target = TARGETS[target_name]
    results = {
        "target": target_name,
        "description": target["description"],
        "errors": [],
        "warnings": []
    }

    # Load schema
    schema_data = load_json(target["schema"])
    if isinstance(schema_data, tuple):
        results["errors"].append(schema_data[1])
        return results

    # Load data
    data_path = os.path.join(PROJECTS_DIR, project_id, target["data_file"])
    data = load_json(data_path)
    if isinstance(data, tuple):
        results["errors"].append(data[1])
        return results

    # Validate
    validator = Draft7Validator(schema_data)
    validation_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

    for error in validation_errors:
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        results["errors"].append({
            "path": path,
            "message": error.message,
            "schema_path": ".".join(str(p) for p in error.schema_path)
        })

    # Additional semantic checks
    if target_name == "characters" and data:
        results["warnings"].extend(check_characters_semantic(data))
    elif target_name == "script_breakdown" and data:
        results["warnings"].extend(check_breakdown_semantic(data))

    return results


def check_characters_semantic(data):
    """Semantic checks beyond schema validation for characters.json."""
    warnings = []
    characters = data.get("characters", [])

    for i, char in enumerate(characters):
        name = char.get("name", f"character[{i}]")

        # Check tok_description starts with <TOK> if present and non-empty
        tok = char.get("tok_description", "")
        if tok and not tok.startswith("<TOK>"):
            warnings.append(f"{name}: tok_description should start with '<TOK>'")

        # Check design_status consistency with asset_dir
        status = char.get("design_status", "")
        asset_dir = char.get("asset_dir", "")
        if status == "designed" and not asset_dir:
            warnings.append(f"{name}: design_status='designed' but asset_dir is empty")
        if status == "designed" and not tok:
            warnings.append(f"{name}: design_status='designed' but tok_description is empty")

        # Check visual_identifiers exist for designed characters
        if status == "designed" and not char.get("visual_identifiers"):
            warnings.append(f"{name}: design_status='designed' but no visual_identifiers")

    return warnings


def check_breakdown_semantic(data):
    """Semantic checks beyond schema validation for script_breakdown.json."""
    warnings = []
    valid_durations = {4, 5, 10, 15}

    # Check for Sub-Scripts
    sub_script_keys = [k for k in data.keys() if k.startswith("Sub-Script")]
    if not sub_script_keys:
        warnings.append("No Sub-Script keys found at top level")
        return warnings

    shot_count = 0
    for ss_key in sub_script_keys:
        ss = data[ss_key]
        scene_annotation = ss.get("Scene Annotation", {})

        scene_keys = [k for k in scene_annotation.keys() if k.startswith("Scene")]
        for sc_key in scene_keys:
            scene = scene_annotation[sc_key]
            shot_annotation = scene.get("Shot Annotation", {})

            shot_keys = [k for k in shot_annotation.keys()
                         if k.startswith("Shot") and k != "Shot Annotation"]
            for sh_key in shot_keys:
                shot = shot_annotation[sh_key]
                shot_count += 1
                shot_path = f"{ss_key}.{sc_key}.{sh_key}"

                # Check Duration is valid Seedance tier
                duration = shot.get("Duration")
                if duration and duration not in valid_durations:
                    warnings.append(
                        f"{shot_path}: Duration={duration} not in valid tiers {valid_durations}"
                    )

                # Check image_prompt is in English (basic heuristic)
                img_prompt = shot.get("image_prompt", "")
                if img_prompt:
                    # Check for Chinese characters as a rough heuristic
                    chinese_chars = sum(1 for c in img_prompt if '\u4e00' <= c <= '\u9fff')
                    if chinese_chars > len(img_prompt) * 0.1:
                        warnings.append(f"{shot_path}: image_prompt appears to contain Chinese text")

                # Check audio_prompt is in Chinese
                audio_prompt = shot.get("audio_prompt", "")
                if audio_prompt:
                    chinese_chars = sum(1 for c in audio_prompt if '\u4e00' <= c <= '\u9fff')
                    if chinese_chars < len(audio_prompt) * 0.1:
                        warnings.append(
                            f"{shot_path}: audio_prompt may not be in Chinese"
                        )

                # Check required Shot fields
                required_shot_fields = [
                    "Shot Type", "Camera Movement", "Duration",
                    "image_prompt", "video_prompt", "audio_prompt",
                    "Involving Characters", "Plot/Visual Description",
                    "Coarse Plot", "Subtitles"
                ]
                for field in required_shot_fields:
                    if field not in shot or not shot[field]:
                        warnings.append(f"{shot_path}: missing or empty field '{field}'")

    if shot_count == 0:
        warnings.append("No shots found in any Sub-Script")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Validate pipeline JSON outputs against schemas")
    parser.add_argument("--target", required=True, choices=list(TARGETS.keys()) + ["all"],
                        help="Which output to validate")
    parser.add_argument("--project", required=True, help="Project ID")
    args = parser.parse_args()

    # Verify project exists
    project_dir = os.path.join(PROJECTS_DIR, args.project)
    if not os.path.isdir(project_dir):
        print(json.dumps({
            "status": "failed",
            "error": f"Project directory not found: {project_dir}"
        }))
        sys.exit(1)

    targets = list(TARGETS.keys()) if args.target == "all" else [args.target]
    all_results = []
    has_errors = False

    for target in targets:
        result = validate_target(target, args.project)
        all_results.append(result)
        if result["errors"]:
            has_errors = True

    output = {
        "status": "failed" if has_errors else "success",
        "project_id": args.project,
        "results": all_results
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
