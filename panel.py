import bpy


def marked_parts(context):
    return [obj for obj in context.scene.objects if obj.type == "MESH" and obj.get("aivision_role") == "part"]


def marked_joints(context):
    return [obj for obj in context.scene.objects if obj.get("aivision_role") == "joint"]


class AIVISION_PT_panel(bpy.types.Panel):
    bl_label = "AI Vision Annotation v0.3.0"
    bl_idname = "AIVISION_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AI Vision"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.aivision

        box = layout.box()
        box.label(text="Project")
        box.prop(scene, "aivision_object_type")
        box.prop(scene, "aivision_annotator")
        box.prop(scene, "aivision_object_confidence")
        box.prop(scene, "aivision_model_source")
        box.prop(scene, "aivision_output_path")

        box = layout.box()
        box.label(text="Part")
        box.prop(settings, "annotation_confidence")
        box.operator("aivision.mark_part", icon="MESH_CUBE")
        box.label(text="Select mesh object(s), then click above")
        parts = marked_parts(context)
        box.label(text=f"Marked parts: {len(parts)}")
        for obj in parts:
            confidence = float(obj.get("aivision_confidence", 0.5))
            box.label(text=f"{obj.name}  confidence={confidence:.2f}", icon="CHECKMARK")

        box = layout.box()
        box.label(text="Joint")
        box.prop(settings, "joint_type")
        box.prop(settings, "joint_axis")
        box.prop(settings, "annotation_confidence")
        box.prop(settings, "notes")
        box.operator("aivision.mark_joint", icon="EMPTY_ARROWS")
        box.label(text="Place 3D Cursor first")
        joints = marked_joints(context)
        box.label(text=f"Marked joints: {len(joints)}")
        for obj in joints:
            confidence = float(obj.get("aivision_confidence", 0.5))
            position = tuple(round(value, 2) for value in obj.location)
            box.label(text=f"{obj.name}  {position}  c={confidence:.2f}", icon="EMPTY_ARROWS")
        box.operator("aivision.remove_last_joint", icon="X")

        layout.separator()
        layout.operator("aivision.export_json", icon="FILE_TICK")
        layout.operator("aivision.clear_marks", icon="TRASH")


def register():
    bpy.utils.register_class(AIVISION_PT_panel)


def unregister():
    bpy.utils.unregister_class(AIVISION_PT_panel)
