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
| 1000002 | Escritura del setpoint (holding register 0) desde cualquiera que no sea el HMI (192.168.20.20) | T0836 |
| 1000003 | Cualquier escritura por red al coil de la bomba (coil 0) | T0855 |
| 1000004 | Lectura del proceso desde cualquiera que no sea el HMI | T0801 |

## Ejecutar la comparación antes/después

```bash
make up
make flat
make attack-write-setpoint      # el ataque llega al PLC
docker compose logs suricata     # confirma la alerta SID 1000002 en stdout
cp detection/evidence/eve.json detection/evidence/eve_flat.json

make segmented
make attack-write-setpoint      # el mismo ataque, ahora bloqueado en el router
docker compose logs router       # confirma la linea "CONDUCTO-BLOQUEADO"
```

`detection/evidence/eve.json` (montado desde el contenedor `suricata`) es el
log real de Suricata en formato
[EVE JSON](https://docs.suricata.io/en/latest/output/eve/eve-json-format.html).
`detection/evidence/eve_flat.example.json` incluido en este repo es un
**ejemplo ilustrativo** del formato esperado (para poder revisar la
estructura sin tener que levantar el laboratorio) — la evidencia real se
genera ejecutando los pasos de arriba.
