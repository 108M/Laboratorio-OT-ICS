"""
01_recon.py - Reconocimiento pasivo/activo del dispositivo Modbus del laboratorio.

MITRE ATT&CK for ICS: T0846 - Remote System Discovery (tactica Discovery, TA0102)
https://attack.mitre.org/techniques/T0846/

Modbus TCP no tiene ningun mecanismo de descubrimiento con autenticacion: un
cliente cualquiera puede sondear un rango de holding registers y coils para
inferir que expone el dispositivo, sin necesitar ninguna credencial. Esto es
exactamente lo que hace este script contra el PLC virtual del laboratorio.

Uso: python 01_recon.py [--host 192.168.20.10] [--port 502]
"""
import argparse

from pymodbus.client import ModbusTcpClient

from _lab_guard import ensure_lab_target

RANGO_REGISTROS = range(0, 8)
RANGO_COILS = range(0, 8)


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

    print(f"[*] Conectado a {args.host}:{args.port} sin ninguna credencial.\n")

    print("[*] Sondeando holding registers (FC03)...")
    for addr in RANGO_REGISTROS:
        resp = client.read_holding_registers(address=addr, count=1, device_id=args.unit_id)
        if not resp.isError():
            print(f"    holding_register[{addr}] = {resp.registers[0]}")

    print("\n[*] Sondeando coils (FC01)...")
    for addr in RANGO_COILS:
        resp = client.read_coils(address=addr, count=1, device_id=args.unit_id)
        if not resp.isError():
            print(f"    coil[{addr}] = {resp.bits[0]}")

    client.close()
    print(
        "\n[*] Reconocimiento completo. Ningun paso anterior requirio "
        "autenticacion: asi es como un atacante mapea un PLC Modbus "
        "desconocido antes de decidir que registro manipular."
    )


if __name__ == "__main__":
    main()
