-- =============================================================
-- 03_views.sql
-- Представления (3+)
-- =============================================================
USE HotelDB;
GO

-- 1) Активные (текущие) заселения с полной информацией о госте, номере и сотруднике
IF OBJECT_ID('dbo.vw_ActiveStays', 'V') IS NOT NULL
    DROP VIEW dbo.vw_ActiveStays;
GO
CREATE VIEW dbo.vw_ActiveStays
AS
SELECT
    s.StayID,
    r.RoomNumber,
    rc.CategoryName,
    rc.BasePrice,
    g.FullName        AS GuestFullName,
    g.PassportNumber,
    g.Phone           AS GuestPhone,
    e.FullName        AS EmployeeFullName,
    s.CheckInDate,
    s.PlannedCheckOutDate,
    DATEDIFF(DAY, s.CheckInDate, s.PlannedCheckOutDate) AS PlannedDays,
    s.Notes
FROM dbo.Stays AS s
INNER JOIN dbo.Rooms          AS r  ON r.RoomID = s.RoomID
INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID
INNER JOIN dbo.Guests         AS g  ON g.GuestID = s.GuestID
INNER JOIN dbo.Employees      AS e  ON e.EmployeeID = s.EmployeeID
WHERE s.ActualCheckOutDate IS NULL;
GO

-- 2) Полный журнал заселений (как активные, так и завершённые) для отчётов
IF OBJECT_ID('dbo.vw_StayDetails', 'V') IS NOT NULL
    DROP VIEW dbo.vw_StayDetails;
GO
CREATE VIEW dbo.vw_StayDetails
AS
SELECT
    s.StayID,
    r.RoomNumber,
    rc.CategoryName,
    rc.BasePrice,
    g.FullName  AS GuestFullName,
    g.PassportNumber,
    e.FullName  AS EmployeeFullName,
    s.CheckInDate,
    s.PlannedCheckOutDate,
    s.ActualCheckOutDate,
    CASE WHEN s.ActualCheckOutDate IS NULL THEN N'Активно' ELSE N'Завершено' END AS Status,
    s.TotalCost,
    s.Notes
FROM dbo.Stays AS s
INNER JOIN dbo.Rooms          AS r  ON r.RoomID = s.RoomID
INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID
INNER JOIN dbo.Guests         AS g  ON g.GuestID = s.GuestID
INNER JOIN dbo.Employees      AS e  ON e.EmployeeID = s.EmployeeID;
GO

-- 3) Доход по категориям номеров (для аналитики и отчётов)
IF OBJECT_ID('dbo.vw_RevenueByCategory', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevenueByCategory;
GO
CREATE VIEW dbo.vw_RevenueByCategory
AS
SELECT
    rc.CategoryID,
    rc.CategoryName,
    COUNT(s.StayID)                 AS StaysCount,
    ISNULL(SUM(s.TotalCost), 0)     AS TotalRevenue,
    ISNULL(AVG(NULLIF(s.TotalCost, 0)), 0) AS AverageStayCost
FROM dbo.RoomCategories AS rc
LEFT JOIN dbo.Rooms AS r ON r.CategoryID = rc.CategoryID
LEFT JOIN dbo.Stays AS s ON s.RoomID = r.RoomID AND s.ActualCheckOutDate IS NOT NULL
GROUP BY rc.CategoryID, rc.CategoryName;
GO

-- 4) Список занятости номеров (служебное представление)
IF OBJECT_ID('dbo.vw_RoomOccupancy', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RoomOccupancy;
GO
CREATE VIEW dbo.vw_RoomOccupancy
AS
SELECT
    r.RoomID,
    r.RoomNumber,
    rc.CategoryName,
    rc.BasePrice,
    r.Floor,
    r.Status,
    (SELECT TOP 1 g.FullName
       FROM dbo.Stays AS s
       INNER JOIN dbo.Guests AS g ON g.GuestID = s.GuestID
       WHERE s.RoomID = r.RoomID AND s.ActualCheckOutDate IS NULL
       ORDER BY s.CheckInDate DESC) AS CurrentGuest
FROM dbo.Rooms AS r
INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID;
GO
