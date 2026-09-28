import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty, StringProperty


class AIVISION_PG_scene(bpy.types.PropertyGroup):
    annotation_confidence: FloatProperty(name="Annotation confidence", default=0.5, min=0.0, max=1.0)
    joint_axis: EnumProperty(
        name="Joint axis",
        items=[("X", "X", "Rotation axis X"), ("Y", "Y", "Rotation axis Y"), ("Z", "Z", "Rotation axis Z")],
        default="Y",
    )
    joint_type: StringProperty(name="Joint type", default="hinge_candidate")
    notes: StringProperty(name="Notes", default="")


classes = (AIVISION_PG_scene,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.aivision = PointerProperty(type=AIVISION_PG_scene)
    bpy.types.Scene.aivision_object_type = StringProperty(name="Object type", default="unknown")
    bpy.types.Scene.aivision_annotator = StringProperty(name="Annotator", default="")
    bpy.types.Scene.aivision_created_at = StringProperty(name="Created at", default="")
    bpy.types.Scene.aivision_model_source = StringProperty(
        name="Source model",
        subtype="FILE_PATH",
        default="",
    )
    bpy.types.Scene.aivision_output_path = StringProperty(
        name="Output JSON",
        subtype="FILE_PATH",
        default="//annotations/annotation.json",
    )
    bpy.types.Scene.aivision_object_confidence = FloatProperty(
        name="Object confidence", default=0.5, min=0.0, max=1.0
    )


def unregister():
    for name in (
        "aivision_object_type",
        "aivision_annotator",
        "aivision_created_at",
        "aivision_model_source",
        "aivision_output_path",
        "aivision_object_confidence",
        "aivision",
    ):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
