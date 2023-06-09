from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np
import os

### global variables ###

# about camera
g_cam_pos = glm.vec3(1.0, 1.0, 1.0)
g_target = glm.vec3(0.0, 0.0, 0.0)
g_azimuth = 45.0
g_elevation = 45.0
g_dist = glm.distance(g_cam_pos, g_target)

# mode
g_persp = True
g_single_mesh = True
g_wireframe = False

# about vectors
g_up_vector = glm.vec3(0.0, 1.0, 0.0)
g_w_vec = glm.normalize(g_cam_pos - g_target)
g_u_vec = glm.normalize(glm.cross(glm.vec3(0.0, 1.0, 0.0), g_w_vec))
g_v_vec = glm.cross(g_w_vec, g_u_vec)

# about mouse
g_mouse_right = False
g_mouse_left = False
g_last_x = 0.
g_last_y = 0.
g_zoom = 1.0

# g_Pers = glm.perspective(np.radians(45), 1, .1, 100.0)
# g_Orth = glm.ortho(-1, 1, -1, 1, -1, 1)

# about obj file io
g_obj_list = []
g_obj_VAO_list = []
g_obj_hier_VAO_list = []
g_obj_hier_list = []

########################

g_vertex_shader_src = '''
#version 330 core

layout (location = 0) in vec3 vin_pos; 
layout (location = 1) in vec3 vin_normal; 

out vec3 vout_surface_pos;
out vec3 vout_normal;

uniform mat4 MVP;
uniform mat4 M;

void main()
{
    vec4 p3D_in_hcoord = vec4(vin_pos.xyz, 1.0);
    gl_Position = MVP * p3D_in_hcoord;

    vout_surface_pos = vec3(M * vec4(vin_pos, 1));
    vout_normal = normalize( mat3(inverse(transpose(M)) ) * vin_normal);
}
'''

g_fragment_shader_src = '''
#version 330 core

in vec3 vout_surface_pos;
in vec3 vout_normal;

out vec4 FragColor;

uniform vec3 view_pos;
uniform float factor;
uniform vec3 color;

void main()
{
    // light and material properties
    vec3 light_pos = vec3(3,2,4);
    vec3 another_light_pos = vec3(-3, 2, -4);
    vec3 light_color = vec3(1,1,1);
    vec3 material_color = color;
    float material_shininess = 32.0;

    // light components
    vec3 light_ambient = factor*light_color;
    vec3 light_diffuse = light_color;
    vec3 light_specular = light_color;

    // material components
    vec3 material_ambient = material_color;
    vec3 material_diffuse = material_color;
    vec3 material_specular = light_color;  // for non-metal material

    // ambient
    vec3 ambient = light_ambient * material_ambient;

    // for diffiuse and specular
    vec3 normal = normalize(vout_normal);
    vec3 surface_pos = vout_surface_pos;
    vec3 light_dir = normalize(light_pos - surface_pos);
    vec3 another_light_dir = normalize(another_light_pos - surface_pos);

    // diffuse
    float diff = max(dot(normal, light_dir), 0);
    float another_diff = max(dot(normal, another_light_dir), 0);
    vec3 diffuse = diff * light_diffuse * material_diffuse;
    vec3 another_diffuse = another_diff * light_diffuse * material_diffuse;


    // specular
    vec3 view_dir = normalize(view_pos - surface_pos);
    vec3 reflect_dir = reflect(-light_dir, normal);
    vec3 another_reflect_dir = reflect(-another_light_dir, normal);
    float spec = pow( max(dot(view_dir, reflect_dir), 0.0), material_shininess);
    float another_spec = pow(max(dot(view_dir, another_reflect_dir), 0.0), material_shininess);
    vec3 specular = spec * light_specular * material_specular;
    vec3 another_specular = another_spec * light_specular * material_specular;

    vec3 color = ambient + diffuse + specular;
    color += ambient + another_diffuse + another_specular;
    FragColor = vec4(color, 1.);
}
'''

