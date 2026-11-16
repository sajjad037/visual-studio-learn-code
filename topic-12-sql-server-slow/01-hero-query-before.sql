-- 01 - The hero query, measured BEFORE any fix (Step 1 of the tutorial).
-- Run it in its own session with a cold buffer cache (DROPCLEANBUFFERS)
-- so the fingerprints are honest. Measured in the tutorial on SQL Server
-- 2025 (17.0.5065.9) on Linux: 12,388 logical reads, 15 ms elapsed,
-- returning 2,061 Toronto rows.

USE DemoDb;
DBCC DROPCLEANBUFFERS;
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SELECT OrderId, CustomerId, OrderDate, Total
FROM dbo.Orders
WHERE City = N'Toronto';
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
