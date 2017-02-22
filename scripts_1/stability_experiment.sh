#!/bin/bash

minutes=$1
duration=0
let "duration=minutes*60"
echo "Running stability experiment for $minutes minutes starting"
date

ssh gtouloupas@asl11vms8 "memcached -p 11212 -t 1 &"
ssh gtouloupas@asl11vms9 "memcached -p 11212 -t 1 &"
ssh gtouloupas@asl11vms10 "memcached -p 11212 -t 1 &"

sleep 1
#java -jar middleware-gtouloup.jar -l asl11vms11 -p 11212 -t 64 -r 3 -m 10.0.0.4:11212 10.0.0.11:11212 10.0.0.8:11212 > middleware.log 2>&1 &

for i in `seq 1 3`
do
    ssh gtouloupas@asl11vms$i "~/libmemcached-1.0.18/clients/memaslap -s asl11vms11:11212 -T 64 -c 64 -o0.9 -S 1s -t ${duration}s -F ~/memaslap-workloads/smallvalue.cfg > ~/logfiles/stability_${i}.log &"
done
sleep $duration

