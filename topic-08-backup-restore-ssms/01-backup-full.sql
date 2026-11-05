-- 01 - Full backup of DemoDb, exactly what SSMS's Script button generated
-- in Step 5 of the tutorial (SSMS 22.11.3, SQL Server 2025).
-- NOINIT = append to the file if it already exists (the SSMS default).
-- FORMAT would wipe the file and start a new media set instead.

BACKUP DATABASE [DemoDb]
TO DISK = N'C:\VSL-Backups\DemoDb-full-2026-11-05.bak'
WITH NOFORMAT, NOINIT,
     NAME = N'DemoDb-Full Database Backup',
     SKIP, NOREWIND, NOUNLOAD, STATS = 10;
GO

-- Optional sanity check: confirm the backup set in the file is complete
-- and readable. (This does not prove a restore works - only a restore does.)
RESTORE VERIFYONLY
FROM DISK = N'C:\VSL-Backups\DemoDb-full-2026-11-05.bak';
GO
