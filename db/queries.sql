-- db/queries.sql  —  SQUELETTE (branche main)
-- ============================================
-- Requêtes utiles pour vérifier les données en démo.
-- À exécuter dans MariaDB :  sudo mariadb iot_b3 < db/queries.sql
--
-- TODO (branche feature/logger-mariadb) :
--   Compléter les 3 requêtes de démo.

USE iot_b3;

-- Requête 1 — 10 dernières mesures
-- TODO : SELECT ... FROM telemetry ORDER BY id DESC LIMIT 10;

-- Requête 2 — 10 dernières commandes
-- TODO : SELECT ... FROM events WHERE kind='cmd' ORDER BY id DESC LIMIT 10;

-- Requête 3 — Nombre d'événements par type
-- TODO : SELECT kind, COUNT(*) AS n FROM events GROUP BY kind;
