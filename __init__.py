import os
import bpy
import bmesh
import colorsys
from bpy.props import *


bl_info = {
    "name":         "ob2blender",
    "author":       "stone-temple-pilot",
    "blender": (4, 5, 2),
    "version": (1, 0, 0),
    "location":     "File > Import-Export",
    "description":  "Import and Export Runescape 3D model format (.ob2)",
    "category":     "Import-Export",
}

from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator

# ################################################################
# Import / Export Model
# ################################################################

class ImportOB2(Operator, ImportHelper):
    bl_idname = "import.model"
    bl_label = "Import Model"
    bl_description = "Import a Runescape .ob2 model file"

    filename_ext = ".ob2"
    filter_glob = StringProperty( default="*.ob2", options={"HIDDEN"})
    
    def execute( self, context ):
        import ob2blender.import_model
        return ob2blender.import_model.load(self)

class ExportOB2(Operator, ExportHelper):
    bl_idname = "export.model"
    bl_label = "Export Model"
    bl_description = "Export selected objects individually as objectname.ob2"

    filename_ext = ".ob2"
    filter_glob = StringProperty( default="*.ob2", options={"HIDDEN"})
    
    def execute( self, context ):
        import ob2blender.export_model
        directory = os.path.dirname(self.filepath)
        self.directory = directory
        self.export_as_one = True
        ob2blender.export_model.export_to_ob2(self.directory, False)
        return {'FINISHED'}
# ################################################################
# Common
# ################################################################
def menu_func_import( self, context ):
    self.layout.operator(ImportOB2.bl_idname, text="Runescape Model (.ob2)")

def menu_func_export( self, context ):
    self.layout.operator(ExportOB2.bl_idname, text="Runescape Model (.ob2)")


## Timer-based attribute picker - polls selection while any picker is enabled ##
_picker_timer_running = False

def _picker_timer():
    """Timer callback that reads selection attributes while pickers are active."""
    global _picker_timer_running
    scene = bpy.context.scene
    
    # Check if any picker is still enabled
    if not (
        getattr(scene, "ob2_vskin_pick", False)
        or getattr(scene, "ob2_tskin_pick", False)
        or getattr(scene, "ob2_pri_pick", False)
        or getattr(scene, "ob2_alpha_pick", False)
    ):
        _picker_timer_running = False
        return None  # Stop timer
    
    _read_active_attributes()
    return 0.1  # Continue polling every 100ms

def _start_picker_timer():
    """Start the picker timer if not already running."""
    global _picker_timer_running
    if not _picker_timer_running:
        _picker_timer_running = True
        bpy.app.timers.register(_picker_timer, first_interval=0.0)

def _read_active_attributes():
    """Read attributes from active vertex/face and update scene labels."""
    scene = bpy.context.scene
    obj = bpy.context.active_object

    if not obj or obj.type != 'MESH' or bpy.context.mode != 'EDIT_MESH':
        return

    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    # Check selection mode: (vert, edge, face)
    select_mode = bpy.context.tool_settings.mesh_select_mode
    vert_mode = select_mode[0]
    face_mode = select_mode[2]

    # Get bmesh attribute layers
    vskin_layer = bm.verts.layers.int.get("VSKIN")
    tskin_layer = bm.faces.layers.int.get("TSKIN")
    pri_layer = bm.faces.layers.int.get("PRI")
    alpha_layer = bm.faces.layers.int.get("ALPHA")

    # Find active vertex
    v_elem = None
    if vert_mode and (getattr(scene, "ob2_vskin_pick", False)):
        if bm.select_history:
            for e in reversed(bm.select_history):
                if isinstance(e, bmesh.types.BMVert):
                    v_elem = e
                    break
        if v_elem is None:
            for vert in bm.verts:
                if vert.select:
                    v_elem = vert
                    break
        
        if v_elem is not None:
            scene.ob2_vskin_label = 0 if not vskin_layer else v_elem[vskin_layer]
            # 0 (Default) if no vskin attribute, otherwise assign vskin of active vertex.

    # Find active face
    f_elem = None
    if face_mode and (getattr(scene, "ob2_tskin_pick", False)
        or getattr(scene, "ob2_pri_pick", False) or getattr(scene, "ob2_alpha_pick", False)):
        #enable face picking if any face picker is on (3 of them).
        if bm.select_history:
            for e in reversed(bm.select_history):
                if isinstance(e, bmesh.types.BMFace):
                    f_elem = e
                break
        if f_elem is None:
            for face in bm.faces:
                if face.select:
                    f_elem = face
                    break   

    # Update face attrs from face
    if f_elem is not None:
        if getattr(scene, "ob2_tskin_pick", False):
            scene.ob2_tskin_label = 0 if not tskin_layer else f_elem[tskin_layer]
        if getattr(scene, "ob2_pri_pick", False):
            scene.ob2_pri_label = 0 if not pri_layer else f_elem[pri_layer]
        if getattr(scene, "ob2_alpha_pick", False):
            scene.ob2_alpha_label = 0 if not alpha_layer else f_elem[alpha_layer]
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

