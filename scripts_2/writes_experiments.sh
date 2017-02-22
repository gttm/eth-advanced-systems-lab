#!/bin/bash

duration=150
threads=24
clients=87

mkdir ~/logfiles/writes_current
rm ~/logfiles/writes_current/*
for client in {1..3}
do
    ssh gtouloupas@asl11vms$client "rm ~/logfiles/*"
done

for W in 1 5 10
do
    for S in 3 5 7
    do
        for R in 1 $S
        do
            echo "$W, $S, $R"
            let "mcEnd=S+3"
            echo "Start memcached servers"
            addresses=""
            for mc in `seq 4 $mcEnd`
            do
                ssh gtouloupas@asl11vms$mc "nohup memcached -p 11212 -t 1 &> /dev/null &"
                addresses+="asl11vms$mc:11212 "
            done
            sleep 5
            echo "addresses: $addresses"
            
            echo "Start middleware"
            java -jar ~/middleware-gtouloup.jar -l asl11vms11 -p 11212 -t $threads -r $R -m $addresses &> ~/logfiles/writes_current/writes_${W}_${S}_${R}_mw.log &
            sleep 5
            
            echo "Start memaslap clients"
            for client in {1..3}
            do
                ssh gtouloupas@asl11vms$client "nohup ~/libmemcached-1.0.18/clients/memaslap -s asl11vms11:11212 -T $clients -c $clients -o0.9 -S 1s -t ${duration}s -F ~/memaslap-workloads/smallvalue_${W}.cfg &> ~/logfiles/writes_${W}_${S}_${R}_${client}.log &"
            done
            sleep 10
            sleep $duration

            echo "Stop middleware"
            sudo pkill -f 'middleware-gtouloup.jar'
            mv middleware_logger.log ~/logfiles/writes_current/writes_${W}_${S}_${R}_mw_logger.log
            
            echo "Stop memcached servers"
            
            for mc in `seq 4 $mcEnd`
            do
                ssh gtouloupas@asl11vms$mc "sudo killall memcached"
            done
        done
    done
done

echo "Collect logs"
for client in {1..3}
do
    scp gtouloupas@asl11vms$client:~/logfiles/* ~/logfiles/writes_current
done

