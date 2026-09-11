#!/bin/sh
# Habilita el forwarding IP dentro del namespace de red de este contenedor
# (requiere cap_add: NET_ADMIN en docker-compose.yml; no hace falta --privileged).
set -e
sysctl -w net.ipv4.ip_forward=1 >/dev/null

# Estado inicial del laboratorio: red plana (sin segmentacion). Cambiar de
# modo despues de arrancar con: docker compose exec router /rules/segmented.sh
/rules/flat.sh

echo "[router] modo inicial: FLAT (sin segmentacion). Usa /rules/segmented.sh para aplicar el conducto IEC 62443."
exec tail -f /dev/null
