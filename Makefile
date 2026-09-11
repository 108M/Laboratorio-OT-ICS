.PHONY: up down ps logs flat segmented attack-recon attack-read attack-write-setpoint attack-write-coil capture-evidence clean openplc-upstream

up: openplc-upstream
	@echo "Ajustando net.bridge.bridge-nf-call-iptables=0 (necesario en Linux/WSL2 para"
	@echo "que el contenedor router pueda reenviar trafico entre las dos redes; ver"
	@echo "README.md > Solucion de problemas). Se ignora el error si no aplica (p. ej. Docker Desktop en macOS)."
	-sysctl -w net.bridge.bridge-nf-call-iptables=0 2>/dev/null || sudo sysctl -w net.bridge.bridge-nf-call-iptables=0 2>/dev/null || true
	docker compose up -d --build

## openplc/Dockerfile extiende esta imagen (le añade iproute2, que la oficial
## no trae). Se construye aparte porque BuildKit no permite usar un contexto
## git remoto como FROM de otro Dockerfile.
openplc-upstream:
	docker build -t openplc-upstream:latest https://github.com/thiagoralves/OpenPLC_v3.git

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

## --- Segmentacion (conducto IEC 62443) ---
flat:
	docker compose exec router /rules/flat.sh

segmented:
	docker compose exec router /rules/segmented.sh

## --- Cadena de ataque de demostracion (ver attack/README.md) ---
attack-recon:
	docker compose exec attacker python 01_recon.py

attack-read:
	docker compose exec attacker python 02_unauthorized_read.py

attack-write-setpoint:
	docker compose exec attacker python 03_unauthorized_write_setpoint.py --valor 1000

attack-write-coil:
	docker compose exec attacker python 04_unauthorized_write_coil.py --segundos 10

## --- Evidencia para detection/evidence/ (ver detection/README.md) ---
capture-evidence:
	@echo "Copiando eve.json actual a detection/evidence/ (renombra segun el modo activo)"
	cp detection/evidence/eve.json detection/evidence/eve_$$(date +%s).json

clean:
	docker compose down -v --remove-orphans
