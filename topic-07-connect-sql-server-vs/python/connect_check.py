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
    "DATABASE=SqlConnectDemo;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes"
)

SETUP_SQL = """
IF OBJECT_ID(N'dbo.DemoRows', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DemoRows
    (
        Id int NOT NULL PRIMARY KEY,
        Tool nvarchar(60) NOT NULL,
        Category nvarchar(60) NOT NULL
    );
END;

MERGE dbo.DemoRows AS target
USING (VALUES
    (1, N'Visual Studio', N'Development environment'),
    (2, N'SQL Server', N'Database engine'),
    (3, N'SQL Server Management Studio', N'Administration tool')
) AS source (Id, Tool, Category)
ON target.Id = source.Id
WHEN MATCHED THEN
    UPDATE SET Tool = source.Tool, Category = source.Category
WHEN NOT MATCHED THEN
    INSERT (Id, Tool, Category)
    VALUES (source.Id, source.Tool, source.Category);
"""


def database_name(connection_string: str) -> str:
    match = re.search(r"(?i)(?:DATABASE|Initial Catalog)\s*=\s*([^;]+)", connection_string)
    return match.group(1).strip() if match else "SqlConnectDemo"


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
            "SELECT Id, Tool, Category FROM dbo.DemoRows ORDER BY Id;"
        ):
            print(f"{row.Id} | {row.Tool} | {row.Category}")

    print("Success: SQL Server connection check passed.")


if __name__ == "__main__":
    main()
