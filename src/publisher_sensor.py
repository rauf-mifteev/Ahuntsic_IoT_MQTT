"""
publisher_sensor.py  —  implémentation complète (branche feature/publisher)
============================================================================
Rôle : lire la température (CPU du Pi ou simulation),
       construire un message JSON,
       publier sur MQTT toutes les 2 secondes.

Architecture :
    Raspberry Pi (ce script)
        ──JSON──► ahuntsic/.../sensors/temperature
        ──value─► ahuntsic/.../sensors/temperature/value
        ──LWT───► ahuntsic/.../status/online  (online / offline, retained)

Lancer :
    python3 src/publisher_sensor.py

Tester (dans un autre terminal) :
    mosquitto_sub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/#" -v
"""

import json
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------
# 1) Paramètres (adaptez TEAM et DEVICE à notre équipe)
# ---------------------------------------------------------------------
BROKER_HOST = "localhost"   # Mosquitto tourne sur le même Pi
BROKER_PORT = 1883
KEEPALIVE_S = 60

TEAM   = "team01"
DEVICE = "pi01"

PREFIX       = f"ahuntsic/aec-iot/b3/{TEAM}/{DEVICE}"
TOPIC_JSON   = f"{PREFIX}/sensors/temperature"         # payload JSON complet
TOPIC_VALUE  = f"{PREFIX}/sensors/temperature/value"   # valeur simple (pour la jauge MQTT Dash)
TOPIC_ONLINE = f"{PREFIX}/status/online"               # Last Will and Testament

PUBLISH_PERIOD_S = 2.0
QOS_SENSOR       = 0

# Global flag pour savoir si on est connecté
connected = False

# ---------------------------------------------------------------------
# 2) Logique de lecture du capteur
# ---------------------------------------------------------------------
def read_sensor() -> float:
    """
    Simule la lecture d'une température. 
    Sur un vrai Pi, on pourrait lire /sys/class/thermal/thermal_zone0/temp
    """
    return round(random.uniform(20.0, 26.0), 1)

def build_payload(value: float) -> dict:
    """
    Construit le dictionnaire (JSON) avec les métadonnées requises.
    """
    return {
        "device_id": DEVICE,
        "sensor": "cpu_temp",
        "value": value,
        "unit": "C",
        "ts": datetime.now(timezone.utc).isoformat()
    }

# ---------------------------------------------------------------------
# 3) Callbacks MQTT
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        print(f"[CONNECT] connecté au broker {BROKER_HOST}")
        connected = True
        # Publier le statut online dès la connexion (retained=True)
        client.publish(TOPIC_ONLINE, "online", qos=1, retain=True)
    else:
        print(f"[ERROR] échec connexion, code={rc}")

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    # Optionnel : loguer chaque publication réussie
    pass

def on_disconnect(client, userdata, reason_code, properties=None):
    global connected
    connected = False
    print(f"[DISCONNECT] reason_code={reason_code}")

# ---------------------------------------------------------------------
# 4) Configuration du Client MQTT (avec LWT)
# ---------------------------------------------------------------------
client = mqtt.Client(
    client_id=f"b3-pub-{TEAM}-{DEVICE}",
    protocol=mqtt.MQTTv311,
)

# Configuration du Last Will and Testament (LWT)
# Si le script plante ou perd le Wi-Fi, le broker publiera "offline" pour nous.
client.will_set(TOPIC_ONLINE, payload="offline", qos=1, retain=True)

client.on_connect    = on_connect
client.on_publish    = on_publish
client.on_disconnect = on_disconnect

# ---------------------------------------------------------------------
# 5) Connexion
# ---------------------------------------------------------------------
print(f"[INFO] Démarrage du publisher ({TEAM}/{DEVICE})...")
client.reconnect_delay_set(min_delay=1, max_delay=30)

# connect_async + loop_start = connexion non bloquante + thread réseau en arrière-plan
client.connect_async(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
client.loop_start()

# ---------------------------------------------------------------------
# 6) Boucle principale : lire le capteur → publier
# ---------------------------------------------------------------------
try:
    while True:

        # Si pas encore connecté, on attend (la boucle réseau tente de se connecter)
        if not connected:
            print("[WAIT] connexion MQTT en cours...")
            time.sleep(1.0)
            continue

        # Lire le capteur
        value   = read_sensor()
        payload = build_payload(value)

        # Publier le JSON complet (utile pour le logger MariaDB)
        client.publish(TOPIC_JSON, json.dumps(payload), qos=QOS_SENSOR, retain=False)

        # Publier la valeur simple (utile pour la jauge MQTT Dash)
        client.publish(TOPIC_VALUE, str(value), qos=QOS_SENSOR, retain=False)

        print(f"[PUB] {TOPIC_JSON} -> {payload}")

        time.sleep(PUBLISH_PERIOD_S)

except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé (Ctrl+C)")

finally:
    # Arrêt propre : on publie "offline" nous-mêmes avant de fermer
    # (le LWT ne se déclenche pas lors d'un arrêt propre)
    client.publish(TOPIC_ONLINE, "offline", qos=1, retain=True)
    client.loop_stop()
    client.disconnect()
    print("[EXIT] déconnecté proprement.")
