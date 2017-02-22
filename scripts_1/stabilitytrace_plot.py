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

#print TPS
#print RAVG
#print RSTD

# sample
TPS = [TPS[i] for i in range(0, len(TPS), rate)]
RAVG = [RAVG[i]/1000 for i in range(0, len(RAVG), rate)]
RSTD = [RSTD[i]/1000 for i in range(0, len(RSTD), rate)]

# plotting
seconds = range(0, len(TPS)*rate, rate)
minutes = [float(a)/60 for a in seconds]
ticks = range(0, 61, 5)

# throughput
plt.figure(1)
plt.plot(minutes, TPS, '-')
plt.xticks(ticks)
plt.ylim(ymin=0)
plt.grid()
plt.xlabel('Time in mins')
plt.ylabel('TPS')
#plt.title('Throughput')
plt.savefig('stabilitytrace_throughput.png')

plt.figure(2)
plt.errorbar(minutes, RAVG, yerr=RSTD, fmt='-', ecolor='r')
plt.xticks(ticks)
plt.ylim(ymin=0)
plt.grid()
plt.xlabel('Time in mins')
plt.ylabel('Response time in msecs')
#plt.title('Response time')
plt.savefig('stabilitytrace_response_time.png')

