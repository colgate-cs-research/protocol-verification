#!/bin/bash

declare -i starttime
declare -i endtime
declare -i dockertime
declare -i conttime
declare -i testtime
declare -i copytime

dockertime=0
conttime=0
testtime=0
copytime=0

starttime=0
endtime=0

for filename in configs/*; do
    
    starttime=$(date +%s)
    python3 frr_config.py -c single_bgp.json -a stop
    python3 frr_config.py -c single_bgp.json -a start -b $filename
    endtime=$(date +%s)
    dockertime=$(($dockertime+$endtime-$starttime))
    
    #Get container id
    starttime=$(date +%s)
    containers=$(docker ps)
    [[ $containers =~ [a-z0-9]{12} ]]
    container_id=$BASH_REMATCH
    endtime=$(date +%s)
    conttime=$(($conttime+$endtime-$starttime))
    
    #Go to docker container and run tests
    starttime=$(date +%s)
    docker cp create_expect.py $container_id:/etc/frr
    docker exec -i $container_id bash < in_docker.sh
    endtime=$(date +%s)
    testtime=$(($testtime+$endtime-$starttime))
    
    #Copy test logs, generated configs, and expect tests from docker container
    starttime=$(date +%s)
    file=$(basename $filename)
    docker cp $container_id:/etc/frr/tests.log logs/
    mv logs/tests.log logs/$file.tests.log
    docker cp $container_id:/etc/frr/bgpd.conf configs_generated/
    mv configs_generated/bgpd.conf configs_generated/$file.conf
    docker cp $container_id:/etc/frr/run_tests tests/
    mv tests/run_tests tests/$file.tests
    endtime=$(date +%s)
    copytime=$(($copytime+$endtime-$starttime))

done

python3 frr_config.py -c single_bgp.json -a stop

echo "Setting up routers" $dockertime
echo "Getting container info" $conttime
echo "Making/Running tests" $testtime
echo "Copying file" $copytime

