-- 07 - THE FIX: build exactly the index Check 4 recommended.
-- City is the key (equality lookups); CustomerId, OrderDate and Total
-- ride along as INCLUDE columns so the hero query is answered from the
-- index alone and never goes back to the table.
-- STATISTICS TIME shows the build cost. Measured in the tutorial:
-- 524 ms elapsed to create on the 200,000-row table.

USE DemoDb;
SET STATISTICS TIME ON;
CREATE NONCLUSTERED INDEX IX_Orders_City
ON dbo.Orders (City)
INCLUDE (CustomerId, OrderDate, Total);
SET STATISTICS TIME OFF;
