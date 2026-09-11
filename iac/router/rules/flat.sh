#!/bin/sh
# Estado "ANTES": red plana. El router reenvia todo el trafico entre la zona
# IT/atacante y la zona de Control sin ninguna restriccion — asi suelen estar
# hoy muchas redes OT que nunca se segmentaron.
set -e

nft flush ruleset

nft add table inet conduit
nft add chain inet conduit forward '{ type filter hook forward priority 0; policy accept; }'

echo "[router] modo FLAT aplicado: todo el trafico entre zonas esta permitido."
