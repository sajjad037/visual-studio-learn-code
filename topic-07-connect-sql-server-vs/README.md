# Connect SQL Server to Visual Studio — connection check

Companion code for Visual Studio Learn Topic #7, **“Connect SQL Server to
Visual Studio.”** It proves the same connection two ways:

- a C# console app using **Microsoft.Data.SqlClient 6.1.7**;
- a Python variant using **pyodbc 5.3.0** and Microsoft ODBC Driver 18.

Both programs connect to LocalDB by default, create the `DemoDb`
database and the three-row `DemoCustomers` table when needed, print
`SELECT @@VERSION`, and then print the rows — the same table and the
same three rows (Amara in Toronto, Jonas in Berlin, Priya in Lagos)
that Method 2 of the post creates and the videos show. Change one
environment variable to run either program against a local SQL Server
Developer-edition instance instead.

The database work is deliberately idempotent: running a program more than
once updates the same three demo rows instead of duplicating them.

## Version pins

| Item | Version used here |
|---|---|
| Visual Studio | 2022, version 17.14.44 (the same steps also apply to Visual Studio 2026) |
| SQL Server | 2025 (17.x), LocalDB or a Developer edition |
| .NET | 8.0 (`net8.0`, so the project builds in Visual Studio 2022 and 2026) |
| Microsoft.Data.SqlClient | 6.1.7 (LTS) |
| Python package | pyodbc 5.3.0, pinned from PyPI on November 3, 2026 |
| ODBC | Microsoft ODBC Driver 18 for SQL Server |

## Prerequisites

### Visual Studio and LocalDB

1. Install Visual Studio 2022 Community, Professional, or Enterprise.
2. In Visual Studio Installer, select these workloads:
   - **Data storage and processing** — supplies SQL Server Data Tools and
     LocalDB;
   - **.NET desktop development** — supplies the desktop .NET tooling used
     with this console project.
3. Finish the installation and open a terminal.
4. Verify LocalDB:

   ```powershell
   sqllocaldb info
   sqllocaldb info MSSQLLocalDB
   ```

LocalDB is Windows-only and starts on demand. It is installed by the Visual
Studio workloads or SQL Server Express; installing the SqlClient NuGet
package does not install LocalDB.

### Optional: SQL Server 2025 Developer edition

LocalDB is enough for the default run. To use a full local instance:

1. Open Microsoft’s SQL Server downloads page:
   <https://www.microsoft.com/en-us/sql-server/sql-server-downloads>
2. Download **Enterprise Developer** for the complete Enterprise feature set,
   or **Standard Developer** when production uses Standard edition. Both are
   free for development and test use, not for production.
3. Run setup and choose **New SQL Server stand-alone installation**.
4. Keep the default instance or give the instance a name and write down the
   exact `HOSTNAME\INSTANCE` value.
5. For this sample, Windows Authentication is enough. Add your Windows
   account as a SQL Server administrator during setup.
6. Confirm in Windows Services that the SQL Server Database Engine for the
   instance is running.

Microsoft’s edition details are in “Editions and supported features of
SQL Server 2025”:
<https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2025?view=sql-server-ver17>

### Python variant

Install:

- a current Python 3 release;
- **Microsoft ODBC Driver 18 for SQL Server**.

The driver name in the connection string must match the installed driver
exactly: `ODBC Driver 18 for SQL Server`.

## Folder contents

| Path | Purpose |
|---|---|
| `SqlConnectCheck/SqlConnectCheck.csproj` | .NET 8 project with the pinned SqlClient package |
| `SqlConnectCheck/Program.cs` | C# connection check |
| `python/connect_check.py` | Python/pyodbc connection check |
| `python/requirements.txt` | Pinned Python dependency |
| `setup.sql` | The exact Method 2 script printed in the post — creates `dbo.DemoCustomers` and seeds the three demo rows |
| `.env.example` | LocalDB and Developer-instance connection-string examples |

No real credentials are included. The examples use Windows Authentication
and local servers only.

## Configure the target server

### C# — `SQLCONN`

With no variable set, `Program.cs` uses LocalDB:

```text
Server=(localdb)\MSSQLLocalDB;Database=DemoDb;Integrated Security=true;Encrypt=true;TrustServerCertificate=true;
```

To use a named Developer-edition instance in PowerShell, replace
`HOSTNAME\INSTANCE` with your installation’s exact names:

