FROM alpine:3

# Prepare base system
RUN apk update && apk upgrade && \
    apk add python3 py3-pip

# Install sma-em daemon
RUN mkdir -p /opt/smaemd && mkdir -p /etc/smaemd
WORKDIR /opt/smaemd
COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt 

RUN mkdir -p /opt/smaemd/features && mkdir -p /opt/smaemd/libs

COPY daemon3x.py \
sma-daemon.py \
sma-em-capture-package.py \
sma-em-measurement.py \
speedwiredecoder.py ./

COPY run_smaemd.sh /root/
RUN chmod +x /root/*

CMD ["/root/run_smaemd.sh"]

COPY libs/* libs/

COPY features/* features/

