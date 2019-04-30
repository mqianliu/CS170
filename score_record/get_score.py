input = open("score1.txt","r")
s = 0
for line in input:
    l = line.split()
    if len(l) > 1 and l[1] == 'Score:':
        print(l[2])
        s += (float)(l[2])
print(s)
print(s/24)
