from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np

### global variables ###

# about camera
g_cam_pos = glm.vec3(0.3, 0.3, 0.3)
g_target = glm.vec3(0.0, 0.0, 0.0)
g_azimuth = 45.0
g_elevation = 45.0
g_dist = glm.distance(g_cam_pos, g_target)
g_persp = True
g_ortho = False

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

########################

g_vertex_shader_src = '''
#version 330 core

layout (location = 0) in vec3 vin_pos; 
layout (location = 1) in vec3 vin_color; 

out vec4 vout_color;

uniform mat4 MVP;

void main()
{
    // 3D points in homogeneous coordinates
    vec4 p3D_in_hcoord = vec4(vin_pos.xyz, 1.0);

    gl_Position = MVP * p3D_in_hcoord;

    vout_color = vec4(vin_color, 1.);
}
'''

g_fragment_shader_src = '''
#version 330 core

in vec4 vout_color;

out vec4 FragColor;

void main()
{
    FragColor = vout_color;
}
'''

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
    global g_persp, g_ortho
    if key==GLFW_KEY_ESCAPE and action==GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action==GLFW_PRESS or action==GLFW_REPEAT:
            if key==GLFW_KEY_V:
                if g_persp:
                    g_persp = False
                    g_ortho = True
                else:
                    g_persp = True
                    g_ortho = False
        
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
    for z in range(-30, 31):
        if z != 0:
            arr.extend([
                -3.0, 0.0, z / 10.0, 1.0, 1.0, 1.0,
                 3.0, 0.0, z / 10.0, 1.0, 1.0, 1.0
            ])
        else:
            arr.extend([
                -3.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                 3.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            ])
    
    for x in range(-30, 31):
        if x != 0:
            arr.extend([
                x / 10.0, 0.0, -3.0, 1.0, 1.0, 1.0,
                x / 10.0, 0.0,  3.0, 1.0, 1.0, 1.0
            ])
        else:
            arr.extend([
                0.0, 0.0, -3.0, 0.0, 1.0, 0.0,
                0.0, 0.0,  3.0, 0.0, 1.0, 0.0,
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

# Draw a cube
def prepare_vao_cube():
    # prepare vertex data (in main memory)
    # 36 vertices for 12 triangles
    vertices = glm.array(glm.float32,
        # position            color
        -0.1 ,  0.1 ,  0.1 ,  1, 0, 0, # v0
         0.1 , -0.1 ,  0.1 ,  1, 0, 0, # v2
         0.1 ,  0.1 ,  0.1 ,  1, 0, 0, # v1
                    
        -0.1 ,  0.1 ,  0.1 ,  1, 0, 0, # v0
        -0.1 , -0.1 ,  0.1 ,  1, 0, 0, # v3
         0.1 , -0.1 ,  0.1 ,  1, 0, 0, # v2
                    
        -0.1 ,  0.1 , -0.1 ,  1, .5, 0, # v4
         0.1 ,  0.1 , -0.1 ,  1, .5, 0, # v5
         0.1 , -0.1 , -0.1 ,  1, .5, 0, # v6
                    
        -0.1 ,  0.1 , -0.1 ,  1, .5, 0, # v4
         0.1 , -0.1 , -0.1 ,  1, .5, 0, # v6
        -0.1 , -0.1 , -0.1 ,  1, .5, 0, # v7
                    
        -0.1 ,  0.1 ,  0.1 ,  1, 1, 0, # v0
         0.1 ,  0.1 ,  0.1 ,  1, 1, 0, # v1
         0.1 ,  0.1 , -0.1 ,  1, 1, 0, # v5
                    
        -0.1 ,  0.1 ,  0.1 ,  1, 1, 0, # v0
         0.1 ,  0.1 , -0.1 ,  1, 1, 0, # v5
        -0.1 ,  0.1 , -0.1 ,  1, 1, 0, # v4
 
        -0.1 , -0.1 ,  0.1 ,  1, 1, 1, # v3
         0.1 , -0.1 , -0.1 ,  1, 1, 1, # v6
         0.1 , -0.1 ,  0.1 ,  1, 1, 1, # v2
                    
        -0.1 , -0.1 ,  0.1 ,  1, 1, 1, # v3
        -0.1 , -0.1 , -0.1 ,  1, 1, 1, # v7
         0.1 , -0.1 , -0.1 ,  1, 1, 1, # v6
                    
         0.1 ,  0.1 ,  0.1 ,  0, 0, 1, # v1
         0.1 , -0.1 ,  0.1 ,  0, 0, 1, # v2
         0.1 , -0.1 , -0.1 ,  0, 0, 1, # v6
                    
         0.1 ,  0.1 ,  0.1 ,  0, 0, 1, # v1
         0.1 , -0.1 , -0.1 ,  0, 0, 1, # v6
         0.1 ,  0.1 , -0.1 ,  0, 0, 1, # v5
                    
        -0.1 ,  0.1 ,  0.1 ,  0, 1, 0, # v0
        -0.1 , -0.1 , -0.1 ,  0, 1, 0, # v7
        -0.1 , -0.1 ,  0.1 ,  0, 1, 0, # v3
                    
        -0.1 ,  0.1 ,  0.1 ,  0, 1, 0, # v0
        -0.1 ,  0.1 , -0.1 ,  0, 1, 0, # v4
        -0.1 , -0.1 , -0.1 ,  0, 1, 0, # v7
    )

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
    # glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)

    width, height = glfwGetFramebufferSize(window)
    glViewport(0, 0, width, height)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)

    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')
    
    # prepare vaos
    vao_grid = prepare_vao_grid()
    vao_cube = prepare_vao_cube()

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
        MVP = P*V*I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))

        # draw xz grid && xz axis
        glBindVertexArray(vao_grid)
        glDrawArrays(GL_LINES, 0, 244)

        glBindVertexArray(vao_cube)
        # glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glDrawArrays(GL_TRIANGLES, 0, 36)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()