-- Topic #12 setup: build the slow scene from Step 0 of the tutorial.
-- Creates DemoDb with a 200,000-row Orders table (eight Canadian cities,
-- 2,061 of them Toronto) and deliberately NO index on City - that missing
-- index is the planted fault the four checks go hunting for.
-- Run this first; every other script assumes DemoDb exists.

CREATE DATABASE DemoDb;
GO
USE DemoDb;
GO
CREATE TABLE dbo.Orders (
    OrderId     INT IDENTITY(1,1) CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId  INT           NOT NULL,
    City        NVARCHAR(40)  NOT NULL,
    OrderDate   DATE          NOT NULL,
    Total       DECIMAL(10,2) NOT NULL,
    Notes       NVARCHAR(300) NOT NULL
);
GO
WITH Tally AS (
    SELECT TOP (200000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.Orders (CustomerId, City, OrderDate, Total, Notes)
SELECT
    (n % 5000) + 1,
    CASE WHEN n % 97 = 0 THEN N'Toronto'
         ELSE CHOOSE((n % 7) + 1, N'Ottawa', N'Montreal', N'Calgary',
                     N'Vancouver', N'Edmonton', N'Winnipeg', N'Halifax') END,
    DATEADD(DAY, n % 730, '2024-01-01'),
    CAST(10 + (n % 990) AS DECIMAL(10,2)),
    REPLICATE(N'x', 200)
FROM Tally;
GO
SELECT COUNT(*) AS orders_rows FROM dbo.Orders;
SELECT City, COUNT(*) AS rows_per_city FROM dbo.Orders GROUP BY City ORDER BY rows_per_city DESC;
GO
