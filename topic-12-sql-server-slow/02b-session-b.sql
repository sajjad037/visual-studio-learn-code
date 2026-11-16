-- 02b - Blocking scene, SESSION B (Check 1 staging - run this SECOND).
-- Run this in a SECOND query window while Session A (02a-session-a.sql)
-- is still inside its 40-second hold. B tries to update the same row
-- (OrderId 42) and blocks - it cannot finish until A rolls back.
-- That suspended, waiting state is exactly what Check 1 then reads.

USE DemoDb;
SELECT 'B tries to update the same row...' AS session_b_state;
UPDATE dbo.Orders SET Total = Total + 1 WHERE OrderId = 42;
SELECT 'B finished - the row is free again' AS session_b_state;
