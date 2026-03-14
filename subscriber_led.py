"""
subscriber_led.py  —  SQUELETTE (branche main)
===============================================
Rôle : recevoir une commande MQTT sur .../actuators/led/cmd,
       allumer / éteindre la DEL GPIO,
       publier l'état réel sur .../actuators/led/state (retained).

TODO (branche feature/subscriber-led) :
    1. Initialiser l'objet LED (gpiozero)
    2. Implémenter parse_command()
    3. Implémenter publish_state()
    4. Compléter on_connect (subscribe + publish état initial)
    5. Compléter on_message (parser → action GPIO → publish state)
"""

import json
from typing import Optional

import paho.mqtt.client as mqtt
# from gpiozero import LED   # TODO : décommenter sur le vrai Pi

# ---------------------------------------------------------------------
# 1) Paramètres
# ---------------------------------------------------------------------
BROKER_HOST = "localhost"
BROKER_PORT = 1883
KEEPALIVE_S = 60

TEAM   = "team01"    # TODO : même valeur que publisher_sensor.py
DEVICE = "pi01"

PREFIX      = f"ahuntsic/aec-iot/b3/{TEAM}/{DEVICE}"
TOPIC_CMD   = f"{PREFIX}/actuators/led/cmd"    # on s'abonne ici (commandes)
TOPIC_STATE = f"{PREFIX}/actuators/led/state"  # on publie ici (état réel, retained)

LED_PIN_BCM = 17   # GPIO BCM 17 (à adapter selon câblage)


# ---------------------------------------------------------------------
# 2) Initialisation de la DEL  —  TODO : implémenter
# ---------------------------------------------------------------------

# TODO : créer l'objet LED
# led = LED(LED_PIN_BCM)

# ---------------------------------------------------------------------
# 3) Analyser la commande reçue  —  TODO : implémenter
# ---------------------------------------------------------------------
def parse_command(payload_text: str) -> Optional[str]:
    """
    Interprète le payload JSON et retourne "on", "off" ou None si invalide.
    Formats acceptés : {"state":"on"} / {"state":"off"}
    TODO : parser le JSON et retourner la commande normalisée.
    """
    # TODO : json.loads → extraire "state" → retourner "on" / "off" / None
    return None   # placeholder

# ---------------------------------------------------------------------
# 4) Publier l'état réel de la DEL  —  TODO : implémenter
# ---------------------------------------------------------------------
def publish_state(client: mqtt.Client) -> None:
    """
    Publie l'état courant de la DEL sur TOPIC_STATE (retain=True).
    TODO : lire led.is_lit, construire le payload, publier.
    """
    # TODO : lire l'état réel de la DEL et publier sur TOPIC_STATE
    pass

# ---------------------------------------------------------------------
# 5) Callbacks MQTT  —  TODO : compléter
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    # TODO : s'abonner à TOPIC_CMD (QoS 1) + publier l'état initial
    pass

def on_message(client, userdata, msg):
    # TODO : décoder payload → parse_command() → action GPIO → publish_state()
    pass

def on_disconnect(client, userdata, reason_code, properties=None):
    # TODO : afficher le code de déconnexion
    pass

# ---------------------------------------------------------------------
# 6) Démarrage du client MQTT
# ---------------------------------------------------------------------
client = mqtt.Client(client_id=f"b3-sub-{TEAM}-{DEVICE}-led", protocol=mqtt.MQTTv311)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
client.loop_forever()   # bloquant — tourne comme un service
