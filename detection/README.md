# Detección: Suricata sobre Modbus TCP

## Dónde se sitúa el sensor

El servicio `suricata` de `docker-compose.yml` arranca con
`network_mode: "service:openplc"`: comparte el *network namespace* del
contenedor del PLC en vez de tener su propia red. Así ve, sin necesitar un
puerto espejo ni una interfaz en modo promiscuo sobre un bridge de Docker,
exactamente el tráfico que entra y sale del PLC — la posición correcta para
un IDS "en el conducto" según IEC 62443.

Consecuencia importante (ver también `segmentation/IEC62443_zonas_conductos.md`
§5): en modo `segmented`, el tráfico bloqueado por el `router` **nunca llega**
a esta interfaz, así que no genera alerta de Suricata — el bloqueo ocurre una
capa antes. Esto no es un fallo de la regla, es la prueba de que la
segmentación está funcionando.

## Reglas (`suricata/modbus.rules`)

| SID | Detecta | Técnica ATT&CK for ICS |
|-----|---------|---------------------------|
| 1000001 | Ráfaga de peticiones Modbus desde un mismo origen (recon) | T0846 |
| 1000002 | Escritura del setpoint (holding register 0) vía FC16 (Write Multiple Registers) desde cualquiera que no sea el HMI | T0836 |
| 1000003 | Escritura de coils vía FC15 (Write Multiple Coils) | T0855 |
| 1000004 | Lectura del proceso desde cualquiera que no sea el HMI | T0801 |
| 1000005 | Escritura del setpoint vía FC06 (Write Single Register) — la que realmente usa `attack/03_unauthorized_write_setpoint.py`/pymodbus | T0836 |
| 1000006 | Escritura de un coil vía FC05 (Write Single Coil) — la que realmente usa `attack/04_unauthorized_write_coil.py`/pymodbus | T0855 |

Las reglas 1000002/1000003 (con la palabra clave de alto nivel `modbus:
access write ...`) y 1000005/1000006 (con `modbus: function 6/5` explícito)
son intencionalmente redundantes: en las pruebas de este laboratorio, con
Suricata 8.0.6 la keyword `access write holding/coils` **no** disparó con
FC06/FC05 (las que usa pymodbus por defecto), solo con las variantes
"multiple". Se documentan ambas para cubrir cualquier cliente Modbus,
sea cual sea la función que use — y el hallazgo en sí queda registrado en
[`docs/lecciones_aprendidas.md`](../docs/lecciones_aprendidas.md).

## Ejecutar la comparación antes/después

```bash
make up
make flat
make attack-write-setpoint

# Las alertas van al log EVE (no a stdout de Suricata):
grep -o '"signature":"[^"]*"' detection/evidence/eve.json | sort -u
cp detection/evidence/eve.json detection/evidence/eve_flat.json

make segmented
make attack-write-setpoint      # ahora falla con timeout: el router lo bloquea antes de llegar al PLC

# Evidencia del bloqueo (contador de la regla, no depende de dmesg/journald):
docker compose exec router nft list ruleset
```

`detection/evidence/eve.json` (montado desde el contenedor `suricata`) es el
log real de Suricata en formato
[EVE JSON](https://docs.suricata.io/en/latest/output/eve/eve-json-format.html).
`detection/evidence/eve_flat.example.json` incluido en este repo es un
**ejemplo ilustrativo** del formato esperado — la evidencia real se genera
ejecutando los pasos de arriba (verificado end-to-end al construir este
laboratorio).
