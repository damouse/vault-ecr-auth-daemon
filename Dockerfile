# FROM damouse/python-common
FROM python:3.6.8-alpine3.6

# RUN apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev

# ENV PYTHONPATH "${PYTHONPATH}:/app/authdaemon/:/app/common"

# Hatch system deps
# RUN apt-get update && \
#     apt-get install -y \
#     openvpn \
#     iptables \
#     openssh-client \
#     iputils-ping 

# Hatch deps-- DO NOT EDIT
RUN pip install \
    hvac==0.6.3 \
    # pyopenssl==18.0.0 \
    # psutil==5.4.2 \
    # haikunator==2.1.0 \
    # pexpect==4.3.1 \
    # websockets==4.0.1 \
    # colorama==0.3.9 \
    PyYAML==3.12 \
    boto3==1.9.31 \
    # pexpect==4.3.1 \
    aiofiles==0.3.2

RUN apk update && apk add ca-certificates wget && update-ca-certificates   

# Docker client
# RUN wget https://download.docker.com/linux/static/stable/x86_64/docker-18.03.1-ce.tgz  && \
#     tar xzvf docker-18.03.1-ce.tgz --strip 1 -C /usr/local/bin docker/docker && \
#     rm docker-18.03.1-ce.tgz

# COPY common common
# RUN git -C common checkout -f 1.1.20 
# COPY tests tests

# TODO: move to top
WORKDIR /app
ENV HOME=/app
ENV PYTHONUNBUFFERED 1


COPY main.py main.py 
CMD python main.py
