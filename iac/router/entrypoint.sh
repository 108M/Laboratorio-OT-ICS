#!/bin/sh
# El forwarding IP (net.ipv4.ip_forward=1) lo aplica docker-compose.yml via la
# clave "sysctls" (no usamos el binario sysctl aqui, no viene instalado con
# nftables/iproute2).
set -e

# Estado inicial del laboratorio: red plana (sin segmentacion). Cambiar de
# modo despues de arrancar con: docker compose exec router /rules/segmented.sh
/rules/flat.sh

echo "[router] modo inicial: FLAT (sin segmentacion). Usa /rules/segmented.sh para aplicar el conducto IEC 62443."
exec tail -f /dev/null
