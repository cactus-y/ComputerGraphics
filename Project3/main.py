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
g_line = True
g_animate = False

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

# about bvh file io
g_node_list = []
g_line_vao_list = []
g_box_vao_list = []

g_frame_list = []
g_frameTime_list = []

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

class Node:
    def __init__(self, parent):
        self.offset = []
        self.rotation = []
        self.position = []
        self.parent = parent
        self.name = ""
        self.channel = 0
        self.chanList = []
        self.endsite = []
        self.order = []
        self.children = []
        self.joint_transform = glm.mat4()
        self.global_transform = glm.mat4()
        self.shape_transform = glm.mat4()
        if parent is not None:
            parent.children.append(self)
    
    def setName(self, name):
        self.name = name
    
    # def setParent(self, node):
    #     self.parent = node

    def setJointTransform(self, joint):
        self.joint_transform = joint

    def updateGlobal(self):
        if self.parent is not None:
            self.global_transform = self.parent.global_transform * glm.translate(glm.vec3(self.offset[0], self.offset[1], self.offset[2])) * self.joint_transform
        else:
            self.global_transform = glm.translate(glm.vec3(self.offset[0], self.offset[1], self.offset[2])) * self.joint_transform

        for child in self.children:
            child.updateGlobal()
    
    def setOffset(self, offset):
        self.offset = offset
    
    def setOrder(self, order):
        self.order = order
    
    def setEndsite(self, endsite):
        self.endsite = endsite
    
    def addRotation(self, rotation):
        self.rotation.append(rotation)

    # may be only for root
    def addPosition(self, position):
        self.position.append(position)
    
    def setChannel(self, channel):
        self.channel = channel
    
    def setChanList(self, chanList):
        self.chanList = chanList

    # def setShapeTransform(self):
        
    

