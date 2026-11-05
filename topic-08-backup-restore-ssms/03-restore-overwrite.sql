-- 03 - Restore DemoDb over itself from the full backup.
-- The T-SQL equivalent of the SSMS clicks in Steps 9-15:
--   Options page: Overwrite the existing database (WITH REPLACE)  -> REPLACE
--                 Recovery state: RESTORE WITH RECOVERY          -> RECOVERY
--                 Take tail-log backup before restore: UNCHECKED -> no tail-log step
--                 Close existing connections                      -> the
--                   SINGLE_USER block below (that checkbox flips the database
--                   to single-user, restores, and returns it to multi-user).
--
-- REPLACE bypasses SQL Server's safety checks on purpose. Only run this
-- against a database you genuinely mean to overwrite.

USE master;
GO

ALTER DATABASE [DemoDb] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

RESTORE DATABASE [DemoDb]
FROM DISK = N'C:\VSL-Backups\DemoDb-full-2026-11-05.bak'
WITH REPLACE, RECOVERY, STATS = 10;
GO

ALTER DATABASE [DemoDb] SET MULTI_USER;
GO
