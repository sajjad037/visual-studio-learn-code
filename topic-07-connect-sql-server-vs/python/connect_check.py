"""Connect to LocalDB or SQL Server Developer edition with pyodbc.

Set SQLCONN_ODBC to switch servers. With no variable set, this uses the
LocalDB automatic instance installed by Visual Studio.
"""

import os
import re

import pyodbc


DEFAULT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=DemoDb;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes"
)

# The table is the post's Method 2 table — dbo.DemoCustomers — seeded with
# the same three rows the post, setup.sql and the videos all show. The
# MERGE keys on Name (Id is an IDENTITY column), so re-running updates the
# same three rows instead of duplicating them.
SETUP_SQL = """
IF OBJECT_ID(N'dbo.DemoCustomers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DemoCustomers
    (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(100) NOT NULL,
        City NVARCHAR(100) NOT NULL
    );
END;

MERGE dbo.DemoCustomers AS target
USING (VALUES
    (N'Amara', N'Toronto'),
    (N'Jonas', N'Berlin'),
    (N'Priya', N'Lagos')
) AS source (Name, City)
ON target.Name = source.Name
WHEN MATCHED THEN
    UPDATE SET City = source.City
WHEN NOT MATCHED THEN
    INSERT (Name, City)
    VALUES (source.Name, source.City);
"""


def database_name(connection_string: str) -> str:
    match = re.search(r"(?i)(?:DATABASE|Initial Catalog)\s*=\s*([^;]+)", connection_string)
    return match.group(1).strip() if match else "DemoDb"


def with_database(connection_string: str, database: str) -> str:
    if re.search(r"(?i)(?:DATABASE|Initial Catalog)\s*=", connection_string):
        return re.sub(
            r"(?i)((?:DATABASE|Initial Catalog)\s*=\s*)[^;]+",
            rf"\g<1>{database}",
            connection_string,
            count=1,
        )
    return f"{connection_string};DATABASE={database}"


def main() -> None:
    connection_string = os.environ.get("SQLCONN_ODBC", DEFAULT_CONNECTION_STRING)
    target_database = database_name(connection_string)

    if target_database.lower() != "master":
        master_connection_string = with_database(connection_string, "master")
        with pyodbc.connect(master_connection_string, autocommit=True) as master:
            quoted = target_database.replace("]", "]]")
            literal = target_database.replace("'", "''")
            master.execute(
                f"IF DB_ID(N'{literal}') IS NULL CREATE DATABASE [{quoted}];"
            )

    with pyodbc.connect(connection_string, autocommit=True) as connection:
        cursor = connection.cursor()
        cursor.execute(SETUP_SQL)

        version, server_name = cursor.execute(
            "SELECT @@VERSION, @@SERVERNAME;"
        ).fetchone()

        print(f"Connected to server: {server_name}")
        print(f"Database: {target_database}")
        print("SQL Server version:")
        print(version)
        print("Demo rows:")

        for row in cursor.execute(
            "SELECT Id, Name, City FROM dbo.DemoCustomers ORDER BY Id;"
        ):
            print(f"{row.Id} | {row.Name} | {row.City}")

    print("Success: SQL Server connection check passed.")


if __name__ == "__main__":
    main()
