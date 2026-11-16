-- 03 - CHECK 1: is anything blocking my query?
-- Run this while the blocking scene from 02 is live (inside A's
-- 40-second hold). One row here names the blocked session, the session
-- blocking it, the wait type and how long it has already waited.
-- In the tutorial this returned: 57 blocked by 51, LCK_M_X, 4,998 ms.

SELECT session_id, blocking_session_id, wait_type, wait_time, status
FROM sys.dm_exec_requests
WHERE blocking_session_id <> 0;
