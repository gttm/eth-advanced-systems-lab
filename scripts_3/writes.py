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
    finalTpsReps = [[] for op in range(len(OP))]
    finalTpsRepsData = [[] for op in range(len(OP))]
    finalTpsStd = [[] for op in range(len(OP))]
    finalResponseAvg= [[] for op in range(len(OP))]
    finalResponseStd= [[] for op in range(len(OP))]
    for op in range(len(OP)):
        repetitionData = [(tps[op][r*repetitionSec: (r + 1)*repetitionSec], responseAvg[op][r*repetitionSec: (r + 1)*repetitionSec], responseStd[op][r*repetitionSec: (r + 1)*repetitionSec]) for r in range(1, repetitionNo + 1)]
        repetitionResults = [(sum(repTps)/repetitionSec, sum(repResponseAvg)/repetitionSec, sqrt(sum(repResponseStd)/repetitionSec)) for (repTps, repResponseAvg, repResponseStd) in repetitionData]
        finalTps[op] = sum(repTps for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo
        finalTpsReps[op] = [repTps for (repTps, repResponseAvg, repResponseStd) in repetitionResults]
        finalTpsRepsData[op] = [repTps for (repTps, repResponseAvg, repResponseStd) in repetitionData]
        finalTpsStd[op] = stdev(repTps for (repTps, repResponseAvg, repResponseStd) in repetitionResults)
        finalResponseAvg[op] = sum(repResponseAvg for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo
        finalResponseStd[op] = sqrt(sum(repResponseStd*repResponseStd for (repTps, repResponseAvg, repResponseStd) in repetitionResults)/repetitionNo)
    return finalTps, finalTpsStd, finalResponseAvg, finalResponseStd, finalTpsReps, finalTpsRepsData


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
W = [1, 5, 10]
S = [3, 5, 7]
R = [[1, mc] for mc in S]
#percentiles = [50, 90, 99]
percentiles = [50, 90]
OP = ["total", "get", "set"]

TPS = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TPSMAX = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TPSREPS = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TPSSTD = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
RT = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
RTSTD = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TMWPCT = [[[[[] for r in R[0]] for mc in S] for p in percentiles] for op in range(len(OP))]
TQUEUEPCT = [[[[[] for r in R[0]] for mc in S] for p in percentiles] for op in range(len(OP))]
TSERVERPCT = [[[[[] for r in R[0]] for mc in S] for p in percentiles] for op in range(len(OP))]
TMW = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TQUEUE = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]
TSERVER = [[[[] for r in R[0]] for mc in S] for op in range(len(OP))]

# Extract data
for mcIndex in range(len(S)):
    for rIndex in range(len(R[0])):
        for wIndex in range(len(W)):
            w = W[wIndex]
            mc = S[mcIndex]
            r = R[mcIndex][rIndex]
            print w, mc, r
            benchmark = benchmarkPath + "/writes_{}_{}_{}_mw.log".format(w, mc, r)
            tMWAll, tQueueAll, tServerAll = extractMWValues(benchmark)
            for op in range(len(OP)):
                TMW[op][mcIndex][rIndex].append(mean(tMWAll[op]))
                TQUEUE[op][mcIndex][rIndex].append(mean(tQueueAll[op]))
                TSERVER[op][mcIndex][rIndex].append(mean(tServerAll[op]))
                for pIndex in range(len(percentiles)):
                    TMWPCT[op][pIndex][mcIndex][rIndex].append(percentile(tMWAll[op], percentiles[pIndex]))
                    TQUEUEPCT[op][pIndex][mcIndex][rIndex].append(percentile(tQueueAll[op], percentiles[pIndex]))
                    TSERVERPCT[op][pIndex][mcIndex][rIndex].append(percentile(tServerAll[op], percentiles[pIndex]))
            aggregateTps = [0 for op in range(len(OP))]
            aggregateTpsReps = [[0 for rep in range(repetitionNo)] for op in range(len(OP))]
            aggregateTpsRepsData = [[[0 for sec in range(repetitionSec)] for rep in range(repetitionNo)] for op in range(len(OP))]
            aggregateTpsStd = [0 for op in range(len(OP))]
            averageRt = [0 for op in range(len(OP))]
            averageRtStd = [0 for op in range(len(OP))]
            for client in range(1, clientNo + 1):
                benchmark = benchmarkPath + "/writes_{}_{}_{}_{}.log".format(w, mc, r, client)
                tps, tpsStd, responseAvg, responseStd, tpsReps, tpsRepsData = extractMemaslapValues(benchmark)
                for op in range(len(OP)):
                    aggregateTps[op] += tps[op]
                    aggregateTpsStd[op] += tpsStd[op]*tpsStd[op]
                    for rep in range(repetitionNo):
                        aggregateTpsReps[op][rep] += tpsReps[op][rep]
                        for sec in range(repetitionSec):
                            aggregateTpsRepsData[op][rep][sec] += tpsRepsData[op][rep][sec]
                    averageRt[op] += responseAvg[op]
                    averageRtStd[op] += responseStd[op]*responseStd[op]
            for op in range(len(OP)):
                aggregateTpsStd[op] = sqrt(aggregateTpsStd[op])
                averageRt[op] /= clientNo
                averageRtStd[op] = sqrt(averageRtStd[op])
                TPS[op][mcIndex][rIndex].append(aggregateTps[op])
                TPSSTD[op][mcIndex][rIndex].append(aggregateTpsStd[op])
                TPSREPS[op][mcIndex][rIndex].append(aggregateTpsReps[op])
                TPSMAX[op][mcIndex][rIndex].append(max(max(aggregateTpsRepsData[op][rep] for rep in range(repetitionNo))))
                RT[op][mcIndex][rIndex].append(averageRt[op])
                RTSTD[op][mcIndex][rIndex].append(averageRtStd[op])
        for op in range(len(OP)):
            RT[op][mcIndex][rIndex] = [a/1000 for a in RT[op][mcIndex][rIndex]]
            RTSTD[op][mcIndex][rIndex] = [a/1000 for a in RTSTD[op][mcIndex][rIndex]]
            TMW[op][mcIndex][rIndex] = [a/1000 for a in TMW[op][mcIndex][rIndex]]
            TQUEUE[op][mcIndex][rIndex] = [a/1000 for a in TQUEUE[op][mcIndex][rIndex]]
            TSERVER[op][mcIndex][rIndex] = [a/1000 for a in TSERVER[op][mcIndex][rIndex]]
            for pIndex in range(len(percentiles)):
                TMWPCT[op][pIndex][mcIndex][rIndex] = [a/1000 for a in TMWPCT[op][pIndex][mcIndex][rIndex]]
                TQUEUEPCT[op][pIndex][mcIndex][rIndex] = [a/1000 for a in TQUEUEPCT[op][pIndex][mcIndex][rIndex]]
                TSERVERPCT[op][pIndex][mcIndex][rIndex] = [a/1000 for a in TSERVERPCT[op][pIndex][mcIndex][rIndex]]


print "----------------------"
print "TPS:", TPS
print "TPSSTD:", TPSSTD
print "RT:", RT
print "RTSTD:", RTSTD
print "TMWPCT:", TMWPCT
print "TQUEUEPCT:", TQUEUEPCT
print "TSERVERPCT:", TSERVERPCT
print "TMW:", TMW
print "TQUEUE:", TQUEUE
print "TSERVER:", TSERVER
print "----------------------"

def printTable(T):
    for op in range(len(OP)):
        for rIndex in range(len(R[0])):
            print "op:{}, rIndex:{}".format(OP[op], rIndex)
            for mcIndex in range(len(S)):
                mc = S[mcIndex]
                r = R[mcIndex][rIndex]
                print "({}, {}) {}".format(r, mc, T[op][mcIndex][rIndex])

print "TPS"
printTable(TPS)
print "TPSSTD"
printTable(TPSSTD)
print "TPSMAX"
printTable(TPSMAX)
print "RT"
printTable(RT)
print "TMW"
printTable(TMW)
print "TQUEUE"
printTable(TQUEUE)
print "TSERVER"
printTable(TSERVER)

def changePCT(tps, base):
    return (tps - base)/base

print "CHANGE"
base = TPS[0][0][0][0]
for mcIndex in range(len(S)):
    for rIndex in range(len(R[0])):
        change = [changePCT(TPS[0][mcIndex][rIndex][wIndex], base)*100 for wIndex in range(len(W))]
        print "(S:{}, R:{}) {}".format(S[mcIndex], rIndex, change)

print "----------------------"
print "2^kr analysis"
for mcIndex in [0, 2]:
    for rIndex in [0, 1]:
        for wIndex in [0, 2]:
            print S[mcIndex], R[mcIndex][rIndex], W[wIndex], TPSREPS[0][mcIndex][rIndex][wIndex] 

print "----------------------"
print "M/M/m"
for mcIndex in [0, 1, 2]:
    for rIndex in [1]:
        for wIndex in [2]:
            print S[mcIndex], R[mcIndex][rIndex], W[wIndex], TPS[0][mcIndex][rIndex][wIndex], TPSMAX[0][mcIndex][rIndex][wIndex], RT[0][mcIndex][rIndex][wIndex], RTSTD[0][mcIndex][rIndex][wIndex]

TNET = [[[[RT[op][mcIndex][rIndex][wIndex] - TMW[op][mcIndex][rIndex][wIndex] for wIndex in range(len(W))] for rIndex in range(len(R[0]))] for mcIndex in range(len(S))] for op in range(len(OP))]
THASH = [[[[TMW[op][mcIndex][rIndex][wIndex] - TQUEUE[op][mcIndex][rIndex][wIndex] - TSERVER[op][mcIndex][rIndex][wIndex] for wIndex in range(len(W))] for rIndex in range(len(R[0]))] for mcIndex in range(len(S))] for op in range(len(OP))]

mcIndex = 0
rIndex = 1
wIndex = 2
print "----------------------"
print "Queuing network, configuration:", S[mcIndex], R[mcIndex][rIndex], W[wIndex]
print "TPS:", TPS[0][mcIndex][rIndex][wIndex], TPS[1][mcIndex][rIndex][wIndex], TPS[2][mcIndex][rIndex][wIndex]
print "RT:", RT[0][mcIndex][rIndex][wIndex], RT[1][mcIndex][rIndex][wIndex], RT[2][mcIndex][rIndex][wIndex]
print "TMW:", TMW[0][mcIndex][rIndex][wIndex], TMW[1][mcIndex][rIndex][wIndex], TMW[2][mcIndex][rIndex][wIndex]
print "TQUEUE:", TQUEUE[0][mcIndex][rIndex][wIndex], TQUEUE[1][mcIndex][rIndex][wIndex], TQUEUE[2][mcIndex][rIndex][wIndex]
print "TSERVER:", TSERVER[0][mcIndex][rIndex][wIndex], TSERVER[1][mcIndex][rIndex][wIndex], TSERVER[2][mcIndex][rIndex][wIndex]
print "TNET:", TNET[0][mcIndex][rIndex][wIndex], TNET[1][mcIndex][rIndex][wIndex], TNET[2][mcIndex][rIndex][wIndex]
print "THASH:", THASH[0][mcIndex][rIndex][wIndex], THASH[1][mcIndex][rIndex][wIndex], THASH[2][mcIndex][rIndex][wIndex]

