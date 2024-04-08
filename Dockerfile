FROM ubuntu:20.04 AS build
ARG TARGETOS TARGETARCH
LABEL MAINTAINER="Anatolii Makarov <anatolii.makaroff@gmail.com>"

RUN apt-get update && \
    apt-get -y install \
        curl \
        git \
        libldap2-dev libsasl2-dev \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        vim-tiny && \
    apt-get -qq clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# RUN useradd -ms /bin/bash appuser
COPY . /app
RUN rm -rf /app/app.yaml /app/config/app.db
# RUN chown -R appuser:appuser /app
RUN python3 -m venv pyenv && pyenv/bin/pip install --upgrade pip wheel setuptools \
 && pyenv/bin/pip install -r requirements.txt

RUN chgrp -R 0 /app && \
    chmod -R g=u /app 
RUN chown -R 1001:0 /app

RUN touch //.gitconfig && chgrp -R 0 //.gitconfig && chmod -R g=u //.gitconfig && \
    chown 1001:0 //.gitconfig

USER 1001

ENV PORT=8082 
ENV LOGLEVEL=INFO
ENV PYENV=/app/pyenv/bin

CMD ["./start"]
