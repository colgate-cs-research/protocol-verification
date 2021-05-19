j = 6
for i in range(1,j):
    name = "lb1000_"+str(i)+"_2.txt"
    with open (name,"w") as efile:
        efile.write("~\n")