## toolbar specific to OB2 operations laid out here ##
class OB2_OT_main_panel(bpy.types.Panel):
    bl_label = "RuneScape .ob2"
    bl_idname = "OB2_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OB2"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Import / Export")
        col.operator("import.model", text="Import .ob2")
        col.operator("export.model", text="Export Individual .ob2")
        

        # col.operator("ob2.ensure_vskin", text="Add VSKIN")
        # col.operator("ob2.ensure_tskin", text="Add TSKIN")
        # col.operator("ob2.ensure_pri", text="Add PRI")
        # col.operator("ob2.ensure_alpha", text="Add ALPHA")

        scene = context.scene

        # Vertex foldout header
        col.separator()
        row = col.row(align=True)
        row.prop(
            scene,
            "ob2_vskin_foldout",
            icon='TRIA_DOWN' if scene.ob2_vskin_foldout else 'TRIA_RIGHT',
            emboss=False,
            text="Vertex Label",
        )

        if scene.ob2_vskin_foldout:
            row = col.row(align=True)
            row.prop(scene, "ob2_vskin_label", text="VSKIN")
            row.prop(scene, "ob2_vskin_pick", text="", icon='EYEDROPPER')
            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Select Only")
            op.type = "VSKIN"
            op.add = False
            op.deselect = False

            op = row.operator("ob2.select_labeled", text="Select More")
            op.type = "VSKIN"
            op.add = True
            op.deselect = False

            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Deselect")
            op.type = "VSKIN"
            op.add = True
            op.deselect = True

            op = row.operator("ob2.apply_label", text="Apply Label")
            op.type = "VSKIN"


        # Face foldout header
        col.separator()
        row = col.row(align=True)
        row.prop(
            scene,
            "ob2_tskin_foldout",
            icon='TRIA_DOWN' if scene.ob2_tskin_foldout else 'TRIA_RIGHT',
            emboss=False,
            text="Face Label",
        )

        
        if scene.ob2_tskin_foldout:
            row = col.row(align=True)
            row.prop(scene, "ob2_tskin_label", text="TSKIN")
            row.prop(scene, "ob2_tskin_pick", text="", icon='EYEDROPPER')
            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Select Only")
            op.type = "TSKIN"
            op.add = False
            op.deselect = False

            op = row.operator("ob2.select_labeled", text="Select More")
            op.type = "TSKIN"
            op.add = True
            op.deselect = False

            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Deselect")
            op.type = "TSKIN"
            op.add = True
            op.deselect = True

            op = row.operator("ob2.apply_label", text="Apply Label")
            op.type = "TSKIN"
        
        col.separator()
        row = col.row(align=True)
        row.prop(
            scene,
            "ob2_pri_foldout",
            icon='TRIA_DOWN' if scene.ob2_pri_foldout else 'TRIA_RIGHT',
            emboss=False,
            text="Priority Label",
        )

        if scene.ob2_pri_foldout:
            row = col.row(align=True)
            row.prop(scene, "ob2_pri_label", text="PRI")
            row.prop(scene, "ob2_pri_pick", text="", icon='EYEDROPPER')
            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Select Only")
            op.type = "PRI"
            op.add = False
            op.deselect = False

            op = row.operator("ob2.select_labeled", text="Select More")
            op.type = "PRI"
            op.add = True
            op.deselect = False

            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Deselect")
            op.type = "PRI"
            op.add = True
            op.deselect = True

            op = row.operator("ob2.apply_label", text="Apply Label")
            op.type = "PRI"
        
        col.separator()
        row = col.row(align=True)
        row.prop(
            scene,
            "ob2_alpha_foldout",
            icon='TRIA_DOWN' if scene.ob2_alpha_foldout else 'TRIA_RIGHT',
            emboss=False,
            text="Alpha Label",
        )
        if scene.ob2_alpha_foldout:
            row = col.row(align=True)
            row.prop(scene, "ob2_alpha_label", text="ALPHA")
            row.prop(scene, "ob2_alpha_pick", text="", icon='EYEDROPPER')
            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Select Only")
            op.type = "ALPHA"
            op.add = False
            op.deselect = False

            op = row.operator("ob2.select_labeled", text="Select More")
            op.type = "ALPHA"
            op.add = True
            op.deselect = False

            row = col.row(align=True)

            op = row.operator("ob2.select_labeled", text="Deselect")
            op.type = "ALPHA"
            op.add = True
            op.deselect = True

            op = row.operator("ob2.apply_label", text="Apply Label")
            op.type = "ALPHA"

        # Color conversion foldout
        col.separator()
        row = col.row(align=True)
        row.prop(
            scene,
            "ob2_color_foldout",
            icon='TRIA_DOWN' if scene.ob2_color_foldout else 'TRIA_RIGHT',
            emboss=False,
            text="Color Picker",
        )

        if scene.ob2_color_foldout:
            row = col.row(align=True)
            row.prop(scene, "ob2_color_value", text="Value")
            col.separator()
            row = col.row(align=True)
            row.operator("ob2.create_color_material", text="RGB15 to New").mode = "RGB15"
            row.operator("ob2.create_color_material", text="HSL16 to New").mode = "HSL16"
            col.separator()
            row = col.row(align=True)
            row.operator("ob2.convert_color_value", text="RGB15→HSL16").mode = "RGB15_TO_HSL16"
            row.operator("ob2.convert_color_value", text="HSL16→RGB15").mode = "HSL16_TO_RGB15"
            col.separator()
            row = col.row(align=True)
            row.operator("ob2.get_material_color", text="Mat to RGB15").mode = "RGB15"
            row.operator("ob2.get_material_color", text="Mat to HSL16").mode = "HSL16"

