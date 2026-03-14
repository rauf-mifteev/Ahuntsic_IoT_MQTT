"""
publisher_sensor.py  —  SQUELETTE (branche main)
=================================================
Rôle : lire un capteur (ou simuler), construire un message JSON,
       et publier sur MQTT toutes les N secondes.

Architecture :
    Raspberry Pi (ce script) ──MQTT──► Mosquitto (broker) ──► MQTT Dash / logger

TODO (branche feature/publisher) :
    1. Compléter les constantes TEAM et DEVICE avec notre équipe
    2. Implémenter read_sensor()
    3. Implémenter build_payload()
    4. Compléter la boucle principale (publish JSON + value)
    5. Ajouter LWT + statut online/offline
"""

import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------
# 1) Paramètres de connexion (à adapter à notre équipe)
# ---------------------------------------------------------------------
BROKER_HOST = "localhost"   # Mosquitto tourne sur le Pi
BROKER_PORT = 1883
KEEPALIVE_S = 60

TEAM   = "team01"           # TODO : remplacer par notre équipe
DEVICE = "pi01"             # TODO : remplacer par notre Pi

# Topics (construits automatiquement à partir du préfixe)
PREFIX       = f"ahuntsic/aec-iot/b3/{TEAM}/{DEVICE}"
TOPIC_JSON   = f"{PREFIX}/sensors/temperature"        # payload JSON complet
TOPIC_VALUE  = f"{PREFIX}/sensors/temperature/value"  # valeur brute (pour MQTT Dash)
TOPIC_ONLINE = f"{PREFIX}/status/online"              # retained : online / offline

PUBLISH_PERIOD_S = 2.0   # publier toutes les 2 secondes

# ---------------------------------------------------------------------
# 2) Lecture du capteur  —  TODO : implémenter
# ---------------------------------------------------------------------
def read_sensor() -> float:
    """
    Retourne la valeur du capteur en °C.
    TODO : remplacer la valeur simulée par notre capteur réel.
    """
    # TODO : lire le vrai capteur ici
    return 0.0   # valeur placeholder

# ---------------------------------------------------------------------
# 3) Construction du payload JSON  —  TODO : implémenter
# ---------------------------------------------------------------------
def build_payload(value: float) -> dict:
    """
    Construit le dictionnaire JSON à publier.
    TODO : remplir les champs device, sensor, value, unit, ts.
    """
    # TODO : retourner un dict avec les bons champs
    return {}

# ---------------------------------------------------------------------
# 4) Callbacks MQTT  —  TODO : compléter on_connect
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    # TODO : afficher le code de connexion + publier le statut "online"
    pass

def on_disconnect(client, userdata, reason_code, properties=None):
    # TODO : afficher le code de déconnexion
    pass

# ---------------------------------------------------------------------
# 5) Création du client MQTT  —  TODO : ajouter LWT
# ---------------------------------------------------------------------
client = mqtt.Client(client_id=f"b3-pub-{TEAM}-{DEVICE}", protocol=mqtt.MQTTv311)
client.on_connect    = on_connect
client.on_disconnect = on_disconnect

# TODO : configurer le LWT (will_set) pour publier "offline" si le Pi tombe

# ---------------------------------------------------------------------
# 6) Connexion + boucle  —  TODO : compléter la boucle principale
# ---------------------------------------------------------------------
client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
client.loop_start()

try:
    while True:
        # TODO : lire le capteur, construire le payload, publier JSON + value
        time.sleep(PUBLISH_PERIOD_S)

except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé (Ctrl+C)")

finally:
    # TODO : publier "offline" proprement avant de quitter
    client.loop_stop()
    client.disconnect()
