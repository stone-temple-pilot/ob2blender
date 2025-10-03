import bpy
import os
import colorsys
from ob2blender.byte_buffer import ByteBuffer
import numpy as np

def export_to_ob2(export_dir, export_as_one=False):
    # Ensure export directory exists
    os.makedirs(export_dir, exist_ok=True)

    selected_objects = bpy.context.selected_objects

    if not selected_objects:
        print("No objects selected for export.")
        return

    if export_as_one:
        # Combine selected objects into one mesh
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = selected_objects[0]
        bpy.ops.object.join()
        combined_obj = bpy.context.active_object

        # Ensure mesh is triangulated
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Run through assemble_ob2 and save
        mesh = combined_obj.data
        ob2_data = assemble_ob2(mesh)
        export_path = os.path.join(export_dir, "combined_model.ob2")
        with open(export_path, "wb") as f:
            f.write(ob2_data)
        print(f"Exported combined model to {export_path}")

    else:
        # Export each selected object individually
        for obj in selected_objects:
            # Deselect all, select only current object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Ensure mesh is triangulated
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode='OBJECT')

            blender_mesh = obj.data
            ob2_data = assemble_ob2(blender_mesh)
            export_path = os.path.join(export_dir, f"{obj.name}.ob2")
            with open(export_path, "wb") as f:
                f.write(ob2_data)
            print(f"Exported {obj.name} to {export_path}")

