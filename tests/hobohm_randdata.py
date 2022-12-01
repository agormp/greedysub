import random, sys
nseq = int(sys.argv[1]) + 1
for i in range(1,nseq):
    for j in range(i,nseq):
        similarity = random.random()
        print ("seq%s seq%s %f" % (i,j,similarity))