class ObjData:
    def __init__(self):
        self.vertex_position = []
        self.normal_vector = []
        self.vertex_index = []
        self.normal_index = []
        self.filename = '' # may be it should be changed as relative path
        self.num_face = 0
        self.three_v = 0
        self.four_v = 0
        self.more_four_v = 0
        self.color = glm.vec3(1.0, 1.0, 1.0)

    def prepare(self, filestr):
        # prepare for VAO data
        for itr in filestr:
            if(itr == ''): break
            line = itr.strip()
            v = line.split(' ')
            
            remove_blank = {' ', ''}
            v = [x for x in v if x not in remove_blank]

            # check a line of data
            if not v:
                continue
            if v[0] == 'v':
                # vertex position list
                v.remove('v')
                v = list(map(float, v))
                self.vertex_position.append(v)

            elif v[0] == 'vn':
                # vertex normal list
                v.remove('vn')
                v = list(map(float, v))
                self.normal_vector.append(v)

            elif v[0] == 'f':
                v.remove('f')
                self.num_face += 1
                polygon = len(v)
                temp_vertex = []
                temp_normal = []
                # put vertex index and vertex normal index into temporary lists
                for str in v:
                    if '/' in str:
                        temp = str.split("/")
                        if len(temp) == 2:
                            temp_vertex.append(int(temp[0]) - 1)
                        else:
                            temp_vertex.append(int(temp[0]) - 1)
                            temp_normal.append(int(temp[2]) - 1)
                    else:
                        # has only vertex index
                        temp_vertex.append(int(str) - 1)

                # change all polygons in face into triangles
                if polygon > 3:
                    j = 1
                    if polygon == 4:
                        self.four_v += 1
                    else:
                        self.more_four_v += 1
                    while j < polygon - 1:
                        vit = []
                        nit = []
                        vit = [temp_vertex[0], temp_vertex[j], temp_vertex[j + 1]]
                        if temp_normal:
                            nit = [temp_normal[0], temp_normal[j], temp_normal[j + 1]]
                        self.vertex_index.append(vit)
                        self.normal_index.append(nit)
                        j += 1   
                else:
                    self.vertex_index.append(temp_vertex)
                    self.normal_index.append(temp_normal)
                    self.three_v += 1
    
    def setFileName(self, fileName):
        self.filename = fileName

    def setColor(self, color):
        self.color = color

class Node:
    def __init__(self, parent, scale, color):
        # hierarchy
        self.parent = parent
        self.children = []
        if parent is not None:
            parent.children.append(self)

        # transform
        self.transform = glm.mat4()
        self.global_transform = glm.mat4()

        # shape
        self.scale = scale
        self.color = color

    def set_transform(self, transform):
        self.transform = transform

    def update_tree_global_transform(self):
        if self.parent is not None:
            self.global_transform = self.parent.get_global_transform() * self.transform
        else:
            self.global_transform = self.transform

        for child in self.children:
            child.update_tree_global_transform()

    def get_global_transform(self):
        return self.global_transform
    def get_scale(self):
        return self.scale
    def get_color(self):
        return self.color

def load_shaders(vertex_shader_source, fragment_shader_source):
    # build and compile our shader program
    # ------------------------------------
    
    # vertex shader 
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)    # create an empty shader object
    glShaderSource(vertex_shader, vertex_shader_source) # provide shader source code
    glCompileShader(vertex_shader)                      # compile the shader object
    
    # check for shader compile errors
    success = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(vertex_shader)
        print("ERROR::SHADER::VERTEX::COMPILATION_FAILED\n" + infoLog.decode())
        
    # fragment shader
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)    # create an empty shader object
    glShaderSource(fragment_shader, fragment_shader_source) # provide shader source code
    glCompileShader(fragment_shader)                        # compile the shader object
    
    # check for shader compile errors
    success = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(fragment_shader)
        print("ERROR::SHADER::FRAGMENT::COMPILATION_FAILED\n" + infoLog.decode())

    # link shaders
    shader_program = glCreateProgram()               # create an empty program object
    glAttachShader(shader_program, vertex_shader)    # attach the shader objects to the program object
    glAttachShader(shader_program, fragment_shader)
    glLinkProgram(shader_program)                    # link the program object

    # check for linking errors
    success = glGetProgramiv(shader_program, GL_LINK_STATUS)
    if (not success):
        infoLog = glGetProgramInfoLog(shader_program)
        print("ERROR::SHADER::PROGRAM::LINKING_FAILED\n" + infoLog.decode())
        
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return shader_program    # return the shader program

