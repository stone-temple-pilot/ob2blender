import os
import bpy
import colorsys
import numpy as np
from ob2blender.runescape_mesh import RunescapeMesh


def read_mesh(filepath):
    try:
        with open(filepath, "rb") as file:
            data = file.read()
        mesh = RunescapeMesh()
        mesh.decode(mesh, data)
        return mesh
    except IOError:
        print("Error: Failed to read file.")

#To do: actually import and use real materials rather than a UV map to a palette texture.
def apply_HSV_material(rs_mesh, blender_mesh):
    if rs_mesh.face_indices_a and rs_mesh.face_indices_b and rs_mesh.face_indices_c:
        mesh = blender_mesh
        mesh.materials.clear()
        hsl_bit_cache = []

        #first we're going to store all the bits of the color we need to make a material
        for face in range(rs_mesh.face_count):
            face_color = rs_mesh.face_colors[face]
            #print("Checking face number: ", face, "with face color: ", face_color)
            if face_color not in hsl_bit_cache:
                hsl_bit_cache.append(face_color) #we can check from this
                #H has 6 bits, S has 3 bits, L has 7 bits
                H = (face_color >> 10) & 0x3F
                S = (face_color >> 7) & 0x07
                L = face_color & 0x7F
                r, g, b = colorsys.hsv_to_rgb(H / 63.0, S / 7.0, L / 127.0)
                rgba = tuple(round(n, 4) for n in (r,g,b,1.0))
                #nomen = 'mat' + str(hsl_bit_cache.index(face_color))
                nomen = 'H' + str(H) + '_S' + str(S) + '_L' + str(L)
                mat = bpy.data.materials.new(name=nomen)
                mat.diffuse_color = rgba #I need solid mode to enable backface culling, which is crucial for lowpoly models.
                mesh.materials.append(mat)
            mesh.polygons[face].material_index = hsl_bit_cache.index(face_color) #applies face color

    #     for face in range(rs_mesh.face_count):
    #         if rs_mesh.texture_ids is not None and rs_mesh.texture_ids[face] != -1:
    #             uv_coordinates = get_uv_from_pmn(rs_mesh, face)
    #             for uv_coord in zip(uv_coordinates[0], uv_coordinates[1]):
    #                 uv_data[i] = uv_coord
    #                 i += 1


