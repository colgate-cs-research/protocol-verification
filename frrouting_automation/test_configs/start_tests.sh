#!/bin/bash 

for filename in configs_temp/*; do
    
    sudo python3 frr_config.py -c triangle_bgp.json -a stop
    sudo python3 frr_config.py -c triangle_bgp.json -a start -b $filename
    
    #Get container id
    containers=$(docker ps)
    [[ $containers =~ [a-z0-9]{12} ]]
    container_id=$BASH_REMATCH

    #Go to docker container and run tests
    docker cp create_expect.py $container_id:/etc/frr
    docker exec -i $container_id bash < in_docker.sh

    #Copy test logs, generated configs, and expect tests from docker container
    file=$(basename $filename)
    docker cp $container_id:/etc/frr/tests.log logs/
    sudo mv logs/tests.log logs/$file.tests.log
    docker cp $container_id:/etc/frr/bgpd.conf configs_generated/
    sudo mv configs_generated/bgpd.conf configs_generated/$file.conf
    docker cp $container_id:/etc/frr/run_tests tests/
    sudo mv tests/run_tests tests/$file.tests

done

sudo python3 frr_config.py -c triangle_bgp.json -a stop

