# Topic #8 — Backup and Restore a SQL Server Database in SSMS

Companion code for the Visual Studio Learn tutorial
**"How Do I Backup and Restore a SQL Server Database in SSMS? (Step by Step, 2026)"**

- Post: [T8-BLOG-URL]
- Video: https://www.youtube.com/watch?v=R47KIDjby_g

## What this folder contains

The exact scripts from the post, in run order. Everything runs in
SQL Server Management Studio (SSMS) against a local SQL Server 2025
instance — the same DemoDb database Topic #7 created.

| File | What it does |
|---|---|
| `setup.sql` | Creates DemoDb + dbo.DemoCustomers with the 3 demo rows (Amara/Toronto, Jonas/Berlin, Priya/Lagos) |
| `01-backup-full.sql` | The full backup — the exact statement SSMS's Script button generated in Step 5, plus an optional `RESTORE VERIFYONLY` check |
| `02-break-it.sql` | The Step 8 accident: one wrong UPDATE (Jonas → Munich) and one DELETE (Priya) |
| `03-restore-overwrite.sql` | Restores DemoDb over itself (WITH REPLACE, RECOVERY) — the T-SQL form of Steps 9–15, including the single-user block behind "Close existing connections" |
| `04-restore-as-copy.sql` | Restores the same backup as **DemoDbCopy** with WITH MOVE — the T-SQL form of Steps 16–18 |
| `05-verify.sql` | The restore-proof SELECTs: 3 rows again, Jonas back in Berlin |

## What you'll need (the post's environment section)

- A Windows PC where you are an administrator, ~10 GB of free disk, internet for the downloads
- **SQL Server 2025 — Enterprise Developer edition** (free; development and testing only, not production). Default instance is fine.
- **SSMS 22** (built and verified on 22.11.3) — a separate free download from Microsoft
- A folder for backups: the scripts use `C:\VSL-Backups` (create it first)

## Run order

1. `setup.sql` — build the demo database
2. `01-backup-full.sql` — take the full backup (or click through Steps 1–7 in SSMS)
3. `02-break-it.sql` — break the data on purpose
4. `03-restore-overwrite.sql` — restore over the damage (or click through Steps 9–15)
5. `04-restore-as-copy.sql` — restore again, as a copy (or Steps 16–18)
6. `05-verify.sql` — prove it: three rows, Jonas back in Berlin

## Verify it worked

SSMS connects to your instance, DemoDb appears under Databases, and
`setup.sql`'s final SELECT returns the three rows. At the end, Object
Explorer shows **both** DemoDb and DemoDbCopy.

Built and verified on SQL Server 2025 Enterprise Developer (build
17.0.1000.7) with SSMS 22.11.3, November 5, 2026.
