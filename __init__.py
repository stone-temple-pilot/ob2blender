import os


bl_info = {
    "name":         "ob2blender",
    "author":       "Tamatea, stone-temple-pilot",
    "blender": (3, 4, 1),
    "version": (1, 0, 0),
    "location":     "File > Import-Export",
    "description":  "Import Runescape Lost City data format (.ob2)",
    "category":     "Import-Export",
}

import bpy
from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator


# ################################################################
# Import Model
# ################################################################

class ImportOB2(Operator, ImportHelper):
    bl_idname = "import.model"
    bl_label = "Import Model"

    filename_ext = ".ob2"
    filter_glob = StringProperty( default="*.ob2", options={"HIDDEN"})
    
    def execute( self, context ):
        import ob2blender.import_model
        return ob2blender.import_model.load(self)


# ################################################################
# Common
# ################################################################
def menu_func_import( self, context ):
    self.layout.operator(ImportOB2.bl_idname, text="Runescape Model (.ob2)")


# Register classes
classes = (
    ImportOB2,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()