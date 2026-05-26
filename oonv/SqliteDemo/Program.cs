using Microsoft.Data.Sqlite;

class Program
{
    static SqliteConnection db = new SqliteConnection("Data Source=contacts.db");

    static void InitSchema()
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = """
            CREATE TABLE IF NOT EXISTS Contacts (
                Id        INTEGER PRIMARY KEY AUTOINCREMENT,
                FirstName TEXT NOT NULL,
                LastName  TEXT NOT NULL,
                Phone     TEXT
            );
            """;
        cmd.ExecuteNonQuery();
    }

    static int Insert(string firstName, string lastName, string? phone)
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = """
            INSERT INTO Contacts (FirstName, LastName, Phone)
            VALUES ($fn, $ln, $ph);
            SELECT last_insert_rowid();
            """;
        cmd.Parameters.AddWithValue("$fn", firstName);
        cmd.Parameters.AddWithValue("$ln", lastName);
        cmd.Parameters.AddWithValue("$ph", phone ?? (object)DBNull.Value);
        return Convert.ToInt32(cmd.ExecuteScalar());
    }

    static void SelectOne(int id)
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "SELECT * FROM Contacts WHERE Id=$id;";
        cmd.Parameters.AddWithValue("$id", id);

        using var reader = cmd.ExecuteReader();
        if (reader.Read())
            Console.WriteLine($"  Nalezen: {FormatRow(reader)}");
        else
            Console.WriteLine("  Nenalezen.");
        Console.WriteLine();
    }

    static void Update(int id, string newPhone)
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "UPDATE Contacts SET Phone=$ph WHERE Id=$id;";
        cmd.Parameters.AddWithValue("$ph", newPhone);
        cmd.Parameters.AddWithValue("$id", id);
        int changed = cmd.ExecuteNonQuery();
        Console.WriteLine($"  Změněno řádků: {changed}");
    }

    static void Delete(int id)
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "DELETE FROM Contacts WHERE Id=$id;";
        cmd.Parameters.AddWithValue("$id", id);
        cmd.ExecuteNonQuery();
    }

    static void PrintAll()
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "SELECT * FROM Contacts ORDER BY Id;";

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            Console.WriteLine($"  {FormatRow(reader)}");
        Console.WriteLine();
    }

    static void Search(string query)
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "SELECT * FROM Contacts WHERE LastName LIKE $q;";
        cmd.Parameters.AddWithValue("$q", $"%{query}%");

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            Console.WriteLine($"  {FormatRow(reader)}");
        Console.WriteLine();
    }

    static long Count()
    {
        var cmd = db.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM Contacts;";
        return (long)cmd.ExecuteScalar()!;
    }

    static string FormatRow(SqliteDataReader r)
    {
        var phone = r.IsDBNull(3) ? "(bez telefonu)" : r.GetString(3);
        return $"Id={r.GetInt32(0)}  {r.GetString(1),-10} {r.GetString(2),-12}  {phone}";
    }

    static void Main(string[] args)
    {
        db.Open();
        InitSchema();

        Console.WriteLine("=== SQLite CRUD demo ===\n");

        // INSERT
        Console.WriteLine("--- INSERT ---");
        int id1 = Insert("Jan",  "Novák",     "123 456 789");
        int id2 = Insert("Eva",  "Svobodová", "987 654 321");
        int id3 = Insert("Petr", "Dvořák",    null);
        Console.WriteLine($"Vloženo Id={id1}, Id={id2}, Id={id3}\n");

        // SELECT ALL
        Console.WriteLine("--- SELECT ALL ---");
        PrintAll();

        // SELECT ONE
        Console.WriteLine("--- SELECT ONE (Id=2) ---");
        SelectOne(2);

        // UPDATE
        Console.WriteLine("--- UPDATE (Id=1, nový telefon) ---");
        Update(id1, "111 222 333");
        PrintAll();

        // DELETE
        Console.WriteLine("--- DELETE (Id=3) ---");
        Delete(id3);
        PrintAll();

        // SEARCH
        Console.WriteLine("--- SEARCH (příjmení obsahuje 'ov') ---");
        Search("ov");

        // COUNT
        Console.WriteLine("--- COUNT ---");
        Console.WriteLine($"  Celkem kontaktů: {Count()}\n");

        db.Close();
        Console.WriteLine("Hotovo. Soubor contacts.db je na disku.");
    }
}