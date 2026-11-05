-- Topic #8 setup: the demo database used by the backup/restore walkthrough.
-- This is the exact script run in the tutorial (Topic #7's canonical demo data).
-- Creates DemoDb with one table and three rows. Run it in SSMS before Step 1.

CREATE DATABASE DemoDb;
GO

USE DemoDb;
GO

CREATE TABLE dbo.DemoCustomers (
    CustomerId INT IDENTITY(1,1) PRIMARY KEY,
    FullName NVARCHAR(100) NOT NULL,
    City NVARCHAR(100) NOT NULL
);
GO

INSERT INTO dbo.DemoCustomers (FullName, City) VALUES
(N'Amara', N'Toronto'),
(N'Jonas', N'Berlin'),
(N'Priya', N'Lagos');
GO

SELECT CustomerId, FullName, City FROM dbo.DemoCustomers;
GO
