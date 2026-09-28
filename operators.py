import bpy
from mathutils import Vector

from .annotation_data import default_output_path, export_annotation, utc_now, validate_annotation


def selected_meshes():
    return [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]


class AIVISION_OT_mark_part(bpy.types.Operator):
    bl_idname = "aivision.mark_part"
    bl_label = "Add selected as part"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        objects = selected_meshes()
        if not objects:
            self.report({"WARNING"}, "Select one or more mesh objects first")
            return {"CANCELLED"}
        for obj in objects:
            obj["aivision_role"] = "part"
            obj["aivision_part_label"] = obj.name
            obj["aivision_confidence"] = context.scene.aivision.annotation_confidence
        self.report({"INFO"}, f"Marked {len(objects)} part(s)")
        return {"FINISHED"}


class AIVISION_OT_mark_joint(bpy.types.Operator):
    bl_idname = "aivision.mark_joint"
    bl_label = "Add joint at 3D cursor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        for existing in scene.objects:
            if existing.get("aivision_role") == "joint":
                if (existing.location - scene.cursor.location).length < 0.0001:
                    self.report({"WARNING"}, f"A joint already exists at {existing.name}")
                    return {"CANCELLED"}
        joint_count = len([obj for obj in scene.objects if obj.get("aivision_role") == "joint"])
        joint = bpy.data.objects.new(f"joint_{joint_count + 1:02d}", None)
        joint.empty_display_type = "ARROWS"
        joint.empty_display_size = 3.0
        joint.location = scene.cursor.location.copy()
        joint["aivision_role"] = "joint"
        joint["aivision_joint_type"] = scene.aivision.joint_type
        joint["aivision_confidence"] = scene.aivision.annotation_confidence
        joint["aivision_notes"] = scene.aivision.notes
        joint["aivision_connected_parts"] = [obj.name for obj in selected_meshes()]
        axis = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}[scene.aivision.joint_axis]
        joint["aivision_axis"] = list(axis)
        scene.collection.objects.link(joint)
        scene.aivision_created_at = utc_now()
        self.report({"INFO"}, f"Added {joint.name} at the 3D cursor")
        return {"FINISHED"}


class AIVISION_OT_remove_last_joint(bpy.types.Operator):
    bl_idname = "aivision.remove_last_joint"
    bl_label = "Remove last joint"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        joints = [obj for obj in context.scene.objects if obj.get("aivision_role") == "joint"]
        if not joints:
            self.report({"INFO"}, "No joint annotations")
            return {"CANCELLED"}
        joint = sorted(joints, key=lambda obj: obj.name)[-1]
        bpy.data.objects.remove(joint, do_unlink=True)
        self.report({"INFO"}, f"Removed {joint.name}")
        return {"FINISHED"}


class AIVISION_OT_export(bpy.types.Operator):
    bl_idname = "aivision.export_json"
    bl_label = "Save annotation JSON"

    def execute(self, context):
        errors = validate_annotation()
        if errors:
            self.report({"ERROR"}, "；".join(errors[:2]))
            return {"CANCELLED"}
        try:
            output_path = default_output_path()
            context.scene.aivision_output_path = output_path
            path = export_annotation(output_path)
        except (OSError, ValueError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Saved annotation: {path}")
        return {"FINISHED"}


class AIVISION_OT_clear_marks(bpy.types.Operator):
    bl_idname = "aivision.clear_marks"
    bl_label = "Clear annotation marks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in list(context.scene.objects):
            if obj.get("aivision_role") == "joint":
                bpy.data.objects.remove(obj, do_unlink=True)
            elif obj.type == "MESH":
                for key in ("aivision_role", "aivision_part_label", "aivision_confidence"):
                    obj.pop(key, None)
        self.report({"INFO"}, "Cleared annotation marks")
        return {"FINISHED"}


classes = (
    AIVISION_OT_mark_part,
    AIVISION_OT_mark_joint,
    AIVISION_OT_remove_last_joint,
    AIVISION_OT_export,
    AIVISION_OT_clear_marks,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
