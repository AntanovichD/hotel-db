-- =============================================================
-- 01_create_database.sql
-- Создание базы данных HotelDB
-- =============================================================
USE master;
GO

IF DB_ID('HotelDB') IS NOT NULL
BEGIN
    ALTER DATABASE HotelDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE HotelDB;
END
GO

CREATE DATABASE HotelDB
COLLATE Cyrillic_General_CI_AS;
GO

USE HotelDB;
GO
