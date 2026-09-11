.PHONY: up down ps logs flat segmented attack-recon attack-read attack-write-setpoint attack-write-coil capture-evidence clean

up:
	docker compose up -d --build

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
