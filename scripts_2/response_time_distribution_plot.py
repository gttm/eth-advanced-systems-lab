import sys
from statistics import stdev, mean
from numpy import percentile
import random
import numpy as np
from scipy.stats import gamma
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def extractMemaslapValues(benchmark):
    f = open(benchmark, 'r')
    responseTimeAll = []
    flag = 0
    for line in f:
        if "Log2 Dist:" in line:
            line = next(f)
            while not line.startswith("\n"):
                line = line.strip().split()
                exp = int(line[0].split(':')[0])
                counts = [int(i) for i in line[1:]]
                for c in counts:
                    bucket = 2**exp*(3.0/4.0)
                    responseTimeAll += [bucket for i in range(c)]
                    '''
                    bucketMin = 2**(exp - 1)
                    bucketMax = 2**exp
                    responseTimeAll += [random.randrange(bucketMin, bucketMax + 1) for i in range(c)]
                    '''
                    exp += 1
                line = next(f)
    return responseTimeAll


def extractMWValues(benchmark):
    def lineToSec(line):
        time = [int(i) for i in line.split()[3].split(":")]
        extra = int(line.split()[1].split(',')[0])*24*60*60
        if line[4] == "PM":
            extra += 12*60*60
        return int(extra + time[0]%12*60*60 + time[1]*60 + time[2])

    f = open(benchmark, 'r')
    line = next(f)
    start = lineToSec(line)

    flag = 0
    startRep = 0
    repetition = 1
    tMWAll = []
    tQueueAll = []
    tServerAll = []
    for line in f:
        if flag == 0 and "M ch.ethz" in line:
            sec = lineToSec(line)
            if sec >= start + setupTime:
                flag = 1
                startRep = sec
        if flag == 1 and "WriteHandler" in line:
            print "Set after setupTime"
        if flag == 1 and "ReadHandler" in line:
            sec = lineToSec(line)
            if sec > startRep + repetitionSec:
                startRep = sec
                repetition += 1
                if repetition > repetitionNo:
                    return tMWAll, tQueueAll, tServerAll
            line = next(f)
            metrics = [int(i.strip(",")) for i in line.split()[1:]]
            tMWAll.append(metrics[1])
            tQueueAll.append(metrics[2])
            tServerAll.append(metrics[3])

    print "Only finished {} complete repetitions for {}".format(repetition - 1, benchmark)
    return tMWAll, tQueueAll, tServerAll


if len(sys.argv) != 2:
    print "Usage: python {} <logfile_directory>".format(sys.argv[0])
    exit(0)

benchmarkPath = sys.argv[1]
repetitionNo = 3
repetitionSec = 30
setupTime = 40
clientNo = 5
threads = 24
percentiles = [50, 90, 99]
# clients
start = 20
stop = 400
step = 20

RTMW = []
RTMEM = []
# Extract data
for totalClients in range(start, stop + 1, step):
    print totalClients
    benchmark = benchmarkPath + "/maxthroughput_{}_{}_mw.log".format(totalClients, threads)
    tMWAll, tQueueAll, tServerAll = extractMWValues(benchmark)
    RTMW.append(tMWAll)

    responseTimeAll = []
    for client in range(1, clientNo + 1):
        benchmark = benchmarkPath + "/maxthroughput_{}_{}_{}.log".format(totalClients, threads, client)
        responseTimeAll += extractMemaslapValues(benchmark)
    RTMEM.append(responseTimeAll)

#RTMWPCT50 = [percentile(MWList, 50)/1000 for MWList in RTMW]
#RTMEMPCT50 = [percentile(MEMList, 50)/1000 for MEMList in RTMEM]
RTMWPCT50 = [mean(MWList)/1000 for MWList in RTMW]
RTMEMPCT50 = [mean(MEMList)/1000 for MEMList in RTMEM]

print "RTMWPCT50:", RTMWPCT50
print "RTMEMPCT50:", RTMEMPCT50

responseTimeAll = RTMEM[13]
tMWAll = RTMW[13]

maxValue = percentile(responseTimeAll, 99.9)
responseTimeAll = [v/1000.0 for v in responseTimeAll if v <= maxValue]
print min(responseTimeAll), max(responseTimeAll), mean(responseTimeAll), stdev(responseTimeAll)
tMWAll = [v/1000.0 for v in tMWAll if v <= maxValue]
print min(tMWAll), max(tMWAll), mean(tMWAll), stdev(tMWAll)


# Plotting
def darken(color):
    l = []
    for c in range(3):
        l.append(color[c]*0.50)
    return (l[0], l[1], l[2])

clients = range(start, stop + 1, step)
ticks = range(0, stop + 1, step*2)
colors = [(27,158,119), (217,95,2), (117,112,179), (231,41,138), (102,166,30), (230,171,2)]
colors = [(r/255.0, g/255.0, b/255.0) for r, g, b in colors]
#cmap = plt.get_cmap("Dark2")
#colors = [cmap(0), cmap(0.7)]
#N = 4
#colors = [cmap(float(i)/(N-1)) for i in range(N)]

# response time distributions
x = np.linspace(0, maxValue/1000, 300)
param = gamma.fit(responseTimeAll, floc=0)
responseTimeFit = gamma.pdf(x, *param)
param = gamma.fit(tMWAll, floc=0)
tMWFit = gamma.pdf(x, *param)

plt.figure()
plt.plot(x, responseTimeFit, color=darken(colors[0]))
plt.plot(x, tMWFit, color=darken(colors[1]))
plt.hist(responseTimeAll, bins=20, normed=True, color=colors[0], label="Memaslap")
plt.hist(tMWAll, bins=20, normed=True, color=colors[1], alpha=0.60, label="Middleware")
plt.ylim(ymin=0)
plt.grid()
plt.xlabel("Response time in msecs")
plt.ylabel("Probability")
plt.legend()
plt.savefig("distribution_response_time.png")

# memaslap vs middleware response time
plt.figure()
plt.plot(clients, RTMEMPCT50, "-o", color=colors[0], label="Memaslap")
plt.plot(clients, RTMWPCT50, "-o", color=colors[1], label="Middleware")
plt.legend(loc="best")
plt.xticks(ticks)
plt.xlim(xmax=(stop + step))
plt.ylim(ymin=0)
plt.grid()
plt.xlabel("Clients")
plt.ylabel("Response time (msec)")
plt.savefig("response_time_difference.png")
