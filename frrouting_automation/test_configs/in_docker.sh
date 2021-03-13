#!/bin/bash 

cd /etc/frr

apk add expect

vtysh 

write file

exit

python3 create_expect.py bgpd.conf

expect run_tests

echo "yeet"
