# Ataque de demostración: por qué Modbus TCP no tiene autenticación

> **Ámbito:** estos scripts solo funcionan contra el PLC virtual de este
> laboratorio (`_lab_guard.py` aborta la ejecución si el objetivo no está en
> la subred `192.168.20.0/24`). No están pensados ni deben usarse contra
> ningún sistema real.

## Por qué Modbus TCP es vulnerable por diseño

Modbus (1979) se diseñó para buses serie punto a punto dentro de un armario
eléctrico, con confianza implícita en el medio físico. Modbus TCP (años 90)
lo encapsuló sobre TCP/IP sin añadir autenticación, cifrado ni control de
acceso — el protocolo no tiene concepto de "usuario" ni de "permiso de
escritura". Cualquier cliente TCP que alcance el puerto 502 puede leer o
escribir cualquier registro que el dispositivo exponga. Esta es la causa raíz
que ilustra todo este laboratorio; no es un bug de OpenPLC ni de pymodbus.

## Cadena de ataque, mapeada a MITRE ATT&CK for ICS

| # | Script | Acción | Táctica ATT&CK for ICS | Técnica |
|---|--------|--------|--------------------------|---------|
| 1 | `01_recon.py` | Sondea holding registers y coils sin ninguna credencial | Discovery (TA0102) | [T0846 – Remote System Discovery](https://attack.mitre.org/techniques/T0846/) |
| 2 | `02_unauthorized_read.py` | Lee setpoint, nivel, bomba y alarma | Collection (TA0100) | [T0801 – Monitor Process State](https://attack.mitre.org/techniques/T0801/) |
| 3 | `03_unauthorized_write_setpoint.py` | Escribe un setpoint malicioso (100 %) | Impair Process Control (TA0106) | [T0836 – Modify Parameter](https://attack.mitre.org/techniques/T0836/) |
| 4 | `04_unauthorized_write_coil.py` | Bombardea el coil de la bomba para forzarla ON | Impair Process Control (TA0106) | [T0855 – Unauthorized Command Message](https://attack.mitre.org/techniques/T0855/) |
| — | *(consecuencia de 3 y 4)* | Bomba forzada, alarma de nivel alto parpadeando | Impact (TA0105) | [T0831 – Manipulation of Control](https://attack.mitre.org/techniques/T0831/) |

Tabla ampliada, con capturas de pantalla y explicación de cada campo, en
[`docs/mitre_attack_ics_mapping.md`](../docs/mitre_attack_ics_mapping.md).

## Cómo ejecutar la demo

Con el laboratorio en pie (`make up`, ver README principal) y en modo `flat`
(`make flat`):

```bash
docker compose exec attacker python 01_recon.py
docker compose exec attacker python 02_unauthorized_read.py
docker compose exec attacker python 03_unauthorized_write_setpoint.py --valor 1000
docker compose exec attacker python 04_unauthorized_write_coil.py --segundos 10
```

Observa el HMI en `http://localhost:5000` mientras se ejecutan: el nivel del
depósito, la bomba y la alarma reaccionan en tiempo real a un tráfico que
nunca pasó por el HMI ni por ninguna credencial.

Repite la misma secuencia tras `make segmented` (ver
[`segmentation/IEC62443_zonas_conductos.md`](../segmentation/IEC62443_zonas_conductos.md))
para comprobar que el conducto IEC 62443 bloquea el tráfico antes de que
llegue al PLC.