# Keyboard Input
def key_callback(window, key, scancode, action, mods):
    global g_persp, g_single_mesh, g_wireframe
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action == GLFW_PRESS or action == GLFW_REPEAT:
            if key == GLFW_KEY_V:
                if g_persp:
                    g_persp = False
                else:
                    g_persp = True
            if key == GLFW_KEY_H:
                if g_single_mesh:
                    g_single_mesh = False
                    load_objs_for_h_mode("stoneman.obj")
                    load_objs_for_h_mode("groudon.obj")
                    load_objs_for_h_mode("ball.obj")
                    load_objs_for_h_mode("horse.obj")
                    load_objs_for_h_mode("skull.obj")
                else:
                    change_to_mesh()
            if key == GLFW_KEY_Z:
                if g_wireframe:
                    g_wireframe = False
                else:
                    g_wireframe = True
        
# mouse button clicked
def mouse_button_callback(window, button, action, mod):
    global g_mouse_left, g_mouse_right, g_last_x, g_last_y
    if button == GLFW_MOUSE_BUTTON_LEFT:
        if action == GLFW_PRESS:
            g_mouse_left = True
            g_last_x, g_last_y = glfwGetCursorPos(window)
        elif action == GLFW_RELEASE:
            g_mouse_left = False
    elif button == GLFW_MOUSE_BUTTON_RIGHT:
        if action == GLFW_PRESS:
            g_mouse_right = True
            g_last_x, g_last_y = glfwGetCursorPos(window)
        elif action == GLFW_RELEASE:
            g_mouse_right = False

# mouse cursor moving
def cursor_callback(window, xpos, ypos):
    global g_last_x, g_last_y, g_azimuth, g_elevation, g_cam_pos, g_target
    # Orbit
    if g_mouse_left and not g_mouse_right:
        if g_up_vector.y > 0:
            delta_x = xpos - g_last_x
            delta_y = ypos - g_last_y
        else:
            delta_x = g_last_x - xpos
            delta_y = ypos - g_last_y

        g_azimuth += delta_x * 0.5
        g_elevation += delta_y * 0.5      

        g_last_x = xpos
        g_last_y = ypos

    # Pan
    elif g_mouse_right and not g_mouse_left:
        if g_zoom > 0.001:
            delta_x = (g_last_x -xpos) * 0.05
            delta_y = (ypos - g_last_y) * 0.05

            du = delta_x * g_u_vec
            dv = delta_y * g_v_vec

            g_cam_pos += du + dv
            g_target += du + dv

            g_last_x = xpos
            g_last_y = ypos
        else:
            print("You cannot pan. Please zoom out first.")

# mouse wheel scroll
def scroll_callback(window, xoffset, yoffset):
    global g_zoom
    if xoffset == 0:
        if g_zoom - yoffset * 0.1 < 0.001:
            g_zoom = 0.001
        else:
            g_zoom -= yoffset * 0.1
    else:
        if g_zoom - xoffset * 0.1 < 0.001:
            g_zoom = 0.001
        else:
            g_zoom -= xoffset * 0.1

