f = open("sphere-tri-quad.obj", "rt")
vertex_position = []
normal_coord = []
vertex_index = []
normal_index = []

check = f.readlines()

i = 0
three = 0
four = 0
etc = 0

for itr in check:
    if(itr == ''): break
    line = itr.strip()
    v = line.split(' ')
    # print(v)
    if v[0] == 'v':
        v.remove('v')
        v = list(map(float, v))
        v.extend([1.0, 0.0, 0.0]) # color as red
        vertex_position.append(v)
    elif v[0] == 'f':
        v.remove('f')
        polygon = len(v)
        temp_vertex = []
        temp_normal = []
        # put vertex index and vertex normal index into temporary lists
        for str in v:
            temp = str.split("/")
            if len(temp) == 2:
                temp_vertex.append(int(temp[0]))
            else:
                temp_vertex.append(int(temp[0]))
                temp_normal.append(int(temp[2]))
        
        print(temp_vertex)
        print(temp_normal)

        # change all polygons in face into triangles
        if polygon > 3:
            j = 0
            while j < polygon - 1:
                vit = []
                nit = []
                # first triangle
                if j == 0:
                    vit = [temp_vertex[j], temp_vertex[j + 1], temp_vertex[j + 2]]
                    nit = [temp_normal[j], temp_normal[j + 1], temp_normal[j + 2]]
                    j += 1
                else:
                    vit = [temp_vertex[j], temp_vertex[j + 1], temp_vertex[0]]
                    nit = [temp_normal[j], temp_normal[j + 1], temp_normal[0]]
                vertex_index.append(vit)
                normal_index.append(nit)
                j += 1   
        else:
            vertex_index.append(temp_vertex)
            normal_index.append(temp_normal)
                
        if polygon == 3:
            three += 1
        elif polygon == 4:
            four += 1
        else:
            etc += 1

        print(polygon)
        print("{}th face list".format(i))
        print("vertex index list")
        print(temp_vertex)
        print("vertex normal index list")
        print(temp_normal)


        # vertex_index.append(v)
        i += 1
    elif v[0] == 'vn':
        v.remove('vn')
        v = list(map(float, v))
        normal_coord.append(v)


# while True:
    
#     # check = f.readline()
#     if(check == ''): break
#     line = check.strip()

#     v = line.split(' ')

#     if v[0] == 'v':
#         v.remove('v')
#         vertex_position.append(v)
#     elif v[0] == 'f':
#         v.remove('f')
#         vertex_index.append(v)
#     elif v[0] == 'vn':
#         v.remove('vn')
#         normal_coord.append(v)

print("vertex list")
print(vertex_position)


print("vertex normal list")
print(normal_coord)

print("vertex index list")
print(vertex_index)

print("normal index list")
print(normal_index)

print("vertex list count:")
print(len(vertex_position))
print("vertex normal list count:")
print(len(normal_coord))
print("vertex index list count:")
print(len(vertex_index))
print("normal index list count:")
print(len(normal_index))

# print("triangle: {}, rectangle: {}, etc: {}".format(three, four, etc))

f.close()