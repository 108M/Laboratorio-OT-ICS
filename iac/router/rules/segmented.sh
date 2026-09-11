#!/bin/sh
# Estado "DESPUES": conducto IEC 62443 aplicado entre la zona IT/atacante
# (192.168.10.0/24) y la zona de Control (192.168.20.0/24).
#
# Politica: DROP por defecto entre zonas; unico permiso explicito = el
# conducto legitimo HMI -> PLC sobre Modbus TCP/502. Todo lo demas que
# intente cruzar de una zona a otra se descarta y se registra.
set -e

HMI_IP="192.168.20.20"
PLC_IP="192.168.20.10"
ZONA_IT="192.168.10.0/24"
ZONA_CONTROL="192.168.20.0/24"

nft flush ruleset

nft add table inet conduit
nft add chain inet conduit forward '{ type filter hook forward priority 0; policy drop; }'

# Trafico de vuelta de conexiones ya establecidas (respuestas Modbus, etc.)
nft add rule inet conduit forward ct state established,related accept

# Unico conducto permitido: HMI -> PLC, Modbus TCP (puerto 502)
nft add rule inet conduit forward ip saddr $HMI_IP ip daddr $PLC_IP tcp dport 502 accept

# Cualquier otro intento de la zona IT hacia la zona de Control queda
# registrado y contado explicitamente antes de caer en la politica DROP por
# defecto. El "counter" es la evidencia portable (consultar con
# `docker compose exec router nft list ruleset`); el "log" solo aparece en
# `dmesg` si el kernel del host expone el target LOG a este namespace de red
# (no siempre es el caso, p. ej. en WSL2 -- ver docs/lecciones_aprendidas.md).
nft add rule inet conduit forward ip saddr $ZONA_IT ip daddr $ZONA_CONTROL counter log prefix \"CONDUCTO-BLOQUEADO \" drop

echo "[router] modo SEGMENTED aplicado: solo $HMI_IP -> $PLC_IP:502 permitido entre zonas."
echo "[router] evidencia de bloqueos: docker compose exec router nft list ruleset"
