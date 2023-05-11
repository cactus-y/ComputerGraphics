f = open("cylinder-tri.obj", "rt")
vlist = []
vnlist = []
flist = []
tlist = []

while True:
    
    check = f.readline()
    if(check == ''): break
    line = check.strip()

    v = line.split(' ')

    if v[0] == 'v':
        v.remove('v')
        vlist.append(v)
    elif v[0] == 'f':
        v.remove('f')
        flist.append(v)
    elif v[0] == 'vn':
        v.remove('vn')
        vnlist.append(v)

print("vertex list")
print(vlist)


print("vertex normal list")
print(vnlist)

print("face list")
print(flist)

print("vertex list count:")
print(len(vlist))
print("vertex normal list count:")
print(len(vnlist))
print("face list count:")
print(len(flist))


f.close()