class OB2_OT_create_color_material(Operator):
    bl_idname = "ob2.create_color_material"
    bl_label = "Create Color Material"
    bl_description = "Create a material from a color value"

    mode: StringProperty(
        name="Mode",
        description="Conversion mode: RGB15 or HSL16",
        default="RGB15",
    ) # type: ignore

    def execute(self, context):
        value = context.scene.ob2_color_value

        if self.mode == "RGB15":
            if value > 32767:
                self.report({'ERROR'}, f"RGB15 value {value} exceeds maximum (32767)")
                return {'CANCELLED'}
            # RGB15: 5 bits R (10-14), 5 bits G (5-9), 5 bits B (0-4)
            r = ((value >> 10) & 0x1F) / 31.0
            g = ((value >> 5) & 0x1F) / 31.0
            b = (value & 0x1F) / 31.0
            mat_name = f"RGB15_{value}"
        else:  # HSL16
            # HSL16: 6 bits H (10-15), 3 bits S (7-9), 7 bits L (0-6)
            h = ((value >> 10) & 0x3F) / 63.0
            s = ((value >> 7) & 0x07) / 7.0
            l = (value & 0x7F) / 127.0
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            mat_name = f"HSL16_{value}"

        # Create or get material
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
        mat.diffuse_color = (r, g, b, 1.0)

        # Assign to active object if it's a mesh
        obj = context.active_object
        if obj and obj.type == 'MESH':
            if mat.name not in obj.data.materials:
                obj.data.materials.append(mat)
            self.report({'INFO'}, f"Created material '{mat_name}' and added to {obj.name}")
        else:
            self.report({'INFO'}, f"Created material '{mat_name}'")

        return {'FINISHED'}

