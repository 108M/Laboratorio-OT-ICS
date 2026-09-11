FROM ubuntu:24.04
# Suricata se retiro del archivo estable de Debian (dependencias Rust rotas);
# se instala desde el repositorio oficial de OISF para Ubuntu.
RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:oisf/suricata-stable \
    && apt-get update \
    && apt-get install -y --no-install-recommends suricata iproute2 \
    && rm -rf /var/lib/apt/lists/*
COPY modbus.rules /rules/modbus.rules
