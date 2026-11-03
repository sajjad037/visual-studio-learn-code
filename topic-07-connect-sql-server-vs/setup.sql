CREATE TABLE dbo.DemoCustomers (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    City NVARCHAR(100) NOT NULL
);
INSERT INTO dbo.DemoCustomers (Name, City) VALUES
    (N'Amara', N'Toronto'),
    (N'Jonas', N'Berlin'),
    (N'Priya', N'Lagos');
SELECT * FROM dbo.DemoCustomers;
