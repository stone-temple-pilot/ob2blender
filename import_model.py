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

def load(self):
    mesh = read_mesh(self.filepath)
    create_blender_mesh(mesh, self.filepath)
    return {"FINISHED"}

def create_blender_mesh(rs_mesh, filepath):
    # Create a new mesh
    blender_mesh = bpy.data.meshes.new("Mesh")

    # since it's runescapes XYZ is different, and y axis inverted?? or maybe not
    vertices = [(rs_mesh.vertices_x[i], rs_mesh.vertices_z[i], -rs_mesh.vertices_y[i]) for i in range(rs_mesh.vertex_count)]

    # Set faces
    faces = [(rs_mesh.face_indices_a[i], rs_mesh.face_indices_b[i], rs_mesh.face_indices_c[i]) for i in
             range(rs_mesh.face_count)]
    
    # Set the mesh data
    # validate/filter faces before passing to Blender
    valid_faces = validate_and_filter_faces(rs_mesh, vertices, faces)
    blender_mesh.from_pydata(vertices, [], valid_faces)
    blender_mesh.update()


    filename = os.path.splitext(os.path.basename(filepath))[0]
    obj = bpy.data.objects.new(filename, blender_mesh)

    

    #now assign colors, and handle if both color and texture exist.
    create_or_get_material(rs_mesh, blender_mesh) #runescape colors are stored as HSL16 values
    #the following is just to set the proper shading, referring to face_draw_types again.
    use_draw_types = rs_mesh.face_draw_types
    if use_draw_types:
        for i, poly in enumerate(blender_mesh.polygons):
            # The last bit (bit 0) of face_draw_types determines shading: 0 = smooth, 1 = flat
            poly.use_smooth = (use_draw_types[i] & 1) == 0
    else:
        for i, poly in enumerate(blender_mesh.polygons):
            poly.use_smooth = True  # Default to all smooth shading if no draw types are provided.

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


    if rs_mesh.vertex_labels: #VSKIN, vertex labels
        VSKIN_values = np.zeros(rs_mesh.vertex_count, dtype=np.int8)
        for i in range(rs_mesh.vertex_count):
            VSKIN_values[i] = rs_mesh.vertex_labels[i]
        VSKIN = blender_mesh.attributes.new(name='VSKIN', type='INT', domain='POINT')
        VSKIN.data.foreach_set("value", VSKIN_values)
        
    PRI_values = np.zeros(rs_mesh.face_count, dtype=np.int8)
    if rs_mesh.face_priorities: #per-face priorities
        for i in range(rs_mesh.face_count):
            PRI_values[i] = rs_mesh.face_priorities[i]
    else: #model-wide priority
        for i in range(rs_mesh.face_count):
            PRI_values[i] = rs_mesh.model_priority #e.g. if model priority is 2, all faces get 2
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

