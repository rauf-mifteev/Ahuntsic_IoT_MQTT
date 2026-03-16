"""
subscriber_led.py  —  implémentation complète (branche feature/subscriber-led)
===============================================================================
Rôle : recevoir une commande JSON sur .../actuators/led/cmd,
       allumer / éteindre la DEL sur GPIO 17,
       publier l'état réel sur .../actuators/led/state (retained).

Câblage DEL :
    GPIO 17 (BCM) ── résistance 220 Ω ── anode DEL ── cathode ── GND

Lancer :
    python3 src/subscriber_led.py

Tester (dans un autre terminal) :
    mosquitto_pub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/actuators/led/cmd" \
                  -m '{"state":"on"}' -q 1
    mosquitto_pub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/actuators/led/cmd" \
                  -m '{"state":"off"}' -q 1
"""

import json
from typing import Optional

import paho.mqtt.client as mqtt

# Sur un Raspberry Pi réel, décommenter la ligne suivante :
# from gpiozero import LED

# ---------------------------------------------------------------------
# 1) Paramètres
# ---------------------------------------------------------------------
BROKER_HOST = "localhost"
BROKER_PORT = 1883
KEEPALIVE_S = 60

TEAM   = "team01"
DEVICE = "pi01"

PREFIX      = f"ahuntsic/aec-iot/b3/{TEAM}/{DEVICE}"
TOPIC_CMD   = f"{PREFIX}/actuators/led/cmd"    # on écoute ici (commandes)
TOPIC_STATE = f"{PREFIX}/actuators/led/state"  # on publie ici (état réel, retained)

QOS_CMD   = 1   # commandes : QoS 1 (on veut être sûr que la commande arrive)
QOS_STATE = 1   # état      : QoS 1

LED_PIN_BCM = 17

# ---------------------------------------------------------------------
# 2) Initialisation de la DEL
# ---------------------------------------------------------------------

# Sur un Raspberry Pi réel :
led = LED(LED_PIN_BCM)
#
# Pour simuler sans matériel (tests sur PC) :

class _SimulatedLED:
    """Simulation de la DEL pour tester sans Raspberry Pi."""
    def __init__(self):
        self.is_lit = False
    def on(self):
        self.is_lit = True
        print("[SIM] DEL allumée ")
    def off(self):
        self.is_lit = False
        print("[SIM] DEL éteinte ")

# led = _SimulatedLED()   # remplacer par LED(LED_PIN_BCM) du vrai LED

# ---------------------------------------------------------------------
# 3) Analyser la commande reçue
# ---------------------------------------------------------------------
def parse_command(payload_text: str) -> Optional[str]:
    """
    Interprète le payload JSON et retourne "on", "off" ou None si invalide.

    Formats acceptés :
        {"state": "on"}  /  {"state": "off"}
        {"state": "ON"}  /  {"state": "OFF"}  (insensible à la casse)

    Retourne None si le JSON est cassé ou si le champ "state" est absent.
    Un retour None → message ignoré (log + pas de crash).
    """
    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError:
        # JSON invalide : on log et on ignore sans planter
        print(f"[WARN] JSON invalide reçu : {payload_text!r}")
        return None

    if "state" not in data:
        print(f"[WARN] Champ 'state' manquant dans : {data}")
        return None

    command = str(data["state"]).strip().lower()

    if command not in ("on", "off"):
        print(f"[WARN] Valeur 'state' inconnue : {data['state']!r}")
        return None

    return command

# ---------------------------------------------------------------------
# 4) Publier l'état réel de la DEL
# ---------------------------------------------------------------------
def publish_state(client: mqtt.Client) -> None:
    """
    Lit l'état réel de la DEL et le publie sur TOPIC_STATE.
    retain=True : le broker conserve cette valeur → un nouvel abonné
    (ex. MQTT Dash qui redémarre) voit immédiatement le bon état.
    """
    state = "on" if led.is_lit else "off"
    client.publish(TOPIC_STATE, state, qos=QOS_STATE, retain=True)
    print(f"[STATE] {TOPIC_STATE} -> {state}")

# ---------------------------------------------------------------------
# 5) Callbacks MQTT
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    Appelée quand le broker répond à la connexion.
    C'est ici qu'on s'abonne — pour que l'abonnement soit refait
    automatiquement si on se reconnecte après une coupure.
    """
    print(f"[CONNECT] reason_code={reason_code}")

    if reason_code == 0:
        # S'abonner au topic de commandes (QoS 1 : on veut recevoir les commandes)
        client.subscribe(TOPIC_CMD, qos=QOS_CMD)
        print(f"[SUB] {TOPIC_CMD} (qos={QOS_CMD})")

        # Publier l'état actuel dès la connexion (synchronise le dashboard)
        publish_state(client)
    else:
        print("[ERROR] Connexion refusée. Vérifier Mosquitto, host, port.")

def on_message(client, userdata, msg):
    """
    Appelée à chaque message reçu sur TOPIC_CMD.
    Séquence : décoder - analyser - action GPIO - publier état.
    """
    payload_text = msg.payload.decode("utf-8", errors="replace")
    print(f"[MSG] topic={msg.topic} qos={msg.qos} retain={msg.retain} payload={payload_text}")

    command = parse_command(payload_text)

    if command is None:
        # Commande invalide : on ignore (le log est déjà fait dans parse_command)
        return

    # Action GPIO
    if command == "on":
        led.on()
    else:
        led.off()

    # Publier l'état réel (source de vérité — pas la commande reçue)
    publish_state(client)

def on_disconnect(client, userdata, reason_code, properties=None):
    print(f"[DISCONNECT] reason_code={reason_code}")

# ---------------------------------------------------------------------
# 6) Démarrage du client MQTT
# ---------------------------------------------------------------------
client = mqtt.Client(
    client_id=f"b3-sub-{TEAM}-{DEVICE}-led",
    protocol=mqtt.MQTTv311,
)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

# Reconnexion automatique (utile si Mosquitto redémarre)
client.reconnect_delay_set(min_delay=1, max_delay=30)

client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
print("[INFO] Subscriber DEL démarré. CTRL+C pour arrêter.")

# loop_forever() est bloquant : ce script tourne comme un service en continu
client.loop_forever()
