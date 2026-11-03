-- Topic #7 sample setup for Visual Studio SQL Server Object Explorer or SSMS.
-- Safe to run more than once.

IF DB_ID(N'SqlConnectDemo') IS NULL
BEGIN
    CREATE DATABASE SqlConnectDemo;
END;
GO

USE SqlConnectDemo;
GO

IF OBJECT_ID(N'dbo.DemoRows', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DemoRows
    (
        Id int NOT NULL PRIMARY KEY,
        Tool nvarchar(60) NOT NULL,
        Category nvarchar(60) NOT NULL
    );
END;

MERGE dbo.DemoRows AS target
USING (VALUES
    (1, N'Visual Studio', N'Development environment'),
    (2, N'SQL Server', N'Database engine'),
    (3, N'SQL Server Management Studio', N'Administration tool')
) AS source (Id, Tool, Category)
ON target.Id = source.Id
WHEN MATCHED THEN
    UPDATE SET Tool = source.Tool, Category = source.Category
WHEN NOT MATCHED THEN
    INSERT (Id, Tool, Category)
    VALUES (source.Id, source.Tool, source.Category);

SELECT @@VERSION AS SqlServerVersion, @@SERVERNAME AS ServerName;

SELECT Id, Tool, Category
FROM dbo.DemoRows
ORDER BY Id;