```powershell
$env:SQLCONN = "Server=HOSTNAME\INSTANCE;Database=DemoDb;Integrated Security=true;Encrypt=true;TrustServerCertificate=true;"
```

For a default instance, use just the host name as the server value.

### Python — `SQLCONN_ODBC`

With no variable set, `connect_check.py` uses LocalDB:

```text
DRIVER={ODBC Driver 18 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=DemoDb;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes
```

To switch the Python program to a named Developer-edition instance:

```powershell
$env:SQLCONN_ODBC = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=HOSTNAME\INSTANCE;DATABASE=DemoDb;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
```

## Optional: run `setup.sql` first

The programs create the database and table themselves, so this step is
optional. It is useful when following the Object Explorer part of the
tutorial — `setup.sql` is the post's Method 2 script, word for word:

1. In Visual Studio, open **View → SQL Server Object Explorer**.
2. Add the LocalDB or Developer-edition server.
3. Create the `DemoDb` database if it does not exist yet (right-click
   **Databases → Add New Database**), or let a run of either checker
   create it for you.
4. Right-click `DemoDb` and open a new query, then open and run
   `setup.sql`. It creates `dbo.DemoCustomers` in the database the
   query window targets and seeds the three rows.
5. Confirm that the result grid contains Amara, Jonas and Priya.

## Run the C# program

### Command line

From this folder:

```powershell
cd .\SqlConnectCheck
dotnet run
```

### Visual Studio

1. Open `SqlConnectCheck/SqlConnectCheck.csproj` in Visual Studio.
2. Wait for NuGet restore to finish.
3. Press **F5**.

## Run the Python program

From this folder:

```powershell
cd .\python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\connect_check.py
```

## Expected output

Your server name and the full version text vary by installation. The shape
and final success line should match:

```text
Connected to server: <your server name>
Database: DemoDb
SQL Server version:
Microsoft SQL Server 2025 ... <the rest of your @@VERSION result>
Demo rows:
1 | Amara | Toronto
2 | Jonas | Berlin
3 | Priya | Lagos
Success: SQL Server connection check passed.
```

## The Encrypt and certificate error

Modern Microsoft.Data.SqlClient and current Visual Studio data tools enable
`Encrypt` by default. A local SQL Server normally presents a self-signed
certificate whose chain your machine does not trust, so the first connection
can fail with an error like:

```text
The certificate chain was issued by an authority that is not trusted.
```

For a **local development instance only**, the samples include:

- C#: `Encrypt=true;TrustServerCertificate=true;`
- Python: `Encrypt=yes;TrustServerCertificate=yes`

That pair tells the client to encrypt the connection while accepting the
local server’s certificate. Do not use `TrustServerCertificate` as the
production fix: a production server should present a certificate issued by
a trusted authority.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Certificate chain was issued by an authority that is not trusted | This is the Encrypt-by-default behaviour above. For local development, keep the `Encrypt` + `TrustServerCertificate` pair in the sample string. |
| Network-related or instance-specific error; Named Pipes Provider, error 40 | The instance name is wrong or the Database Engine service is stopped. Check the exact `\INSTANCE` spelling and Windows Services. |
| Login failed for user, error 18456 | The login does not exist, or a SQL login is being used against a Windows-Authentication-only server. This sample expects Windows Authentication. |
| `(localdb)` server was not found | LocalDB is missing. Modify Visual Studio and add the Data storage and processing workload or the SQL Server Express LocalDB component; then run `sqllocaldb info`. |
| A named instance on another machine is unreachable | TCP/IP may be disabled, SQL Server Browser may be stopped, or the firewall may block port 1433. This sample is designed for localhost use. |
| Python says a data source name was not found or the driver was not specified | Microsoft ODBC Driver 18 is not installed, or the `DRIVER={...}` value does not match its installed name exactly. |

## Ten-minute practice

1. Run either program against LocalDB and save the `@@VERSION` output.
2. In SQL Server Object Explorer, use **New Query** to run
   `CREATE DATABASE PracticeDb;`.
3. Change only the database name in the environment variable to
   `PracticeDb` and run the program again. PracticeDb starts empty, so
   the program creates the `DemoCustomers` table inside it, seeds the
   same three rows, prints them back, and ends with the same success
   line.
4. Mistype the instance name, run once more, and compare the failure with
   the troubleshooting table.
