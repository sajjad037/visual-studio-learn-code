using Microsoft.Data.SqlClient;

// SQLCONN selects the server. The fallback is the LocalDB automatic instance
// that Visual Studio installs with the Data storage and processing workload.
const string defaultConnectionString =
    "Server=(localdb)\\MSSQLLocalDB;Database=SqlConnectDemo;" +
    "Integrated Security=true;Encrypt=true;TrustServerCertificate=true;";

string connectionString =
    Environment.GetEnvironmentVariable("SQLCONN") ?? defaultConnectionString;

var builder = new SqlConnectionStringBuilder(connectionString);
if (string.IsNullOrWhiteSpace(builder.InitialCatalog))
{
    builder.InitialCatalog = "SqlConnectDemo";
    connectionString = builder.ConnectionString;
}

string targetDatabase = builder.InitialCatalog;
string quotedDatabase = targetDatabase.Replace("]", "]]", StringComparison.Ordinal);
string databaseLiteral = targetDatabase.Replace("'", "''", StringComparison.Ordinal);

// Create the demo database first. LocalDB and a Developer-edition instance
// both accept this through the master database.
if (!targetDatabase.Equals("master", StringComparison.OrdinalIgnoreCase))
{
    var masterBuilder = new SqlConnectionStringBuilder(connectionString)
    {
        InitialCatalog = "master"
    };

    await using var masterConnection = new SqlConnection(masterBuilder.ConnectionString);
    await masterConnection.OpenAsync();

    await using var createDatabase = new SqlCommand(
        $"IF DB_ID(N'{databaseLiteral}') IS NULL CREATE DATABASE [{quotedDatabase}];",
        masterConnection);
    await createDatabase.ExecuteNonQueryAsync();
}

await using var connection = new SqlConnection(connectionString);
await connection.OpenAsync();

await using (var setup = new SqlCommand(
    """
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
    """,
    connection))
{
    await setup.ExecuteNonQueryAsync();
}

string serverName;
string version;

await using (var info = new SqlCommand(
    "SELECT @@VERSION AS Version, @@SERVERNAME AS ServerName;", connection))
await using (var reader = await info.ExecuteReaderAsync())
{
    await reader.ReadAsync();
    version = reader.GetString(0);
    serverName = reader.GetString(1);
}

Console.WriteLine($"Connected to server: {serverName}");
Console.WriteLine($"Database: {targetDatabase}");
Console.WriteLine("SQL Server version:");
Console.WriteLine(version);
Console.WriteLine("Demo rows:");

await using (var rows = new SqlCommand(
    "SELECT Id, Tool, Category FROM dbo.DemoRows ORDER BY Id;", connection))
await using (var reader = await rows.ExecuteReaderAsync())
{
    while (await reader.ReadAsync())
    {
        Console.WriteLine($"{reader.GetInt32(0)} | {reader.GetString(1)} | {reader.GetString(2)}");
    }
}

Console.WriteLine("Success: SQL Server connection check passed.");
