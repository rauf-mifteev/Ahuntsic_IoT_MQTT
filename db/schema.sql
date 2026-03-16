-- db/schema.sql  
-- =============================================================================
-- Crée la base de données IoT et ses deux tables.
-- On peut relancer ce script sans erreur (IF NOT EXISTS).
--
-- Exécuter UNE seule fois sur le Raspberry Pi :
--   sudo mariadb < db/schema.sql
--
-- Vérifier ensuite :
--   sudo mariadb iot_b3 -e "SHOW TABLES;"

-- -----------------------------------------------------------------------------
-- Base de données
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS iot_b3
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Utilisateur dédié 
CREATE USER IF NOT EXISTS 'iot'@'localhost' IDENTIFIED BY 'iot';
GRANT ALL PRIVILEGES ON iot_b3.* TO 'iot'@'localhost';
FLUSH PRIVILEGES;

USE iot_b3;

-- -----------------------------------------------------------------------------
-- Table 1 : telemetry — mesures des capteurs
-- -----------------------------------------------------------------------------
-- Chaque ligne = un message publié sur un topic .../sensors/...
-- value et unit peuvent être NULL si le payload n'est pas un JSON standard.
CREATE TABLE IF NOT EXISTS telemetry (
    id      BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,   -- clé primaire auto
    ts_utc  DATETIME(3)      NOT NULL,                  -- temps UTC (ms)
    device  VARCHAR(32)      NOT NULL,                  -- ex. "pi01"
    topic   VARCHAR(255)     NOT NULL,                  -- topic MQTT complet
    value   DOUBLE           NULL,                      -- valeur numérique
    unit    VARCHAR(16)      NULL,                      -- ex. "C", "%", "lux"
    payload TEXT             NOT NULL,                  -- payload brut (JSON ou texte)

    PRIMARY KEY (id),
    INDEX idx_telemetry_device_ts (device, ts_utc)      -- accélère les requêtes "dernières mesures par appareil"
);

-- -----------------------------------------------------------------------------
-- Table 2 : events — commandes, états, statuts
-- -----------------------------------------------------------------------------
-- Chaque ligne = un message sur /cmd/, /state/ ou /status/
CREATE TABLE IF NOT EXISTS events (
    id      BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    ts_utc  DATETIME(3)      NOT NULL,
    device  VARCHAR(32)      NOT NULL,
    topic   VARCHAR(255)     NOT NULL,
    kind    VARCHAR(16)      NOT NULL,                  -- "cmd" / "state" / "status" / "other"
    payload TEXT             NOT NULL,

    PRIMARY KEY (id),
    INDEX idx_events_device_ts (device, ts_utc)
);
