(*
  tank_control.st
  Laboratorio OT/ICS - control de nivel de un deposito (100% simulado)

  Mapa de registros Modbus (ver plc/PROCESO.md):
    Holding register 0 (%MW0) -> setpoint     (0-1000, escritura esperada solo del HMI)
    Holding register 1 (%MW1) -> nivel        (0-1000, solo lectura)
    Coil 0             (%QX0.0) -> bomba      (solo lectura, la escribe este programa)
    Coil 1             (%QX0.1) -> alarma     (solo lectura, la escribe este programa)

  alto_nivel_alarma es una VAR local, sin AT %..., por lo que NUNCA se expone
  como registro Modbus: el interlock de seguridad no es alcanzable por red.
*)

PROGRAM tank_control
VAR
    setpoint          AT %MW0  : INT := 500;
    nivel             AT %MW1  : INT := 0;
    bomba             AT %QX0.0 : BOOL;
    alarma            AT %QX0.1 : BOOL;

    alto_nivel_alarma : INT := 900;
    histeresis        : INT := 20;
END_VAR

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