def assemble_ob2(blender_mesh):
    #initiate things we will actually write into binary
        vertex_count = 0
        vertex_flags = []
        vertex_labels = []
        delta_x = []
        delta_y = []
        delta_z = []

        face_count = 0
        face_opcodes = []
        face_deltas = []

        face_draw_types = [] #smooth or flat, textured or not
        face_priorities = [] #PRI
        face_alphas = []
        face_colors = []
        face_labels = []  #TSKIN

        textured_face_count = 0
        texture_coords_p = []  # p
        texture_coords_m = []  # m
        texture_coords_n = []  # n

        #define flags first so we know what we have.
        has_vertex_labels = False
        has_face_labels = False
        has_priority = 0 #255 if true (11111111), 0 if false (00000000)
        has_alpha = False
        has_face_info = False
        #gather vertices

        total_x = 0
        total_y = 0
        total_z = 0
        total_facedelta = 0
        
        
        # blender_mesh.update()
        #then I don't have to update face indices or anything like that.
        #First - flip axes x, y, z to x, z, -y before anything else.
        for v in blender_mesh.vertices:
            v.co.z, v.co.y = v.co.y, -v.co.z
        vertex_flags, delta_x, delta_y, delta_z, vertex_count, vertex_labels, has_vertex_labels = encode_vertices(blender_mesh)
        face_count, face_opcodes, face_deltas = encode_face_indices(blender_mesh)
        face_colors, textured_face_count = encode_face_colors_and_textures(blender_mesh)

        has_face_info, face_draw_types, texture_coords_p, texture_coords_m, texture_coords_n = encode_face_draw_types(blender_mesh)
        face_priorities, face_alphas, face_labels, has_priority, has_alpha, has_face_labels = encode_face_pris_alphas_labels(blender_mesh, face_count)
        #Flip vertices back now that we are done.
        for v in blender_mesh.vertices:
            v.co.z, v.co.y = -v.co.y, v.co.z

        #print some debug info
        # print(f"Vertex count: {vertex_count}, Face count: {face_count}, Textured face count: {textured_face_count}")
        # print(f"Has vertex labels: {has_vertex_labels}, Has face labels: {has_face_labels}, Has priority: {has_priority}, Has alpha: {has_alpha}, Has face info: {has_face_info}")
        # print(f"Vertex flags: {len(vertex_flags)} {vertex_flags}")
        # print(f"Face opcodes: {len(face_opcodes)} {face_opcodes}")
        # print(f"Face deltas: {len(face_deltas)} {face_deltas}")
        # print(f"Face draw types: {len(face_draw_types)} {face_draw_types}")
        # print(f"Face priorities: {len(face_priorities)} {face_priorities}")
        # print(f"Face alphas: {len(face_alphas)} {face_alphas}")
        # print(f"Vertex labels: {len(vertex_labels)} {vertex_labels}")
        # print(f"Face labels: {len(face_labels)} {face_labels}")
        # print(f"Face colors: {len(face_colors)} {face_colors}")
        # print(f"Texture coords P: {len(texture_coords_p)} {texture_coords_p}")
        # print(f"Texture coords M: {len(texture_coords_m)} {texture_coords_m}")
        # print(f"Texture coords N: {len(texture_coords_n)} {texture_coords_n}")
        # print(f"Delta X: {len(delta_x)} {delta_x}")
        # print(f"Delta Y: {len(delta_y)} {delta_y}")
        # print(f"Delta Z: {len(delta_z)} {delta_z}")
        

        #Write ob2 with ByteBuffer
        ob2writer = ByteBuffer(1)
        ob2writer.position = 0
        #Start writing ob2
        for vf in vertex_flags:
            ob2writer.put_byte(int(vf))
        # print("position after vertex flags:", ob2writer.position)
        for fo in face_opcodes:
            ob2writer.put_byte(int(fo))
        # print("position after face opcodes:", ob2writer.position)
        if has_priority == 255:
            for pri in face_priorities:
                ob2writer.put_byte(int(pri))
            # print("position after face priorities:", ob2writer.position)
        if has_face_labels:
            for flabel in face_labels:
                ob2writer.put_byte(int(flabel))
            # print("position after face labels:", ob2writer.position)
        if has_face_info:
            for ftype in face_draw_types:
                ob2writer.put_byte(int(ftype))
            # print("position after face draw types:", ob2writer.position)
        if has_vertex_labels:
            for vlabel in vertex_labels:
                ob2writer.put_byte(int(vlabel))
            # print("position after vertex labels:", ob2writer.position)
        if has_alpha:
            for alpha in face_alphas:
                ob2writer.put_byte(int(alpha))
            # print("position after face alphas:", ob2writer.position)
        pos = ob2writer.position
        for fd in face_deltas:
            ob2writer.put_signed_smart(fd)
        total_facedelta = ob2writer.position - pos
        # print("position after face deltas:", ob2writer.position)
        for fc in face_colors:
            ob2writer.put_short(int(fc))
        # print("position after face colors:", ob2writer.position)
        if textured_face_count > 0:
            for index in range(textured_face_count):
                ob2writer.put_short(int(texture_coords_p[index]))
                ob2writer.put_short(int(texture_coords_m[index]))
                ob2writer.put_short(int(texture_coords_n[index]))
            # print("position after texture coords:", ob2writer.position)
        pos = ob2writer.position
        for dx in delta_x:
            ob2writer.put_signed_smart(int(dx))
        total_x = ob2writer.position - pos
        # print("position after delta x:", ob2writer.position)
        pos = ob2writer.position
        for dy in delta_y:
            ob2writer.put_signed_smart(int(dy))
        total_y = ob2writer.position - pos
        # print("position after delta y:", ob2writer.position)
        pos = ob2writer.position
        for dz in delta_z:
            ob2writer.put_signed_smart(int(dz))
        total_z = ob2writer.position - pos
        # print("position after delta z and before footer:", ob2writer.position)
        #File footer -  last 18 bytes are read first. Holds vertex count, face count and flags.
        ob2writer.put_short(int(vertex_count))
        ob2writer.put_short(int(face_count))
        ob2writer.put_byte(int(textured_face_count))
        ob2writer.put_byte(int(has_face_info))
        ob2writer.put_byte(int(has_priority))
        ob2writer.put_byte(int(has_alpha))
        ob2writer.put_byte(int(has_face_labels))
        ob2writer.put_byte(int(has_vertex_labels))
        ob2writer.put_short(int(total_x))
        ob2writer.put_short(int(total_y))
        ob2writer.put_short(int(total_z))
        ob2writer.put_short(int(total_facedelta))
        print("position after footer:", ob2writer.position)
        #set length to current position
        ob2writer.length = ob2writer.position
        return ob2writer.getData()   


