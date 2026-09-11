# Mapeo detallado a MITRE ATT&CK for ICS

Cada paso de `attack/` mapeado a la [matriz MITRE ATT&CK for ICS](https://attack.mitre.org/matrices/ics/),
con la mitigación real de MITRE y cómo la aborda (o no) este laboratorio.

## TA0102 – Discovery → T0846 Remote System Discovery

- **Qué hace `01_recon.py`:** sondea holding registers y coils 0-7 sin
  ninguna credencial para inferir qué expone el dispositivo.
- **Referencia:** <https://attack.mitre.org/techniques/T0846/>
- **Mitigación MITRE:** segmentación de red y control de acceso para
  limitar qué hosts pueden alcanzar el dispositivo Modbus.
- **En este laboratorio:** `segmentation/` implementa exactamente esa
  mitigación — en modo `segmented`, el `attacker` ni siquiera puede alcanzar
  el puerto 502 del PLC, así que el recon falla en el primer paquete.

## TA0100 – Collection → T0801 Monitor Process State

- **Qué hace `02_unauthorized_read.py`:** lee setpoint, nivel, bomba y
  alarma — inteligencia sobre el estado del proceso.
- **Referencia:** <https://attack.mitre.org/techniques/T0801/>
- **Mitigación MITRE:** control de acceso a la red y encriptación de las
  comunicaciones (Modbus TCP nativo no soporta ninguna de las dos).
- **En este laboratorio:** la regla Suricata SID 1000004 detecta lecturas
  desde un origen distinto del HMI; la segmentación de red impide que la
  zona IT comprometida llegue a leer nada del PLC.

## TA0106 – Impair Process Control → T0836 Modify Parameter

- **Qué hace `03_unauthorized_write_setpoint.py`:** escribe un setpoint
  malicioso (holding register 0) sin pasar por el HMI.
- **Referencia:** <https://attack.mitre.org/techniques/T0836/>
- **Ejemplo real citado por MITRE:** FrostyGoop (ataque a Modbus TCP en
  Ucrania, 2024) se mapea a T0836 + T0801 + T0869 + T0885 + T0807 — la
  misma familia de técnicas que ilustra este laboratorio, sobre el mismo
  protocolo.
- **Mitigación MITRE:** validar los parámetros recibidos contra rangos
  seguros antes de aplicarlos; separar la función de seguridad (interlock)
  del parámetro de control.
- **En este laboratorio:** el interlock de nivel alto (`alto_nivel_alarma`
  en `plc/tank_control.st`) es exactamente esa separación — no está mapeado
  a Modbus, así que el ataque al setpoint no puede desactivar la función de
  seguridad, solo forzar un comportamiento anómalo dentro de sus límites.

## TA0106 – Impair Process Control → T0855 Unauthorized Command Message

- **Qué hace `04_unauthorized_write_coil.py`:** bombardea el coil de la
  bomba con escrituras para forzarla ON, compitiendo con el ciclo de scan
  del PLC.
- **Referencia:** <https://attack.mitre.org/techniques/T0855/>
- **Ejemplo real citado por MITRE:** Dallas Siren Incident (activación no
  autorizada de sirenas de alarma de tornado).
- **Mitigación MITRE:** los dispositivos que reciben comandos deberían
  verificarlos antes de actuar; *allow-listing* de comandos de protocolo
  automatización a nivel de red.
- **En este laboratorio:** las reglas Suricata SID 1000003/1000006 alertan
  ante cualquier escritura por red a ese coil (nadie debería escribirlo
  nunca; ver `detection/README.md` sobre por qué son dos reglas y no una);
  un firewall consciente de protocolo (Modbus-aware) en el conducto sería
  el siguiente paso natural (ver "trabajo futuro" en `segmentation/`).

## TA0105 – Impact → T0831 Manipulation of Control

- **Consecuencia observable** de T0836/T0855: la bomba se enciende más de
  lo previsto, el nivel se acerca al límite de seguridad y la alarma de
  nivel alto empieza a activarse/desactivarse (alarm chattering) — visible
  en vivo en `hmi-dashboard` (`http://localhost:5000`).
- **Referencia:** <https://attack.mitre.org/techniques/T0831/>
- **Por qué no hay overflow real:** el interlock de seguridad (independiente
  del setpoint) limita el daño — el impacto demostrado es degradación del
  proceso y fatiga de la función de seguridad, no destrucción física. Es una
  representación más realista de un incidente OT que un "todo o nada".