def create_or_get_material(rs_mesh, blender_mesh):
    if rs_mesh.face_indices_a and rs_mesh.face_indices_b and rs_mesh.face_indices_c: #sanity check
        
        mesh = blender_mesh

        combo_cache = []    #for all Blender materials, regardless of type.

        hsl_cache = []  
        rgba_cache = []    # paired because one HSL corresponds to one RGBA

        for face in range(rs_mesh.face_count):
            face_color = rs_mesh.face_colors[face]
            if face_color not in hsl_cache:
                H = (face_color >> 10) & 0x3F
                S = (face_color >> 7) & 0x07
                L = face_color & 0x7F
                r, g, b = colorsys.hls_to_rgb(H / 63.0, L / 127.0, S / 7.0)
                rgba = (round(r, 6), round(g, 6), round(b, 6), 1.0)
                print("import_model.py: Creating new color:", (H, S, L), "->", rgba)
                hsl_cache.append(face_color)  # just to track which HSL we've seen
                rgba_cache.append(rgba) # corresponding RGBA value
            else:
                rgba = rgba_cache[hsl_cache.index(face_color)]

            # Detect textured faces
            has_texture = bool(rs_mesh.face_draw_types) and (rs_mesh.face_draw_types[face] >> 1) & 1

            if has_texture:
                texture_id = rs_mesh.face_colors[face]

                # texture_id = 37 #temp override for testing
                key = (texture_id, face_color)

                if key not in combo_cache:
                    # Create a combined material that multiplies texture by the face color
                    # mat_name = f"T{texture_id}_H{H}_S{S}_L{L}"
                    mat_name = f"T{texture_id}"
                    mat = bpy.data.materials.new(mat_name)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    nodes.clear()

                    output_node = nodes.new(type='ShaderNodeOutputMaterial')
                    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                    tex_node = nodes.new(type='ShaderNodeTexImage')

                    # load image if available (reuse existing image if loaded)
                    texture_path = os.path.join(os.path.dirname(__file__), "textures", f"{texture_id}.png")
                    if os.path.exists(texture_path):
                        tex_node.image = bpy.data.images.load(filepath=texture_path, check_existing=True)

                    mat.use_backface_culling = True
                    mat.blend_method = 'CLIP'

                    mesh.materials.append(mat)
                    combo_cache.append(key)

                mat_index = combo_cache.index(key)
                mesh.polygons[face].material_index = mat_index
                # Ensure UV layer exists
                if not mesh.uv_layers:
                    mesh.uv_layers.new(name="UVMap")
                uv_layer = mesh.uv_layers.active.data

                # Get UVs from p, m, n coordinates
                uvs = get_uv_from_pmn(rs_mesh, face)
                poly = mesh.polygons[face]
                for loop_idx, (u, v) in zip(poly.loop_indices, zip(uvs[0], uvs[1])):
                    uv_layer[loop_idx].uv = (u, v)

                #print(f"Face {face} PMN coords:", rs_mesh.texture_coords_p[rs_mesh.texture_coord_indices[face]],rs_mesh.texture_coords_m[rs_mesh.texture_coord_indices[face]],rs_mesh.texture_coords_n[rs_mesh.texture_coord_indices[face]])

            else:
                key = (-1, face_color)
                if key not in combo_cache:
                    mat_name = f"H{H}_S{S}_L{L}"
                    mat = bpy.data.materials.new(mat_name)
                    mat.diffuse_color = rgba
                    # keep nodes enabled for consistency with above.
                    mat.use_nodes = True
                    # Optionally create a simple node setup for solid color:
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    nodes.clear()
                    output_node = nodes.new(type='ShaderNodeOutputMaterial')
                    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                    rgb_node = nodes.new(type='ShaderNodeRGB')
                    rgb_node.outputs[0].default_value = rgba
                    links.new(rgb_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

                    mat.use_backface_culling = True
                    mat.blend_method = 'CLIP'

                    mesh.materials.append(mat)
                    combo_cache.append(key)

                mat_index = combo_cache.index(key)
                mesh.polygons[face].material_index = mat_index


def get_uv_from_pmn(rs_mesh, i):
    # Get the indices for the texture coordinates
    coordinate = rs_mesh.texture_coord_indices[i]
    faceA = rs_mesh.face_indices_a[i]
    faceB = rs_mesh.face_indices_b[i]
    faceC = rs_mesh.face_indices_c[i]

    # Get the 3D coordinates for the triangle vertices
    a = np.array([rs_mesh.vertices_x[faceA], rs_mesh.vertices_y[faceA], rs_mesh.vertices_z[faceA]])
    b = np.array([rs_mesh.vertices_x[faceB], rs_mesh.vertices_y[faceB], rs_mesh.vertices_z[faceB]])
    c = np.array([rs_mesh.vertices_x[faceC], rs_mesh.vertices_y[faceC], rs_mesh.vertices_z[faceC]])

    # Get the PMN coordinates
    p = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_p[coordinate]],
                rs_mesh.vertices_y[rs_mesh.texture_coords_p[coordinate]],
                rs_mesh.vertices_z[rs_mesh.texture_coords_p[coordinate]]])
    m = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_m[coordinate]],
                rs_mesh.vertices_y[rs_mesh.texture_coords_m[coordinate]],
                rs_mesh.vertices_z[rs_mesh.texture_coords_m[coordinate]]])
    n = np.array([rs_mesh.vertices_x[rs_mesh.texture_coords_n[coordinate]],
                rs_mesh.vertices_y[rs_mesh.texture_coords_n[coordinate]],
                rs_mesh.vertices_z[rs_mesh.texture_coords_n[coordinate]]])

    print("import_model.py: Calculating UVs for face", i, "with PMN coords:", p, m, n)
    f1 = m - p
    f2 = n - p

    f1DotF1 = np.dot(f1, f1)
    f1DotF2 = np.dot(f1, f2)
    f2DotF2 = np.dot(f2, f2)
    print("import_model.py: PMN triangle dot products:", f1DotF1, f1DotF2, f2DotF2)

    det = (f1DotF1 * f2DotF2) - (f1DotF2 * f1DotF2)
    print("import_model.py: PMN triangle determinant:", det)
    if det == 0:
        print("PMN triangle is degenerate (determinant is zero). Defaulting det to 1.")
        det = 1

    invDet = 1.0 / det

    # Inverse of the Gram matrix
    inverse = np.array([
        [f2DotF2 * invDet, -f1DotF2 * invDet],
        [-f1DotF2 * invDet, f1DotF1 * invDet]
    ])

    pA = a - p
    pB = b - p
    pC = c - p

    projectionA = np.array([np.dot(f1, pA), np.dot(f2, pA)])
    projectionB = np.array([np.dot(f1, pB), np.dot(f2, pB)])
    projectionC = np.array([np.dot(f1, pC), np.dot(f2, pC)])

    uv0 = inverse @ projectionA
    uv1 = inverse @ projectionB
    uv2 = inverse @ projectionC

    # Return as two lists: ([u0, u1, u2], [v0, v1, v2])
    return [float(uv0[0]), float(uv1[0]), float(uv2[0])], [float(uv0[1]), float(uv1[1]), float(uv2[1])]

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
