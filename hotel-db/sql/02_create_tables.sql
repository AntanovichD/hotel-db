-- =============================================================
-- 02_create_tables.sql
-- Создание таблиц предметной области «Гостиница»
-- =============================================================
USE HotelDB;
GO

-- Справочник категорий номеров
CREATE TABLE dbo.RoomCategories
(
    CategoryID    INT            IDENTITY(1, 1) NOT NULL,
    CategoryName  NVARCHAR(64)   NOT NULL,
    BasePrice     DECIMAL(10, 2) NOT NULL,
    Description   NVARCHAR(256)  NULL,
    CONSTRAINT PK_RoomCategories PRIMARY KEY (CategoryID),
    CONSTRAINT UQ_RoomCategories_Name UNIQUE (CategoryName),
    CONSTRAINT CK_RoomCategories_Price CHECK (BasePrice >= 0)
);
GO

-- Справочник номеров
CREATE TABLE dbo.Rooms
(
    RoomID      INT           IDENTITY(1, 1) NOT NULL,
    RoomNumber  NVARCHAR(16)  NOT NULL,
    CategoryID  INT           NOT NULL,
    Floor       INT           NOT NULL,
    Status      NVARCHAR(16)  NOT NULL CONSTRAINT DF_Rooms_Status DEFAULT (N'Свободен'),
    Notes       NVARCHAR(256) NULL,
    CONSTRAINT PK_Rooms PRIMARY KEY (RoomID),
    CONSTRAINT UQ_Rooms_Number UNIQUE (RoomNumber),
    CONSTRAINT FK_Rooms_Categories FOREIGN KEY (CategoryID)
        REFERENCES dbo.RoomCategories (CategoryID),
    CONSTRAINT CK_Rooms_Floor  CHECK (Floor BETWEEN 1 AND 50),
    CONSTRAINT CK_Rooms_Status CHECK (Status IN (N'Свободен', N'Занят', N'Ремонт'))
);
GO

-- Справочник гостей
CREATE TABLE dbo.Guests
(
    GuestID         INT          IDENTITY(1, 1) NOT NULL,
    FullName        NVARCHAR(128) NOT NULL,
    PassportNumber  NVARCHAR(32)  NOT NULL,
    BirthDate       DATE          NULL,
    Phone           NVARCHAR(32)  NULL,
    Email           NVARCHAR(128) NULL,
    CONSTRAINT PK_Guests PRIMARY KEY (GuestID),
    CONSTRAINT UQ_Guests_Passport UNIQUE (PassportNumber)
);
GO

-- Справочник сотрудников (администраторы, регистрирующие заселение)
CREATE TABLE dbo.Employees
(
    EmployeeID INT           IDENTITY(1, 1) NOT NULL,
    FullName   NVARCHAR(128) NOT NULL,
    Position   NVARCHAR(64)  NOT NULL,
    Phone      NVARCHAR(32)  NULL,
    HireDate   DATE          NOT NULL CONSTRAINT DF_Employees_HireDate DEFAULT (CAST(GETDATE() AS DATE)),
    CONSTRAINT PK_Employees PRIMARY KEY (EmployeeID)
);
GO

-- Справочник дополнительных услуг
CREATE TABLE dbo.AdditionalServices
(
    ServiceID   INT            IDENTITY(1, 1) NOT NULL,
    ServiceName NVARCHAR(128)  NOT NULL,
    Price       DECIMAL(10, 2) NOT NULL,
    Description NVARCHAR(256)  NULL,
    CONSTRAINT PK_AdditionalServices PRIMARY KEY (ServiceID),
    CONSTRAINT UQ_AdditionalServices_Name UNIQUE (ServiceName),
    CONSTRAINT CK_AdditionalServices_Price CHECK (Price >= 0)
);
GO

-- Журнал заселений (главная таблица учёта)
CREATE TABLE dbo.Stays
(
    StayID                INT            IDENTITY(1, 1) NOT NULL,
    RoomID                INT            NOT NULL,
    GuestID               INT            NOT NULL,
    EmployeeID            INT            NOT NULL,
    CheckInDate           DATETIME2(0)   NOT NULL CONSTRAINT DF_Stays_CheckInDate DEFAULT (SYSDATETIME()),
    PlannedCheckOutDate   DATE           NOT NULL,
    ActualCheckOutDate    DATETIME2(0)   NULL,
    TotalCost             DECIMAL(12, 2) NOT NULL CONSTRAINT DF_Stays_TotalCost DEFAULT (0),
    Notes                 NVARCHAR(256)  NULL,
    CONSTRAINT PK_Stays PRIMARY KEY (StayID),
    CONSTRAINT FK_Stays_Rooms     FOREIGN KEY (RoomID)     REFERENCES dbo.Rooms (RoomID),
    CONSTRAINT FK_Stays_Guests    FOREIGN KEY (GuestID)    REFERENCES dbo.Guests (GuestID),
    CONSTRAINT FK_Stays_Employees FOREIGN KEY (EmployeeID) REFERENCES dbo.Employees (EmployeeID),
    CONSTRAINT CK_Stays_PlannedDate CHECK (PlannedCheckOutDate >= CAST(CheckInDate AS DATE)),
    CONSTRAINT CK_Stays_ActualDate  CHECK (ActualCheckOutDate IS NULL OR ActualCheckOutDate >= CheckInDate),
    CONSTRAINT CK_Stays_TotalCost   CHECK (TotalCost >= 0)
);
GO

CREATE INDEX IX_Stays_RoomID            ON dbo.Stays (RoomID);
CREATE INDEX IX_Stays_GuestID           ON dbo.Stays (GuestID);
CREATE INDEX IX_Stays_CheckInDate       ON dbo.Stays (CheckInDate);
CREATE INDEX IX_Stays_ActualCheckOut    ON dbo.Stays (ActualCheckOutDate);
GO

-- Заказанные дополнительные услуги по конкретному заселению
CREATE TABLE dbo.StayServices
(
    StayServiceID INT            IDENTITY(1, 1) NOT NULL,
    StayID        INT            NOT NULL,
    ServiceID     INT            NOT NULL,
    ServiceDate   DATETIME2(0)   NOT NULL CONSTRAINT DF_StayServices_Date DEFAULT (SYSDATETIME()),
    Quantity      INT            NOT NULL CONSTRAINT DF_StayServices_Qty  DEFAULT (1),
    Cost          DECIMAL(10, 2) NOT NULL,
    CONSTRAINT PK_StayServices PRIMARY KEY (StayServiceID),
    CONSTRAINT FK_StayServices_Stays    FOREIGN KEY (StayID)    REFERENCES dbo.Stays (StayID) ON DELETE CASCADE,
    CONSTRAINT FK_StayServices_Services FOREIGN KEY (ServiceID) REFERENCES dbo.AdditionalServices (ServiceID),
    CONSTRAINT CK_StayServices_Qty   CHECK (Quantity > 0),
    CONSTRAINT CK_StayServices_Cost  CHECK (Cost >= 0)
);
GO

CREATE INDEX IX_StayServices_StayID ON dbo.StayServices (StayID);
GO
