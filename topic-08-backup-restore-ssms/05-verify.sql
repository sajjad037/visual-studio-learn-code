-- 05 - The restore-proof (Step 15 of the tutorial).
-- After the restore over itself, this must return the original 3 rows -
-- and check the VALUE, not just the count: Jonas must be back in Berlin.
-- If Priya's row is back but Jonas still says Munich, you restored the
-- wrong backup set (see "Errors you may hit" in the post).

USE DemoDb;
GO

SELECT CustomerId, FullName, City FROM dbo.DemoCustomers;
GO

-- The copy from Part D holds the same rows:
USE DemoDbCopy;
GO

SELECT CustomerId, FullName, City FROM dbo.DemoCustomers;
GO