class OB2_OT_convert_color_value(Operator):
    bl_idname = "ob2.convert_color_value"
    bl_label = "Convert Color Value"
    bl_description = "Convert color value between RGB15 and HSL16 formats"

    mode: StringProperty(
        name="Mode",
        description="Conversion direction",
        default="RGB15_TO_HSL16",
    ) # type: ignore

    def execute(self, context):
        value = context.scene.ob2_color_value

        if self.mode == "RGB15_TO_HSL16":
            if value > 32767:
                self.report({'ERROR'}, f"RGB15 value {value} exceeds maximum (32767)")
                return {'CANCELLED'}
            # Decode RGB15 to RGB
            r = ((value >> 10) & 0x1F) / 31.0
            g = ((value >> 5) & 0x1F) / 31.0
            b = (value & 0x1F) / 31.0
            # Convert RGB to HLS
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            # Encode as HSL16
            new_value = ((round(h * 63.0) & 0x3F) << 10) | ((round(s * 7.0) & 0x07) << 7) | (round(l * 127.0) & 0x7F)
            context.scene.ob2_color_value = new_value
            self.report({'INFO'}, f"Converted RGB15 {value} → HSL16 {new_value}")
        else:  # HSL16_TO_RGB15
            # Decode HSL16 to RGB
            h = ((value >> 10) & 0x3F) / 63.0
            s = ((value >> 7) & 0x07) / 7.0
            l = (value & 0x7F) / 127.0
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            # Encode as RGB15
            new_value = ((round(r * 31.0) & 0x1F) << 10) | ((round(g * 31.0) & 0x1F) << 5) | (round(b * 31.0) & 0x1F)
            context.scene.ob2_color_value = new_value
            self.report({'INFO'}, f"Converted HSL16 {value} → RGB15 {new_value}")

        return {'FINISHED'}

class OB2_OT_get_material_color(Operator):
    bl_idname = "ob2.get_material_color"
    bl_label = "Get Material Color"
    bl_description = "Get the active material's diffuse color and convert to RGB15 or HSL16"

    mode: StringProperty(
        name="Mode",
        description="Output format: RGB15 or HSL16",
        default="RGB15",
    ) # type: ignore

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object")
            return {'CANCELLED'}

        if not obj.active_material:
            self.report({'ERROR'}, "No active material on object")
            return {'CANCELLED'}

        mat = obj.active_material
        r, g, b = mat.diffuse_color[:3]  # Ignore alpha

        if self.mode == "RGB15":
            # Encode as RGB15: 5 bits each for R, G, B
            value = ((round(r * 31.0) & 0x1F) << 10) | ((round(g * 31.0) & 0x1F) << 5) | (round(b * 31.0) & 0x1F)
            context.scene.ob2_color_value = value
            self.report({'INFO'}, f"Material '{mat.name}' to RGB15: {value}")
        else:  # HSL16
            # Convert RGB to HLS, then encode as HSL16
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            value = ((round(h * 63.0) & 0x3F) << 10) | ((round(s * 7.0) & 0x07) << 7) | (round(l * 127.0) & 0x7F)
            context.scene.ob2_color_value = value
            self.report({'INFO'}, f"Material '{mat.name}' to HSL16: {value}")

        return {'FINISHED'}

