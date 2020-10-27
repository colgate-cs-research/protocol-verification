FROM ubuntu:latest
RUN apt update && apt install -y nano bird2 iproute2; exit 0
RUN touch /usr/share/doc/bird2/examples/bird.conf && apt install -y bird2
CMD ["/bin/bash"]
