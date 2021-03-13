#!/bin/bash 

#Get container id
containers=$(docker ps)
[[ $containers =~ [a-z0-9]{12} ]]
container_id=$BASH_REMATCH
echo "$container_id"

#Go to docker container and run tests
docker cp create_expect.py $container_id:/etc/frr
docker exec -i $container_id bash < in_docker.sh

#Copy test logs from docker container
docker cp $container_id:/etc/frr/tests.log logs/
