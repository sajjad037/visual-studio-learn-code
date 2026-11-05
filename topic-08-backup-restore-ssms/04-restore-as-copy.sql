-- 04 - Restore the same backup AS A COPY, under a new name (Steps 16-18).
-- The original database is never touched: the backup lands in DemoDbCopy.
--
-- WITH MOVE is the T-SQL form of the Files page "Restore As" edits.
-- The logical file names ('DemoDb' and 'DemoDb_log') come from the backup
-- itself - confirm yours with RESTORE FILELISTONLY if your database differs.
-- The target folder is this machine's instance data folder; change it to
-- any folder the SQL Server service account can write to.
--
-- NOTE: no REPLACE here - DemoDbCopy does not exist yet, so there is
-- nothing to overwrite, and SSMS does not ask for it.
-- NOTE: leave the tail-log option OFF for a restore-as-copy. Microsoft's
-- documentation warns that a tail-log backup taken during a restore under
-- a NEW name can leave the ORIGINAL database in the Restoring state.

USE master;
GO

RESTORE DATABASE [DemoDbCopy]
FROM DISK = N'C:\VSL-Backups\DemoDb-full-2026-11-05.bak'
WITH
    MOVE 'DemoDb'     TO 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\DemoDbCopy.mdf',
    MOVE 'DemoDb_log' TO 'C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\DATA\DemoDbCopy_log.ldf',
    RECOVERY, STATS = 10;
GO
