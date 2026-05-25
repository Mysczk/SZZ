namespace oonv.Patterns;

// ── Memento – snapshot stavu ───────────────────────────────────────────────
// record = immutable datová třída, ideální pro snapshot
public record EditorMemento(string Content);

// ── Originator – vytváří a obnovuje snapshoty ──────────────────────────────
public class TextEditor
{
    public string Content { get; set; } = "";

    public EditorMemento Save()            => new(Content);
    public void Restore(EditorMemento m)   => Content = m.Content;

    public override string ToString() => $"\"{Content}\"";
}

// ── Caretaker – ukládá historii ────────────────────────────────────────────
public class EditorHistory
{
    private readonly Stack<EditorMemento> _snapshots = new();

    public void Backup(TextEditor e)
    {
        _snapshots.Push(e.Save());
        Console.WriteLine($"  [Backup] Uložen stav: {e}");
    }

    public void Undo(TextEditor e)
    {
        if (_snapshots.Count == 0) { Console.WriteLine("  Nic k vrácení."); return; }
        e.Restore(_snapshots.Pop());
        Console.WriteLine($"  [Undo]   Obnoven stav: {e}");
    }
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class MementoDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Memento ===\n");

        var editor  = new TextEditor();
        var history = new EditorHistory();

        editor.Content = "Ahoj";
        history.Backup(editor);

        editor.Content = "Ahoj světe";
        history.Backup(editor);

        editor.Content = "Toto smažeme...";
        Console.WriteLine($"\n  Aktuální: {editor}");

        Console.WriteLine("\nUndo:");
        history.Undo(editor);
        history.Undo(editor);
        history.Undo(editor);    // nic k vrácení
    }
}
