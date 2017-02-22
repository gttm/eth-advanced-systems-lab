#!/bin/bash

for cl in {1..10}
do
    #ssh gtouloupas@asl11vms$cl "mkdir ~/logfiles"
    #ssh gtouloupas@asl11vms$cl "mkdir ~/memaslap-workloads"
    #ssh gtouloupas@asl11vms$cl "rm ~/logfiles/*"
    #ssh gtouloupas@asl11vms$cl "ls -lh ~/logfiles"
    ssh gtouloupas@asl11vms$cl "ps aux | grep memcached"
    ssh gtouloupas@asl11vms$cl "ps aux | grep memaslap"
    #ssh gtouloupas@asl11vms$cl "sudo killall memcached"
    #scp gtouloupas@asl11vms$cl:~/logfiles/* ~/logfiles/
    #scp ~/memaslap-workloads/* gtouloupas@asl11vms$cl:~/memaslap-workloads
done

