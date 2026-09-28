"""AI Vision Annotation helper for Blender 4.x/5.x."""

bl_info = {
    "name": "AI Vision Annotation Helper",
    "author": "4D Printing AI Vision Team",
    "version": (0, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > AI Vision",
    "description": "Record part and joint annotations as versioned JSON.",
    "category": "3D View",
}

import bpy

from . import annotation_data, operators, panel, properties


def register():
    properties.register()
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
