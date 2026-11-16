-- 06 - CHECK 4: which index does SQL Server say is missing?
-- The missing-index DMVs remember what the optimiser wished it had.
-- Read avg_user_impact as "how much cheaper these queries could have
-- been, in percent" and check the columns before believing any row.
-- Measured in the tutorial: one suggestion for [City] INCLUDE
-- (CustomerId, OrderDate, Total), avg_user_impact 98.19, 5 seeks.

USE DemoDb;
SELECT migs.avg_total_user_cost, migs.avg_user_impact, migs.user_seeks,
       mid.statement, mid.equality_columns, mid.inequality_columns, mid.included_columns
FROM sys.dm_db_missing_index_group_stats AS migs
JOIN sys.dm_db_missing_index_groups AS mig
  ON migs.group_handle = mig.index_group_handle
JOIN sys.dm_db_missing_index_details AS mid
  ON mig.index_handle = mid.index_handle
WHERE mid.database_id = DB_ID('DemoDb')
ORDER BY migs.avg_user_impact DESC;
