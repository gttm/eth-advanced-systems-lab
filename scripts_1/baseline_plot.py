import sys
from os import listdir
from math import sqrt
from statistics import stdev
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def extractValues(benchmark):
    f = open(benchmark, 'r')
    flag = 0
    for line in f:
        if line.startswith("Run time: "):
            tps = float(line.split(' ')[6])
        elif line.startswith("Total Statistics ("):
            flag = 1;
        elif flag == 1:
            if "Avg:" in line:
                responseAvg = float(line.split(' ')[-1].strip())
            elif "Std:" in line:
                responseStd = float(line.split(' ')[-1].strip())
    return tps, responseAvg, responseStd
            
benchmarkPath = sys.argv[1]
clientNo = 2
repetitionNo = 5

# extract 1 client data
aggregateTpsVals = []
finalTps = 0
finalResponseAvg = 0
finalResponseStd = 0
for repetition in range(1, repetitionNo + 1):
    benchmark = benchmarkPath + "/baselinebench_1_{}.log".format(repetition)
    tps, responseAvg, responseStd = extractValues(benchmark)
    aggregateTpsVals.append(tps)
    finalTps += tps
    finalResponseAvg += responseAvg
    finalResponseStd += responseStd*responseStd
finalTps /= repetitionNo
finalResponseAvg /= repetitionNo
finalResponseStd = sqrt(finalResponseStd/repetitionNo)
TPS = [finalTps]
TPSSTD = [stdev(aggregateTpsVals)]
RAVG = [finalResponseAvg]
RSTD = [finalResponseStd]

c = 168
# extract the rest of the data
for totalClients in range(8, c + 1, 8):
    aggregateTpsVals = []
    finalTps = 0
    finalResponseAvg = 0
    finalResponseStd = 0
    for repetition in range(1, repetitionNo + 1):
        aggregateTps = 0
        avgResponseAvg = 0
        avgResponseStd = 0
        for client in range(1, clientNo + 1):
            benchmark = benchmarkPath + "/baselinebench_{}_{}_{}.log".format(totalClients, repetition, client)
            tps, responseAvg, responseStd = extractValues(benchmark)
            aggregateTps += tps
            avgResponseAvg += responseAvg
            avgResponseStd += responseStd*responseStd
        avgResponseAvg /= clientNo
        avgResponseStd = sqrt(avgResponseStd)
        aggregateTpsVals.append(aggregateTps)
        finalTps += aggregateTps
        finalResponseAvg += avgResponseAvg
        finalResponseStd += avgResponseStd*avgResponseStd
    finalTps /= repetitionNo
    finalResponseAvg /= repetitionNo
    finalResponseStd = sqrt(finalResponseStd/repetitionNo)
    TPS.append(finalTps)
    TPSSTD.append(stdev(aggregateTpsVals))
    RAVG.append(finalResponseAvg)
    RSTD.append(finalResponseStd)

RAVG = [a/1000 for a in RAVG]
RSTD = [a/1000 for a in RSTD]

print TPS
print TPSSTD
print RAVG
print RSTD

# plotting
clients = [1] + range(8, c + 1, 8)
ticks = [1] + range(8, c + 1, 16)
print clients

# throughput
plt.figure(1)
plt.errorbar(clients, TPS, yerr=TPSSTD, fmt='-o', ecolor='r')
plt.xticks(ticks)
plt.ylim(ymin=0)
plt.grid()
plt.xlabel('Clients')
plt.ylabel('TPS')
#plt.title('Throughput')
plt.savefig('baseline_throughput.png')

# response time
plt.figure(2)
plt.errorbar(clients, RAVG, yerr=RSTD, fmt='-o', ecolor='r')
plt.xticks(ticks)
plt.ylim(ymin=0)
plt.grid()
plt.xlabel('Clients')
plt.ylabel('Response time in msecs')
#plt.title('Response time')
plt.savefig('baseline_response_time.png')

