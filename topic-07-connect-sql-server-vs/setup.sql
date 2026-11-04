CREATE TABLE dbo.DemoCustomers (
    CustomerId INT IDENTITY(1,1) PRIMARY KEY,
    FullName NVARCHAR(100) NOT NULL,
    City NVARCHAR(100) NOT NULL
);
INSERT INTO dbo.DemoCustomers (FullName, City) VALUES
(N'Amara', N'Toronto'),
(N'Jonas', N'Berlin'),
(N'Priya', N'Lagos');
SELECT CustomerId, FullName, City FROM dbo.DemoCustomers;
