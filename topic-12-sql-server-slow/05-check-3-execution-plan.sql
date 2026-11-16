-- 05 - CHECK 3: what does the execution plan say?
-- STATISTICS XML returns the actual execution plan as XML alongside the
-- results. In SSMS you can instead tick "Include Actual Execution Plan"
-- (Ctrl+M) and read the graphical plan - same information.
-- BEFORE the fix (first statement): a Clustered Index Scan of the whole
-- table, estimated cost 8.897, and the plan itself carries a
-- MissingIndex suggestion for [City] INCLUDE (CustomerId, OrderDate,
-- Total) - the bridge into Check 4.
-- AFTER the fix (second statement, run it once 07 has created the
-- index): an Index Seek on IX_Orders_City, estimated cost 0.0133.

-- ==================== BEFORE: the plan that scans ====================
USE DemoDb;
SET STATISTICS XML ON;
SELECT OrderId, CustomerId, OrderDate, Total
FROM dbo.Orders
WHERE City = N'Toronto';
SET STATISTICS XML OFF;

-- ==================== AFTER: the plan that seeks =====================
-- (Run this half after 07-the-fix-create-index.sql.)
USE DemoDb;
SET STATISTICS XML ON;
SELECT OrderId, CustomerId, OrderDate, Total
FROM dbo.Orders
WHERE City = N'Toronto';
SET STATISTICS XML OFF;
