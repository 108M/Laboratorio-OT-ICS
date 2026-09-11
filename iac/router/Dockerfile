FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nftables iproute2 iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY rules/ /rules/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /rules/*.sh /entrypoint.sh

# Arranca en modo "flat" (red plana, sin segmentacion) por defecto y se queda
# corriendo en foreground. Cambiar de modo en caliente, sin reiniciar el
# contenedor, con:
#   docker compose exec router /rules/segmented.sh
#   docker compose exec router /rules/flat.sh
ENTRYPOINT ["/entrypoint.sh"]
