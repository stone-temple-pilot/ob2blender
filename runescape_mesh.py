#all credit goes to Tamatea for this code
from ob2blender.byte_buffer import ByteBuffer

def to_signed_byte(value):
    value %= 256
    if value > 127:
        value -= 256
    return value

class RunescapeMesh: #todo: recreate this for all parameters in 244-type models based on model.ts (typescript) from Lost-City
    def __init__(self):

        # rs3 vars
        # self.texture_scale_x = None
        # self.texture_scale_y = None
        # self.texture_scale_z = None
        # self.texture_rotation = None
        # self.texture_direction = None
        # self.texture_speed = None
        # self.texture_u_trans = None
        # self.texture_v_trans = None
        # self.uv_map_vertex_offset = None
        # self.uv_face_indices_a = None
        # self.uv_face_indices_b = None
        # self.uv_face_indices_c = None
        # self.uv_coord_u = None
        # self.uv_coord_v = None
        # self.uv_coords_count = 0
        # self.highest_vertex = 0
        # self.emitters = None
        # self.effectors = None
        # self.billboards = None

        self.model_version = None
        self.texture_coord_indices = None
        self.texture_ids = None
        self.skeletal_bones = None
        self.skeletal_weights = None
        self.model_type = ""

        self.vertex_count = 0
        self.vertices_x = []
        self.vertices_y = []
        self.vertices_z = []
        self.face_count = 0
        self.face_indices_a = []  # indices
        self.face_indices_b = []
        self.face_indices_c = []
        self.face_draw_types = [] #smooth or flat, textured or not
        self.face_priorities = [] #PRI
        self.face_alphas = []
        self.face_colors = []
        self.model_priority = 0
        self.vertex_labels = []  #VSKIN
        self.face_labels = []  #TSKIN
        self.textured_face_count = 0
        self.texture_coords_p = []  # p
        self.texture_coords_m = []  # m
        self.texture_coords_n = []  # n
        self.texture_types = []
        self.grouped_vertices = []
        self.grouped_faces = []
        self.bone_groups = None

    @staticmethod
    # Leaving this here because I like it
    # def decode(self, data):
    #     last = to_signed_byte(data[-1])
    #     second_last = to_signed_byte(data[-2])
    #     if data[0] == 1:
    #         return self.decode_rs3(data)
    #     elif last == -3 and second_last == -1:
    #         return self.decode_type_three(data)
    #     elif last == -2 and second_last == -1:
    #         return self.decode_type_two(data)
    #     elif last == -1 and second_last == -1:
    #         return self.decode_new(data)
    #     else:
    #         return self.decode_old(data)
    def decode(self, data):

        buffer_indices = ByteBuffer(data)
        buffer_face_info = ByteBuffer(data)
        buffer_face_priorities = ByteBuffer(data)
        buffer_face_alphas = ByteBuffer(data)
        buffer_face_labels = ByteBuffer(data)

        buffer_indices.set_pos(len(data) - 18)
        vertex_count = buffer_indices.read_unsigned_short()
        face_count = buffer_indices.read_unsigned_short()
        textured_face_count = buffer_indices.read_unsigned_byte()
        
        self.vertex_count = vertex_count
        self.face_count = face_count
        self.textured_face_count = textured_face_count

        hasInfo = buffer_indices.read_unsigned_byte() #for shading
        priority = buffer_indices.read_unsigned_byte()
        hasAlpha = buffer_indices.read_unsigned_byte()
        hasFaceLabels = buffer_indices.read_unsigned_byte() #has TSKIN
        hasVertexLabels = buffer_indices.read_unsigned_byte()

        vertices_x_length = buffer_indices.read_unsigned_short()
        vertices_y_length = buffer_indices.read_unsigned_short()
        vertices_z_length = buffer_indices.read_unsigned_short()
        face_indices_length = buffer_indices.read_unsigned_short()

        pos = 0

        vertex_flags_offset = pos
        pos += vertex_count

        face_indices_flag_offset = pos
        pos += face_count

        face_priority_offset = pos
        if priority == 255:
            pos += face_count

        face_labels_offset = pos
        if hasFaceLabels == 1:
            pos += face_count

        face_info_offset = pos
        if hasInfo == 1:
            pos += face_count

        vertex_labels_offset = pos
        if hasVertexLabels == 1:
            pos += vertex_count

        face_alpha_offset = pos
        if hasAlpha == 1:
            pos += face_count

        face_indices_offset = pos
        pos += face_indices_length

        face_colors_offset = pos
        pos += face_count * 2

        textured_face_offset = pos
        pos += textured_face_count * 6

        vertices_x_offset = pos
        pos += vertices_x_length

        vertices_y_offset = pos
        pos += vertices_y_length

        vertices_z_offset = pos

        self.vertices_x = [0] * vertex_count
        self.vertices_y = [0] * vertex_count
        self.vertices_z = [0] * vertex_count
        self.face_indices_a = [0] * face_count
        self.face_indices_b = [0] * face_count
        self.face_indices_c = [0] * face_count

        if textured_face_count > 0:
            self.texture_types = [0] * textured_face_count
            self.texture_coords_p = [0] * textured_face_count
            self.texture_coords_m = [0] * textured_face_count
            self.texture_coords_n = [0] * textured_face_count