def create_blender_mesh(rs_mesh, filepath):
    # Create a new mesh
    blender_mesh = bpy.data.meshes.new("Mesh")

    # since it's runescapes XYZ is different, and y axis inverted
    # vertices = [
    #     ((rs_mesh.vertices_x[i] * 0.0078125), rs_mesh.vertices_z[i] * 0.0078125, (-rs_mesh.vertices_y[i] * 0.0078125))
    vertices = [(rs_mesh.vertices_x[i], rs_mesh.vertices_z[i], -rs_mesh.vertices_y[i]) for i in range(rs_mesh.vertex_count)]
    #when I write the export script, this will need to be reversed.
    # Set faces
    faces = [(rs_mesh.face_indices_a[i], rs_mesh.face_indices_b[i], rs_mesh.face_indices_c[i]) for i in
             range(rs_mesh.face_count)]
    # Set the mesh data
    # validate/filter faces before passing to Blender
    valid_faces = validate_and_filter_faces(rs_mesh, vertices, faces)
    blender_mesh.from_pydata(vertices, [], valid_faces)
    blender_mesh.update()

    # Set the uv data for each face
    
    rs_mesh.create_groups()
    apply_HSV_material(rs_mesh, blender_mesh) #runescape colors are stored as HSL16 values
    #going to need commands to apply smoothshading/flatshading data.

    # Create a new object for the mesh
    # Shall be named the same as the imported file name.
    filename = os.path.splitext(os.path.basename(filepath))[0]
    obj = bpy.data.objects.new(filename, blender_mesh)

    vertex_group_labels = set(rs_mesh.vertex_labels)  # Get unique vertex labels

    for label in vertex_group_labels:
            vertex_group = obj.vertex_groups.new(name=f"{label}")
            vertex_indices = [i for i, value in enumerate(rs_mesh.vertex_labels) if value == label]
            weight = label / 100.0
            vertex_group.add(vertex_indices, weight, 'REPLACE')
            # Set the same weight for all vertices in the group
            for vertex_index in vertex_indices:
                vertex_group.add([vertex_index], weight, 'REPLACE')

    #look at face_draw_types for smooth/flat shading, texture or no texture.
    # Set smooth/flat shading for polygons
    use_draw_types = rs_mesh.face_draw_types if rs_mesh.face_draw_types else [0] * rs_mesh.face_count
    for i, poly in enumerate(blender_mesh.polygons):
        poly.use_smooth = (use_draw_types[i] != 1)

    # for face in range(rs_mesh.face_count): #assigns materials
    #     if rs_mesh.face_alphas is not None and len(rs_mesh.face_alphas) > 0 and rs_mesh.face_alphas[face] != 0:
    #         alpha = rs_mesh.face_alphas[face]
    #         mat = Materials.create_or_get_alpha_palette_material(obj, alpha)
    #         obj.data.polygons[face].material_index = obj.data.materials.find(mat.name)
    #     elif rs_mesh.texture_ids is not None and rs_mesh.texture_ids[face] != -1:
    #         texture_id = rs_mesh.texture_ids[face]
    #         mat = Materials.create_or_get_runescape_texture_material(obj, texture_id)
    #         obj.data.polygons[face].material_index = obj.data.materials.find(mat.name)
    #     else:
    #          obj.data.polygons[face].material_index = obj.data.materials.find("palette")

    # Link the object to the scene collection
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # Set the viewport shading mode to palette_material preview
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'
                    if not space.shading.show_backface_culling:
                        space.shading.show_backface_culling = True

    # Set the active object and select it
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(True)

    # If face priorities exist, create a custom integer attribute for them.
    #I don't believe the importer actually pulls priorities yet.
    # In newer versions of Blender, you can assign custom attributes to things like faces and vertices. You can take advantage of this to store the face priorities.
 
    if rs_mesh.face_priorities: #PRI; currently bugged with PRI: 10 showing up as nothing.
        PRI_values = np.zeros(rs_mesh.face_count, dtype=np.int8)
        for i in range(rs_mesh.face_count):
            PRI_values[i] = rs_mesh.face_priorities[i]
        PRI = blender_mesh.attributes.new(name='PRI', type='INT', domain='FACE')
        PRI.data.foreach_set("value", PRI_values)

    if rs_mesh.face_labels: #TSKIN, face labels
        TSKIN_values = np.zeros(rs_mesh.face_count, dtype=np.int8)
        for i in range(rs_mesh.face_count):
            TSKIN_values[i] = rs_mesh.face_labels[i]
        TSKIN = blender_mesh.attributes.new(name='TSKIN', type='INT', domain='FACE')
        TSKIN.data.foreach_set("value", TSKIN_values)

    if rs_mesh.face_alphas: #runescape doesn't do alpha by material, but by face.
        ALPHA = blender_mesh.attributes.new(name='ALPHA', type='INT', domain='FACE')
        ALPHA_values = np.zeros(rs_mesh.face_count, dtype=np.int8)
        for i in range(rs_mesh.face_count):
            ALPHA_values[i] = rs_mesh.face_alphas[i]
        ALPHA.data.foreach_set("value", ALPHA_values)

    return obj


# def create_skeletal_groups(obj, mesh):
#     for vertex_index in range(mesh.vertex_count):
#         bone_ids = mesh.skeletal_bones[vertex_index]
#         weights = mesh.skeletal_weights[vertex_index]

#         for i in range(len(bone_ids)):
#             bone_id = bone_ids[i]
#             weight = weights[i]
#             vertex_group_name = f"Bone_{bone_id}"
#             vertex_group = obj.vertex_groups.get(vertex_group_name)
#             if not vertex_group:
#                 vertex_group = obj.vertex_groups.new(name=vertex_group_name)
#             vertex_group.add([vertex_index], weight / 255, 'ADD')


# def get_hsl_from_coord(u, v):
#     width = 128
#     height = 512

