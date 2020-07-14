FROM frrouting/frr as source-builder
USER root
RUN apk add --update py-pip
RUN pip install --upgrade pip \
    pip3 install --pre scapy[basic] \