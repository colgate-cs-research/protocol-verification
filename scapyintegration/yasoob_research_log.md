## 9th November 2020

I was able to generate the OSPF neighbor entry on the frr router. Set up the router:

```
./frr_config.py -c ospf_scapy_frr.json -a start
```

Generate the OSPF packet using scapy:

```python
from scapy.contrib.ospf import *
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')#/Dot1Q(vlan=33)
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2')
packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, inter=1, iface="eth1")
```

Pay attention to options entry. If T option is set, the packet isn't processed by frr. In this case, we have E option set. I had looked at the packet exchange between two frr instances to figure out that E option was being used. The rest of the log was almost nonsensical and confusing for me.

The picture below show different options that can be set in a Hello packet. E stands for External Routing.

![image-20201109012457566](/Users/yasoob/Library/Application Support/typora-user-images/image-20201109012457566.png)

To verify a neighbor was added:

```bash
$ vtysh
$ show ip ospf neighbor

Neighbor ID     Pri State           Dead Time Address         Interface                        RXmtL RqstL DBsmL
10.10.0.2         1 Init/DROther      19.043s 10.10.0.2       eth1:10.10.0.3                       0     0     0

```

I was able to figure out which packets are transferred when by using tcpdump on the routers. You can install tcpdump like this:

```shell
$ apk add tcpdump
```

Then you run tcpdump and filter for ospf packets:

```bash
$ tcpdump --interface any proto 0x59
```

A short excerpt of the output looks like this:

```
05:46:29.357393 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:34.070228 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:39.273326 IP router1.bridge1 > 6b9f6373be93: OSPFv2, Database Description, length 32
05:46:39.357462 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:44.068591 IP 6b9f6373be93 > router1.bridge1: OSPFv2, Database Description, length 32
05:46:44.069198 IP router1.bridge1 > 6b9f6373be93: OSPFv2, Database Description, length 52
05:46:44.069686 IP 6b9f6373be93 > router1.bridge1: OSPFv2, Database Description, length 52
05:46:44.069838 IP 6b9f6373be93 > router1.bridge1: OSPFv2, LS-Request, length 36
05:46:44.070111 IP router1.bridge1 > 6b9f6373be93: OSPFv2, Database Description, length 32
05:46:44.070367 IP router1.bridge1 > 6b9f6373be93: OSPFv2, LS-Request, length 36
05:46:44.070398 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:44.070678 IP router1.bridge1 > ospf-dsig.mcast.net: OSPFv2, LS-Update, length 64
05:46:44.070978 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, LS-Update, length 64
05:46:44.072866 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, LS-Update, length 96
05:46:44.072968 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, LS-Update, length 64
05:46:44.073542 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, LS-Update, length 64
05:46:44.274225 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, LS-Ack, length 64
05:46:45.068424 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, LS-Ack, length 44
05:46:49.366194 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:54.070050 IP router1.bridge1 > 6b9f6373be93: OSPFv2, LS-Update, length 64
05:46:54.071694 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:46:54.072015 IP 6b9f6373be93 > router1.bridge1: OSPFv2, LS-Update, length 64
05:46:54.072147 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, LS-Ack, length 44
05:46:54.276096 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, LS-Ack, length 44
05:46:59.357568 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:47:04.070503 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:47:09.357630 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:47:14.071479 IP 6b9f6373be93 > ospf-all.mcast.net: OSPFv2, Hello, length 48
05:47:19.357688 IP router1.bridge1 > ospf-all.mcast.net: OSPFv2, Hello, length 48
```

I downloaded the pcap file from docker to server and then to my local machine so that I could inspect it using wireshark.

```bash
$ docker cp router1:output router1.pcap
$ scp ykhalid@picard.cs.colgate.edu:router2.pcap ~/Desktop/router1.pcap
```

You can clearly see OSPF state changes:

![image-20201109011348817](/Users/yasoob/Library/Application Support/typora-user-images/image-20201109011348817.png)

The main benefit of using wireshark is that I can clearly see how the headers are layered. Scapy has bunch of OSPF classes and I was having a tough time figuring out how to layer them. Hopefully, it would be easier now.

### Useful links:

- [OSPF finite state machine](https://cyruslab.net/2012/04/01/ospf-finite-state-machine/)
- [OSPF state machine in detail](https://forum.huawei.com/enterprise/en/ospf-state-machine-in-detail/thread/484359-863)
- [OSPF RFC](https://tools.ietf.org/html/rfc2328#section-9.3)
- [Scapy OSPF docs](https://scapy.readthedocs.io/en/latest/api/scapy.contrib.ospf.html)
- [OSPF Adjacency & Neighbor Forming Process](http://www.firewall.cx/networking-topics/routing/ospf-routing-protocol/1129-ospf-adjacency-neighbor-forming-process-hello-packets-lsr-lsu.html)

### Next steps:

- Read more about how the designated router is decided. In this pcap dump 10.0.0.3 was decided as DR
- Why is the src dest of ethernet is 10.0.0.2/3 and the OSPF src/dest is 172.17.0.2/3?
- Maybe I wasn't able to generate the DB Description packet because of the IP mismatch. I use same addr for IP header and  OSPF header but wireshark says something else.
- How is the topology set up? What is a bridge and link?
- Figure out how to run tcpdump before `frr` is run so that I have even more concrete data to work with
- The modified packets were dropped by frr if something didn't match. Try to find a packet that crashes the router



It is easier to see the ip address discrepancy in this image:

![image-20201109014221321](/Users/yasoob/Library/Application Support/typora-user-images/image-20201109014221321.png)

## 10th November, 2020

### Meeting with Aaron:

- Change the packet length of hello packet. Essentially saying there is a hello but don't put one
- Generate byte data of packet and mutate it
- Change message type
- Change OSPF version
- Set Router Dead Interval to 0
- Change Priority to 0?
- `ospf router-id` http://docs.frrouting.org/en/latest/ospfd.html#configuring-ospf
- Change auth type to 2?
- Try to simulate a normal conversation using Scapy.....?

## 7th December, 2020

Had to update permissions for a lot of files to make it work again. `jchauhan` has reverted the permissions...

- /tmp/daemons
- /tmp/vtysh.conf
- /tmp/ospfd.conf

### command: 

```
sudo chown -R root:root /tmp/vtysh.conf
```

- Tried changing Packet length without adding a hello layer

```
2020/12/07 11:07:51 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:07:51 OSPF: ospf_packet_examin: packet length error (24 real, 48+0 declared)
```

### Message Type

- Changed message type to 2 

```python
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2', type=2, len=48)
packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, inter=1, iface="eth1")
```

```
2020/12/07 11:10:05 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:10:05 OSPF: ospf_lsaseq_examin: undersized (16 B) trailing (#0) LSA header
2020/12/07 11:10:05 OSPF: ospf_packet_examin: malformed Database Description packet
```

- Changed message type to 3

```python
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2', type=3)
#packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, inter=1, iface="eth1")
```

```
2020/12/07 11:10:40 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:10:40 OSPF: Link State Request received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 11:10:40 OSPF:  src [10.10.0.2],
2020/12/07 11:10:40 OSPF:  dst [10.10.0.3]
2020/12/07 11:10:40 OSPF: [EC 134217741] Link State Request: Unknown Neighbor 10.10.0.2
```

Even when I added/removed the hello layer, the output stayed the same.

- Changed type to 7

```python
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2', type=7, len=48)
packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, inter=1, iface="eth1")
```

```
2020/12/07 11:12:32 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:12:32 OSPF: ospf_packet_examin: invalid packet type 0x07
```



### OSPF Version

- Used version = 1

```
2020/12/07 11:20:49 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:20:49 OSPF: ospf_packet_examin: invalid (1) protocol version
```

- Used version = 3

```
2020/12/07 11:21:30 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:21:30 OSPF: ospf_packet_examin: invalid (3) protocol version
```

- Used version = 255

```
2020/12/07 11:23:16 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:23:16 OSPF: ospf_packet_examin: invalid (255) protocol version
```

- Used version = 999999

No output on the router side

### Hello Interval

- Used hellointerval=0

```
2020/12/07 11:24:33 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:24:33 OSPF: Hello received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 11:24:33 OSPF:  src [10.10.0.2],
2020/12/07 11:24:33 OSPF:  dst [10.10.0.3]
2020/12/07 11:24:33 OSPF: [EC 134217741] Packet 10.10.0.2 [Hello:RECV]: HelloInterval mismatch (expected 10, but received 0).
```



### Router Interval

- Used deadinterval=0

```
2020/12/07 11:25:43 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:25:43 OSPF: Hello received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 11:25:43 OSPF:  src [10.10.0.2],
2020/12/07 11:25:43 OSPF:  dst [10.10.0.3]
2020/12/07 11:25:43 OSPF: [EC 134217741] Packet 10.10.0.2 [Hello:RECV]: RouterDeadInterval mismatch (expected 40, but received 0).
```

- Used deadinterval=255

```
2020/12/07 11:26:52 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:26:52 OSPF: Hello received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 11:26:52 OSPF:  src [10.10.0.2],
2020/12/07 11:26:52 OSPF:  dst [10.10.0.3]
2020/12/07 11:26:52 OSPF: [EC 134217741] Packet 10.10.0.2 [Hello:RECV]: RouterDeadInterval mismatch (expected 40, but received 255).
```

- Used deadinterval=999999999

```
2020/12/07 13:22:43 OSPF: ospf_recv_packet: fd 15(default) on interface 4090(eth1)
2020/12/07 13:22:43 OSPF: Hello received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 13:22:43 OSPF:  src [10.10.0.2],
2020/12/07 13:22:43 OSPF:  dst [10.10.0.3]
2020/12/07 13:22:43 OSPF: [EC 134217741] Packet 10.10.0.2 [Hello:RECV]: RouterDeadInterval mismatch (expected 40, but received 999999999).
```



### Priority

- Changed prio=0 but seems to be working fine

```
2020/12/07 11:47:31 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:47:31 OSPF: Hello received from [10.10.0.2] via [eth1:10.10.0.3]
2020/12/07 11:47:31 OSPF:  src [10.10.0.2],
2020/12/07 11:47:31 OSPF:  dst [10.10.0.3]
2020/12/07 11:47:31 OSPF: Packet 10.10.0.2 [Hello:RECV]: Options *|-|-|-|-|-|E|- vrf default
2020/12/07 11:47:31 OSPF: NSM[eth1:10.10.0.3:10.10.0.2:default]: Init (PacketReceived)
2020/12/07 11:47:31 OSPF: NSM[eth1:10.10.0.3:10.10.0.2:default]: Init (1-WayReceived)
```

```
router2# show ip ospf neighbor

Neighbor ID     Pri State           Dead Time Address         Interface                        RXmtL RqstL DBsmL
10.10.0.2         0 Init/DROther       5.099s 10.10.0.2       eth1:10.10.0.3                       0     0     0
```

- Changed prio=255:

```router2# show ip ospf neighbor

Neighbor ID     Pri State           Dead Time Address         Interface                        RXmtL RqstL DBsmL
10.10.0.2       255 Init/DROther      39.714s 10.10.0.2       eth1:10.10.0.3                       0     0     0
```



### Auth 

- Changed authtype=1

```python
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2', authtype=3)
packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, inter=1, iface="eth1")
```

```
2020/12/07 11:51:12 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:51:12 OSPF: [EC 134217741] interface eth1:10.10.0.3: auth-type mismatch, local Null, rcvd Simple
2020/12/07 11:51:12 OSPF: ospf_read[10.10.0.2]: Header check failed, dropping.
```

- authtype=2

```
2020/12/07 11:52:07 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:52:07 OSPF: ospf_packet_examin: unsupported crypto auth length (0 B)
```

- authtype=3

```
2020/12/07 11:54:17 OSPF: ospf_recv_packet: fd 15(default) on interface 4017(eth1)
2020/12/07 11:54:17 OSPF: [EC 134217741] interface eth1:10.10.0.3: invalid packet auth-type (03)
2020/12/07 11:54:17 OSPF: ospf_read[10.10.0.2]: Header check failed, dropping.
```



### High int value error

Previously it was giving me an error whenever I tried to set a value of > 255 for an int field. Got over it by using this:

```
packet.setfieldval('authtype',300)
```





### Meeting with Aaron

- What happens if you set the deadinterval in the config to a nonsensical value as well? Ex. 0
- Look at the source code and see if we can find something? Look at the if condition boundaries
- Mutate the bytes of packets
- Simulate basic OSPF using scapy

Write a paper discussing what we want to do and why. What we have done so far. and what are the next steps
10.5pt



- A lot of work on verifying routing configs but not enough work on verifying correctness of routing software itself
- Want to push the field by working on verifying routing software



- We are trying to find vulnerabilities in ways routers handle routing control messages
- What is a vulnerability? A router crashes, router accepts an incorrect packet and continues execution when it should fail. This continued exection might lead to someone controlling how the routing is happening (hacking).



- We want to do it > less bugs for everyone



- Black box vs white box
- Black box: feed msgs and see what happens
- white box: look at source code and see if any bugs exist
- Challenges: Space of possible packets is big
- Source code is complex and lots of branching (makes symbolic execution hard to implement)
- Spec is informal and contains gaps that leaves a lot of stuff for individual interpretation



- How am I planning on solving this?
- Randomly mutate a packet's bytes
- Make different fields take edge values
- edge values determined by the values defined in the standard
- How did I do this? Talk about. scapy and how I examined logs to see whether it worked or not. 
- We are using frr as routing server
- In all cases router implementation accurately identified and rejected the packets



- End up  with an automated way for testing different values for different fields
- Explore whitebox approaches



Discuss related work as well.



- [radamsa (fuzzer)](https://gitlab.com/akihe/radamsa)
- [Automated fuzzer](https://github.com/blazeinfosec/pcrappyfuzzer/blob/master/pcrappyfuzzer.py)



Challenges And Possible Approaches

Our goal is to not necessarily to check a router's conformance to the protocol specification but rather what security vulnerabilities exist in the existing protocol implementation. The security vulnerabilities might be caused by errors in protocol specification or protocol implementation. We will be looking at the latter whereas the former is also an area of active research. Non-conformance to protocol specification does not by default lead to security vulnerabilities. 

There are a lot of challenges associated with testing routing software implementations. The code for protocols is often long and complex and this makes manual checks almost impossible. The protocol implementation might not conform exactly to the protocol specification and that leads to extra effort for manually making sense of the code. On top of that, a router might continue to function properly after receiving a faulty packet in one state but might error out after receiving the same faulty packet while being in a different internal state. For example, the router might not fail after receiving a faulty OSPF Hello packet right after booting up but might fail after receiving a faulty OSPF Hello packet right after receiving a Link State Update packet. 

There are two broad testing methedologies.

1. Whitebox testing

This approach requires access to the source code. One form of whitebox testing is symbolic execution. The basic idea is to explore some or all code paths that are present in the routing software and check if it leads to a crash or to an unwanted internal state. An example of white box testing is the paper by Pedrosa et al. \cite{189016} and their usage of symbolic execution to automatically derive tests by analyzing protocol code. This helped them automate for the search of tests that would trigger non-interoperability between two protocol implementations. 

Symbolic execution also runs into the previously mentioned issue of implementation code being long and complex. There is already some research \cite{189016} on how to solve this problem. Pedrosa et al. \cite{189016} solved it by introducing new search techniques that direct execution towards those parts that might lead to non-interoperability issues. This is in contrast to traditional symbolic execution that uses Depth First Search (DFS) to explore all possible code paths.

Other related white box testing approaches include Model Based Testing and creating a formally verified reference implementation. Each of these have their own benefits and drawbacks. For example, McMillan et. al \cite{10.1145/3341302.3342087} spent a lot of time translating the QUIC protocol specification into a formally verified implementation. However, there is no guarantee that the decisions they took while converting the informal and loose specifications into more concrete states and scenarios are exactly the same as the decisions made by other protocol implementors. 



2. Blackbox testing

This approach does not require access to the source code. It involves sending arbitrary control packets to the routing software and checking its effect. It still does require access to the router logs to check for more granular effect to the routing caused by the arbitrary control packets. The major challenges for blackbox testing are similar to the challenges for whitebox testing. There are a lot of possible packet permutations that need to be tested and the protocol specification is not formal. However, we don't need to know too much about the specification. We just need to know about the different internal states and the packet orders that will lead to those states. 

As far as I am aware, there hasn't been a lot of research on black box testing so I decided to start my research by following this methedology and testing an OSPF protocol implementation.


\section{My Approach}

I decided to start by testing one specific implementation of the OSPF protocol. The first step is to figure out the starting state of the router and then explore different states from there. We need to test all possible states and state transitions because, as mentioned in the previous section, a router might cause an error only after reciving a faulty packet in a specific state. In order to figure out these possible states and state transitions, I need to closely study protocol specification and write down all possible combinations.

There are three possible ways to craft the packets themselves for the testing. We can look at the specification and find out the different fields and their value bounds within different layers. After that, we can either manually select values within bounds, randomly select values between bounds or manually select edge values. I decided to go with the last approach of manually selecting edge values as "off-by-one" is a very common logic error in programming \cite{off-by-one}. However, as we will see in the next section, this approach did not yield any fruitful results in the preliminary experiments and necessitated a change in approach.

We also need to further define what something going wrong with the router means. In the most extreme case, this means that the router has crashed. This is easy to detect depending on how we are running the router software. For example, if we are running the software within docker, we can easily check for running docker processes to figure out if a container has failed. In a more granular case, failure might mean that the router did something that it wasn't supposed to. For instance, the router is showing an OSPF neighbour while it should not. Testing for this kind of failure requires deep knowledge about the logging output for a router and that knowledge is often non-transferrable as each router has its own way of outputing logs. This more granular failure detection is an open question.

\section{Implementation}

I used Docker containers for setting up the test bed on a single Ubuntu based server. I used FRRouting as an OSPF protocol implementation and Scapy (Python framework) for generating and sending custom packets. I started by setting up two FRRouting instances in two separate docker containers that shared the same network. I ran tcpdump on these containers and  analyzed the packet dump using Wireshark to get better understanding of a normal OSPF packet communication (\ref{fig:wireshark}). After that I ran Scapy on one docker container and FRR on another and sent custom packets from Scapy to FRR. I monitored the logs of FRR to verify the reception and processing of packets. 

I started testing by sending the OSPF Hello packet from Scapy. I read the OSPF specification to figure out the different fields in an OSPF Hello packet and then set the edge values based on that. Some example code for sending an OSPF packet with custom neighbour, dead interval and, options can be seen in code listing (TODO: x). I set the edge values for message type, OSPF version, Hello interval, router interval, priority and auth type.

```python
from scapy.contrib.ospf import *
packet = Ether(src='02:42:0a:0a:00:02',dst='02:42:0a:0a:00:03')
packet = packet/IP(src='10.10.0.2',dst='10.10.0.3')
packet = packet/OSPF_Hdr(src='10.10.0.2')
packet = packet/OSPF_Hello(router='10.10.0.2',neighbors=['10.10.0.3'], mask="255.255.255.248", options=0x02, deadinterval=0)
sendp(packet, loop=True, inter=1, iface="eth1")
```

These experiments did not cause the router to crash. FRR accurately identified erronous packets and all packets were correctly accepted or dropped as appropriate. 

\section{Future Work}

I need to look at more packet types and transmit packets in different orders to test all possible router states. Moreover, so far I have manually modified packets before sending them to FRR. This is time consuming and does not scale. I want to end up with an automated method for testing values of different fields in routing control packets. This might take the shape of specifying Scapy layers in an XML and then using a smart fuzzing framework like Radamsa to automatically specify and mutate packet values before sending it over the wire \cite{6227765}.





1. Blackbox testing

- Goal is to focus on the ideas. Including different approaches, challenges that come up, what I have done and obtained in terms of experimental results and what that leads to in terms of next steps.
- Intro: What has already been done.
  - There has been extensive work in white box testing but we worked on black box that hasn't received enough attention
- Here are the challenges that we face. What might we do. We might take a white box approach to these challenges. Most are fixed by existing research but not all. No clear good solution for lack of clear RFC.
- With black box we still face this branching issue. We still need to know the spec but we don't need to know enough.
- Our goal is not necessarily to check a router's conformance to the spec. Goal is to understand what security vulns exist and where  have error conditions not properly been checked. Some error conditions may be in spec some may be in code. Good defensive coding should prevent most of these.
- Section 2 becomes "challenges and possible approaches"
- You need to know enough spec to know what packets are allowed and what routers might respond with
- Another challenge is if you send a faulty packet at the beginning, router will accept, however, if you send it later on, when the router has reached a specific state, router might fail. Ex. Link State Update might not fail. But if you send Hello and then LSU then it might fail.



- For "My Approach", change idea from experiment.

- Approach: 

  - Whats the starting state of the router? How do you explore different states of the router? 
    - In some sense we care about completeness
    - Here is the approach and say that you have begun to experiment with the first component
    - Look at the spec. Write down the packets that need to be sent for the router to end up at each specific state.

  - How do you craft these packets.
    - Look at the spec, either manually select values within bounds, randomly select values between bounds or manually select edge values
    - Talk about why we choose edge value test and random mutation separately
    - As we show in section 4, our priliminary approach using this didn't work.
  - How do you detect that something has gone wrong
    - Extreme case of looking at docker crash
    - Requires understanding of looking at logs
      - Remains an open question. So far doing manually



Section 4

- Then talk about the second component. Talk about experimental setup. Docker, FRR, Scapy. What packets was I mutating. Right now I talk generally about edge values. Write more specifically about which fields I looked at. (Edge values) and packet crafting. 
- It wasn't illiciting errors. Talk about the need for a change in approach. Something that keeps the search space small, Smart fuzzing etc.
- Call it preliminary testing.



- Used FRR and used Scapy. Talk about approach. we weren't able to get errors. Just like we alluded in Section 3, need to look at More packets.




It follows the Dravida style of construction that is apparent in the pyramidal construction style of the temple.