class OB2_OT_select_labeled(Operator):
    bl_idname = "ob2.select_labeled"
    bl_label = "Select Labeled"
    bl_description = "Select items whose label matches the given label"

    # If True: add to selection. If False: replace selection (only).
    add: BoolProperty(
        name="Add",
        description="Add to existing selection instead of replacing it",
        default=False,
    ) # type: ignore

    deselect: BoolProperty(
        name="Deselect",
        description="Deselect items whose label matches the given label",
        default=False,
    ) # type: ignore

    type: StringProperty(
        name="Attribute Type",
        description="The attribute to select by",
        default="VSKIN",
    ) # type: ignore

    def execute(self, context):
        if self.type == "VSKIN":
            target = context.scene.ob2_vskin_label
        elif self.type == "TSKIN":
            target = context.scene.ob2_tskin_label
        elif self.type == "PRI":
            target = context.scene.ob2_pri_label
        elif self.type == "ALPHA":
            target = context.scene.ob2_alpha_label
        else:
            self.report({'ERROR'}, f"Unknown attribute type: {self.type}")
            return {'CANCELLED'}
        start_mode = context.mode

        # Which objects to affect?
        objs = []
        if start_mode == 'EDIT_MESH':
            # All meshes currently in edit mode (multi-object edit supported)
            objs = [o for o in getattr(context, "objects_in_mode", []) if o.type == 'MESH']
        else:
            # From object mode: use selected meshes, or fallback to active mesh
            if context.selected_objects:
                objs = [o for o in context.selected_objects if o.type == 'MESH']
            elif context.active_object and context.active_object.type == 'MESH':
                objs = [context.active_object]

        if not objs:
            self.report({'ERROR'}, "No mesh object(s) to operate on")
            return {'CANCELLED'}

        # Go to object mode to edit vertex/face selection flags
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        try:
            if self.type == "VSKIN":
                # Vertex-based selection
                context.tool_settings.mesh_select_mode = (True, False, False)
            else:
                # Face-based selection (TSKIN, PRI, ALPHA, etc.)
                context.tool_settings.mesh_select_mode = (False, False, True)
        except AttributeError:
            pass

        has_attr = False

        for obj in objs:
            mesh = obj.data
            attr = mesh.attributes.get(self.type)
            #print(f"Checking object '{obj.name}' for attribute '{self.type}': {'Found' if attr else 'Not Found'}")
            if not attr or attr.domain not in {'POINT', 'FACE'}:
                continue

            has_attr = True

            # Clear everything in "Select Only" mode
            if not self.add:
                for v in mesh.vertices:
                    v.select = False
                for e in mesh.edges:
                    e.select = False
                for p in mesh.polygons:
                    p.select = False

            data = attr.data
            
            
            if self.type == "VSKIN":
                deselect_list = [] #gotta do something different for vertices - force unselect faces and edges as well.
                for i, v in enumerate(mesh.vertices):
                    if data[i].value != target:
                        continue

                    if not self.deselect:
                        v.select = True
                    else:
                        deselect_list.append(i)
                if self.deselect and deselect_list:
                    deselect_set = set(deselect_list)
                    for i in deselect_set:
                        mesh.vertices[i].select = False
                    for e in mesh.edges:
                        if any(vidx in deselect_set for vidx in e.vertices):
                            e.select = False
                    for p in mesh.polygons:
                        if any(vidx in deselect_set for vidx in p.vertices):
                            p.select = False    
                        
            else: # because everything else is a face attribute.
                for i, p in enumerate(mesh.polygons):
                    if data[i].value != target:
                        continue

                    if not self.deselect:
                        p.select = True
                    else:
                        p.select = False
                        for vidx in p.vertices:
                                mesh.vertices[vidx].select = False
                        for edgx in p.edge_keys:
                            edge = mesh.edge_keys.index(edgx)
                            mesh.edges[edge].select = False

            # Ensure these objects stay selected for edit mode
            obj.select_set(True)

        if not has_attr:
            self.report({'ERROR'}, f"No {self.type} attribute found on selected mesh(es).")
            return {'CANCELLED'}

        # Return to edit mode (or stay in edit mode) as requested
        if start_mode in {'EDIT_MESH', 'OBJECT'}:
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.ed.undo_push(message=f"Select {self.type}={target}")
        return {'FINISHED'}

