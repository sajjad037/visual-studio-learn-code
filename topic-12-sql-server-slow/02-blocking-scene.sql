-- 02 - Stage the blocking scene for Check 1.
-- Open TWO query windows (two sessions) against DemoDb.
-- Run SESSION A first: it updates OrderId 42 inside a transaction and
-- holds the lock for 40 seconds. While A is holding, run SESSION B in
-- the other window: B tries to update the same row and blocks.
-- Then run 03-check-1-blocking.sql from a third window to see the block.
-- Measured in the tutorial: session 57 blocked by session 51,
-- wait type LCK_M_X, wait_time 4,998 ms at capture time.

-- ============================ SESSION A ============================
USE DemoDb;
BEGIN TRANSACTION;
UPDATE dbo.Orders SET Total = Total + 1 WHERE OrderId = 42;
SELECT 'A holds the lock on OrderId 42' AS session_a_state;
WAITFOR DELAY '00:00:40';
ROLLBACK TRANSACTION;
SELECT 'A rolled back - lock released' AS session_a_state;

-- ============================ SESSION B ============================
USE DemoDb;
SELECT 'B tries to update the same row...' AS session_b_state;
UPDATE dbo.Orders SET Total = Total + 1 WHERE OrderId = 42;
SELECT 'B finished - the row is free again' AS session_b_state;
