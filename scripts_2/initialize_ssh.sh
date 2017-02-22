#!/bin/bash

rm ~/.ssh/known_hosts
#eval `ssh-agent -s`
#ssh-add ~/.ssh/id_rsa

for vm in {1..10}
do
    ssh -o StrictHostKeyChecking=no gtouloupas@asl11vms$vm "exit" 
done

