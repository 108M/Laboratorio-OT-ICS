"""
Guardarrail compartido por todos los scripts de attack/.

Estos scripts son EJERCICIOS DE LABORATORIO. Solo deben apuntar al PLC
virtual de este repositorio, dentro de la red aislada que crea
docker-compose.yml (subred de control 192.168.20.0/24 por defecto). Nunca
deben usarse contra un sistema real, y este modulo aborta la ejecucion si el
objetivo declarado no esta dentro de esa subred de laboratorio.
"""
import ipaddress
import os
import sys

LAB_SUBNET = ipaddress.ip_network(os.environ.get("LAB_SUBNET", "192.168.20.0/24"))

DISCLAIMER = """
==============================================================================
 EJERCICIO DE LABORATORIO - uso exclusivo contra el PLC virtual de este repo.
 No autorizado para ningun sistema fuera de la red aislada de este proyecto.
 Ver README.md y attack/README.md antes de ejecutar.
==============================================================================
"""


def ensure_lab_target(host: str) -> None:
    print(DISCLAIMER)
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        print(f"[abort] '{host}' no es una direccion IP valida.")
        sys.exit(1)
    if ip not in LAB_SUBNET:
        print(
            f"[abort] {host} esta fuera de la subred del laboratorio "
            f"({LAB_SUBNET}). Este script se niega a ejecutarse contra "
            f"cualquier otro objetivo."
        )
        sys.exit(1)
