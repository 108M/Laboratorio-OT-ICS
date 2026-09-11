# Extiende la imagen oficial de OpenPLC v3 (construida por separado desde
# https://github.com/thiagoralves/OpenPLC_v3.git, ver Makefile) con iproute2,
# necesario para la ruta estatica hacia la zona IT/atacante a traves del router
# (ver docker-compose.yml). La imagen upstream no lo incluye.
FROM openplc-upstream:latest
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 \
    && rm -rf /var/lib/apt/lists/*
