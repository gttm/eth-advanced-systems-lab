#!/bin/bash

ssh gtouloupas@asl11vms10 "memcached -p 11212 -t 1 &"

#echo "1 client"
#for j in `seq 1 5`
#do
#    ssh gtouloupas@asl11vms1 "~/libmemcached-1.0.18/clients/memaslap -s asl11vms10:11212 -T 1 -c 1 -o1 -S 1s -t 30s -F ~/memaslap-workloads/smallvalue.cfg > ~/logfiles/baselinebench_1_${j}.log &"
#    sleep 32
#done

step=4
i=68
total=0
let "total=i*2"
while [ $i -le 128 ]
do
    echo "$total clients"
    for j in `seq 1 5`
    do
        ssh gtouloupas@asl11vms1 "~/libmemcached-1.0.18/clients/memaslap -s asl11vms10:11212 -T $i -c $i -o0.9 -S 1s -t 30s -F ~/memaslap-workloads/smallvalue.cfg > ~/logfiles/baselinebench_${total}_${j}_1.log &"
        ssh gtouloupas@asl11vms2 "~/libmemcached-1.0.18/clients/memaslap -s asl11vms10:11212 -T $i -c $i -o0.9 -S 1s -t 30s -F ~/memaslap-workloads/smallvalue.cfg > ~/logfiles/baselinebench_${total}_${j}_2.log &"
        sleep 32
    done
    let "i=i+step"
    let "total=i*2"
done
