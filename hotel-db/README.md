# Гостиница — информационная система учёта заселения и освобождения номеров

Курсовая работа по дисциплине «Технологии баз данных».
Предметная область № 5: «Гостиница». Стек: **Python 3.11+ · customtkinter · pyodbc · MS SQL Server**.

Программа автоматизирует:
- ведение справочников (категории номеров, номера, гости, сотрудники, дополнительные услуги);
- регистрацию заселения и освобождения номеров с автоматическим расчётом стоимости;
- ведение журнала всех заселений с поиском и фильтрацией;
- формирование отчёта за выбираемый период с экспортом в **Microsoft Word** и **печатью** на принтер.

Полная инструкция запуска под Windows + локально установленный SQL Server описана в файле [docs/USER_MANUAL.md](docs/USER_MANUAL.md). Описание базы данных — в [docs/DATABASE.md](docs/DATABASE.md).

---

## 1. Состав проекта

```
hotel_db/
├── sql/                              SQL-скрипты для MS SQL Server
│   ├── 01_create_database.sql        создание базы HotelDB
│   ├── 02_create_tables.sql          7 таблиц + ограничения PK/FK/CHECK/UNIQUE
│   ├── 03_views.sql                  4 представления (VIEW)
│   ├── 04_functions.sql              4 пользовательских функции
│   ├── 05_procedures.sql             4 хранимые процедуры
│   ├── 06_triggers.sql               4 триггера
│   ├── 07_seed_data.sql              тестовые данные
│   └── run_all.sql                   последовательный запуск всего пакета
├── app/                              Python-приложение
│   ├── main.py                       точка входа
│   ├── config.py                     загрузка параметров из .env
│   ├── db/
│   │   ├── connection.py             pyodbc-обёртка
│   │   └── repository.py             CRUD + вызовы процедур / функций
│   ├── forms/
│   │   ├── main_window.py            главное окно «Журнал заселений»
│   │   ├── dictionaries.py           формы справочников
│   │   ├── checkin.py                заселение и выселение
│   │   ├── report.py                 отчёт + экспорт в Word + печать
│   │   └── widgets.py                таблица и общие виджеты
│   └── reports/
│       └── word_export.py            формирование .docx
├── docs/
│   ├── USER_MANUAL.md                инструкция пользователя
│   └── DATABASE.md                   описание базы данных
├── requirements.txt
├── .env.example                      шаблон параметров подключения
└── README.md
```

## 2. Быстрый старт (Windows)

> Требуется: Windows 10/11, Python 3.11+, MS SQL Server 2019/2022 (Express или Developer), драйвер «ODBC Driver 18 for SQL Server».

1. Установить MS SQL Server и драйвер ODBC 18 (стандартные мастера).
2. В SQL Server Management Studio (SSMS) открыть и **выполнить по очереди** скрипты из `sql/01_… 07_seed_data.sql` (или один файл `sql/run_all.sql` в режиме SQLCMD).
3. Скопировать `.env.example` в `.env` и заполнить параметры подключения.
4. Установить зависимости и запустить приложение:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Подробности — в [docs/USER_MANUAL.md](docs/USER_MANUAL.md).

## 3. Объекты базы данных

| Тип | Кол-во | Имена |
|-----|:---:|------|
| Таблицы | 7 | RoomCategories, Rooms, Guests, Employees, AdditionalServices, Stays, StayServices |
| Представления (VIEW) | 4 | vw_ActiveStays, vw_StayDetails, vw_RevenueByCategory, vw_RoomOccupancy |
| Функции (FUNCTION) | 4 | fn_CalculateStayCost, fn_GetOccupancyRate, fn_GetGuestStayHistory, fn_IsRoomAvailable |
| Хранимые процедуры | 4 | sp_CheckInGuest, sp_CheckOutGuest, sp_GetReportByPeriod, sp_AddStayService |
| Триггеры | 4 | tr_Stays_AfterInsert, tr_Stays_AfterCheckOut, tr_Stays_PreventOverlap, tr_RoomCategories_PreventDelete |

Все объекты соответствуют требованиям задания (по 3+ каждого вида) и содержат проверки целостности и автоматизации (триггеры запрещают двойное заселение и автоматически меняют статус номера).

## 4. Скриншоты главных форм

При первом запуске пользователь видит «Журнал активных заселений», из него по меню «Справочники» открываются формы CRUD, кнопкой «Заселить» / «Выселить» — формы регистрации, в меню «Отчёты» — форма построения отчёта за период с экспортом в Word и печатью.
