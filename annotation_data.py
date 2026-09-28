"""Build and write annotation JSON without changing the source mesh."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

SCHEMA_VERSION = "1.0"


def safe_object_type_name(value: str) -> str:
    """Convert Object type into a portable filename stem."""
    name = value.strip().lower()
    name = re.sub(r"[^a-z0-9._-]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("._-")
    return name or "annotation"


def default_output_path() -> str:
    object_type = safe_object_type_name(bpy.context.scene.aivision_object_type)
    if bpy.data.filepath:
        base_dir = Path(bpy.data.filepath).parent
        return str(base_dir / "annotations" / f"{object_type}.json")
    return f"//annotations/{object_type}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def vector_to_list(value: Vector) -> list[float]:
    return [round(float(component), 6) for component in value]


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_path() -> Path | None:
    configured = bpy.context.scene.aivision_model_source
    if configured:
        return Path(bpy.path.abspath(configured)).resolve()
    if bpy.data.filepath:
        return Path(bpy.data.filepath).resolve()
    return None


def source_file_metadata() -> dict[str, Any]:
    path = source_path()
    blend_path = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if path is None:
        return {
            "file_name": "unsaved_model",
            "source_model": None,
            "blend_file": str(blend_path) if blend_path else None,
            "model_fingerprint": None,
            "fingerprint_status": "configure_source_model_path",
        }
    return {
        "file_name": path.name,
        "source_model": str(path),
        "blend_file": str(blend_path) if blend_path else None,
        "model_fingerprint": sha256_file(path),
        "fingerprint_status": "source_model_or_blend_fingerprint",
        "source_path_configured": bool(bpy.context.scene.aivision_model_source),
    }


def object_record(obj: bpy.types.Object, index: int) -> dict[str, Any]:
    label = obj.get("aivision_part_label") or obj.name
    return {
        "id": f"part_{index:02d}",
        "object_name": obj.name,
        "label": label,
        "type": "part",
        "confidence": round(float(obj.get("aivision_confidence", 0.5)), 3),
        "geometry_ref": {
            "type": "blender_object",
            "object_name": obj.name,
        },
    }


def joint_record(obj: bpy.types.Object, index: int) -> dict[str, Any]:
    axis = Vector((0.0, 1.0, 0.0))
    if obj.get("aivision_axis"):
        axis = Vector(obj["aivision_axis"])
    if axis.length == 0:
        axis = Vector((0.0, 1.0, 0.0))
    axis.normalize()
    linked_parts = list(obj.get("aivision_connected_parts", []))
    return {
        "id": f"joint_{index:02d}",
        "object_name": obj.name,
        "type": obj.get("aivision_joint_type", "hinge_candidate"),
        "position_model_mm": vector_to_list(obj.location),
        "axis_model": vector_to_list(axis),
        "connected_parts": linked_parts,
        "confidence": round(float(obj.get("aivision_confidence", 0.5)), 3),
        "evidence": ["manual_annotation"],
        "needs_human_review": True,
        "notes": obj.get("aivision_notes", ""),
    }


def build_annotation() -> dict[str, Any]:
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    part_objects = [obj for obj in mesh_objects if obj.get("aivision_role") == "part"]
    joint_objects = [obj for obj in bpy.context.scene.objects if obj.get("aivision_role") == "joint"]

    return {
        "schema_version": SCHEMA_VERSION,
        "model": source_file_metadata(),
        "coordinate_system": {
            "name": "model_local_right_handed_z_up",
            "unit": "mm",
            "note": "Confirm Blender scene scale before using coordinates.",
        },
        "object_type": {
            "label": bpy.context.scene.aivision_object_type,
            "confidence": round(float(bpy.context.scene.aivision_object_confidence), 3),
        },
        "parts": [object_record(obj, index) for index, obj in enumerate(part_objects, 1)],
        "joint_candidates": [joint_record(obj, index) for index, obj in enumerate(joint_objects, 1)],
        "magnetization_candidates": [],
        "annotation": {
            "annotator": bpy.context.scene.aivision_annotator,
            "created_at": bpy.context.scene.aivision_created_at or utc_now(),
            "tool": "Blender AI Vision Annotation Helper",
            "status": "draft",
        },
    }


def validate_annotation() -> list[str]:
    scene = bpy.context.scene
    errors: list[str] = []
    if not scene.aivision_annotator.strip():
        errors.append("请填写 Annotator（标注人姓名）")
    if not scene.aivision_object_type.strip() or scene.aivision_object_type == "unknown":
        errors.append("请填写 Object type（物体类别）")
    if not scene.aivision_model_source:
        errors.append("请在 Source model 中选择原始 STL/OBJ/GLB 文件")
    elif sha256_file(source_path()) is None:
        errors.append("Source model 文件不存在或无法读取")
    if not any(obj.get("aivision_role") == "part" for obj in scene.objects if obj.type == "MESH"):
        errors.append("尚未标注任何部件，请先点击 Add selected as part")
    if not any(obj.get("aivision_role") == "joint" for obj in scene.objects):
        errors.append("尚未标注任何关节，请先添加 joint")
    return errors


def validate_annotation() -> list[str]:
    scene = bpy.context.scene
    errors: list[str] = []
    if not scene.aivision_annotator.strip():
        errors.append("请填写 Annotator（标注人姓名）")
    if not scene.aivision_object_type.strip() or scene.aivision_object_type == "unknown":
        errors.append("请填写 Object type（物体类别）")
    if not scene.aivision_model_source:
        errors.append("请在 Source model 中选择原始 STL/OBJ/GLB 文件")
    elif sha256_file(source_path()) is None:
        errors.append("Source model 文件不存在或无法读取")
    if not any(obj.get("aivision_role") == "part" for obj in scene.objects if obj.type == "MESH"):
        errors.append("尚未标注任何部件，请先点击 Add selected as part")
    if not any(obj.get("aivision_role") == "joint" for obj in scene.objects):
        errors.append("尚未标注任何关节，请先添加 joint")
    return errors


def export_annotation(output_path: str) -> Path:
    path = Path(bpy.path.abspath(output_path)).resolve()
    if path.suffix.lower() != ".json":
        path = path.with_suffix(".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_annotation(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