class OB2_OT_apply_label(Operator):
    bl_idname = "ob2.apply_label"
    bl_label = "Apply Label"
    bl_description = "Apply label to selected geometry"

    type: StringProperty(
        name="Attribute Type",
        description="The attribute to apply",
        default="VSKIN",
    ) # type: ignore

    def execute(self, context):
        if self.type == "VSKIN":
            target = context.scene.ob2_vskin_label
        elif self.type == "TSKIN":
            target = context.scene.ob2_tskin_label
        elif self.type == "PRI":
            target = context.scene.ob2_pri_label
        elif self.type == "ALPHA":
            target = context.scene.ob2_alpha_label
        else:
            self.report({'ERROR'}, f"Unknown attribute type: {self.type}")
            return {'CANCELLED'}
    
        # Which objects to affect?
        objs = []
        start_mode = context.mode
        if start_mode == 'EDIT_MESH':
            objs = [o for o in getattr(context, "objects_in_mode", []) if o.type == 'MESH']
        else:
            if context.selected_objects:
                objs = [o for o in context.selected_objects if o.type == 'MESH']
            elif context.active_object and context.active_object.type == 'MESH':
                objs = [context.active_object]

        if not objs:
            self.report({'ERROR'}, "No mesh object(s) to operate on")
            return {'CANCELLED'}

        # Go to edit mode
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        try:
            if self.type == "VSKIN":
                context.tool_settings.mesh_select_mode = (True, False, False)
            else:
                context.tool_settings.mesh_select_mode = (False, False, True)
        except AttributeError:
            pass

        # Apply the attribute value to selected geometry using bmesh
        for obj in objs:
            mesh = obj.data
            bm = bmesh.from_edit_mesh(mesh)
            
            layer = None
            if self.type == "VSKIN":
                layer = bm.verts.layers.int.get(self.type)
                if not layer:
                    self.report({'ERROR'}, f"No {self.type} attribute found on mesh '{obj.name}'.")
                    continue
                for vert in bm.verts:
                    if vert.select:
                        vert[layer] = target
            else:
                layer = bm.faces.layers.int.get(self.type)
                if not layer:
                    self.report({'ERROR'}, f"No {self.type} attribute found on mesh '{obj.name}'.")
                    continue
                for face in bm.faces:
                    if face.select:
                        face[layer] = target
            
            bmesh.update_edit_mesh(mesh)
        
        bpy.ops.ed.undo_push(message=f"Apply {self.type}={target}")
        return {'FINISHED'}


# Register classes
classes = (
    ImportOB2,
    ExportOB2,
    OB2_OT_main_panel,
    OB2_OT_select_labeled,
    OB2_OT_apply_label,
    OB2_OT_create_color_material,
    OB2_OT_convert_color_value,
    OB2_OT_get_material_color,
)

# Update callbacks start the picker timer when any picker is enabled
def _update_timer_pick(self, context):
    if (context.scene.ob2_vskin_pick,
        context.scene.ob2_tskin_pick,
        context.scene.ob2_pri_pick,
        context.scene.ob2_alpha_pick):
        _start_picker_timer()

def _update_ob2_vskin_foldout(self, context):
    # Turn off VSKIN picker when foldout is collapsed.
    if not context.scene.ob2_vskin_foldout:
        context.scene.ob2_vskin_pick = False
    # Turn back on when expanded.
    else:
        context.scene.ob2_vskin_pick = True

def _update_ob2_tskin_foldout(self, context):
    # Turn off TSKIN pickers when foldout is collapsed.
    if not context.scene.ob2_tskin_foldout:
        context.scene.ob2_tskin_pick = False
    # Turn back on when expanded.
    else:
        context.scene.ob2_tskin_pick = True

