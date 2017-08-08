import sys
from math import sqrt
from statistics import stdev, mean
from numpy import percentile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def extractMemaslapValues(benchmark):
    f = open(benchmark, 'r')
    tps = [[] for op in range(len(OP))]
    responseAvg = [[] for op in range(len(OP))]
    responseStd = [[] for op in range(len(OP))]
    flag = -1
    for line in f:
        if line == "Total Statistics\n":
            flag = 0
        elif line == "Get Statistics\n":
            flag = 1
        elif line == "Set Statistics\n":
            flag = 2
        elif flag != -1 and line.startswith("Period"):
            tps[flag].append(float(line.split()[3]))
            responseAvg[flag].append(float(line.split()[8]))
            responseStd[flag].append(float(line.split()[9])*float(line.split()[9]))
            flag = -1
    if len(tps[0]) == 0:
        print "Did not perform any operations {}".format(benchmark)
    elif len(tps[0]) < (150 - repetitionSec):
        print "Performed for {} seconds instead of 150 {}".format(len(tps[0]), benchmark)
    finalTps = [[] for op in range(len(OP))]
    finalTpsStd = [[] for op in range(len(OP))]
    finalResponseAvg= [[] for op in range(len(OP))]
    finalResponseStd= [[] for op in range(len(OP))]
    for op in range(len(OP)):
        repetitionData = [(tps[op][r*repetitionSec: (r + 1)*repetitionSec], responseAvg[op][r*repetitionSec: (r + 1)*repetitionSec], responseStd[op][r*repetitionSec: (r + 1)*repetitionSec]) for r in range(1, repetitionNo + 1)]
        repetitionResults = [(sum(repTps)/repetitionSec, sum(repResponseAvg)/repetitionSec, sqrt(sum(repResponseStd)/repetitionSec)) for (repTps, repResponseAvg, repResponseStd) in repetitionData]
        finalTps[op] = sum(repTps for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo
        finalTpsStd[op] = stdev(repTps for (repTps, repResponseAvg, repResponseStd) in repetitionResults)
        finalResponseAvg[op] = sum(repResponseAvg for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo
        finalResponseStd[op] = sqrt(sum(repResponseStd*repResponseStd for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo)
    return finalTps, finalTpsStd, finalResponseAvg, finalResponseStd


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
    tMWAll = [[] for op in range(len(OP))]
    tQueueAll = [[] for op in range(len(OP))]
    tServerAll = [[] for op in range(len(OP))]
    repetitionResults = []
    for line in f:
        if flag == 0 and "M ch.ethz" in line:
            sec = lineToSec(line)
            if sec >= start + setupTime:
                flag = 1
                startRep = sec
        if flag != 0 and "Handler" in line:
            if "ReadHandler" in line:
                flag = 1
            elif "WriteHandler" in line:
                flag = 2
            else:
                print "Bad line"
            sec = lineToSec(line)
            if sec > startRep + repetitionSec:
                startRep = sec
                repetition += 1
                if repetition > repetitionNo:
                    return tMWAll, tQueueAll, tServerAll
            line = next(f)
            metrics = [int(i.strip(",")) for i in line.split()[1:]]
            tMWAll[flag].append(metrics[1])
            tQueueAll[flag].append(metrics[2])
            tServerAll[flag].append(metrics[3])
            tMWAll[0].append(metrics[1])
            tQueueAll[0].append(metrics[2])
            tServerAll[0].append(metrics[3])
    print "Only finished {} complete repetitions for {}".format(repetition - 1, benchmark)
    return tMWAll, tQueueAll, tServerAll


if len(sys.argv) != 2:
    print "Usage: python {} <logfile_directory>".format(sys.argv[0])
    exit(0)

benchmarkPath = sys.argv[1]
clientNo = 3
repetitionNo = 3
repetitionSec = 30
setupTime = 30
S = [3, 5, 7]
R = [[1, mc/2 + 1, mc] for mc in S]
#percentiles = [50, 90, 99]
percentiles = [50, 90]
OP = ["total", "get", "set"]

TPS = [[[] for mc in S] for op in range(len(OP))]
TPSSTD = [[[] for mc in S] for op in range(len(OP))]
TMWPCT = [[[[] for mc in S] for p in percentiles]  for op in range(len(OP))]
TQUEUEPCT = [[[[] for mc in S] for p in percentiles] for op in range(len(OP))]
TSERVERPCT = [[[[] for mc in S] for p in percentiles] for op in range(len(OP))]

# Extract data
for mcIndex in range(len(S)):
    for rIndex in range(len(R[0])):
        mc = S[mcIndex]
        r = R[mcIndex][rIndex]
        print mc, r
        benchmark = benchmarkPath + "/replication_{}_{}_mw.log".format(mc, r)
        tMWAll, tQueueAll, tServerAll = extractMWValues(benchmark)
        for op in range(len(OP)):
            for pIndex in range(len(percentiles)):
                TMWPCT[op][pIndex][mcIndex].append(percentile(tMWAll[op], percentiles[pIndex]))
                TQUEUEPCT[op][pIndex][mcIndex].append(percentile(tQueueAll[op], percentiles[pIndex]))
                TSERVERPCT[op][pIndex][mcIndex].append(percentile(tServerAll[op], percentiles[pIndex]))
        aggregateTps = [0 for op in range(len(OP))]
        aggregateTpsStd = [0 for op in range(len(OP))]
        for client in range(1, clientNo + 1):
            benchmark = benchmarkPath + "/replication_{}_{}_{}.log".format(mc, r, client)
            tps, tpsStd, responseAvg, responseStd = extractMemaslapValues(benchmark)
            for op in range(len(OP)):
                aggregateTps[op] += tps[op]
                aggregateTpsStd[op] += tpsStd[op]*tpsStd[op]
        for op in range(len(OP)):
            aggregateTpsStd[op] = sqrt(aggregateTpsStd[op])
            TPS[op][mcIndex].append(aggregateTps[op])
            TPSSTD[op][mcIndex].append(aggregateTpsStd[op])
    for op in range(len(OP)):
        for pIndex in range(len(percentiles)):
            TMWPCT[op][pIndex][mcIndex] = [a/1000 for a in TMWPCT[op][pIndex][mcIndex]]
            TQUEUEPCT[op][pIndex][mcIndex] = [a/1000 for a in TQUEUEPCT[op][pIndex][mcIndex]]
            TSERVERPCT[op][pIndex][mcIndex] = [a/1000 for a in TSERVERPCT[op][pIndex][mcIndex]]


print "----------------------"
print "TPS:", TPS
print "TPSSTD:", TPSSTD
print "TMWPCT:", TMWPCT
print "TQUEUEPCT:", TQUEUEPCT
print "TSERVERPCT:", TSERVERPCT
print "----------------------"

def printTable(T):
    for op in range(len(OP)):
        print "op:", OP[op]
        for mcIndex in range(len(S)):
            mc = S[mcIndex]
            print mc, T[op][mcIndex]

print "TPS"
printTable(TPS)
print "TPSSTD"
printTable(TPSSTD)


# Plotting
def modifyColor(color, p):
    l = []
    for c in range(3):
        l.append(color[c]*p)
    return (l[0], l[1], l[2])

colors = [(27,158,119), (217,95,2), (117,112,179), (231,41,138), (102,166,30), (230,171,2)]
colors = [(r/255.0, g/255.0, b/255.0) for r, g, b in colors]
hatches = ['/', '.', 'x']
labelsR = ["No replication", "Half replication", "Full replication"]
maxColorP = -0.35

# throughput
width = 0.35 
for op in range(len(OP)):
    plt.figure()
    for rIndex in range(len(R[0])):
        offset = [mc + (rIndex - len(R[0])/2.0)*width for mc in S]
        values = [TPS[op][mcIndex][rIndex] for mcIndex in range(len(S))]
        valuesStd = [TPSSTD[op][mcIndex][rIndex] for mcIndex in range(len(S))]
        plt.bar(offset, values, width, color=colors[rIndex], hatch=hatches[rIndex], yerr=valuesStd, label=labelsR[rIndex])
    plt.legend(loc="best")
    plt.xticks(S)
    plt.ylim(ymin=0)
    plt.grid(axis='y')
    plt.xlabel("Servers")
    plt.ylabel("Throughput (operations/sec)")
    plt.savefig("replication_throughput_{}.png".format(OP[op]))

# middleware response time percentiles
width = 0.5/len(percentiles)
for op in range(len(OP)):
    plt.figure()
    for rIndex in range(len(R[0])):
        for pIndex in range(len(percentiles)):
            offset = [mc + (len(percentiles)*rIndex + pIndex - len(percentiles)*len(R[0])/2.0)*width for mc in S]
            values = [TMWPCT[op][pIndex][mcIndex][rIndex] for mcIndex in range(len(S))]
            color = modifyColor(colors[rIndex], 1 + pIndex*maxColorP/(len(percentiles) - 1))
            plt.bar(offset, values, width, color=color, hatch=hatches[rIndex], label="{} ({}th percentile)".format(labelsR[rIndex], percentiles[pIndex]))
    lgd = plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1))
    plt.xticks(S)
    plt.ylim(ymin=0)
    plt.grid(axis='y')
    plt.xlabel("Servers")
    plt.ylabel("Response time (msec)")
    plt.savefig("replication_mw_response_time_{}.png".format(OP[op]), bbox_extra_artists=(lgd,), bbox_inches="tight")

# middleware queue time percentiles
width = 0.5/len(percentiles)
for op in range(len(OP)):
    plt.figure()
    for rIndex in range(len(R[0])):
        for pIndex in range(len(percentiles)):
            offset = [mc + (len(percentiles)*rIndex + pIndex - len(percentiles)*len(R[0])/2.0)*width for mc in S]
            values = [TQUEUEPCT[op][pIndex][mcIndex][rIndex] for mcIndex in range(len(S))]
            color = modifyColor(colors[rIndex], 1 + pIndex*maxColorP/(len(percentiles) - 1))
            plt.bar(offset, values, width, color=color, hatch=hatches[rIndex], label="{} ({}th percentile)".format(labelsR[rIndex], percentiles[pIndex]))
    lgd = plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1))
    plt.xticks(S)
    plt.ylim(ymin=0)
    plt.grid(axis='y')
    plt.xlabel("Servers")
    plt.ylabel("Queue time (msec)")
    plt.savefig("replication_mw_queue_time_{}.png".format(OP[op]), bbox_extra_artists=(lgd,), bbox_inches="tight")

# middleware server time percentiles
width = 0.5/len(percentiles)
for op in range(len(OP)):
    plt.figure()
    for rIndex in range(len(R[0])):
        for pIndex in range(len(percentiles)):
            offset = [mc + (len(percentiles)*rIndex + pIndex - len(percentiles)*len(R[0])/2.0)*width for mc in S]
            values = [TSERVERPCT[op][pIndex][mcIndex][rIndex] for mcIndex in range(len(S))]
            color = modifyColor(colors[rIndex], 1 + pIndex*maxColorP/(len(percentiles) - 1))
            plt.bar(offset, values, width, color=color, hatch=hatches[rIndex], label="{} ({}th percentile)".format(labelsR[rIndex], percentiles[pIndex]))
    lgd = plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1))
    plt.xticks(S)
    plt.ylim(ymin=0)
    plt.grid(axis='y')
    plt.xlabel("Servers")
    plt.ylabel("Server time (msec)")
    plt.savefig("replication_mw_server_time_{}.png".format(OP[op]), bbox_extra_artists=(lgd,), bbox_inches="tight")

