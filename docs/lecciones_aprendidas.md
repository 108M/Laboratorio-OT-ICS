# Qué aprendí construyendo este laboratorio

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

## Depurando el laboratorio de verdad (no solo diseñándolo)

Al levantar esto por primera vez con Docker real (no solo escribir el YAML),
aparecieron varios problemas que no se ven hasta que se ejecutan:

- **matiec (el compilador de OpenPLC) no permite mezclar variables ubicadas
  (`AT %...`) con variables normales en el mismo bloque `VAR`.** El primer
  intento de `tank_control.st` metía `setpoint`/`nivel`/`bomba`/`alarma`
  (con `AT`) y `alto_nivel_alarma`/`histeresis` (sin `AT`) en un único
  bloque — compilaba con "invalid located variable declaration" en las
  variables equivocadas (el error de un parser LALR con recuperación de
  errores no siempre señala la línea causante). Se diagnosticó comparando
  contra el propio código fuente de matiec (`iec_bison.yy`) y reduciendo el
  programa a casos mínimos hasta aislar la combinación exacta que fallaba.
- **`net.bridge.bridge-nf-call-iptables=1` (el valor por defecto en muchos
  hosts Linux/WSL2) rompe un router-en-contenedor.** El ataque no llegaba al
  PLC ni en modo `flat`, y las reglas de `nftables` del propio contenedor
  `router` nunca veían un solo paquete — ni siquiera en su gancho
  `prerouting`. La causa: cuando ese sysctl está activo, el tráfico
  puramente L2 entre dos bridges de Docker se evalúa también contra el
  `FORWARD` del **host** (política `DROP` por defecto en Docker), que no
  tiene ninguna regla para "tráfico de tránsito" hacia una subred de otra
  red Docker — así que lo descarta antes de que llegue al `router`, pese a
  que su propio `nftables` estaba en modo `accept`. Se aisló con un
  reproducible mínimo (3 contenedores Alpine, sin `nftables`, mismo patrón)
  para confirmar que era un comportamiento del host y no un bug de la
  configuración del laboratorio.
- **pymodbus cambia su API de una versión menor a otra.** `slave=` (3.6) se
  convirtió en `device_id=` (3.15) — buena razón para fijar la versión exacta
  en `requirements.txt` en vez de un rango abierto, algo que parece
  paranoico hasta que un `pip install` sin pin rompe la demo delante de
  alguien.
- **`docker port` mintiendo por omisión**: en redes Docker `internal: true`,
  Docker publica el puerto en el compose pero nunca abre el mapeo — ni
  siquiera hacia el propio host. Hubo que añadir una red de gestión aparte
  (`net_mgmt`, no aislada) solo para el HMI y la web de OpenPLC, manteniendo
  las redes de ataque/control totalmente aisladas.
- **`%MW` no es lo mismo que `%QW` para el servidor Modbus de OpenPLC**, y
  este fue el bug más caro de encontrar de todo el laboratorio: con
  `setpoint AT %MW0`, una escritura Modbus se guardaba y se leía de vuelta
  perfectamente (`read_holding_registers` devolvía el valor escrito) — pero
  el *programa* nunca veía ese valor: `IF setpoint >= 500 THEN ...` seguía
  evaluando como si siguiera en 0, por mucho que Modbus confirmara 500. La
  bomba y el nivel se quedaban congelados sin importar lo que se escribiera.
  Costó descartar media docena de teorías (inicialización, hilos muertos,
  volumen persistente con estado viejo) antes de aislarlo con un programa
  mínimo de dos variables y comprobar que cambiando solo `%MW0` por `%QW0`
  el mismo programa empezaba a reaccionar de inmediato. Explicación: el
  runtime de OpenPLC solo sincroniza con el servidor Modbus las variables de
  clase `%I`/`%Q`; `%M` es memoria interna del programa, no de E/S — una
  distinción de la que ningún mensaje de error avisa.
- **La keyword `modbus:` de Suricata no es `modbus.function`/`modbus.access`
  (con punto)**, es una única keyword `modbus:` (con dos puntos) cuyo
  contenido interno se separa por espacios — un error de sintaxis que
  Suricata señalaba claramente ("unknown rule keyword"), fácil de arreglar
  una vez visto. Menos evidente: incluso con la sintaxis correcta,
  `modbus: access write holding` **no disparó** para las escrituras reales
  del ataque (FC06, Write Single Register — la que usa pymodbus por
  defecto), solo para FC16 (Write Multiple Registers). Hubo que añadir
  reglas explícitas por `function code` (`modbus: function 6`) para cubrir
  lo que un cliente Modbus real hace la mayoría de las veces.

Ninguno de estos bugs se ve en un diagrama de arquitectura — todos exigieron
ejecutar el laboratorio de verdad, con logs, `tcpdump` y programas ST
mínimos de prueba, para encontrarlos. Es, honestamente, la parte más
parecida a un incidente real de todo el proyecto — y la prueba de que
"funciona en el diagrama" y "funciona" son cosas distintas.

## Qué haría distinto / próximos pasos

- Añadir un gateway Modbus-aware con *allow-listing* de function codes
  dentro de la propia zona de Control, no solo en el perímetro.
- Automatizar la carga del programa ST en OpenPLC (hoy es un paso manual por
  la web UI) para poder levantar el laboratorio end-to-end sin intervención.
- Probar el mismo laboratorio con un segundo protocolo (p. ej. DNP3 con
  Secure Authentication) para comparar cómo cambia — o no — la historia de
  ataque/detección/segmentación cuando el protocolo sí soporta seguridad.
