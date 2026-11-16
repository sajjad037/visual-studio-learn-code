-- 08 - Verify: the same hero query, the same cold-cache fingerprints.
-- Measured in the tutorial after the fix: 15 logical reads (was
-- 12,388), 1 ms elapsed (was 15 ms), same 2,061 Toronto rows.
-- If your numbers are close to these, the four checks did their job.

USE DemoDb;
DBCC DROPCLEANBUFFERS;
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SELECT OrderId, CustomerId, OrderDate, Total
FROM dbo.Orders
WHERE City = N'Toronto';
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
