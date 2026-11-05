-- 02 - The accident from Step 8 of the tutorial.
-- One UPDATE writes a wrong value; one DELETE removes a row entirely.
-- After this runs, the verify SELECT returns exactly 2 rows,
-- and Jonas is in Munich instead of Berlin.

USE DemoDb;
GO

UPDATE dbo.DemoCustomers SET City = N'Munich' WHERE FullName = N'Jonas';
DELETE FROM dbo.DemoCustomers WHERE FullName = N'Priya';
GO

SELECT CustomerId, FullName, City FROM dbo.DemoCustomers;
GO
