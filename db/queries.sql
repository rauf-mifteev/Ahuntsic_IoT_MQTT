-- db/queries.sql  
-- =============================================================================
-- Requêtes utiles pour la démonstration.
-- Exécuter dans MariaDB :
--   sudo mariadb iot_b3 < db/queries.sql
-- Ou une par une dans la console :
--   sudo mariadb iot_b3

USE iot_b3;

-- -----------------------------------------------------------------------------
-- Requête 1 — 10 dernières mesures de température
-- Utilité : vérifier que le publisher envoie bien des données et qu'elles
--           sont correctement enregistrées en base.
-- -----------------------------------------------------------------------------
SELECT id, ts_utc, device, topic, value, unit
FROM   telemetry
ORDER  BY id DESC
LIMIT  10;

-- -----------------------------------------------------------------------------
-- Requête 2 — 10 dernières commandes envoyées à la DEL
-- Utilité : vérifier que les commandes depuis MQTT Dash sont bien reçues
--           et enregistrées.
-- -----------------------------------------------------------------------------
SELECT id, ts_utc, device, kind, topic, payload
FROM   events
WHERE  kind = 'cmd'
ORDER  BY id DESC
LIMIT  10;

-- -----------------------------------------------------------------------------
-- Requête 3 — Nombre d'événements par type
-- Utilité : avoir une vue d'ensemble rapide de l'activité du système.
-- -----------------------------------------------------------------------------
SELECT   kind, COUNT(*) AS n
FROM     events
GROUP BY kind
ORDER BY n DESC;