def parsing(inputStr):
    line = inputStr.strip()
    l = line.split(' ')

    # remove blank
    remove_blank = {' ', ''}
    l = [x for x in l if x not in remove_blank]
    return l


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
    global g_persp, g_line, g_animate
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action == GLFW_PRESS or action == GLFW_REPEAT:
            if key == GLFW_KEY_V:
                g_persp = not g_persp
            if key == GLFW_KEY_1:
                if not g_line:
                    g_line = True
            if key == GLFW_KEY_2:
                if g_line:
                    g_line = False
            if key == GLFW_KEY_SPACE:
                g_animate = not g_animate
                # reset stickman's node data into rest pose
        
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
    global g_node_list, g_frame_list, g_frameTime_list, g_animate

    if g_animate:
        g_animate = False

    nodeList = []
    frame = 0
    frameTime = 0.

    # file io
    lst = path[0].split('/')
    filename = lst[-1]

    f = open(path[0], "rt")
    filestr = f.readlines()
    f.close()

    isHierarchy = False

    if filestr[0] == '':
        print("Invalid bvh file.")
        return
    else:
        temp = parsing(filestr[0])
        if temp[0] == 'HIERARCHY':
            isHierarchy = True
        else:
            print("Invalid bvh file.")
            return

    # parsing bvh file
    nodeIdx = 0
    endsite = False
    stack = []

    for itr in filestr:
        # if not stack:
        #     nodeIdx = 0
        # else:
        #     if endsite:
        #         nodeIdx = len(stack) - 2
        #     else:
        #         nodeIdx = len(stack) - 1
        if not stack:
            nodeIdx = 0
        else:
            nodeIdx = stack[-1]
        
        if itr == '':
            break
        l = parsing(itr)

        if not l:
            continue
       
        if isHierarchy:
            # HIERARCHY
            if l[0] == 'ROOT':
                node = Node(None)
                node.setName(l[1])
                nodeList.append(node)
            elif l[0] == 'JOINT':
                node = Node(nodeList[nodeIdx])
                node.setName(l[1])
                nodeList.append(node)
            elif l[0] == '{':
                stack.append(len(nodeList) - 1)
            elif l[0] == '}':
                stack.pop()
            elif l[0] == 'OFFSET':
                l.remove('OFFSET')
                l = list(map(float, l))
                if endsite:
                    nodeList[nodeIdx].setEndsite(l)
                    endsite = False
                else:
                    nodeList[nodeIdx].setOffset(l)
            elif l[0] == 'CHANNELS':
                channel = int(l[1])
                nodeList[nodeIdx].setChannel(channel)
                del l[0]
                del l[0]
                # now there are only channels
                nodeList[nodeIdx].setChanList(l)
            elif l[0] == 'End' and l[1] == 'Site':
                endsite = True
            elif l[0] == 'MOTION':
                isHierarchy = False
                continue
        else:
            # MOTION
            if l[0] == 'Frames:':
                frame = int(l[1])
            elif l[0] == 'Frame' and l[1] == 'Time:':
                frameTime = float(l[2])
            else:
                # motions
                # check motion coordinates split by \t
                if len(l) == 1:
                    l = l[0].split('\t')
                i = 0
                pos = [0., 0., 0.]
                rot = [0., 0., 0.]
                order = []
                for node in nodeList:
                    channel = node.channel
                    for idx in range(channel):
                        num = float(l[i + idx])
                        if node.chanList[idx].upper() == 'XPOSITION':
                            pos[0] = num
                        elif node.chanList[idx].upper() == 'YPOSITION':
                            pos[1] = num
                        elif node.chanList[idx].upper() == 'ZPOSITION':
                            pos[2] = num
                        elif node.chanList[idx].upper() == 'XROTATION':
                            rot[0] = num
                            order.append(0)
                        elif node.chanList[idx].upper() == 'YROTATION':
                            rot[1] = num
                            order.append(1)
                        elif node.chanList[idx].upper() == 'ZROTATION':
                            rot[2] = num
                            order.append(2)
                    i += channel
                    if node.parent == None:
                        node.addPosition(pos)
                        node.addRotation(rot)
                        node.setOrder(order)
                    else:
                        node.addRotation(rot)
                        node.setOrder(order)
    
    g_node_list.append(nodeList)
    g_frame_list.append(frame)
    g_frameTime_list.append(frameTime)

    # set initial shape transformation

    # print bvh file info
    print(f"bvh file name: {filename}")
    print(f"Number of frames: {frame}")
    print(f"FPS (1/FrameTime): {1 / frameTime}")
    print(f"Number of joints: {len(nodeList)}")
    print("List of all joint names:")
    for idx in range(len(nodeList)):
        print(nodeList[idx].name)


    # print out
    # for nd in g_node_list[-1]:
    #     print()
    #     print(f"node name: {nd.name}")
    #     if nd.parent:
    #         print(f"parent: {nd.parent.name}")
    #     else:
    #         print(f"parent: None")
    #     print(f"offset: (x, y, z): ({nd.offset[0]}, {nd.offset[1]}, {nd.offset[2]})")
    #     i = 1
    #     for rot in nd.rotation:
    #         print(f"{i}th rotation: (x, y, z): ({rot[0]}, {rot[1]}, {rot[2]})")
    #         i += 1



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

# 
def prepare_vao_line():
    # prepare vertex data (in main memory)
    arr = [ 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.1, 0.0, 0.0, 1.0, 0.0 ]
    
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


def draw_node(vao, node, VP, MVP_loc, color_loc):
    MVP = VP * node.global_transform * node.shape_transform
    color = glm.vec3(0.0, 0.0, 0.5)

    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glUniform3f(color_loc, color.r, color.g, color.b)
    glDrawArrays(GL_LINES, 0, 2)



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
    vao_line = prepare_vao_line()

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glUseProgram(shader_program)
        
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


        # if bvh is given as input
        if len(g_node_list) != 0:
            nodeList = g_node_list[-1]
            frame = g_frame_list[-1]
            frameTime = g_frameTime_list[-1]

            # rest pose
            if g_line:
                for node in nodeList:
                    node.setJointTransform()
                nodeList[0].updateGlobal()
                for node in nodeList:
                    draw_node(vao_line, node, P*V, MVP_loc, color_loc)

            while(g_animate):
                for i in range(frame):
                    if g_line:
                        for node in nodeList:
                            # update joint transformation and global transformation
                            draw_node(vao_line, node, P*V, MVP_loc, color_loc)
                            # use sleep function to set frame time
                    
                


        

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()