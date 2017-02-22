#!/bin/bash

duration=150

mkdir ~/logfiles/maxthroughput_current
rm ~/logfiles/maxthroughput_current/*
for client in {1..5}
do
    ssh gtouloupas@asl11vms$client "rm ~/logfiles/*"
done

for i in {4..80..4}
do
    let "total=i*5"
    for T in {8..32..8}
    do
        echo "$total, $T"
        echo "Start memcached servers"
        for mc in {6..10}
        do
            ssh gtouloupas@asl11vms$mc "nohup memcached -p 11212 -t 1 &> /dev/null &"
        done
        sleep 5
        
        echo "Start middleware"
        java -jar ~/middleware-gtouloup.jar -l asl11vms11 -p 11212 -t $T -r 1 -m asl11vms6:11212 asl11vms7:11212 asl11vms8:11212 asl11vms9:11212 asl11vms10:11212 &> ~/logfiles/maxthroughput_current/maxthroughput_${total}_${T}_mw.log & 
        sleep 5
        
        echo "Start memaslap clients"
        for client in {1..5}
        do
            ssh gtouloupas@asl11vms$client "nohup ~/libmemcached-1.0.18/clients/memaslap -s asl11vms11:11212 -T $i -c $i -o0.9 -w 1k -S 1s -t ${duration}s -F ~/memaslap-workloads/smallvalue_readonly.cfg &> ~/logfiles/maxthroughput_${total}_${T}_${client}.log &"
        done
        sleep 50
        sleep $duration

        echo "Stop middleware"
        sudo pkill -f 'middleware-gtouloup.jar'
        mv middleware_logger.log ~/logfiles/maxthroughput_current/maxthroughput_${total}_${T}_mw_logger.log
        
        echo "Stop memcached servers"
        
        for mc in {6..10}
        do
            ssh gtouloupas@asl11vms$mc "sudo killall memcached"
        done
    done
done

echo "Collect logs"
for client in {1..5}
do
    scp gtouloupas@asl11vms$client:~/logfiles/* ~/logfiles/maxthroughput_current
done

