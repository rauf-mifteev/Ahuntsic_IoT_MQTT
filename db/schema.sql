-- db/schema.sql  —  SQUELETTE (branche main)
-- ============================================
-- Crée la base de données et les tables pour le projet SmartLab.
-- À exécuter UNE seule fois sur le Raspberry Pi :
--   sudo mariadb < db/schema.sql
--
-- TODO (branche feature/logger-mariadb) :
--   1. Compléter CREATE TABLE telemetry (colonnes + index)
--   2. Compléter CREATE TABLE events    (colonnes + index)

-- ---------------------------------------------------------------------
-- Base de données
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS iot_b3
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Créer un utilisateur dédié (mot de passe simple pour le labo)
CREATE USER IF NOT EXISTS 'iot'@'localhost' IDENTIFIED BY 'iot';
GRANT ALL PRIVILEGES ON iot_b3.* TO 'iot'@'localhost';
FLUSH PRIVILEGES;

USE iot_b3;

-- ---------------------------------------------------------------------
-- Table 1 : télémétrie (mesures capteurs)
-- TODO : ajouter les colonnes et l'index
-- ---------------------------------------------------------------------
-- CREATE TABLE telemetry (
--     ...
-- );

-- ---------------------------------------------------------------------
-- Table 2 : événements (commandes / états / statuts)
-- TODO : ajouter les colonnes et l'index
-- ---------------------------------------------------------------------
-- CREATE TABLE events (
--     ...
-- );
