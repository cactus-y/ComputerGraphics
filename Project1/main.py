from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np

g_cam_ang = 0.
g_cam_height = 0.
g_tri_x = 0.
g_tri_y = 0.
g_tri_z = 0.

g_last_x = 0.
g_last_y = 0.

g_elevation = 0.
g_azimuth = 0.

g_mouse_x = 0.
g_mouse_y = 0.

g_mouse_pressed = False


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


def key_callback(window, key, scancode, action, mods):
    global g_cam_ang, g_cam_height, g_tri_x, g_tri_y, g_tri_z
    if key==GLFW_KEY_ESCAPE and action==GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action==GLFW_PRESS or action==GLFW_REPEAT:
            if key==GLFW_KEY_1:
                g_cam_ang += np.radians(-10)
            elif key==GLFW_KEY_3:
                g_cam_ang += np.radians(10)
            elif key==GLFW_KEY_2:
                g_cam_height += .1
            elif key==GLFW_KEY_W:
                g_cam_height += -.1
            # Q, A, E, D, Z, X for the triangle translation
            elif key==GLFW_KEY_Q:
                g_tri_x += .1
            elif key==GLFW_KEY_A:
                g_tri_x -= .1
            elif key==GLFW_KEY_E:
                g_tri_y += .1
            elif key==GLFW_KEY_D:
                g_tri_y -= .1
            elif key==GLFW_KEY_Z:
                g_tri_z += .1
            elif key==GLFW_KEY_X:
                g_tri_z -= .1
        
def mouse_button_callback(window, button, action, mod):
    global g_mouse_pressed, g_last_x, g_last_y
    if button == GLFW_MOUSE_BUTTON_LEFT:
        if action == GLFW_PRESS:
            g_mouse_pressed = True
            g_last_x, g_last_y = glfwGetCursorPos(window)
            print("Left mouse button is pressed.")
            print("Current position of x and y is: (%d, %d)"%(g_last_x, g_last_y))
        elif action == GLFW_RELEASE:
            g_mouse_pressed = False
            print("Left mouse button is released")

def cursor_callback(window, xpos, ypos):
    global g_mouse_pressed, g_last_x, g_last_y, g_azimuth, g_elevation, g_cam_ang, g_cam_height
    if g_mouse_pressed:
        delta_x = xpos - g_last_x
        delta_y = ypos - g_last_y
        print("(delta_x, delta_y) is (%f, %f)"%(delta_x, delta_y))

        g_azimuth = delta_x * 0.005
        g_elevation = delta_y * 0.005
        print("g_azimuth is %f"%g_azimuth)
        print("g_elevation is %f"%g_elevation)

        g_cam_ang += np.radians(g_azimuth)
        g_cam_height += np.radians(g_elevation)
    
    

def prepare_vao_triangle():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
        # position        # color
         0.0, 0.0, 0.0,  1.0, 0.0, 0.0, # v0
         0.5, 0.0, 0.0,  0.0, 1.0, 0.0, # v1
         0.0, 0.5, 0.0,  0.0, 0.0, 1.0, # v2
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

def prepare_vao_frame():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
        # position        # color
         0.0, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis start
         1.0, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis end 
         0.0, 0.0, 0.0,  0.0, 1.0, 0.0, # y-axis start
         0.0, 1.0, 0.0,  0.0, 1.0, 0.0, # y-axis end 
         0.0, 0.0, 0.0,  0.0, 0.0, 1.0, # z-axis start
         0.0, 0.0, 1.0,  0.0, 0.0, 1.0, # z-axis end 
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

def prepare_vao_grid():
    # prepare vertex data (in main memory)
    
    arr = []
    for z in range(-20, 21):
        if z != 0:
            arr.extend([
                -5.0, 0.0, z / 10.0, 1.0, 1.0, 1.0,
                 5.0, 0.0, z / 10.0, 1.0, 1.0, 1.0
            ])
        else:
            arr.extend([
                -5.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                 5.0, 0.0, 0.0, 1.0, 0.0, 0.0
            ])
    
    for x in range(-20, 21):
        if x != 0:
            arr.extend([
                x / 10.0, 0.0, -5.0, 1.0, 1.0, 1.0,
                x / 10.0, 0.0,  5.0, 1.0, 1.0, 1.0
            ])
        else:
            arr.extend([
                0.0, 0.0, -5.0, 0.0, 0.0, 1.0,
                0.0, 0.0,  5.0, 0.0, 0.0, 1.0
            ])

    # arr.extend([
    #     0.0, -5.0, 0.0, 0.0, 1.0, 0.0,
    #     0.0,  5.0, 0.0, 0.0, 1.0, 0.0
    # ])
    
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


 
def main():
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

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)

    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')
    
    # prepare vaos
    vao_triangle = prepare_vao_triangle()
    # vao_frame = prepare_vao_frame()

    vao_grid = prepare_vao_grid()

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glUseProgram(shader_program)

        # projection matrix
        # use orthogonal projection (we'll see details later)
        P = glm.ortho(-1,1,-1,1,-1,1)

        # view matrix
        # rotate camera position with g_cam_ang / move camera up & down with g_cam_height
        V = glm.lookAt(glm.vec3(.1*np.cos(g_cam_ang)*np.cos(g_cam_height),.1*np.sin(g_cam_height),.1*np.sin(g_cam_ang)*np.cos(g_cam_height)), glm.vec3(0,0,0), glm.vec3(0,1,0))
        
        # camera y-coordinate is weird... #

        # current frame: P*V*I (now this is the world frame)
        I = glm.mat4()
        MVP = P*V*I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))

        # draw current frame
        # glBindVertexArray(vao_frame)
        # glDrawArrays(GL_LINES, 0, 6)



        # draw xz grid && xz axis
        glBindVertexArray(vao_grid)
        glDrawArrays(GL_LINES, 0, 165)

        # animating
        t = glfwGetTime()

        # rotation
        th = np.radians(t*90)
        R = glm.rotate(th, glm.vec3(0,0,1))

        # tranlation
        T = glm.translate(glm.vec3(np.sin(t), .2, 0.))

        # key_input translation
        ki_t = glm.translate(glm.vec3(g_tri_x, g_tri_y, g_tri_z))

        # scaling
        S = glm.scale(glm.vec3(np.sin(t), np.sin(t), np.sin(t)))

        u = glm.translate(glm.vec3(0, 0, 0))

        M = u
        # M = T
        # M = S
        # M = R @ T
        # M = T @ R

        # current frame: P*V*M
        MVP = P*V*ki_t*M
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))

        # draw triangle w.r.t. the current frame
        glBindVertexArray(vao_triangle)
        glDrawArrays(GL_TRIANGLES, 0, 3)

        # draw current frame
        glBindVertexArray(vao_grid)
        glDrawArrays(GL_LINES, 0, 6)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()
