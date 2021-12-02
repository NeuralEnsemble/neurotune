"""
Due to the first column of 100pA_1.csv only having 3 significant digits,
this generates the file with correct values in column for time 
"""

f = open("100pA_1.csv")
f2 = open("100pA_1a.csv", "w")
t = 0
dt = 5e-5
for l in f:
    l = l.strip()
    v = l.split(",")[1]
    s = "%s,\t%s" % (t, v)
    print("[%s]  -->  [%s]" % (l, s))
    f2.write(s + "\n")
    t += dt
f.close()
f2.close()
