"""
logger_mariadb.py  —  SQUELETTE (branche main)
===============================================
Rôle : s'abonner à tous les topics de l'équipe,
       classer chaque message (télémétrie ou événement),
       insérer en base MariaDB.

Architecture :
    Mosquitto ── ce script ── MariaDB (tables telemetry + events)

TODO (branche feature/logger-mariadb) :
    1. Compléter db_connect() avec les bons paramètres
    2. Implémenter insert_telemetry()
    3. Implémenter insert_event()
    4. Compléter on_connect (s'abonner au topic filtre)
    5. Compléter on_message (classifier + insérer)
"""

import json
from datetime import datetime, timezone
from typing import Optional

import pymysql
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------
# 1) Paramètres MQTT
# ---------------------------------------------------------------------
BROKER_HOST = "localhost"
BROKER_PORT = 1883
KEEPALIVE_S = 60

TEAM   = "team01"    # TODO : même valeur que les autres scripts
DEVICE = "pi01"

PREFIX       = f"ahuntsic/aec-iot/b3/{TEAM}/{DEVICE}"
TOPIC_FILTER = f"{PREFIX}/#"   # écouter TOUS les topics de l'équipe

# ---------------------------------------------------------------------
# 2) Paramètres MariaDB
# ---------------------------------------------------------------------
DB_HOST     = "localhost"
DB_USER     = "iot"
DB_PASSWORD = "iot"
DB_NAME     = "iot_b3"

# ---------------------------------------------------------------------
# 3) Connexion à la base  —  TODO : vérifier les paramètres
# ---------------------------------------------------------------------
def db_connect() -> pymysql.connections.Connection:
    """
    Ouvre une connexion MariaDB.
    autocommit=True : chaque INSERT est écrit immédiatement.
    TODO : s'assurer que DB_USER / DB_PASSWORD / DB_NAME correspondent à notre schéma.
    """
    # TODO : retourner pymysql.connect(...)
    pass   # placeholder — à remplacer

# Connexion globale (réutilisée par on_message)
db = None   # TODO : appeler db_connect() ici

# ---------------------------------------------------------------------
# 4) Fonctions utilitaires
# ---------------------------------------------------------------------
def utc_now() -> datetime:
    """Retourne l'heure UTC actuelle sans tzinfo (format attendu par MariaDB DATETIME)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def is_telemetry(topic: str) -> bool:
    """Retourne True si le topic est une mesure capteur (/sensors/ mais pas /value)."""
    return "/sensors/" in topic and not topic.endswith("/value")

def classify_kind(topic: str) -> str:
    """Classe l'événement : cmd / state / status / other."""
    if "/cmd/"    in topic : return "cmd"
    if "/state/"  in topic : return "state"
    if "/status/" in topic : return "status"
    return "other"

# ---------------------------------------------------------------------
# 5) Insertion en base  —  TODO : implémenter
# ---------------------------------------------------------------------
def insert_telemetry(ts: datetime, device: str, topic: str, payload_text: str) -> None:
    """
    Insère une ligne dans la table telemetry.
    TODO : extraire value/unit du JSON si possible, puis INSERT.
    """
    # TODO : implémenter
    pass

def insert_event(ts: datetime, device: str, topic: str, kind: str, payload_text: str) -> None:
    """
    Insère une ligne dans la table events.
    TODO : implémenter le INSERT.
    """
    # TODO : implémenter
    pass

# ---------------------------------------------------------------------
# 6) Callbacks MQTT  —  TODO : compléter
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    # TODO : s'abonner à TOPIC_FILTER si reason_code == 0
    pass

def on_message(client, userdata, msg):
    # TODO : décoder payload → is_telemetry? → insert_telemetry ou insert_event
    pass

def on_disconnect(client, userdata, reason_code, properties=None):
    # TODO : afficher le code de déconnexion
    pass

# ---------------------------------------------------------------------
# 7) Démarrage
# ---------------------------------------------------------------------
client = mqtt.Client(client_id=f"b3-logger-{TEAM}-{DEVICE}", protocol=mqtt.MQTTv311)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
print("[INFO] Logger démarré. CTRL+C pour arrêter.")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé")
finally:
    if db:
        db.close()
    client.disconnect()
