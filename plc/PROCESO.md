# Proceso simulado: control de nivel de un depósito

## Descripción física (simulada)

Un depósito con una bomba de llenado y un sensor de nivel. No hay hardware real:
el propio programa del PLC (`tank_control.st`) simula la física del depósito en
cada ciclo de scan, así que el laboratorio es 100% software.

- El **nivel** sube 5 unidades/ciclo cuando la bomba está encendida y baja 2
  unidades/ciclo (fuga/consumo) cuando está apagada. Rango 0–1000 (equivalente
  a 0.0–100.0 %).
- El PLC persigue un **setpoint** de nivel deseado con histéresis simple
  (on/off), como un control de nivel real de bajo coste.
- Existe un **interlock de seguridad** de nivel alto (`alto_nivel_alarma = 900`,
  fijo en el propio programa, **no** expuesto por Modbus) que fuerza la bomba a
  OFF y activa una alarma sin importar lo que diga el setpoint. Esto representa
  una función de seguridad básica (piénsalo como un SIF/interlock separado del
  control normal, en la línea de IEC 61511) independiente del bucle de control.

Este diseño es intencional para la narrativa del laboratorio: el **setpoint**
es un parámetro de proceso normal, sin ninguna protección — y es exactamente
ahí donde Modbus TCP sin autenticación permite el ataque. El interlock de
nivel alto, en cambio, no es alcanzable por Modbus porque nunca se mapeó a un
registro — así se puede explicar en la documentación por qué la manipulación
del setpoint sigue teniendo un techo (capa de seguridad independiente), pero
aun así causa un comportamiento anómalo y peligroso (bomba forzada, alarma
parpadeando, desgaste de la bomba) — un patrón de ataque realista, no un
"todo o nada".

## Mapa de registros Modbus (autoritativo — reutilizado literalmente por `hmi/app.py` y `attack/*.py`)

| Dirección Modbus | Tipo               | Variable IEC 61131-3 | Descripción                                   | Acceso esperado         |
|-------------------|--------------------|-----------------------|------------------------------------------------|--------------------------|
| Holding register 0 | 16-bit (FC03/06/16) | `setpoint AT %MW0`   | Nivel deseado (0–1000)                        | Escritura solo por HMI  |
| Holding register 1 | 16-bit (FC03)       | `nivel AT %MW1`      | Nivel actual del depósito (0–1000)            | Solo lectura            |
| Coil 0              | 1-bit (FC01/05/15)  | `bomba AT %QX0.0`    | Estado de la bomba de llenado                 | Solo lectura (la escribe el propio PLC) |
| Coil 1              | 1-bit (FC01/05/15)  | `alarma AT %QX0.1`   | Alarma de nivel alto (interlock)              | Solo lectura            |

Modbus TCP **no tiene control de acceso**: nada impide técnicamente que
cualquier cliente en la red escriba en `holding register 0` o en `coil 0`,
aunque "el acceso esperado" solo lo use el HMI. Esa brecha entre lo que el
protocolo permite y lo que el diseño espera es exactamente lo que
`attack/03_unauthorized_write_setpoint.py` y `attack/04_unauthorized_write_coil.py`
explotan.

## Por qué la escritura al coil es transitoria (y por qué eso también es interesante)

`bomba` la recalcula el propio programa ST en cada ciclo de scan (decenas de ms).
Una escritura Modbus puntual al coil 0 se sobrescribe casi de inmediato por la
siguiente ejecución del programa. Por eso `04_unauthorized_write_coil.py` no
hace una sola escritura, sino un *bombardeo* de escrituras (T0855 – Unauthorized
Command Message): al competir en frecuencia con el ciclo de scan, el atacante
consigue que la bomba pase mucho más tiempo encendido del que el control legítimo
pretendía. Es un detalle técnico real de los PLC (no todo ataque de escritura es
persistente) que vale la pena documentar en vez de simplificar.
