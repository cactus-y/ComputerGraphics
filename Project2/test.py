f = open("test.obj", "rt")
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
        # v.remove('\n')
        vlist.append(v)
    elif v[0] == 'f':
        v.remove('f')
        # v.remove('\n')
        flist.append(v)
    elif v[0] == 'vn':
        v.remove('vn')
        # v.remove('\n')
        vnlist.append(v)

print("vertex list")
print(vlist)

print("face list")
print(flist)

print("vertex normal list")
print(vnlist)

f.close()