def _update_ob2_pri_foldout(self, context):
    # Turn off PRI pickers when foldout is collapsed.
    if not context.scene.ob2_pri_foldout:
        context.scene.ob2_pri_pick = False
    # Turn back on when expanded.
    else:
        context.scene.ob2_pri_pick = True

def _update_ob2_alpha_foldout(self, context):
    # Turn off ALPHA pickers when foldout is collapsed.
    if not context.scene.ob2_alpha_foldout:
        context.scene.ob2_alpha_pick = False
    # Turn back on when expanded.
    else:
        context.scene.ob2_alpha_pick = True

def register():

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.types.Scene.ob2_vskin_label = IntProperty(
        name="VSKIN",
        description="VSKIN label to select",
        default=0,
        soft_min=0,
        soft_max=255,
    )

    bpy.types.Scene.ob2_tskin_label = IntProperty(
        name="TSKIN",
        description="TSKIN label to select",
        default=0,
        soft_min=0,
        soft_max=255,
    )

    bpy.types.Scene.ob2_pri_label = IntProperty(
        name="PRI",
        description="PRI label to select",
        default=0,
        soft_min=0,
        soft_max=255,
    )

    bpy.types.Scene.ob2_alpha_label = IntProperty(
        name="ALPHA",
        description="ALPHA label to select",
        default=0,
        soft_min=0,
        soft_max=255,
    )

    bpy.types.Scene.ob2_vskin_pick = BoolProperty(
        name="VSKIN Picker",
        description="Click a vertex to set VSKIN label",
        default=False,
        update=_update_timer_pick
    )

    bpy.types.Scene.ob2_tskin_pick = BoolProperty(
        name="TSKIN Picker",
        description="Click a face to set TSKIN label",
        default=False,
        update=_update_timer_pick
    )

    bpy.types.Scene.ob2_pri_pick = BoolProperty(
        name="PRI Picker",
        description="Click a face to set PRI label",
        default=False,
        update=_update_timer_pick
    )

    bpy.types.Scene.ob2_alpha_pick = BoolProperty(
        name="ALPHA Picker",
        description="Click a face to set ALPHA label",
        default=False,
        update=_update_timer_pick
    )

    bpy.types.Scene.ob2_vskin_foldout = BoolProperty(
        name="VSKIN Foldout",
        default=False,
        update=_update_ob2_vskin_foldout
    )

    bpy.types.Scene.ob2_tskin_foldout = BoolProperty(
        name="TSKIN Foldout",
        default=False,
        update=_update_ob2_tskin_foldout
    )

    bpy.types.Scene.ob2_pri_foldout = BoolProperty(
        name="PRI Foldout",
        default=False,
        update=_update_ob2_pri_foldout
    )

    bpy.types.Scene.ob2_alpha_foldout = BoolProperty(
        name="ALPHA Foldout",
        default=False,
        update=_update_ob2_alpha_foldout
    )

    bpy.types.Scene.ob2_color_foldout = BoolProperty(
        name="Color Foldout",
        default=False
    )

    bpy.types.Scene.ob2_color_value = IntProperty(
        name="Color Value",
        description="Color value to convert (0-65535)",
        default=0,
        min=0,
        max=65535,
    )


def unregister():
    del bpy.types.Scene.ob2_color_foldout
    del bpy.types.Scene.ob2_color_value

    del bpy.types.Scene.ob2_vskin_foldout
    del bpy.types.Scene.ob2_tskin_foldout
    del bpy.types.Scene.ob2_pri_foldout
    del bpy.types.Scene.ob2_alpha_foldout

    del bpy.types.Scene.ob2_vskin_pick
    del bpy.types.Scene.ob2_tskin_pick
    del bpy.types.Scene.ob2_pri_pick
    del bpy.types.Scene.ob2_alpha_pick

    del bpy.types.Scene.ob2_vskin_label
    del bpy.types.Scene.ob2_tskin_label
    del bpy.types.Scene.ob2_pri_label
    del bpy.types.Scene.ob2_alpha_label

    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()