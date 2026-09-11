(*
  tank_control.st
  Laboratorio OT/ICS - control de nivel de un deposito (100% simulado)

  Mapa de registros Modbus (ver plc/PROCESO.md):
    Holding register 0 (%QW0) -> setpoint     (0-1000, escritura esperada solo del HMI)
    Holding register 1 (%QW1) -> nivel        (0-1000, solo lectura)
    Coil 0             (%QX0.0) -> bomba      (solo lectura, la escribe este programa)
    Coil 1             (%QX0.1) -> alarma     (solo lectura, la escribe este programa)

  Se usa %QW (no %MW) a proposito: en OpenPLC el servidor Modbus solo
  sincroniza automaticamente las variables de clase %I/%Q con clientes
  Modbus externos -- %M es memoria interna del programa, sin esa
  sincronizacion (una escritura Modbus a un %MW se guarda en la tabla de
  registros pero el programa nunca la ve). Ver docs/lecciones_aprendidas.md.

  alto_nivel_alarma es una VAR local, sin AT %..., por lo que NUNCA se expone
  como registro Modbus: el interlock de seguridad no es alcanzable por red.
*)

PROGRAM tank_control
(* matiec (el compilador de OpenPLC) no permite mezclar variables ubicadas
   (AT %...) con variables normales dentro del mismo bloque VAR: van en
   bloques separados aunque sean parte del mismo PROGRAM. *)
VAR
    setpoint          AT %QW0  : INT;
    nivel             AT %QW1  : INT;
    bomba             AT %QX0.0 : BOOL;
    alarma            AT %QX0.1 : BOOL;
END_VAR
VAR
    alto_nivel_alarma : INT;
    histeresis        : INT;
    ciclo             : INT;
END_VAR

(* --- Inicializacion en el primer ciclo. OpenPLC/matiec no aplica de forma
   fiable los valores "AT %... := valor" de variables ubicadas en el arranque
   (comportamiento habitual en PLCs reales: el valor de arranque de una E/S
   lo fija el programa, no la declaracion) -- por eso se asigna aqui en vez
   de en el VAR. "ciclo" no necesita inicializador: en C arranca en 0 por
   definicion, así que esta comprobación es fiable incluso si la
   inicialización de variables de matiec fallara igual que con las AT %. --- *)
ciclo := ciclo + 1;
IF ciclo = 1 THEN
    setpoint := 500;
    nivel := 0;
    alto_nivel_alarma := 900;
    histeresis := 20;
END_IF;

(* --- Interlock de seguridad: el nivel alto siempre corta la bomba,        *)
(* --- sin importar el setpoint. Esta capa es independiente del bucle      *)
(* --- de control y no depende de ningun registro Modbus.                  *)
IF nivel >= alto_nivel_alarma THEN
    bomba := FALSE;
    alarma := TRUE;
ELSE
    alarma := FALSE;

    (* --- Control on/off con histeresis persiguiendo el setpoint --- *)
    IF nivel < (setpoint - histeresis) THEN
        bomba := TRUE;
    ELSIF nivel >= setpoint THEN
        bomba := FALSE;
    END_IF;
END_IF;

(* --- Modelo fisico simplificado del deposito (simulacion, sin sensor real) --- *)
IF bomba THEN
    nivel := nivel + 5;
ELSE
    IF nivel > 0 THEN
        nivel := nivel - 2;
    END_IF;
END_IF;

IF nivel > 1000 THEN
    nivel := 1000;
END_IF;
IF nivel < 0 THEN
    nivel := 0;
END_IF;

END_PROGRAM

CONFIGURATION Config0
    RESOURCE Res0 ON PLC
        TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
        PROGRAM Inst0 WITH Main : tank_control;
    END_RESOURCE
END_CONFIGURATION