def encode_vertices(blender_mesh):
    vertex_flags = [] #initializing
    delta_x = [] #initializing
    delta_y = [] #initializing
    delta_z = [] #initializing
    vertex_count = 0
    vertex_labels = []  #VSKIN
    has_vertex_labels = False

    #first vertex gets all deltas
    vertex = blender_mesh.vertices[0]
    last_x, last_y, last_z = round(vertex.co.x), round(vertex.co.y), round(vertex.co.z)
    print(f"First vertex coordinates: ({last_x}, {last_y}, {last_z}), converted from ({vertex.co.x}, {vertex.co.y}, {vertex.co.z})")
    vertex_count += 1
    vertex_flags.append(7)  # all deltas present
    delta_x.append(last_x)
    delta_y.append(last_y)
    delta_z.append(last_z)

    for vertex in blender_mesh.vertices[1:]:
        x, y, z = round(vertex.co.x), round(vertex.co.y), round(vertex.co.z)
        vertex_count += 1
        flags = 0
        if x != last_x:
            flags |= 1
            delta_x.append(x - last_x)
            last_x = x
        if y != last_y:
            flags |= 2
            delta_y.append(y - last_y)
            last_y = y
        if z != last_z:
            flags |= 4
            delta_z.append(z - last_z)
            last_z = z
        vertex_flags.append(flags)

    if VSKIN := blender_mesh.attributes.get('VSKIN'):
        has_vertex_labels = True
        VSKIN_data = np.zeros(vertex_count, dtype=int)
        VSKIN.data.foreach_get('value', VSKIN_data)
        vertex_labels.extend(int(v) & 0xFF for v in VSKIN_data)

    return vertex_flags, delta_x, delta_y, delta_z, vertex_count, vertex_labels, has_vertex_labels

def encode_face_indices(blender_mesh):
    
    tris = [p for p in blender_mesh.polygons if len(p.vertices) == 3]
    if not tris:
        return 0, [], []
    # extract vertex indices
    tri_index_a = []
    tri_index_b = []
    tri_index_c = []
    for tri in tris:
        a, b, c = tri.vertices
        tri_index_a.append(a)
        tri_index_b.append(b)
        tri_index_c.append(c)

    face_opcodes = []
    face_deltas = []
    face_count = 0

    a = b = c = last = 0
    def push_delta(val):
        nonlocal last
        d = val - last
        face_deltas.append(d)
        last = val

    #for the first face.
    a, b, c = tris[0].vertices[:]
    face_opcodes.append(1)
    push_delta(a)
    push_delta(b)
    push_delta(c)
    face_count += 1

    for t in range(1, len(tris)):
            ta, tb, tc = tri_index_a[t], tri_index_b[t], tri_index_c[t]
            s = {ta, tb, tc}
            face_count += 1
            # try to share two verts with previous (a,b,c)
            if {a, c}.issubset(s):
                # opcode 2: b = c, c = new (the remaining vertex not in {a,c})
                face_opcodes.append(2)
                new_c = (s - {a, c}).pop()
                # update state
                b = c
                c = new_c
                push_delta(c)
            elif {b, c}.issubset(s):
                # opcode 3: a = c, c = new
                face_opcodes.append(3)
                new_c = (s - {b, c}).pop()
                a = c
                c = new_c
                push_delta(c)
            elif {a, b}.issubset(s):
                # opcode 4: swap a,b, then c = new
                face_opcodes.append(4)
                new_c = (s - {a, b}).pop()
                a, b = b, a
                c = new_c
                push_delta(c)
            else:
                # restart strip: opcode 1 with full (a,b,c)
                face_opcodes.append(1)
                a, b, c = ta, tb, tc
                push_delta(a)
                push_delta(b)
                push_delta(c)

    return face_count, face_opcodes, face_deltas

