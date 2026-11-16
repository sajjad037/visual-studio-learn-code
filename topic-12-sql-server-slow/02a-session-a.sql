-- 02a - Blocking scene, SESSION A (Check 1 staging - run this FIRST).
-- Open TWO query windows against DemoDb. Run THIS file in window 1:
-- it updates OrderId 42 inside a transaction and holds the lock for
-- 40 seconds. While A is holding, run 02b-session-b.sql in window 2,
-- then 03-check-1-blocking.sql from a third window to see the block.
-- Measured in the tutorial: session 57 blocked by session 51,
-- wait type LCK_M_X, wait_time 4,998 ms at capture time.

USE DemoDb;
BEGIN TRANSACTION;
UPDATE dbo.Orders SET Total = Total + 1 WHERE OrderId = 42;
SELECT 'A holds the lock on OrderId 42' AS session_a_state;
WAITFOR DELAY '00:00:40';
ROLLBACK TRANSACTION;
SELECT 'A rolled back - lock released' AS session_a_state;
