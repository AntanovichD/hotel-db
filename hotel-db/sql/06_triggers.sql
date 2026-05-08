-- =============================================================
-- 06_triggers.sql
-- Триггеры (3+)
-- =============================================================
USE HotelDB;
GO

-- 1) После заселения переводим номер в статус «Занят»
IF OBJECT_ID('dbo.tr_Stays_AfterInsert', 'TR') IS NOT NULL
    DROP TRIGGER dbo.tr_Stays_AfterInsert;
GO
CREATE TRIGGER dbo.tr_Stays_AfterInsert
ON dbo.Stays
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE r
    SET r.Status = N'Занят'
    FROM dbo.Rooms AS r
    INNER JOIN inserted AS i ON i.RoomID = r.RoomID
    WHERE i.ActualCheckOutDate IS NULL;
END
GO

-- 2) При выселении (заполнение ActualCheckOutDate) освобождаем номер
IF OBJECT_ID('dbo.tr_Stays_AfterCheckOut', 'TR') IS NOT NULL
    DROP TRIGGER dbo.tr_Stays_AfterCheckOut;
GO
CREATE TRIGGER dbo.tr_Stays_AfterCheckOut
ON dbo.Stays
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT UPDATE(ActualCheckOutDate)
        RETURN;

    UPDATE r
    SET r.Status = N'Свободен'
    FROM dbo.Rooms AS r
    INNER JOIN inserted AS i ON i.RoomID = r.RoomID
    INNER JOIN deleted  AS d ON d.StayID = i.StayID
    WHERE d.ActualCheckOutDate IS NULL
      AND i.ActualCheckOutDate IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM dbo.Stays AS s
          WHERE s.RoomID = i.RoomID
            AND s.ActualCheckOutDate IS NULL
            AND s.StayID <> i.StayID
      );
END
GO

-- 3) Запрет двойного заселения в один и тот же номер (AFTER INSERT)
-- AFTER INSERT нужен потому, что INSTEAD OF INSERT ломает SCOPE_IDENTITY()
-- в вызывающей процедуре (SET @StayID = SCOPE_IDENTITY()).
-- THROW в AFTER-триггере приводит к откату текущей транзакции SQL Server.
IF OBJECT_ID('dbo.tr_Stays_PreventOverlap', 'TR') IS NOT NULL
    DROP TRIGGER dbo.tr_Stays_PreventOverlap;
GO
CREATE TRIGGER dbo.tr_Stays_PreventOverlap
ON dbo.Stays
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM inserted AS i
        INNER JOIN dbo.Stays AS s
            ON s.RoomID = i.RoomID
           AND s.StayID <> i.StayID
           AND s.ActualCheckOutDate IS NULL
        WHERE i.ActualCheckOutDate IS NULL
    )
    BEGIN
        THROW 50100, N'В этом номере уже проживает гость. Сначала выполните выселение.', 1;
    END
END
GO

-- 4) Защита от удаления категории, у которой остались номера
IF OBJECT_ID('dbo.tr_RoomCategories_PreventDelete', 'TR') IS NOT NULL
    DROP TRIGGER dbo.tr_RoomCategories_PreventDelete;
GO
CREATE TRIGGER dbo.tr_RoomCategories_PreventDelete
ON dbo.RoomCategories
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM deleted AS d
        INNER JOIN dbo.Rooms AS r ON r.CategoryID = d.CategoryID
    )
    BEGIN
        THROW 50200, N'Невозможно удалить категорию: к ней привязаны номера.', 1;
        RETURN;
    END

    DELETE rc
    FROM dbo.RoomCategories AS rc
    INNER JOIN deleted AS d ON d.CategoryID = rc.CategoryID;
END
GO