def encode_face_colors_and_textures(blender_mesh):
    face_colors = []
    textured_face_count = 0
    
    mat_export_cache = []
    mat_code_equivalent = [] #we need to keep indexes aligned.

    for face in blender_mesh.polygons:
        if int(face.material_index) not in mat_export_cache:
            #if the material has a texture:
            if isFaceMaterialTextured(face):
                #get the texture id from the material name or some other property.
                try:
                    texture_id = int(bpy.data.materials[face.material_index].name.split('T')[-1])  # Example: material named "T50" gives texture ID 50
                except ValueError:
                    raise ValueError(f"Material name '{bpy.data.materials[face.material_index].name}' cannot be converted to an integer texture ID for face {face.index}")
                mat_export_cache.append(int(face.material_index))
                mat_code_equivalent.append(texture_id)
                textured_face_count += 1
            else:
                #feature: if the material is named ex. 15_9440, consider 9440 as RGB15 and then convert to HLS.
                #RGB15 is always two bytes long.
                #5 bits for R, 5 bits for G, 5 bits for B. Most significant bit is unused.
                #R, G, B are converted from 0.0 - 1.0 to 0 - 31.
                if blender_mesh.materials[face.material_index].name.startswith("15_"):
                    try:
                        rgb_value = int(blender_mesh.materials[face.material_index].name.split('_')[1])
                        if rgb_value < 0 or rgb_value > 32767:  # RGB15 range check
                            raise ValueError(f"RGB15 value {rgb_value} out of range for material '{blender_mesh.materials[face.material_index].name}'")
                        r = ((rgb_value >> 10) & 0x1F) / 31.0
                        g = ((rgb_value >> 5) & 0x1F) / 31.0
                        b = (rgb_value & 0x1F) / 31.0
                        print(f"Converting RGB15 {rgb_value} to HSL for material index {face.material_index}: R={r}, G={g}, B={b}")
                        (H, L, S) = colorsys.rgb_to_hls(r, g, b)
                    except ValueError as e:
                        print(f"Error processing material name '{blender_mesh.materials[face.material_index].name}' for face {face.index}: {e}")
                else:
                    rgb = blender_mesh.materials[face.material_index].diffuse_color
                    #Convert RGB to HSL16 - 6 bits for H, 3 bits for S, 7 bits for L
                    print("Converting RGB to HSL for material index", face.material_index, "rgb:", rgb[0], rgb[1], rgb[2])
                    (H, L, S) = colorsys.rgb_to_hls(rgb[0], rgb[1], rgb[2])
                color = ((round(H * 63.0) & 0x3F) << 10) | ((round(S * 7.0) & 0x07) << 7) | (round(L * 127.0) & 0x7F) & 0xFFFF
                mat_export_cache.append(face.material_index)
                mat_code_equivalent.append(color)
                print("Appended color:", color, "for material index", face.material_index)
        #print(f"Face {face.index} material index: {face.material_index}, color: {mat_code_equivalent[mat_export_cache.index(face.material_index)]}")
        color = mat_code_equivalent[mat_export_cache.index(face.material_index)]
        face_colors.append(color)
    # print(f"mat_export_cache: {mat_export_cache}, mat_code_equivalent: {mat_code_equivalent}")
    return face_colors, textured_face_count

def encode_face_draw_types(blender_mesh):

    textured_face_holder = [] #indices for textured faces that will be used to map to pmn values.

    #check if any meshes use flat shading or have a texture - the has_face_info flag must be set if so.
    has_face_info = False
    if any(not face.use_smooth for face in blender_mesh.polygons) or any(isFaceMaterialTextured(face) for face in blender_mesh.polygons):
        has_face_info = True

        face_draw_types = [0] * len(blender_mesh.polygons)  # Initialize all to 0 (flat, untextured)
        for i, face in enumerate(blender_mesh.polygons):
            if face.use_smooth == False:
                face_draw_types[i] |= 1  # Set flat bit
            if isFaceMaterialTextured(face):
                face_draw_types[i] |= 2  # Set textured bit
                # Assign PMN index (for simplicity, using face index)
                textured_face_holder.append(i)

        tuple_library = [] #list of unique PMN tuples that are sometimes shared between faces.
        #the integer index of tuple_library will be used for face_draw_types.
        for face in textured_face_holder: #face here is the index of the face in blender_mesh.polygons
            uvs = [loop[face.loop_indices] for loop in blender_mesh.uv_layers.active.data]
            PMNtuple = uv_to_pmn(uvs[0], uvs[1], blender_mesh, face)
            if PMNtuple not in tuple_library:
                tuple_library.append(PMNtuple)
            face_draw_types[face] |= (tuple_library.index(PMNtuple) << 2)  # Store PMN index in higher 6 bits

        texture_coords_p = []  # p
        texture_coords_m = []  # m
        texture_coords_n = []  # n

        def find_closest_vertex(point):
            closest_index = None
            closest_dist = float('inf')
            for v in blender_mesh.vertices:
                dist = (v.co.x - point[0])**2 + (v.co.y - point[1])**2 + (v.co.z - point[2])**2
                if dist < closest_dist:
                    closest_dist = dist
                    closest_index = v.index
            return closest_index
        
        for tuple in tuple_library:
            p, m, n = tuple
            #p, m, n are all tuples representing a point in 3D space. We need to find the nearest vertex index in the mesh for each.
            #one list for p, one list for m, one list for n.
            pmn_index = []
            for point in (p, m, n):
                closest_vertex = find_closest_vertex(point)
                pmn_index.append(closest_vertex)
            texture_coords_p.append(pmn_index[0])
            texture_coords_m.append(pmn_index[1])
            texture_coords_n.append(pmn_index[2])

        return has_face_info, face_draw_types, texture_coords_p, texture_coords_m, texture_coords_n
    else:
        return has_face_info, [], [], [], [] #default empty lists if no face info

