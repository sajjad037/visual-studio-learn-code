# Topic #12 — Why Is My SQL Server Slow?

Companion code for the Visual Studio Learn tutorial **"Why Is My SQL Server
Slow? A 4-Step Diagnosis with Blocking, Wait Stats, Execution Plans and
Missing Indexes (2026)"**.

## Watch + read

- Post: https://visualstudiolearn.blogspot.com/2026/11/why-is-my-sql-server-slow-4-step.html
- Video: https://www.youtube.com/watch?v=jSroBM7mijs
- Short: https://www.youtube.com/shorts/ILIsWi-XKqg
- Also on dev.to: https://dev.to/visualstudiolearn/why-is-my-sql-server-slow-a-4-step-diagnosis-with-blocking-wait-stats-execution-plans-and-45e5

The tutorial diagnoses one slow query with four checks, in order — and each
check answers exactly one question:

| Check | Question it answers | Script |
|---|---|---|
| 1 | Is anything **blocking** the query? | `03-check-1-blocking.sql` |
| 2 | What is the server **waiting on**? | `04-check-2-wait-stats.sql` |
| 3 | What does the **execution plan** say? | `05-check-3-execution-plan.sql` |
| 4 | Which **index is missing**? | `06-check-4-missing-index.sql` |

## Files

Run them in number order:

- `00-setup.sql` — builds the slow scene (Step 0): database `DemoDb` and a
  200,000-row `Orders` table with **no index on `City`** — the planted fault.
  2,061 of the rows are Toronto orders.
- `01-hero-query-before.sql` — the hero query ("orders from Toronto") with
  `SET STATISTICS IO/TIME` fingerprints, cold cache. **Before: 12,388 logical
  reads, 15 ms.**
- `02a-session-a.sql` + `02b-session-b.sql` — stage a real block for
  Check 1, one file per query window: Session A holds a lock on
  `OrderId 42` for 40 seconds while Session B tries to update the same
  row. Run A first, then B in a second window while A is still holding.
- `03-check-1-blocking.sql` — Check 1: `sys.dm_exec_requests` filtered to
  blocked sessions. Measured: **session 57 blocked by 51, `LCK_M_X`,
  4,998 ms**.
- `04-check-2-wait-stats.sql` — Check 2: `sys.dm_os_wait_stats` with the full
  idle-wait filter list (the post prints this query in shortened form; this is
  the full version that produced the tutorial's numbers). Measured:
  **`LCK_M_X` on top — 36,044 ms across 3 waits**; `PAGEIOLATCH_SH` only
  337 ms, so the server was waiting on locks, not disk.
- `05-check-3-execution-plan.sql` — Check 3: the hero query under
  `SET STATISTICS XML`, before and after the fix. Before: **Clustered Index
  Scan, cost 8.897**, and the plan itself suggests the missing index. After:
  **Index Seek, cost 0.0133**.
- `06-check-4-missing-index.sql` — Check 4: the missing-index DMVs. Measured:
  **`[City]` INCLUDE `(CustomerId, OrderDate, Total)`, avg_user_impact 98.19,
  5 seeks**.
- `07-the-fix-create-index.sql` — the fix: create exactly the recommended
  index. Build measured at **524 ms** on the 200,000-row table.
- `08-verify-after.sql` — the hero query again, same cold-cache fingerprints.
  **After: 15 logical reads, 1 ms** — the same 2,061 rows.

## What you'll need

- **SQL Server 2025** you can practise on. The tutorial was measured on
  SQL Server 2025 (RTM-CU11, build 17.0.5065.9) on Linux, driven with
  `sqlcmd`. The Developer edition is free.
- **SSMS 22 or sqlcmd** — every script runs unchanged in an SSMS query
  window on Windows; the post maps each step to SSMS. In SSMS you can read
  Check 3's plan graphically with **Include Actual Execution Plan (Ctrl+M)**
  instead of the XML.
- A throwaway database you may break (the scripts create `DemoDb`), and
  permission to see the server's diagnostic views (`VIEW SERVER STATE`;
  SQL Server 2022+ also offers narrower grants such as
  `VIEW SERVER PERFORMANCE STATE` for the server-level views — your own
  local instance's admin login has it either way).
- Re-running the demo from scratch? `00-setup.sql` matches the post
  exactly, so drop the old copy first: `DROP DATABASE IF EXISTS DemoDb;`

## Run order

1. `00-setup.sql` — build the slow scene
2. `01-hero-query-before.sql` — take the before fingerprints
3. `02a-session-a.sql` in one window, then `02b-session-b.sql` in a second window, while A is still holding its lock
4. `03-check-1-blocking.sql` — Check 1, while the block is live (third window)
5. `04-check-2-wait-stats.sql` — Check 2
6. `05-check-3-execution-plan.sql` — Check 3, the "before" half
7. `06-check-4-missing-index.sql` — Check 4
8. `07-the-fix-create-index.sql` — build the index
9. `05-check-3-execution-plan.sql` again — the "after" half (Index Seek)
10. `08-verify-after.sql` — prove it: 15 logical reads

## Things worth knowing before you try this on a real server

- **Wait stats are cumulative since the server started.** On a busy
  production server they rank the server's whole history, not your one slow
  query — snapshot them, wait, and diff if you need a window.
- **The missing-index DMVs are suggestions, not prescriptions.** They reset
  when the server restarts, they can recommend overlapping indexes, and
  `avg_user_impact` is an estimate. Check the columns against your real
  queries before creating anything.
- **`DBCC DROPCLEANBUFFERS` is for the demo only** — never run it on a
  production server to make a query look slower or faster; it evicts the
  whole buffer cache.
- Every number above was measured on the tutorial's demo instance while
  writing the post. Your hardware will differ; the *ratios* (12,388 pages
  down to 15) are the lesson.

Measured on SQL Server 2025 (17.0.5065.9, RTM-CU11) on Linux with sqlcmd,
November 2026. The scripts are plain T-SQL and run unchanged in an SSMS 22
query window on Windows.
