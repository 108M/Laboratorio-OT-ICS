# Qué aprendí construyendo este laboratorio

*(Borrador para personalizar con tu propia voz antes de publicar el repo —
son los puntos que un reclutador técnico suele preguntar en entrevista.)*

## Sobre el protocolo

- Modbus TCP no es "inseguro por un bug": es un protocolo de 1979 (bus serie)
  encapsulado sobre TCP/IP sin que nadie le añadiera autenticación después.
  Verlo explotado con 15 líneas de `pymodbus` (sin exploit, sin bypass, solo
  una conexión TCP y una escritura) deja mucho más claro por qué la
  arquitectura de red importa más que "parchear" en estos entornos: no hay
  parche para "el protocolo no tiene usuarios".
- No toda escritura Modbus tiene el mismo efecto: escribir un *parámetro*
  (setpoint) que el PLC sigue leyendo cada ciclo es persistente; escribir una
  *salida* que el propio programa recalcula cada scan es transitorio salvo
  que se bombardee. Es una distinción que solo se aprecia construyendo el
  PLC, no leyendo sobre el ataque en abstracto.

## Sobre la arquitectura de red

- Levantar de verdad dos zonas Docker separadas por un contenedor router
  (en vez de simular la segmentación con reglas de `iptables` en el propio
  host) obliga a entender rutas estáticas, `internal: true` en redes Docker,
  y `ip_forward` por *namespace* de red — cosas que en un diagrama de
  PowerPoint se dan por hechas y que en la práctica hay que depurar paquete
  a paquete.
- Colocar el IDS compartiendo el *network namespace* del PLC
  (`network_mode: "service:container"`) en vez de intentar montar un puerto
  espejo sobre un bridge de Docker fue la solución más simple y, además, la
  arquitectónicamente correcta: un IDS "en el conducto" ve justo el tráfico
  que le corresponde.

## Sobre la defensa en profundidad (la lección central)

- El hallazgo más importante no es "Suricata detecta" ni "el firewall
  bloquea" por separado, sino verlos fallar de formas *distintas y
  complementarias*: segmentar sin detectar deja ciego cualquier ataque que
  sí entre por el conducto legítimo (p. ej. un HMI comprometido); detectar
  sin segmentar solo avisa después del hecho. Documentarlo con el mismo
  ataque ejecutado dos veces (antes/después) fue más convincente que
  cualquier explicación en texto.
- IEC 62443 no es una checklist de firewalls: obliga a decidir explícitamente
  qué SL-T te propones por zona y a admitir con honestidad qué SL-A logras
  realmente. Segmentar la red no llevó la zona de Control a SL2 pleno (el
  HMI y el PLC siguen confiando ciegamente entre sí dentro de la zona) — y
  decir eso en la documentación, en vez de venderlo como "problema resuelto",
  es la parte del ejercicio que más se parece a un informe real.

## Qué haría distinto / próximos pasos

- Añadir un gateway Modbus-aware con *allow-listing* de function codes
  dentro de la propia zona de Control, no solo en el perímetro.
- Automatizar la carga del programa ST en OpenPLC (hoy es un paso manual por
  la web UI) para poder levantar el laboratorio end-to-end sin intervención.
- Probar el mismo laboratorio con un segundo protocolo (p. ej. DNP3 con
  Secure Authentication) para comparar cómo cambia — o no — la historia de
  ataque/detección/segmentación cuando el protocolo sí soporta seguridad.