#     # Convert u and v to pixel coordinates
#     pixel_x = int(u * width)
#     pixel_y = int(v * height)

#     # Calculate the index from pixel coordinates
#     index = pixel_y * width + pixel_x
#     return index


def get_uv_coordinates(index):
    u = (index % 128) / 128
    v = 1.0 - (index / 128) / 512

    return u, v


def get_uv_from_pmn(rs_mesh, i):
    def cross_product(p1, p2):
        return np.cross(p1, p2)

    def dot_product(p1, p2):
        return np.dot(p1, p2)

    coordinate = rs_mesh.texture_coord_indices[i]
    faceA = rs_mesh.face_indices_a[i]
    faceB = rs_mesh.face_indices_b[i]
    faceC = rs_mesh.face_indices_c[i]

    a = np.array([rs_mesh.vertices_x[faceA], rs_mesh.vertices_y[faceA], rs_mesh.vertices_z[faceA]])
    b = np.array([rs_mesh.vertices_x[faceB], rs_mesh.vertices_y[faceB], rs_mesh.vertices_z[faceB]])
    c = np.array([rs_mesh.vertices_x[faceC], rs_mesh.vertices_y[faceC], rs_mesh.vertices_z[faceC]])

    p = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_p[coordinate]],
                  rs_mesh.vertices_y[rs_mesh.texture_coords_p[coordinate]],
                  rs_mesh.vertices_z[rs_mesh.texture_coords_p[coordinate]]])
    m = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_m[coordinate]],
                  rs_mesh.vertices_y[rs_mesh.texture_coords_m[coordinate]],
                  rs_mesh.vertices_z[rs_mesh.texture_coords_m[coordinate]]])
    n = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_n[coordinate]],
                  rs_mesh.vertices_y[rs_mesh.texture_coords_n[coordinate]],
                  rs_mesh.vertices_z[rs_mesh.texture_coords_n[coordinate]]])

    pM = m - p
    pN = n - p
    pA = a - p
    pB = b - p
    pC = c - p

    pMxPn = cross_product(pM, pN)

    uCoordinate = cross_product(pN, pMxPn)
    mU = 1.0 / dot_product(uCoordinate, pM)

    uA = dot_product(uCoordinate, pA) * mU
    uB = dot_product(uCoordinate, pB) * mU
    uC = dot_product(uCoordinate, pC) * mU

    vCoordinate = cross_product(pM, pMxPn)
    mV = 1.0 / dot_product(vCoordinate, pN)
    vA = dot_product(vCoordinate, pA) * mV
    vB = dot_product(vCoordinate, pB) * mV
    vC = dot_product(vCoordinate, pC) * mV

    u = np.array([float(uA), float(uB), float(uC)])
    v = np.array([float(vA), float(vB), float(vC)])
    return u, v


def load(self):
    mesh = read_mesh(self.filepath)
    create_blender_mesh(mesh, self.filepath)
    return {"FINISHED"}

def validate_and_filter_faces(rs_mesh, vertices, faces):
    vc = rs_mesh.vertex_count
    # basic sanity
    if vc <= 0:
        raise ValueError("vertex_count is zero or negative")
    if len(vertices) != vc:
        raise ValueError(f"vertices length mismatch: got {len(vertices)}, expected {vc}")
    if len(faces) != rs_mesh.face_count:
        print(f"Warning: face_count mismatch: expected {rs_mesh.face_count}, got {len(faces)}")

    # diagnostics
    all_idx = [i for tri in faces for i in tri]
    max_idx = max(all_idx) if all_idx else -1
    min_idx = min(all_idx) if all_idx else -1
    print(f"Vertices: {vc}, Faces: {len(faces)}, index range in faces: {min_idx}..{max_idx}")

    # filter invalid faces
    valid_faces = [tuple(int(i) for i in tri) for tri in faces if all(isinstance(i, (int,)) and 0 <= i < vc for i in tri)]
    dropped = len(faces) - len(valid_faces)
    if dropped:
        print(f"Dropped {dropped} invalid faces (indices out of range or non-integer).")
    return valid_faces
