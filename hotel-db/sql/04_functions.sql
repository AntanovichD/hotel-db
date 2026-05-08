-- =============================================================
-- 04_functions.sql
-- Пользовательские функции (3+)
-- =============================================================
USE HotelDB;
GO

-- 1) Расчёт текущей стоимости проживания по StayID
--    (стоимость = базовая цена категории * фактические дни + сумма доп. услуг)
IF OBJECT_ID('dbo.fn_CalculateStayCost', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_CalculateStayCost;
GO
CREATE FUNCTION dbo.fn_CalculateStayCost (@StayID INT)
RETURNS DECIMAL(12, 2)
AS
BEGIN
    DECLARE @BasePrice  DECIMAL(10, 2);
    DECLARE @CheckIn    DATETIME2(0);
    DECLARE @CheckOut   DATETIME2(0);
    DECLARE @Days       INT;
    DECLARE @Services   DECIMAL(12, 2);
    DECLARE @Total      DECIMAL(12, 2);

    SELECT
        @BasePrice = rc.BasePrice,
        @CheckIn   = s.CheckInDate,
        @CheckOut  = ISNULL(s.ActualCheckOutDate, CAST(s.PlannedCheckOutDate AS DATETIME2(0)))
    FROM dbo.Stays AS s
    INNER JOIN dbo.Rooms          AS r  ON r.RoomID = s.RoomID
    INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID
    WHERE s.StayID = @StayID;

    IF @BasePrice IS NULL
        RETURN 0;

    SET @Days = DATEDIFF(DAY, @CheckIn, @CheckOut);
    IF @Days < 1
        SET @Days = 1;

    SELECT @Services = ISNULL(SUM(Cost * Quantity), 0)
    FROM dbo.StayServices
    WHERE StayID = @StayID;

    SET @Total = (@BasePrice * @Days) + @Services;
    RETURN @Total;
END
GO

-- 2) Заполняемость гостиницы (в процентах) за период
IF OBJECT_ID('dbo.fn_GetOccupancyRate', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_GetOccupancyRate;
GO
CREATE FUNCTION dbo.fn_GetOccupancyRate (@StartDate DATE, @EndDate DATE)
RETURNS DECIMAL(5, 2)
AS
BEGIN
    DECLARE @TotalRoomDays  INT;
    DECLARE @OccupiedDays   INT;
    DECLARE @TotalRooms     INT;
    DECLARE @PeriodDays     INT;

    SELECT @TotalRooms = COUNT(*) FROM dbo.Rooms;
    SET @PeriodDays = DATEDIFF(DAY, @StartDate, @EndDate) + 1;
    IF @TotalRooms = 0 OR @PeriodDays <= 0
        RETURN 0;

    SET @TotalRoomDays = @TotalRooms * @PeriodDays;

    SELECT @OccupiedDays = ISNULL(SUM(
        DATEDIFF(DAY,
            CASE WHEN CAST(s.CheckInDate AS DATE) < @StartDate THEN @StartDate ELSE CAST(s.CheckInDate AS DATE) END,
            CASE WHEN ISNULL(CAST(s.ActualCheckOutDate AS DATE), s.PlannedCheckOutDate) > @EndDate
                 THEN @EndDate
                 ELSE ISNULL(CAST(s.ActualCheckOutDate AS DATE), s.PlannedCheckOutDate)
            END
        ) + 1
    ), 0)
    FROM dbo.Stays AS s
    WHERE CAST(s.CheckInDate AS DATE) <= @EndDate
      AND ISNULL(CAST(s.ActualCheckOutDate AS DATE), s.PlannedCheckOutDate) >= @StartDate;

    RETURN CAST(@OccupiedDays AS DECIMAL(10, 2)) * 100.0 / @TotalRoomDays;
END
GO

-- 3) История проживаний конкретного гостя — табличная функция
IF OBJECT_ID('dbo.fn_GetGuestStayHistory', 'IF') IS NOT NULL
    DROP FUNCTION dbo.fn_GetGuestStayHistory;
GO
CREATE FUNCTION dbo.fn_GetGuestStayHistory (@GuestID INT)
RETURNS TABLE
AS
RETURN
(
    SELECT
        s.StayID,
        r.RoomNumber,
        rc.CategoryName,
        s.CheckInDate,
        s.ActualCheckOutDate,
        s.TotalCost
    FROM dbo.Stays AS s
    INNER JOIN dbo.Rooms          AS r  ON r.RoomID = s.RoomID
    INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID
    WHERE s.GuestID = @GuestID
);
GO

-- 4) Возвращает 1, если номер свободен на дату, иначе 0
IF OBJECT_ID('dbo.fn_IsRoomAvailable', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_IsRoomAvailable;
GO
CREATE FUNCTION dbo.fn_IsRoomAvailable (@RoomID INT, @CheckDate DATE)
RETURNS BIT
AS
BEGIN
    IF EXISTS (
        SELECT 1
        FROM dbo.Stays AS s
        WHERE s.RoomID = @RoomID
          AND CAST(s.CheckInDate AS DATE) <= @CheckDate
          AND ISNULL(CAST(s.ActualCheckOutDate AS DATE), s.PlannedCheckOutDate) >= @CheckDate
    )
        RETURN 0;
    RETURN 1;
END
GO
