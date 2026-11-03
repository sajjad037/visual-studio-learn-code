using Microsoft.Data.SqlClient;

// SQLCONN selects the server. The fallback is the LocalDB automatic instance
// that Visual Studio installs with the Data storage and processing workload.
const string defaultConnectionString =
    "Server=(localdb)\\MSSQLLocalDB;Database=DemoDb;" +
    "Integrated Security=true;Encrypt=true;TrustServerCertificate=true;";

string connectionString =
    Environment.GetEnvironmentVariable("SQLCONN") ?? defaultConnectionString;

var builder = new SqlConnectionStringBuilder(connectionString);
if (string.IsNullOrWhiteSpace(builder.InitialCatalog))
{
    builder.InitialCatalog = "DemoDb";
    connectionString = builder.ConnectionString;
}

string targetDatabase = builder.InitialCatalog;
string quotedDatabase = targetDatabase.Replace("]", "]]", StringComparison.Ordinal);
string databaseLiteral = targetDatabase.Replace("'", "''", StringComparison.Ordinal);

// Create the target database first, if it does not exist yet. LocalDB and a
// Developer-edition instance both accept this through the master database.
// (In the practice exercise you create PracticeDb yourself in Object
// Explorer, so this step simply finds it already there.)
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

// The table is the post's Method 2 table — dbo.DemoCustomers — and the seed
// is the same three rows the post, setup.sql and the videos all show. The
// MERGE keys on Name (Id is an IDENTITY column), so re-running updates the
// same three rows instead of duplicating them.
await using (var setup = new SqlCommand(
    """
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
    "SELECT Id, Name, City FROM dbo.DemoCustomers ORDER BY Id;", connection))
await using (var reader = await rows.ExecuteReaderAsync())
{
    while (await reader.ReadAsync())
    {
        Console.WriteLine($"{reader.GetInt32(0)} | {reader.GetString(1)} | {reader.GetString(2)}");
    }
}

Console.WriteLine("Success: SQL Server connection check passed.");
