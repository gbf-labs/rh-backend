import sys
fname = sys.argv[1]
datas = str(sys.argv[2])

with open(fname, "w") as f:
    for line in datas.split("\\n"):

        f.write(line+"\n")
