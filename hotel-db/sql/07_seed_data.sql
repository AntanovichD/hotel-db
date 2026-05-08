-- =============================================================
-- 07_seed_data.sql
-- Заполнение справочников и журналов тестовыми данными
-- =============================================================
USE HotelDB;
GO

-- Категории номеров
INSERT INTO dbo.RoomCategories (CategoryName, BasePrice, Description) VALUES
(N'Стандарт',     80.00,  N'Одна двуспальная кровать, телевизор, душ.'),
(N'Полулюкс',    140.00,  N'Гостиная зона, мини-бар, ванна.'),
(N'Люкс',        220.00,  N'Две комнаты, рабочий стол, мини-бар.'),
(N'Семейный',    180.00,  N'Две спальни, кухонный уголок.'),
(N'Эконом',       55.00,  N'Односпальная кровать, общая ванная.');
GO

-- Номера
INSERT INTO dbo.Rooms (RoomNumber, CategoryID, Floor, Status, Notes) VALUES
(N'101', 5, 1, N'Свободен', NULL),
(N'102', 5, 1, N'Свободен', NULL),
(N'103', 1, 1, N'Свободен', NULL),
(N'201', 1, 2, N'Свободен', NULL),
(N'202', 1, 2, N'Свободен', NULL),
(N'203', 2, 2, N'Свободен', NULL),
(N'301', 2, 3, N'Свободен', NULL),
(N'302', 4, 3, N'Свободен', NULL),
(N'401', 3, 4, N'Свободен', N'Угловой номер с панорамным видом'),
(N'402', 3, 4, N'Свободен', NULL);
GO

-- Гости
INSERT INTO dbo.Guests (FullName, PassportNumber, BirthDate, Phone, Email) VALUES
(N'Иванов Иван Иванович',     N'AB1234567', '1985-04-12', N'+375291234567', N'ivanov@example.com'),
(N'Петров Пётр Петрович',     N'BC2345678', '1990-09-23', N'+375297654321', N'petrov@example.com'),
(N'Сидорова Анна Сергеевна',  N'CD3456789', '1992-02-05', N'+375293334455', N'sidorova@example.com'),
(N'Козлов Алексей Викторович',N'DE4567890', '1978-11-30', N'+375296667788', NULL),
(N'Романова Мария Олеговна',  N'EF5678901', '1995-07-17', N'+375299990011', N'romanova@example.com');
GO

-- Сотрудники
INSERT INTO dbo.Employees (FullName, Position, Phone, HireDate) VALUES
(N'Михайлова Ольга Павловна', N'Администратор', N'+375291110000', '2022-01-15'),
(N'Соколов Игорь Андреевич',  N'Администратор', N'+375292220000', '2023-03-10'),
(N'Беляев Дмитрий Сергеевич', N'Старший администратор', N'+375293330000', '2020-06-20');
GO

-- Дополнительные услуги
INSERT INTO dbo.AdditionalServices (ServiceName, Price, Description) VALUES
(N'Завтрак',          15.00, N'Континентальный завтрак в ресторане отеля'),
(N'Парковка',         10.00, N'Подземный паркинг (в сутки)'),
(N'Стирка белья',     20.00, N'Стирка и глажка'),
(N'Дополнительная кровать', 25.00, N'Раскладная кровать в номер'),
(N'Wi-Fi премиум',     5.00, N'Скоростной интернет');
GO

-- Тестовые заселения (через процедуру, чтобы триггеры отработали)
DECLARE @StayID INT;
EXEC dbo.sp_CheckInGuest @RoomID = 1, @GuestID = 1, @EmployeeID = 1,
     @PlannedCheckOutDate = '2026-12-31', @Notes = N'Без особых пожеланий', @StayID = @StayID OUTPUT;

EXEC dbo.sp_CheckInGuest @RoomID = 5, @GuestID = 2, @EmployeeID = 2,
     @PlannedCheckOutDate = '2026-12-25', @Notes = NULL, @StayID = @StayID OUTPUT;

EXEC dbo.sp_CheckInGuest @RoomID = 9, @GuestID = 3, @EmployeeID = 3,
     @PlannedCheckOutDate = '2026-12-20', @Notes = N'VIP-гость', @StayID = @StayID OUTPUT;
GO

-- Завершённое заселение для отчётов
INSERT INTO dbo.Stays (RoomID, GuestID, EmployeeID, CheckInDate, PlannedCheckOutDate,
                       ActualCheckOutDate, TotalCost, Notes)
VALUES (3, 4, 1, '2026-04-15 14:00', '2026-04-20', '2026-04-20 11:30', 400.00, N'Командировка');
GO
