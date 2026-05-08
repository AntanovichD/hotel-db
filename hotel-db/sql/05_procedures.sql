-- =============================================================
-- 05_procedures.sql
-- Хранимые процедуры (3+)
-- =============================================================
USE HotelDB;
GO

-- 1) Регистрация заселения гостя в номер
IF OBJECT_ID('dbo.sp_CheckInGuest', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_CheckInGuest;
GO
CREATE PROCEDURE dbo.sp_CheckInGuest
    @RoomID              INT,
    @GuestID             INT,
    @EmployeeID          INT,
    @PlannedCheckOutDate DATE,
    @Notes               NVARCHAR(256) = NULL,
    @StayID              INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM dbo.Rooms WHERE RoomID = @RoomID)
            THROW 50001, N'Указанный номер не найден.', 1;

        IF NOT EXISTS (SELECT 1 FROM dbo.Guests WHERE GuestID = @GuestID)
            THROW 50002, N'Указанный гость не найден.', 1;

        IF NOT EXISTS (SELECT 1 FROM dbo.Employees WHERE EmployeeID = @EmployeeID)
            THROW 50003, N'Указанный сотрудник не найден.', 1;

        IF EXISTS (
            SELECT 1 FROM dbo.Stays
            WHERE RoomID = @RoomID AND ActualCheckOutDate IS NULL
        )
            THROW 50004, N'Этот номер уже занят. Сначала оформите выселение.', 1;

        IF (SELECT Status FROM dbo.Rooms WHERE RoomID = @RoomID) = N'Ремонт'
            THROW 50005, N'Номер находится на ремонте и недоступен для заселения.', 1;

        IF @PlannedCheckOutDate < CAST(GETDATE() AS DATE)
            THROW 50006, N'Плановая дата выселения не может быть в прошлом.', 1;

        INSERT INTO dbo.Stays (RoomID, GuestID, EmployeeID, PlannedCheckOutDate, Notes)
        VALUES (@RoomID, @GuestID, @EmployeeID, @PlannedCheckOutDate, @Notes);

        SET @StayID = SCOPE_IDENTITY();

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
GO

-- 2) Регистрация выселения гостя (с автоматическим расчётом стоимости)
IF OBJECT_ID('dbo.sp_CheckOutGuest', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_CheckOutGuest;
GO
CREATE PROCEDURE dbo.sp_CheckOutGuest
    @StayID    INT,
    @TotalCost DECIMAL(12, 2) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM dbo.Stays WHERE StayID = @StayID)
            THROW 50010, N'Запись о заселении не найдена.', 1;

        IF EXISTS (SELECT 1 FROM dbo.Stays WHERE StayID = @StayID AND ActualCheckOutDate IS NOT NULL)
            THROW 50011, N'Это заселение уже завершено.', 1;

        SET @TotalCost = dbo.fn_CalculateStayCost(@StayID);

        UPDATE dbo.Stays
        SET ActualCheckOutDate = SYSDATETIME(),
            TotalCost = @TotalCost
        WHERE StayID = @StayID;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
GO

-- 3) Отчёт по заселениям за выбираемый период с фильтром по категории и сотруднику
IF OBJECT_ID('dbo.sp_GetReportByPeriod', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_GetReportByPeriod;
GO
CREATE PROCEDURE dbo.sp_GetReportByPeriod
    @StartDate  DATE,
    @EndDate    DATE,
    @CategoryID INT = NULL,
    @EmployeeID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        s.StayID,
        r.RoomNumber,
        rc.CategoryName,
        g.FullName       AS GuestFullName,
        g.PassportNumber,
        e.FullName       AS EmployeeFullName,
        s.CheckInDate,
        s.PlannedCheckOutDate,
        s.ActualCheckOutDate,
        CASE WHEN s.ActualCheckOutDate IS NULL THEN N'Активно' ELSE N'Завершено' END AS Status,
        s.TotalCost
    FROM dbo.Stays AS s
    INNER JOIN dbo.Rooms          AS r  ON r.RoomID = s.RoomID
    INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID
    INNER JOIN dbo.Guests         AS g  ON g.GuestID = s.GuestID
    INNER JOIN dbo.Employees      AS e  ON e.EmployeeID = s.EmployeeID
    WHERE CAST(s.CheckInDate AS DATE) BETWEEN @StartDate AND @EndDate
      AND (@CategoryID IS NULL OR rc.CategoryID = @CategoryID)
      AND (@EmployeeID IS NULL OR e.EmployeeID = @EmployeeID)
    ORDER BY s.CheckInDate DESC;
END
GO

-- 4) Добавление дополнительной услуги к проживанию
IF OBJECT_ID('dbo.sp_AddStayService', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_AddStayService;
GO
CREATE PROCEDURE dbo.sp_AddStayService
    @StayID    INT,
    @ServiceID INT,
    @Quantity  INT = 1
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Price DECIMAL(10, 2);
    SELECT @Price = Price FROM dbo.AdditionalServices WHERE ServiceID = @ServiceID;

    IF @Price IS NULL
        THROW 50020, N'Услуга не найдена.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Stays WHERE StayID = @StayID AND ActualCheckOutDate IS NULL)
        THROW 50021, N'Заселение не найдено или уже завершено.', 1;

    INSERT INTO dbo.StayServices (StayID, ServiceID, Quantity, Cost)
    VALUES (@StayID, @ServiceID, @Quantity, @Price);
END
GO
