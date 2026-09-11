FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends suricata iproute2 \
    && rm -rf /var/lib/apt/lists/*
COPY modbus.rules /rules/modbus.rules