def encode_face_pris_alphas_labels(blender_mesh, face_count):
    face_priorities = [] #PRI
    face_alphas = []
    face_labels = []  #TSKIN
    has_priority = 0 #255 if true (11111111), 0 if false (00000000)
    has_alpha = False
    has_face_labels = False

    #check if any face has a priority set (custom property 'PRI')
    if PRIs := blender_mesh.attributes.get('PRI'):
        has_priority = 255
        PRIs_data = np.zeros(face_count, dtype=int)
        PRIs.data.foreach_get('value', PRIs_data)
        face_priorities.extend(int(v) & 0xFF for v in PRIs_data)

    #check if any face has a custom property 'ALPHA'
    if ALPHAs := blender_mesh.attributes.get('ALPHA'):
        has_alpha = True
        ALPHAs_data = np.zeros(face_count, dtype=int)
        ALPHAs.data.foreach_get('value', ALPHAs_data)
        face_alphas.extend(int(v) & 0xFF for v in ALPHAs_data)

    #check if any face has a custom property 'TSKIN'
    if TSKINs := blender_mesh.attributes.get('TSKIN'):
        has_face_labels = True
        TSKINs_data = np.zeros(face_count, dtype=int)
        TSKINs.data.foreach_get('value', TSKINs_data)
        face_labels.extend(int(v) & 0xFF for v in TSKINs_data)

    return face_priorities, face_alphas, face_labels, has_priority, has_alpha, has_face_labels

# Example usage:
# export_selected_objects("C:/Users/mallo/Desktop/ob2blender/exports", export_as_one=True)
def isFaceMaterialTextured(face):
    material = bpy.data.materials[face.material_index]
    if material and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                return True
    return False


def uv_to_pmn(u, v, blender_mesh, face):

    ia = blender_mesh.face_indices_a[face]
    ib = blender_mesh.face_indices_b[face]
    ic = blender_mesh.face_indices_c[face]

    A = np.array([blender_mesh.vertices_x[ia], blender_mesh.vertices_y[ia], blender_mesh.vertices_z[ia]], dtype=float)
    B = np.array([blender_mesh.vertices_x[ib], blender_mesh.vertices_y[ib], blender_mesh.vertices_z[ib]], dtype=float)
    C = np.array([blender_mesh.vertices_x[ic], blender_mesh.vertices_y[ic], blender_mesh.vertices_z[ic]], dtype=float)

    uA, uB, uC = map(float,u)
    vA, vB, vC = map(float,v)

    # UV deltas relative to vertex A
    du1, dv1 = (uB - uA), (vB - vA)
    du2, dv2 = (uC - uA), (vC - vA)

    e1 = B - A
    e2 = C - A

    det = du1 * dv2 - dv1 * du2
    if abs(det) < 1e-12:
        raise ValueError("Degenerate UV mapping (cannot invert).")
    inv_det = 1.0 / det

    # Solve for basis vectors f1, f2 (same as tangent/bitangent but in your object space)
    f1 = ( e1 * dv2 - e2 * dv1) * inv_det  # maps (1,0)
    f2 = (-e1 * du2 + e2 * du1) * inv_det  # maps (0,1)

    # Recover P so that A maps to (uA,vA)
    # uA = dot(f1, A-P) => P = A - uA*f1 - vA*f2
    P = A - uA * f1 - vA * f2
    M = P + f1
    N = P + f2

    P = np.round(P).astype(int)
    M = np.round(M).astype(int)
    N = np.round(N).astype(int)

    return (P, M, N)