#you'll be referring to these for proper order when you create the exporter
#initialize arrays based on flags.
        if hasVertexLabels == 1:
            self.vertex_labels = [0] * vertex_count

        if hasInfo == 1:
            self.face_draw_types = [0] * face_count

        if priority == 255:
            self.face_priorities = [0] * face_count
        else:
            self.model_priority = priority

        if hasAlpha == 1:
            self.face_alphas = [0] * face_count

        if hasFaceLabels == 1:
            self.face_labels = [0] * face_count

        self.face_colors = [0] * face_count
        buffer_indices.set_pos(vertex_flags_offset) #these buffers are also talented at reading vertex data.
        buffer_face_info.set_pos(vertices_x_offset)
        buffer_face_priorities.set_pos(vertices_y_offset)
        buffer_face_alphas.set_pos(vertices_z_offset)
        buffer_face_labels.set_pos(vertex_labels_offset)
        x = y = z = 0 #the first vertex is position 0
        for vertex in range(vertex_count):
            position_flag = buffer_indices.read_unsigned_byte() #tells us if it is an X, Y, or Z value.
            dx = dy = dz = 0 #following vertices are assigned a 3D delta value

            if position_flag & 1:
                dx = buffer_face_info.readSignedSmart() #can vary in size...? oh no... going to need to factor this into my exporter.
            if position_flag & 2:
                dy = buffer_face_priorities.readSignedSmart()
            if position_flag & 4:
                dz = buffer_face_alphas.readSignedSmart()

            self.vertices_x[vertex] = x + dx
            self.vertices_y[vertex] = y + dy
            self.vertices_z[vertex] = z + dz
            x = self.vertices_x[vertex]
            y = self.vertices_y[vertex]
            z = self.vertices_z[vertex]
            if hasVertexLabels:
                self.vertex_labels[vertex] = buffer_face_labels.read_unsigned_byte()

        buffer_indices.set_pos(face_colors_offset)
        buffer_face_info.set_pos(face_info_offset)
        buffer_face_priorities.set_pos(face_priority_offset)
        buffer_face_alphas.set_pos(face_alpha_offset)
        buffer_face_labels.set_pos(face_labels_offset)

        for face in range(face_count):
            color = buffer_indices.read_unsigned_short() #6 H, 3 S, 7 L = 16bit
            self.face_colors[face] = color

            if hasInfo == 1:
                self.face_draw_types[face] = buffer_face_info.read_unsigned_byte()
            if priority == 255:
                self.face_priorities[face] = buffer_face_priorities.read_signed_byte()

            if hasAlpha == 1:
                self.face_alphas[face] = buffer_face_alphas.read_unsigned_byte()

            if hasFaceLabels == 1:
                self.face_labels[face] = buffer_face_labels.read_unsigned_byte()


        buffer_indices.set_pos(face_indices_offset)
        buffer_face_info.set_pos(face_indices_flag_offset)
        a = b = c = last = 0
        for face in range(face_count):
            opcode = buffer_face_info.read_unsigned_byte()
            if opcode == 1:
                a = buffer_indices.readSignedSmart() + last
                last = a
                b = buffer_indices.readSignedSmart() + last
                last = b
                c = buffer_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c
            if opcode == 2:
                b = c
                c = buffer_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c
            if opcode == 3:
                a = c
                c = buffer_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c
            if opcode == 4:
                temp = a
                a = b
                b = temp
                c = buffer_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c

        buffer_indices.set_pos(textured_face_offset)
        for face in range(textured_face_count):
            self.texture_types[face] = 0
            self.texture_coords_p[face] = buffer_indices.read_unsigned_short()
            self.texture_coords_m[face] = buffer_indices.read_unsigned_short()
            self.texture_coords_n[face] = buffer_indices.read_unsigned_short()
        self.convert_textures()

    def create_groups(self):
        if len(self.vertex_labels) > 0:
            vertex_group_count = [0] * 256
            count = 0

            for v in range(self.vertex_count):
                group = self.vertex_labels[v]
                vertex_group_count[group] += 1
                if group > count:
                    count = group

            self.grouped_vertices = [[] for _ in range(count + 1)]

            for group in range(count + 1):
                self.grouped_vertices[group] = [0] * vertex_group_count[group]
                vertex_group_count[group] = 0

            for v in range(self.vertex_count):
                group = self.vertex_labels[v]
                self.grouped_vertices[group][vertex_group_count[group]] = v
                vertex_group_count[group] += 1

        if len(self.face_labels) > 0:
            face_group_count = [0] * 256
            count = 0

            for f in range(self.face_count):
                group = self.face_labels[f]
                face_group_count[group] += 1
                if group > count:
                    count = group

            self.grouped_faces = [[] for _ in range(count + 1)]

            for group in range(count + 1):
                self.grouped_faces[group] = [0] * face_group_count[group]
                face_group_count[group] = 0

            for face in range(self.face_count):
                group = self.face_labels[face]
                self.grouped_faces[group][face_group_count[group]] = face
                face_group_count[group] += 1

        bones = self.skeletal_bones

        if bones is not None:
            self.bone_groups = {}
            for vertex in range(len(bones)):
                for joint in range(len(bones[vertex])):
                    bone_index = bones[vertex][joint]
                    if bone_index not in self.bone_groups:
                        self.bone_groups[bone_index] = []
                    self.bone_groups[bone_index].append(vertex)

    def convert_textures(self):

        if self.face_draw_types is None or len(self.face_draw_types) < self.face_count:
            return

        if self.textured_face_count == 0:
            return

        if self.texture_coord_indices is None:
            self.texture_coord_indices = [0] * self.face_count

        if self.texture_ids is None:
            self.texture_ids = [0] * self.face_count

        for i in range(self.face_count):
            if self.face_draw_types is not None and self.face_draw_types[i] >= 2:
                texture_index = self.face_draw_types[i] >> 2
                self.texture_coord_indices[i] = texture_index
                self.texture_ids[i] = self.face_colors[i]
            else:
                self.texture_coord_indices[i] = -1
                self. texture_ids[i] = -1

    def decode_faces(self, buffer_face_indices, buffer_flag, buffer_uv):
        a = 0
        b = 0
        c = 0
        last = 0

        for face in range(self.face_count):
            flag = buffer_flag.read_unsigned_byte()
            orientation = flag & 0x7
            if orientation == 1:
                self.face_indices_a[face] = a = buffer_face_indices.readSignedSmart() + last
                self.face_indices_b[face] = b = buffer_face_indices.readSignedSmart() + a
                self.face_indices_c[face] = c = buffer_face_indices.readSignedSmart() + b
                last = c
                if a > self.highest_vertex:
                    self.highest_vertex = a
                if b > self.highest_vertex:
                    self.highest_vertex = b
                if c > self.highest_vertex:
                    self.highest_vertex = c
            if orientation == 2:
                b = c
                c = buffer_face_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c
                if c > self.highest_vertex:
                    self.highest_vertex = c
            if orientation == 3:
                a = c
                c = buffer_face_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = b
                self.face_indices_c[face] = c
                if c > self.highest_vertex:
                    self.highest_vertex = c
            if orientation == 4:
                tmp = a
                a = b
                b = tmp
                c = buffer_face_indices.readSignedSmart() + last
                last = c
                self.face_indices_a[face] = a
                self.face_indices_b[face] = tmp
                self.face_indices_c[face] = c
                if c > self.highest_vertex:
                    self.highest_vertex = c
            if self.uv_coords_count > 0 and (flag & 0x8) != 0:
                self.uv_face_indices_a[face] = buffer_uv.read_unsigned_byte()
                self.uv_face_indices_b[face] = buffer_uv.read_unsigned_byte()
                self.uv_face_indices_c[face] = buffer_uv.read_unsigned_byte()

        self.highest_vertex += 1

    def decode_mapping(self, buffer_pmn, buffer_scaled_pmn, buffer_texture_scale, buffer_texture_rotation,
                       buffer_texture_direction, buffer_texture_speed):
        for textured_face in range(self.textured_face_count):
            mapping = self.texture_types[textured_face] & 0xFF
            if mapping == 0:
                self.texture_coords_p[textured_face] = buffer_pmn.read_unsigned_short()
                self.texture_coords_m[textured_face] = buffer_pmn.read_unsigned_short()
                self.texture_coords_n[textured_face] = buffer_pmn.read_unsigned_short()
            if mapping == 1:
                self.texture_coords_p[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                self.texture_coords_m[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                self.texture_coords_n[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                if self.model_version < 15:
                    self.texture_scale_x[textured_face] = buffer_texture_scale.read_unsigned_short()
                    if self.model_version < 14:
                        self.texture_scale_y[textured_face] = buffer_texture_scale.read_unsigned_short()
                    else:
                        self.texture_scale_y[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_z[textured_face] = buffer_texture_scale.read_unsigned_short()
                else:
                    self.texture_scale_x[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_y[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_z[textured_face] = buffer_texture_scale.read24_bit_int()
                self.texture_rotation[textured_face] = buffer_texture_rotation.read_signed_byte()
                self.texture_direction[textured_face] = buffer_texture_direction.read_signed_byte()
                self.texture_speed[textured_face] = buffer_texture_speed.read_signed_byte()
            if mapping == 2:
                self.texture_coords_p[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                self.texture_coords_m[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                self.texture_coords_n[textured_face] = buffer_scaled_pmn.read_unsigned_short()
                if self.model_version < 15:
                    self.texture_scale_x[textured_face] = buffer_texture_scale.read_unsigned_short()
                    if self.model_version < 14:
                        self.texture_scale_y[textured_face] = buffer_texture_scale.read_unsigned_short()
                    else:
                        self.texture_scale_y[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_z[textured_face] = buffer_texture_scale.read_unsigned_short()
                else:
                    self.texture_scale_x[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_y[textured_face] = buffer_texture_scale.read24_bit_int()
                    self.texture_scale_z[textured_face] = buffer_texture_scale.read24_bit_int()
                self.texture_rotation[textured_face] = buffer_texture_rotation.read_signed_byte()
                self.texture_direction[textured_face] = buffer_texture_direction.read_signed_byte()
                self.texture_speed[textured_face] = buffer_texture_speed.read_signed_byte()
                self.texture_u_trans[textured_face] = buffer_texture_speed.read_signed_byte()
                self.texture_v_trans[textured_face] = buffer_texture_speed.read_signed_byte()
