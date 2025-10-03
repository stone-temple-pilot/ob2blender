import os


bl_info = {
    "name":         "ob2blender",
    "author":       "stone-temple-pilot",
    "blender": (4, 5, 2),
    "version": (1, 0, 0),
    "location":     "File > Import-Export",
    "description":  "Import and Export Runescape 3D model format (.ob2)",
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

class ExportOB2(Operator, ExportHelper):
    bl_idname = "export.model"
    bl_label = "Export Model"

    filename_ext = ".ob2"
    filter_glob = StringProperty( default="*.ob2", options={"HIDDEN"})
    
    def execute( self, context ):
        import ob2blender.export_model
        directory = os.path.dirname(self.filepath)
        self.directory = directory
        self.export_as_one = True
        return ob2blender.export_model.export_to_ob2(self.directory, False)
# ################################################################
# Common
# ################################################################
def menu_func_import( self, context ):
    self.layout.operator(ImportOB2.bl_idname, text="Runescape Model (.ob2)")

def menu_func_export( self, context ):
    self.layout.operator(ExportOB2.bl_idname, text="Runescape Model (.ob2)")

# Register classes
classes = (
    ImportOB2,
    ExportOB2,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":

    register()
