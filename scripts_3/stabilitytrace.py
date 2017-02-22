import sys
from os import listdir
from math import sqrt
from statistics import stdev
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def extractValues(benchmark):
    f = open(benchmark, 'r')
    TPS = []
    RAVG = []
    RSTD = []
    flag = 0
    for line in f:
        if line == "Total Statistics\n":
            flag = 1
        elif flag == 1:
            if "Period" in line:
                tokens = line.split()
                TPS.append(float(tokens[3]))
                RAVG.append(float(tokens[8]))
                RSTD.append(float(tokens[9]))
                flag = 0
    return TPS, RAVG, RSTD 
            
benchmarkPath = sys.argv[1]
clientNo = 3
rate = 30

TPS, RAVG, RSTD = extractValues(benchmarkPath + "/stability_1.log")
RSTD = [a*a for a in RSTD]
for client in range(2, clientNo + 1):
    tps, responseAvg, responseStd = extractValues(benchmarkPath + "/stability_{}.log".format(client))
    TPS = [a + b for a, b in zip(TPS, tps)]
    RAVG = [(a + b)/clientNo for a, b in zip(RAVG, responseAvg)]
    RSTD = [a + b*b for a, b in zip(RSTD, responseStd)]
RSTD = [sqrt(a) for a in RSTD]

print "M/M/1"
print "Average TPS: ", sum(TPS)/float(len(TPS))
print "Max TPS: ", max(TPS)
print "Average RT: ", sum(RAVG)/(float(len(RAVG))*1000)
print "Average RT std: ", sqrt(sum(a/1000*a/1000 for a in RSTD)/float(len(RSTD)))

# sample
TPS = [TPS[i] for i in range(0, len(TPS), rate)]
RAVG = [RAVG[i]/1000 for i in range(0, len(RAVG), rate)]
RSTD = [RSTD[i]/1000 for i in range(0, len(RSTD), rate)]

print "----------------------"
print "After sampling"
print "Average TPS: ", sum(TPS)/float(len(TPS))
print "Max TPS: ", max(TPS)
print "Average RT: ", sum(RAVG)/float(len(RAVG))
print "Average RT std: ", sqrt(sum(a*a for a in RSTD)/float(len(RSTD)))

