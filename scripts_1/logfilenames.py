clientNo = 2
repetitionNo = 5

shortnames = ""

# extract 1 client data
for repetition in range(1, repetitionNo + 1):
    shortnames += "baselinebench\_1\_{}\_1, ".format(repetition)
    print "\hline baselinebench\_1\_{0}\_1 & \url{{https://gitlab.inf.ethz.ch/gtouloup/asl-fall16-project/blob/master/logfiles/baseline/baselinebench_1_{0}_1.log}} \\\\ ".format(repetition)

c = 168
# extract the rest of the data
for totalClients in range(8, c + 1, 8):
    for repetition in range(1, repetitionNo + 1):
        for client in range(1, clientNo + 1):
            shortnames += "baselinebench\_{}\_{}\_{}, ".format(totalClients, repetition, client)
            print "\hline baselinebench\_{0}\_{1}\_{2} & \url{{https://gitlab.inf.ethz.ch/gtouloup/asl-fall16-project/blob/master/logfiles/baseline/baselinebench_{0}_{1}_{2}.log}} \\\\ ".format(totalClients, repetition, client)

# print shortnames

