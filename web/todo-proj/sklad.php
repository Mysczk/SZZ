<?php
// ── DB připojení ───────────────────────────────────────────────────────────
$pdo = new PDO(
    'pgsql:host=postgres;port=5432;dbname=todo',
    'app',
    'heslo',
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
     PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]
);

// ── Vytvoření tabulky pokud neexistuje ─────────────────────────────────────
$pdo->exec("
    CREATE TABLE IF NOT EXISTS products (
        id         SERIAL PRIMARY KEY,
        name       VARCHAR(100) NOT NULL,
        category   VARCHAR(50)  NOT NULL DEFAULT 'obecne',
        quantity   INTEGER      NOT NULL DEFAULT 0,
        min_qty    INTEGER      NOT NULL DEFAULT 5,
        price      NUMERIC(10,2),
        created_at TIMESTAMP DEFAULT NOW()
    )
");

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }

$page   = $_GET['page']   ?? 'list';
$action = $_POST['action'] ?? '';
$err    = '';

// ── Akce ───────────────────────────────────────────────────────────────────
if ($action === 'add') {
    $name = trim($_POST['name'] ?? '');
    if ($name) {
        $pdo->prepare("INSERT INTO products (name, category, quantity, min_qty, price)
                       VALUES (?,?,?,?,?)")
            ->execute([
                $name,
                $_POST['category'] ?? 'obecne',
                (int)($_POST['quantity'] ?? 0),
                (int)($_POST['min_qty']  ?? 5),
                $_POST['price'] !== '' ? (float)$_POST['price'] : null
            ]);
    }
    header('Location: ?page=list'); exit;
}

if ($action === 'edit') {
    $pdo->prepare("UPDATE products SET name=?, category=?, quantity=?, min_qty=?, price=? WHERE id=?")
        ->execute([
            trim($_POST['name'] ?? ''),
            $_POST['category'] ?? 'obecne',
            (int)($_POST['quantity'] ?? 0),
            (int)($_POST['min_qty']  ?? 5),
            $_POST['price'] !== '' ? (float)$_POST['price'] : null,
            (int)$_POST['id']
        ]);
    header('Location: ?page=list'); exit;
}

if ($page === 'delete') {
    $pdo->prepare("DELETE FROM products WHERE id=?")->execute([(int)$_GET['id']]);
    header('Location: ?page=list'); exit;
}

// ── Data pro zobrazení ─────────────────────────────────────────────────────
$cat      = $_GET['category'] ?? '';
$search   = trim($_GET['search'] ?? '');
$editItem = null;

if ($cat && $search) {
    $stmt = $pdo->prepare("SELECT * FROM products WHERE category=? AND name ILIKE ? ORDER BY name");
    $stmt->execute([$cat, "%$search%"]);
} elseif ($cat) {
    $stmt = $pdo->prepare("SELECT * FROM products WHERE category=? ORDER BY name");
    $stmt->execute([$cat]);
} elseif ($search) {
    $stmt = $pdo->prepare("SELECT * FROM products WHERE name ILIKE ? ORDER BY name");
    $stmt->execute(["%$search%"]);
} else {
    $stmt = $pdo->query("SELECT * FROM products ORDER BY name");
}
$products = $stmt->fetchAll();

$lowStock = $pdo->query("SELECT * FROM products WHERE quantity <= min_qty ORDER BY quantity ASC")->fetchAll();

if ($page === 'edit' && isset($_GET['id'])) {
    $stmt = $pdo->prepare("SELECT * FROM products WHERE id=?");
    $stmt->execute([(int)$_GET['id']]);
    $editItem = $stmt->fetch();
}
?>
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Sklad</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
</head>
<body class="container py-4" style="max-width:900px">

<h2 class="mb-3">Skladový systém</h2>

<?php if (!empty($lowStock)): ?>
<div class="alert alert-warning">
    <strong>⚠ Nízké zásoby:</strong>
    <?= implode(', ', array_map(fn($p) => h($p['name']).' ('.$p['quantity'].'ks)', $lowStock)) ?>
</div>
<?php endif; ?>

<!-- Formulář přidat / upravit -->
<div class="card mb-4"><div class="card-body">
<h5><?= $editItem ? 'Upravit produkt' : 'Přidat produkt' ?></h5>
<form method="post">
    <input type="hidden" name="action" value="<?= $editItem ? 'edit' : 'add' ?>">
    <?php if ($editItem): ?><input type="hidden" name="id" value="<?= $editItem['id'] ?>"><?php endif; ?>
    <div class="row g-2">
        <div class="col-md-3">
            <input type="text" name="name" class="form-control" placeholder="Název *"
                   value="<?= $editItem ? h($editItem['name']) : '' ?>" required autofocus>
        </div>
        <div class="col-md-2">
            <select name="category" class="form-select">
                <?php foreach (['obecne'=>'Obecné','elektro'=>'Elektro','nastroje'=>'Nástroje','material'=>'Materiál'] as $v=>$l): ?>
                <option value="<?= $v ?>" <?= ($editItem && $editItem['category']===$v)?'selected':'' ?>><?= $l ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <input type="number" name="quantity" class="form-control" placeholder="Množství"
                   value="<?= $editItem ? $editItem['quantity'] : '0' ?>" min="0">
        </div>
        <div class="col-md-2">
            <input type="number" name="min_qty" class="form-control" placeholder="Min. množství"
                   value="<?= $editItem ? $editItem['min_qty'] : '5' ?>" min="0">
        </div>
        <div class="col-md-2">
            <input type="number" name="price" class="form-control" placeholder="Cena (Kč)"
                   value="<?= $editItem ? $editItem['price'] : '' ?>" step="0.01" min="0">
        </div>
        <div class="col-md-1">
            <button class="btn btn-<?= $editItem ? 'warning' : 'success' ?> w-100"><?= $editItem ? '✎' : '+' ?></button>
        </div>
    </div>
</form>
</div></div>

<!-- Filtr + hledání -->
<form method="get" class="row g-2 mb-3">
    <div class="col-auto">
        <input type="text" name="search" class="form-control form-control-sm"
               placeholder="Hledat..." value="<?= h($search) ?>">
    </div>
    <div class="col-auto">
        <select name="category" class="form-select form-select-sm">
            <option value="">Všechny kategorie</option>
            <?php foreach (['obecne','elektro','nastroje','material'] as $v): ?>
            <option value="<?= $v ?>" <?= $cat===$v?'selected':'' ?>><?= ucfirst($v) ?></option>
            <?php endforeach; ?>
        </select>
    </div>
    <div class="col-auto">
        <button class="btn btn-sm btn-primary">Hledat</button>
        <a href="?" class="btn btn-sm btn-secondary">Reset</a>
    </div>
</form>

<!-- Tabulka -->
<?php if (empty($products)): ?>
    <div class="alert alert-info">Žádné produkty.</div>
<?php else: ?>
<table class="table table-striped table-sm">
<thead class="table-dark">
    <tr><th>Název</th><th>Kategorie</th><th>Množství</th><th>Min.</th><th>Cena</th><th></th></tr>
</thead>
<tbody>
<?php foreach ($products as $p): ?>
<tr class="<?= $p['quantity'] <= $p['min_qty'] ? 'table-danger' : '' ?>">
    <td><?= h($p['name']) ?></td>
    <td><?= h($p['category']) ?></td>
    <td><?= $p['quantity'] ?> ks</td>
    <td><?= $p['min_qty'] ?> ks</td>
    <td><?= $p['price'] !== null ? number_format($p['price'], 2).' Kč' : '–' ?></td>
    <td>
        <a href="?page=edit&id=<?= $p['id'] ?>" class="btn btn-sm btn-warning py-0">✎</a>
        <a href="?page=delete&id=<?= $p['id'] ?>" onclick="return confirm('Smazat?')"
           class="btn btn-sm btn-danger py-0">✕</a>
    </td>
</tr>
<?php endforeach; ?>
</tbody>
</table>
<small class="text-muted">Celkem: <?= count($products) ?> produktů</small>
<?php endif; ?>

</body>
</html>