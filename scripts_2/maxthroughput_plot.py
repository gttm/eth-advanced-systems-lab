import sys
from math import sqrt
from statistics import stdev, mean
from numpy import percentile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def extractMemaslapValues(benchmark):
    f = open(benchmark, 'r')
    tps = []
    responseAvg = []
    responseStd = []
    flag = 0
    for line in f:
        if line == "Get Statistics\n":
            flag = 1
        elif flag == 1 and line.startswith("Period"):
            tps.append(float(line.split()[3]))
            responseAvg.append(float(line.split()[8]))
            responseStd.append(float(line.split()[9])*float(line.split()[9]))
            flag = 0
    if len(tps) == 0:
        print "Did not perform any gets {}".format(benchmark)
    elif len(tps) < (150 - repetitionSec):
        print "Performed for {} seconds instead of 150 {}".format(len(tps), benchmark)
    repetitionData = [(tps[r*repetitionSec: (r + 1)*repetitionSec], responseAvg[r*repetitionSec: (r + 1)*repetitionSec], responseStd[r*repetitionSec: (r + 1)*repetitionSec]) for r in range(1, repetitionNo + 1)]
    repetitionResults = [(sum(tps)/repetitionSec, sum(responseAvg)/repetitionSec, sqrt(sum(responseStd)/repetitionSec)) for (tps, responseAvg, responseStd) in repetitionData]
    tps = sum(tps for (tps, responseAvg, responseStd) in repetitionResults)/repetitionNo
    tpsStd = stdev(tps for (tps, responseAvg, responseStd) in repetitionResults)
    responseAvg = sum(responseAvg for (tps, responseAvg, responseStd) in repetitionResults)/repetitionNo
    responseStd = sqrt(sum(responseStd*responseStd for (tps, responseAvg, responseStd) in repetitionResults)/repetitionNo)
    return tps, tpsStd, responseAvg, responseStd


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
    repetitionResults = []
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
clientNo = 5
repetitionNo = 3
repetitionSec = 30
setupTime = 40
threads = range(8, 33, 8)
percentiles = [50, 90, 99]
# clients
start = 20
stop = 400
step = 20

TPS = [[] for t in threads]
TPSSTD = [[] for t in threads]
RAVG = [[] for t in threads]
RSTD = [[] for t in threads]
TMWPCT = [[[] for t in threads] for p in percentiles] 
TQUEUEPCT = [[[] for t in threads] for p in percentiles] 
TSERVERPCT = [[[] for t in threads] for p in percentiles] 

# Extract data
for tIndex in range(len(threads)):
    for totalClients in range(start, stop + 1, step):
        print totalClients, threads[tIndex]
        benchmark = benchmarkPath + "/maxthroughput_{}_{}_mw.log".format(totalClients, threads[tIndex])
        tMWAll, tQueueAll, tServerAll = extractMWValues(benchmark)
        for pIndex in range(len(percentiles)):
            TMWPCT[pIndex][tIndex].append(percentile(tMWAll, percentiles[pIndex]))
            TQUEUEPCT[pIndex][tIndex].append(percentile(tQueueAll, percentiles[pIndex]))
            TSERVERPCT[pIndex][tIndex].append(percentile(tServerAll, percentiles[pIndex]))

        aggregateTps = 0
        aggregateTpsStd = 0
        avgResponseAvg = 0
        avgResponseStd = 0
        for client in range(1, clientNo + 1):
            benchmark = benchmarkPath + "/maxthroughput_{}_{}_{}.log".format(totalClients, threads[tIndex], client)
            tps, tpsStd, responseAvg, responseStd = extractMemaslapValues(benchmark)
            aggregateTps += tps
            aggregateTpsStd += tpsStd*tpsStd
            avgResponseAvg += responseAvg
            avgResponseStd += responseStd*responseStd
        aggregateTpsStd = sqrt(aggregateTpsStd)
        avgResponseAvg /= clientNo
        avgResponseStd = sqrt(avgResponseStd)
        TPS[tIndex].append(aggregateTps)
        TPSSTD[tIndex].append(aggregateTpsStd)
        RAVG[tIndex].append(avgResponseAvg)
        RSTD[tIndex].append(avgResponseStd)
    RAVG[tIndex] = [a/1000 for a in RAVG[tIndex]]
    RSTD[tIndex] = [a/1000 for a in RSTD[tIndex]]
    for pIndex in range(len(percentiles)):
        TMWPCT[pIndex][tIndex] = [a/1000 for a in TMWPCT[pIndex][tIndex]]
        TQUEUEPCT[pIndex][tIndex] = [a/1000 for a in TQUEUEPCT[pIndex][tIndex]]
        TSERVERPCT[pIndex][tIndex] = [a/1000 for a in TSERVERPCT[pIndex][tIndex]]


