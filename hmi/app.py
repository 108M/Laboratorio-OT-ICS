"""
HMI legitimo del laboratorio OT/ICS.

Unico cliente Modbus "autorizado" del laboratorio: lee nivel/bomba/alarma del
PLC (OpenPLC) y permite escribir un nuevo setpoint dentro de un rango seguro.
Ver plc/PROCESO.md para el mapa de registros Modbus que este cliente respeta.
"""
import os

from flask import Flask, redirect, render_template_string, request
from pymodbus.client import ModbusTcpClient

PLC_HOST = os.environ.get("PLC_HOST", "192.168.20.10")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))
UNIT_ID = int(os.environ.get("PLC_UNIT_ID", "1"))

REG_SETPOINT = 0
REG_NIVEL = 1
COIL_BOMBA = 0
COIL_ALARMA = 1

SETPOINT_MIN, SETPOINT_MAX = 0, 1000

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="2">
  <title>HMI - Deposito (laboratorio OT/ICS)</title>
  <style>
    body { font-family: sans-serif; max-width: 640px; margin: 40px auto; }
    .tanque { width: 120px; height: 240px; border: 3px solid #333; position: relative;
              background: #eee; overflow: hidden; }
    .agua { position: absolute; bottom: 0; width: 100%; background: #3b82c4;
            transition: height 0.3s; }
    .alarma { color: white; background: #c0392b; padding: 6px 10px; border-radius: 4px; }
    .ok { color: white; background: #2e7d32; padding: 6px 10px; border-radius: 4px; }
    .fila { display: flex; gap: 24px; align-items: center; }
    label { display: block; margin-top: 16px; }
  </style>
</head>
<body>
  <h1>HMI del deposito</h1>
  <p>Conectado a PLC {{ plc_host }}:{{ plc_port }} (unit id {{ unit_id }})</p>

  {% if error %}
    <p class="alarma">Error de comunicacion Modbus: {{ error }}</p>
  {% else %}
  <div class="fila">
    <div class="tanque"><div class="agua" style="height: {{ nivel_pct }}%;"></div></div>
    <div>
      <p><b>Nivel actual:</b> {{ nivel_pct }} %</p>
      <p><b>Setpoint:</b> {{ setpoint_pct }} %</p>
      <p><b>Bomba:</b> {{ "ENCENDIDA" if bomba else "apagada" }}</p>
      <p class="{{ 'alarma' if alarma else 'ok' }}">
        {{ "ALARMA: nivel alto (interlock activo)" if alarma else "Sin alarmas" }}
      </p>
    </div>
  </div>

  <form method="post" action="/setpoint">
    <label for="setpoint">Nuevo setpoint (0-100 %)
      <input type="number" id="setpoint" name="setpoint" min="0" max="100" step="1"
             value="{{ setpoint_pct }}">
    </label>
    <button type="submit">Aplicar</button>
  </form>
  {% endif %}
</body>
</html>
"""


def _client():
    client = ModbusTcpClient(PLC_HOST, port=PLC_PORT)
    client.connect()
    return client


@app.route("/")
def index():
    client = _client()
    try:
        hr = client.read_holding_registers(address=REG_NIVEL, count=1, device_id=UNIT_ID)
        sp = client.read_holding_registers(address=REG_SETPOINT, count=1, device_id=UNIT_ID)
        coils = client.read_coils(address=COIL_BOMBA, count=2, device_id=UNIT_ID)
        if hr.isError() or sp.isError() or coils.isError():
            raise IOError("respuesta Modbus con error")
        nivel = hr.registers[0]
        setpoint = sp.registers[0]
        bomba, alarma = coils.bits[0], coils.bits[1]
        return render_template_string(
            PAGE,
            plc_host=PLC_HOST,
            plc_port=PLC_PORT,
            unit_id=UNIT_ID,
            nivel_pct=round(nivel / 10),
            setpoint_pct=round(setpoint / 10),
            bomba=bomba,
            alarma=alarma,
            error=None,
        )
    except Exception as exc:  # noqa: BLE001 - se muestra en la propia pagina
        return render_template_string(
            PAGE,
            plc_host=PLC_HOST,
            plc_port=PLC_PORT,
            unit_id=UNIT_ID,
            error=str(exc),
        )
    finally:
        client.close()


@app.route("/setpoint", methods=["POST"])
def set_setpoint():
    pct = max(0, min(100, int(request.form.get("setpoint", 50))))
    valor = pct * 10
    valor = max(SETPOINT_MIN, min(SETPOINT_MAX, valor))
    client = _client()
    try:
        client.write_register(address=REG_SETPOINT, value=valor, device_id=UNIT_ID)
    finally:
        client.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