# drag file callback
def drop_callback(window, path):
    global g_obj_list, g_obj_VAO_list

    # change mode
    change_to_mesh()

    # file io
    lst = path[0].split('/')

    f = open(path[0], "rt")
    filestr = f.readlines()
    f.close()

    # pass this whole file data to Obj instance
    obj = ObjData()
    obj.prepare(filestr)
    obj.setFileName(lst[-1])
    g_obj_list.append(obj)
    g_obj_VAO_list.append(prepare_vao_obj(obj))

    # print Obj info
    print(f"Obj file name: {obj.filename}")
    print(f"Total number of faces: {obj.num_face}")
    print(f"Number of faces with 3 vertices: {obj.three_v}")
    print(f"Number of faces with 4 vertices: {obj.four_v}")
    print(f"Number of faces with more than 4 vertices: {obj.more_four_v}")

# def framebuffer_size_callback(window, width, height):
#     global g_Pers, g_Orth

#     glViewport(0, 0, width, height)

#     new_height = 10.
#     new_width = new_height * width/height

#     if g_persp:
#         g_Pers = glm.perspective(np.radians(45), new_width / new_height, .1, 100.0)
#     else:
#         g_Orth = glm.ortho(-1*new_width,1*new_width,-1*new_height,1*new_height,-1,1)


# Draw x-z grid lines
def prepare_vao_grid():
    # prepare vertex data (in main memory)
    arr = []
    for z in range(-100, 101):
        if z != 0:
            arr.extend([
                -10.0, 0.0, z / 10.0, 1.0, 1.0, 1.0,
                 10.0, 0.0, z / 10.0, 1.0, 1.0, 1.0
            ])

    
    for x in range(-100, 101):
        if x != 0:
            arr.extend([
                x / 10.0, 0.0, -10.0, 1.0, 1.0, 1.0,
                x / 10.0, 0.0,  10.0, 1.0, 1.0, 1.0
            ])
    
    vertices = glm.array(glm.float32, *arr)

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

# x-axis
def prepare_vao_x_axis():
    # prepare vertex data (in main memory)
    arr = [-10.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            10.0, 0.0, 0.0, 1.0, 0.0, 0.0 ]
    
    vertices = glm.array(glm.float32, *arr)

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

# z-axis
def prepare_vao_z_axis():
    # prepare vertex data (in main memory)
    arr = [ 0.0, 0.0, -10.0, 0.0, 1.0, 0.0,
            0.0, 0.0,  10.0, 0.0, 1.0, 0.0 ]
    
    vertices = glm.array(glm.float32, *arr)

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

# draw an object by using obj file
def prepare_vao_obj(obj):
    arr = []
    for i in range(0, len(obj.vertex_index)):
        if obj.normal_vector:
            arr.extend(obj.vertex_position[obj.vertex_index[i][0]])
            arr.extend(obj.normal_vector[obj.normal_index[i][0]])
            arr.extend(obj.vertex_position[obj.vertex_index[i][1]])
            arr.extend(obj.normal_vector[obj.normal_index[i][1]])
            arr.extend(obj.vertex_position[obj.vertex_index[i][2]])
            arr.extend(obj.normal_vector[obj.normal_index[i][2]])
        else:
            # make normal vector
            pt0 = obj.vertex_position[obj.vertex_index[i][0]]
            pt1 = obj.vertex_position[obj.vertex_index[i][1]]
            pt2 = obj.vertex_position[obj.vertex_index[i][2]]
            v0 = glm.vec3(pt1[0] - pt0[0], pt1[1] - pt0[1], pt1[2] - pt0[2])
            v1 = glm.vec3(pt2[0] - pt0[0], pt2[1] - pt0[1], pt2[2] - pt0[2])
            n = np.cross(v0, v1)

            arr.extend(pt0)
            arr.extend([n[0], n[1], n[2]])
            arr.extend(obj.vertex_position[obj.vertex_index[i][1]])
            arr.extend([n[0], n[1], n[2]])
            arr.extend(obj.vertex_position[obj.vertex_index[i][2]])
            arr.extend([n[0], n[1], n[2]])

    # print(arr)
    vertices = glm.array(glm.float32, *arr)

    # print(vertices)

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex normals
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO
    