print "----------------------"
print "TPS:", TPS
print "TPSSTD:", TPSSTD
print "RAVG:", RAVG
print "RSTD:", RSTD
print "TMWPCT:", TMWPCT
print "TQUEUEPCT:", TQUEUEPCT
print "TSERVERPCT:", TSERVERPCT


# Plotting
clients = range(start, stop + 1, step)
ticks = range(0, stop + 1, step*2)

colors = [(27,158,119), (217,95,2), (117,112,179), (231,41,138), (102,166,30), (230,171,2)]
colors = [(r/255.0, g/255.0, b/255.0) for r, g, b in colors]

# throughput
plt.figure()
for tIndex in range(len(threads)):
    plt.errorbar(clients, TPS[tIndex], yerr=TPSSTD[tIndex], color=colors[tIndex], fmt="-o", label="{} Threads".format(threads[tIndex]))
plt.legend(loc="best")
plt.xticks(ticks)
plt.xlim(xmax=(stop + step))
plt.ylim(ymin=0)
plt.grid()
plt.xlabel("Clients")
plt.ylabel("Throughput (operations/sec)")
plt.savefig("maxthroughput_throughput.png")

# response time
plt.figure()
for tIndex in range(len(threads)):
    plt.errorbar(clients, RAVG[tIndex], yerr=RSTD[tIndex], color=colors[tIndex], fmt="-o", label="{} Threads".format(threads[tIndex]))
plt.legend(loc="best")
plt.xticks(ticks)
plt.xlim(xmax=(stop + step))
plt.ylim(ymin=0)
plt.grid()
plt.xlabel("Clients")
plt.ylabel("Response time (msec)")
plt.savefig("maxthroughput_response_time.png")

for tIndex in range(len(threads)):
    # middleware response time percentiles
    plt.figure()
    plt.title("{} Threads".format(threads[tIndex]))
    for pIndex in range(len(percentiles)):
        plt.plot(clients, TMWPCT[pIndex][tIndex], "-o", color=colors[pIndex], label="{}th percentile".format(percentiles[pIndex]))
    plt.legend(loc="best")
    plt.xticks(ticks)
    plt.xlim(xmax=(stop + step))
    plt.ylim(ymin=0)
    plt.grid()
    plt.xlabel("Clients")
    plt.ylabel("Response time (msec)")
    plt.savefig("maxthroughput_mw_response_time_{}.png".format(threads[tIndex]))

    # middleware queue time percentiles
    plt.figure()
    plt.title("{} Threads".format(threads[tIndex]))
    for pIndex in range(len(percentiles)):
        plt.plot(clients, TQUEUEPCT[pIndex][tIndex], "-o", color=colors[pIndex], label="{}th percentile".format(percentiles[pIndex]))
    plt.legend(loc="best")
    plt.xticks(ticks)
    plt.xlim(xmax=(stop + step))
    plt.ylim(ymin=0)
    plt.grid()
    plt.xlabel("Clients")
    plt.ylabel("Queue time (msec)")
    plt.savefig("maxthroughput_mw_queue_time_{}.png".format(threads[tIndex]))

    # middleware server time percentiles
    plt.figure()
    plt.title("{} Threads".format(threads[tIndex]))
    for pIndex in range(len(percentiles)):
        plt.plot(clients, TSERVERPCT[pIndex][tIndex], "-o", color=colors[pIndex], label="{}th percentile".format(percentiles[pIndex]))
    plt.legend(loc="best")
    plt.xticks(ticks)
    plt.xlim(xmax=(stop + step))
    plt.ylim(ymin=0)
    plt.grid()
    plt.xlabel("Clients")
    plt.ylabel("Server time (msec)")
    plt.savefig("maxthroughput_mw_server_time_{}.png".format(threads[tIndex]))

