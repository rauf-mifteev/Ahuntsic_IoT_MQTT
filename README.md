# SmartLab — Mini-système IoT supervisé

Projet 1 — AEC IoT, Bloc 3 — Collège Ahuntsic  
Équipe : **team01** | Pi : **pi01**
Coauteurs: Rauf Mifteev, Jean-Jacques Arquero

Le lien vers le dépôt GitHub : **https://github.com/rauf-mifteev/Ahuntsic_IoT_MQTT**

---

## Architecture

```
+------------------+   MQTT (QoS 0)    +-------------------+   MQTT (sub)   +------------------+
|  Raspberry Pi    | ───JSON──────────►|  Mosquitto Broker |───────────────►| logger_mariadb   |
|                  |   sensors/temp    |  localhost:1883   |                | (Python)         |
|  publisher_sensor| ───value─────────►|                   |                +──────────────────+
|  (Python)        |                   |                   |                        │
|                  |   status/online   |                   |                    INSERT
|                  | ───retained──────►|                   |                        ▼
+------------------+                   |                   |               +------------------+
         ▲                             |                   |               | MariaDB          |
         │ QoS 1                       |                   |               | table telemetry  |
    actuators/led/state                |                   |               | table events     |
         │                             |                   |               +------------------+
+------------------+   MQTT (QoS 1)    |                   |
| subscriber_led   | ◄──cmd───────────►|                   | ◄──────────── MQTT Dash (mobile)
| (Python + GPIO)  |   actuators/led/  |                   |   sub: sensors/temperature/value
+------------------+                   +-------------------+   pub: actuators/led/cmd
                                                               sub: actuators/led/state
```

---

## Contrat MQTT (topics)

Préfixe commun : `ahuntsic/aec-iot/b3/team01/pi01`

| Topic | Direction | QoS | Retained | Description |
|-------|-----------|-----|----------|-------------|
| `.../sensors/temperature` | Pi → broker | 0 | Non | Mesure JSON complète |
| `.../sensors/temperature/value` | Pi → broker | 0 | Non | Valeur simple (nombre) pour MQTT Dash |
| `.../actuators/led/cmd` | MQTT Dash → Pi | 1 | Non | Commande JSON (`{"state":"on/off"}`) |
| `.../actuators/led/state` | Pi → broker | 1 | **Oui** | État réel de la DEL (`on` ou `off`) |
| `.../status/online` | Pi → broker | 1 | **Oui** | Présence du Pi (`online` / `offline`) |

### Qui publie / qui s'abonne

| Script | Publie sur | S'abonne à |
|--------|-----------|------------|
| `publisher_sensor.py` | `sensors/temperature`, `sensors/temperature/value`, `status/online` | — |
| `subscriber_led.py` | `actuators/led/state` | `actuators/led/cmd` |
| `logger_mariadb.py` | — | `#` (tous les topics) |
| MQTT Dash | `actuators/led/cmd` | `sensors/temperature/value`, `actuators/led/state`, `status/online` |

### Exemples de payload JSON

Mesure capteur :
```json
{
  "device": "pi01",
  "sensor": "temperature",
  "value": 23.42,
  "unit": "C",
  "ts": "2026-02-25T19:22:10.123Z"
}
```

État DEL :
```json
{
  "device": "pi01",
  "actuator": "led",
  "state": "on",
  "ts": "2026-02-25T19:23:01.501Z"
}
```

Commande DEL (depuis MQTT Dash) :
```json
{"state": "on"}
```

---

## Installation

**1. Cloner le dépôt et créer l'environnement virtuel**
```bash
git clone https://github.com/rauf-mifteev/Ahuntsic_IoT_MQTT
cd smartlab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Installer et démarrer Mosquitto**
```bash
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

**3. Installer MariaDB et créer le schéma**
```bash
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
sudo mariadb < db/schema.sql
```

**4. (Optionnel) Vérifier que le schéma est créé**
```bash
sudo mariadb iot_b3 -e "SHOW TABLES;"
```

---

## Exécution

Ouvrir **3 terminaux** (ou 3 sessions SSH) sur le Pi.

**Terminal 1 — Logger MariaDB**
```bash
source .venv/bin/activate
python3 src/logger_mariadb.py
```

**Terminal 2 — Publisher capteur**
```bash
source .venv/bin/activate
python3 src/publisher_sensor.py
```

**Terminal 3 — Subscriber DEL**
```bash
source .venv/bin/activate
python3 src/subscriber_led.py
```

---

## Tester avec mosquitto_pub / mosquitto_sub

**Observer tous les topics de l'équipe :**
```bash
mosquitto_sub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/#" -v
```

**Envoyer une commande ON à la DEL :**
```bash
mosquitto_pub -h localhost \
  -t "ahuntsic/aec-iot/b3/team01/pi01/actuators/led/cmd" \
  -m '{"state":"on"}' -q 1
```

**Envoyer une commande OFF :**
```bash
mosquitto_pub -h localhost \
  -t "ahuntsic/aec-iot/b3/team01/pi01/actuators/led/cmd" \
  -m '{"state":"off"}' -q 1
```

**Vérifier l'état retained de la DEL :**
```bash
mosquitto_sub -h localhost \
  -t "ahuntsic/aec-iot/b3/team01/pi01/actuators/led/state" -v
```

---

## Vérifier MariaDB

**Ouvrir la console MariaDB :**
```bash
sudo mariadb iot_b3
```

**10 dernières mesures :**
```sql
SELECT id, ts_utc, device, value, unit FROM telemetry ORDER BY id DESC LIMIT 10;
```

**10 dernières commandes :**
```sql
SELECT id, ts_utc, kind, payload FROM events WHERE kind='cmd' ORDER BY id DESC LIMIT 10;
```

**Ou exécuter toutes les requêtes de démo d'un coup :**
```bash
sudo mariadb iot_b3 < db/queries.sql
```

---

## Configuration MQTT Client

1. Trouver l'IP du Pi : `hostname -I` (ex. `192.168.0.42`)
2. **Add connection** → Host : `192.168.0.42` | Port : `1883` | Client ID : `dash-team01`
3. **Widget Gauge** (mesure température) :
   - Subscribe topic : `ahuntsic/aec-iot/b3/team01/pi01/sensors/temperature/value`
   - QoS : 0
4. **Widget Switch** (commande DEL) :
   - Publish topic : `ahuntsic/aec-iot/b3/team01/pi01/actuators/led/cmd`
   - Payload ON : `{"state":"on"}` | Payload OFF : `{"state":"off"}`
5. **Widget Indicator** (état DEL) :
   - Subscribe topic : `ahuntsic/aec-iot/b3/team01/pi01/actuators/led/state`