def load_objs_for_h_mode(filename):
    global g_obj_hier_list, g_obj_hier_VAO_list
    # rel_path = os.path.join("./", "objects/", filename)
    rel_path = os.path.join("./", filename)
    print(rel_path)
    f = open(rel_path, "rt")
    filestr = f.readlines()
    f.close()

    # pass this whole file data to Obj instance
    obj = ObjData()
    obj.prepare(filestr)
    obj.setFileName(filename)
    g_obj_hier_list.append(obj)
    g_obj_hier_VAO_list.append(prepare_vao_obj(obj))

    # print Obj info
    print(f"Obj file name: {obj.filename}")
    # print(f"Total number of faces: {obj.num_face}")
    # print(f"Number of faces with 3 vertices: {obj.three_v}")
    # print(f"Number of faces with 4 vertices: {obj.four_v}")
    # print(f"Number of faces with more than 4 vertices: {obj.more_four_v}")

def change_to_mesh():
    global g_single_mesh, g_obj_hier_list, g_obj_hier_VAO_list
    g_single_mesh = True
    g_obj_hier_list = []
    g_obj_hier_VAO_list = []


def draw_node(vao, node, obj, VP, MVP_loc, M_loc, color_loc):
    M = node.get_global_transform() * glm.scale(node.get_scale())
    MVP = VP * node.get_global_transform() * glm.scale(node.get_scale())
    color = node.get_color()

    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glUniformMatrix4fv(M_loc, 1, GL_FALSE, glm.value_ptr(M))
    glUniform3f(color_loc, color.r, color.g, color.b)
    glDrawArrays(GL_TRIANGLES, 0, len(obj.vertex_index) * 3)
    

