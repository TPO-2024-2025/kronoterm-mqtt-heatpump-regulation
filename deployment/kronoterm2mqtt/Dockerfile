FROM mcr.microsoft.com/devcontainers/python:3.11

RUN git clone --recursive https://github.com/nikolabr/kronoterm2mqtt.git
WORKDIR /kronoterm2mqtt

RUN mkdir -p /root/.config/kronoterm2mqtt
COPY kronoterm2mqtt.toml /root/.config/kronoterm2mqtt

COPY kronoterm_ksm.toml /kronoterm2mqtt/kronoterm2mqtt/definitions/kronoterm_ksm.toml