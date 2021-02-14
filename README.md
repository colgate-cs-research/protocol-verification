# protocol-verification
# Package Installation

<p>
Install the following packages using the following commands:
<pre>
$ sudo apt update
$ sudo apt install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
$ sudo apt update
$ sudo apt install docker-ce docker-ce-cli containerd.io
$ docker pull kaazing/tcpdump
</pre>
More details on how to install the packages:https://linuxize.com/post/how-to-install-and-use-docker-on-ubuntu-20-04/
</p>

# Network Establishment and Configuration

<p>
The <code>frr_config.py</code> file can be used to create networks based on topologies provided in <code>.json</code> format, and currently supports routing protocol implementations including OSPF (FRRouting and BIRD) and BGP (FRRouting). All router and interface in the network are constructed using the Docker containers and networks.
  
Following is a detailed description of <code>frr_config.py</code>:
<pre>
usage: python3 frr_config.py [-c Path_to_JSON _config_file] [-a Operation_to_perform] [-t Option_to_have_tcpdump_on] [-d Interfaces_to_apply_delay_to]

optional arguments:
  -c , --config         Input path to JSON config/topology file for creating the network
  -a, --action          Decide on operation to perform on the network
                        Choices=['start', 'stop', 'restart']
  -t, --tcp             Decide on whether to capture transmitted packets using tcpdump or not
                        Choices=['tcpon', NONE]               
  -d, --delay           Input interfaces to apply default delay, seperated by '/'
                        Example input: -d eth1/eth2/eth3      
</pre>
Established network and routers run in the background until stopped and removed, and the interaction with running networks and routers are documented in the next section.
</p>

# Network and Router CLI Commands (FRRouting)

<p>
The Docker <code>exec</code> command allows for interaction with the network and routers running in the background, and the command started using docker exec only runs while the container’s primary process (PID 1) is running, and it is not restarted if the container is restarted.
  
To get interactive access(command line access) and create a new bash session in the container(INSTANCE_NAME):
<pre>
$ docker exec -it INSTANCE_NAME sh
</pre>

Following is a description of some useful <code>exec</code> options:
<pre>
--interactive , -i 	 Keep STDIN open even if not attached 
--privileged 		 Give extended privileges to the command 
--tty , -t               Allocate a pseudo-TTY
</pre>

More_info: https://docs.docker.com/engine/reference/commandline/exec/

While in interactive access, using <code>#vtysh</code> allows for entering the VTY Shell, and some often used VTY Shell commands are:
<pre>
INSTANCE_NAME# show ip ospf              Display general information about OSPF routing processes
INSTANCE_NAME# show ip ospf neighbor     Display OSPF neighbor information on a per-interface basis
INSTANCE_NAME# show ip ospf interface    Display OSPF interface information.
</pre>
More_info: http://docs.frrouting.org/en/latest/ospfd.html
</p>

# Network and Router CLI Commands (BIRD)
<p>
Use command-line client <code>birdc</code> to talk with a running router/containers running BIRD OSPF.
  
Following is a description of some useful supported functions:
<pre>
INSTANCE_NAME# show interfaces [summary]                  Show the list of interfaces. For each interface, print its type, state, MTU and addresses assigned
INSTANCE_NAME# show ospf interface [name] ["interface"]   Show detailed information about OSPF interfaces
INSTANCE_NAME# show ospf neighbors [name] ["interface"]   Show a list of OSPF neighbors and a state of adjacency to them.
</pre>
More_info: https://bird.network.cz/?get_doc&v=20&f=bird-4.html
<p>