def main():
    global g_cam_pos, g_target, g_u_vec, g_v_vec, g_w_vec, g_elevation, g_azimuth, g_up_vector
    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)   # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE) # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(800, 800, '2019032160', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback);
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetCursorPosCallback(window, cursor_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetDropCallback(window, drop_callback)
    # glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)

    width, height = glfwGetFramebufferSize(window)
    glViewport(0, 0, width, height)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)

    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')
    M_loc = glGetUniformLocation(shader_program, 'M')
    view_pos_loc = glGetUniformLocation(shader_program, 'view_pos')
    factor_loc = glGetUniformLocation(shader_program, 'factor')
    color_loc = glGetUniformLocation(shader_program, 'color')
    
    # prepare vaos
    vao_grid = prepare_vao_grid()
    vao_x = prepare_vao_x_axis()
    vao_z = prepare_vao_z_axis()

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glUseProgram(shader_program)

        # polygon mode
        if g_wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # projection matrix
        if g_persp:
            P = glm.perspective(np.radians(45), 1, .1, 100.0)
        else:
            P = glm.ortho(-1, 1, -1, 1, -1, 1)

        # up-vector
        if np.cos(np.radians(g_elevation)) < 0:
            g_up_vector = glm.vec3(0.0, -1.0, 0.0)
        else:
            g_up_vector = glm.vec3(0.0, 1.0, 0.0)
            
        # u, v, w vectors
        g_w_vec = glm.normalize(g_cam_pos - g_target)
        g_u_vec = glm.normalize(glm.cross(g_up_vector, g_w_vec))
        g_v_vec = glm.cross(g_w_vec, g_u_vec)

        # set camera's position
        g_cam_pos.x = g_target.x + g_zoom * g_dist * np.cos(np.radians(g_azimuth)) * np.cos(np.radians(g_elevation))
        g_cam_pos.y = g_target.y + g_zoom * g_dist * np.sin(np.radians(g_elevation))
        g_cam_pos.z = g_target.z + g_zoom * g_dist * np.cos(np.radians(g_elevation)) * np.sin(np.radians(g_azimuth))

        V = glm.lookAt(g_cam_pos, g_target, g_v_vec)

        # current frame: P*V*I (now this is the world frame)
        I = glm.mat4()

        M = glm.mat4()
        MVP = P*V*M

        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glUniformMatrix4fv(M_loc, 1, GL_FALSE, glm.value_ptr(M))
        glUniform3f(view_pos_loc, g_cam_pos.x, g_cam_pos.y, g_cam_pos.z)
        glUniform1f(factor_loc, 1.0)
        glUniform3f(color_loc, 1.0, 1.0, 1.0)

        # draw xz grid
        glBindVertexArray(vao_grid)
        glDrawArrays(GL_LINES, 0, 800)

        # change color and draw x-axis && z-axis
        glUniform3f(color_loc, 1.0, 0.0, 0.0)
        glBindVertexArray(vao_x)
        glDrawArrays(GL_LINES, 0, 2)

        glUniform3f(color_loc, 0.0, 1.0, 0.0)
        glBindVertexArray(vao_z)
        glDrawArrays(GL_LINES, 0, 2)

        # single mesh mode
        if g_single_mesh:     
            if len(g_obj_VAO_list) != 0:
                glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
                glUniformMatrix4fv(M_loc, 1, GL_FALSE, glm.value_ptr(M))
                glUniform1f(factor_loc, 0.1)
                glUniform3f(color_loc, 1.0, 1.0, 1.0)
                glBindVertexArray(g_obj_VAO_list[-1])
                glDrawArrays(GL_TRIANGLES, 0, len(g_obj_list[-1].vertex_index) * 3)
        
        # hierarchical mode
        else:
            if len(g_obj_hier_VAO_list) != 0:
                stoneman = Node(None, glm.vec3(1.0, 1.0, 1.0), glm.vec3(0.82745098039, 0.77647058823, 0.65098039215))
                groudon = Node(stoneman, glm.vec3(1.0, 1.0, 1.0), glm.vec3(0.64705882352, 0.16470588235, 0.16470588235))
                ball = Node(stoneman, glm.vec3(1.0, 1.0, 1.0), glm.vec3(0.32745098039, 0.32745098039, 0.32745098039))
                horse = Node(groudon, glm.vec3(1.0, 1.0, 1.0), glm.vec3(0.43529411764, 0.30980392156, 0.15686274509))
                skull = Node(groudon, glm.vec3(1.0, 1.0, 1.0), glm.vec3(1.0, 1.0, 1.0))
                
                t = glfwGetTime()

                stoneman.set_transform(glm.translate(glm.vec3(3 * glm.sin(t), 0, 0)))
                groudon.set_transform(glm.rotate(t, glm.vec3(0, 1, 0)) * glm.translate(glm.vec3(1.0, 0.0, 1.0)))
                ball.set_transform(glm.rotate(t, glm.vec3(0, 1, 0)) * glm.translate(glm.vec3(2.0, 1.0, -3.0)))
                horse.set_transform(glm.translate(glm.vec3(5 * glm.sin(t), 0, 0)) * glm.translate(glm.vec3(-1.5, 0.0, 0.0)))
                skull.set_transform(glm.rotate(t, glm.vec3(0,0,1)) * glm.translate(glm.vec3(2.0, -1.0, 1.5)))

                stoneman.update_tree_global_transform()

                glUniform1f(factor_loc, 0.1)
                draw_node(g_obj_hier_VAO_list[0], stoneman, g_obj_hier_list[0], P * V, MVP_loc, M_loc, color_loc)
                draw_node(g_obj_hier_VAO_list[1], groudon, g_obj_hier_list[1], P * V, MVP_loc, M_loc, color_loc)
                draw_node(g_obj_hier_VAO_list[2], ball, g_obj_hier_list[2], P * V, MVP_loc, M_loc, color_loc)
                draw_node(g_obj_hier_VAO_list[3], horse, g_obj_hier_list[3], P * V, MVP_loc, M_loc, color_loc)
                draw_node(g_obj_hier_VAO_list[4], skull, g_obj_hier_list[4], P * V, MVP_loc, M_loc, color_loc)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()