"""
logger_mariadb.py  —  implémentation complète (branche feature/logger-mariadb)
===============================================================================
Rôle : s'abonner à tous les topics de notre équipe,
       classer chaque message (télémétrie capteur ou événement),
       insérer en base MariaDB.

Architecture :
    Mosquitto ── ce script ── MariaDB (tables: telemetry, events)
                                  
Pré-requis :
    1. MariaDB installé et actif      (sudo systemctl start mariadb)
    2. Schéma créé                    (sudo mariadb < db/schema.sql)
    3. pymysql installé dans le venv  (pip install pymysql)

Lancer :
    python3 src/logger_mariadb.py

Vérifier en base (dans un autre terminal) :
    sudo mariadb iot_b3 -e "SELECT id, ts_utc, device, value, unit FROM telemetry ORDER BY id DESC LIMIT 10;"
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

TEAM   = "team01"
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
# 3) Connexion à la base
# ---------------------------------------------------------------------
def db_connect() -> pymysql.connections.Connection:
    """
    Ouvre une connexion vers MariaDB.
    autocommit=True : chaque INSERT est validé immédiatement.
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True,
        charset="utf8mb4",
    )

# Connexion globale, réutilisée dans on_message
db = db_connect()

# ---------------------------------------------------------------------
# 4) Fonctions utilitaires
# ---------------------------------------------------------------------
def utc_now() -> datetime:
    """
    Heure UTC actuelle sans tzinfo.
    MariaDB DATETIME ne stocke pas le fuseau : on stocke toujours en UTC
    par convention, ce qui évite les ambiguïtés.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

def extract_device(topic: str) -> str:
    """
    Extrait le nom du device depuis le topic.
    Convention : ahuntsic/aec-iot/b3/<team>/<device>/...
                 index :   0       1   2   3       4
    """
    parts = topic.split("/")
    return parts[4] if len(parts) >= 5 else "unknown"

def is_telemetry(topic: str) -> bool:
    """
    Retourne True si le topic est une mesure capteur.
    On exclut les topics /value (valeur simple publiée pour MQTT Dash)
    pour ne pas doubler les données en base.
    """
    return "/sensors/" in topic and not topic.endswith("/value")

def classify_kind(topic: str) -> str:
    """
    Classe l'événement selon le type de topic :
        cmd / state / status / other
    """
    if "/cmd/"    in topic or topic.endswith("/cmd")   : return "cmd"
    if "/state/"  in topic or topic.endswith("/state") : return "state"
    if "/status/" in topic or topic.endswith("/status"): return "status"
    return "other"

def try_parse_json(payload_text: str) -> Optional[dict]:
    """
    Tente de parser le payload en JSON.
    Retourne un dict si OK, None sinon (JSON cassé ou valeur non-dict).
    On ne lève jamais d'exception ici : le logger ne doit pas crasher.
    """
    try:
        obj = json.loads(payload_text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None

# ---------------------------------------------------------------------
# 5) Insertions en base
# ---------------------------------------------------------------------
def insert_telemetry(ts: datetime, device: str, topic: str, payload_text: str) -> None:
    """
    Insère une ligne dans la table telemetry.
    Si le payload est un JSON valide avec 'value' et 'unit', on les extrait.
    Sinon, value et unit restent NULL (on stocke toujours le payload brut).
    """
    obj   = try_parse_json(payload_text)
    value = None
    unit  = None

    if obj is not None:
        # Extraire value (nombre)
        if "value" in obj:
            try:
                value = float(obj["value"])
            except (TypeError, ValueError):
                value = None

        # Extraire unit (texte, max 16 caractères)
        if "unit" in obj and isinstance(obj["unit"], str):
            unit = obj["unit"][:16]

    sql = """
        INSERT INTO telemetry (ts_utc, device, topic, value, unit, payload)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with db.cursor() as cur:
        cur.execute(sql, (ts, device, topic, value, unit, payload_text))

def insert_event(ts: datetime, device: str, topic: str, kind: str, payload_text: str) -> None:
    """
    Insère une ligne dans la table events (commandes, états, statuts).
    """
    sql = """
        INSERT INTO events (ts_utc, device, topic, kind, payload)
        VALUES (%s, %s, %s, %s, %s)
    """
    with db.cursor() as cur:
        cur.execute(sql, (ts, device, topic, kind, payload_text))

# ---------------------------------------------------------------------
# 6) Callbacks MQTT
# ---------------------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    Appelée quand le broker répond à la connexion.
    L'abonnement est fait ici (et non une seule fois au démarrage)
    pour qu'il soit refait automatiquement après une reconnexion.
    """
    print(f"[CONNECT] reason_code={reason_code}")

    if reason_code == 0:
        client.subscribe(TOPIC_FILTER, qos=0)
        print(f"[SUB] {TOPIC_FILTER}")
    else:
        print("[ERROR] Connexion MQTT échouée.")

def on_message(client, userdata, msg):
    """
    Appelée pour chaque message reçu.
    Décide si c'est une mesure ou un événement, puis insère en BD.
    En cas d'erreur DB, on tente une reconnexion simple.
    """
    global db

    topic        = msg.topic
    payload_text = msg.payload.decode("utf-8", errors="replace")
    device       = extract_device(topic)
    ts           = utc_now()

    try:
        if is_telemetry(topic):
            insert_telemetry(ts, device, topic, payload_text)
            print(f"[DB] telemetry <- {topic}")
        else:
            kind = classify_kind(topic)
            insert_event(ts, device, topic, kind, payload_text)
            print(f"[DB] events({kind}) <- {topic}")

    except pymysql.MySQLError as e:
        # Si la base tombe (ex. MariaDB redémarré), on log et on tente de se reconnecter
        print(f"[DB-ERROR] {e} → tentative de reconnexion...")
        try:
            db.close()
        except Exception:
            pass
        db = db_connect()

def on_disconnect(client, userdata, reason_code, properties=None):
    print(f"[DISCONNECT] reason_code={reason_code}")

# ---------------------------------------------------------------------
# 7) Démarrage
# ---------------------------------------------------------------------
client = mqtt.Client(
    client_id=f"b3-logger-{TEAM}-{DEVICE}",
    protocol=mqtt.MQTTv311,
)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

client.reconnect_delay_set(min_delay=1, max_delay=30)
client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE_S)
print("[INFO] Logger démarré. CTRL+C pour arrêter.")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé")
finally:
    try:
        db.close()
    except Exception:
        pass
    client.disconnect()
    print("[STOP] déconnecté proprement.")
