# IV. Vývoj webové aplikace – PHP + XML + MySQL

> Cheat-sheet. Dvě ukázkové úlohy: XML zápisník úkolů + skladový systém.
> Povinný jazyk: PHP. Volitelně: HTML5, CSS3, Bootstrap, JS.

---

## Obsah
1. [XML – základy a struktura](#1-xml--základy-a-struktura)
2. [XSD – validace XML](#2-xsd--validace-xml)
3. [PHP a XML – čtení a zápis](#3-php-a-xml--čtení-a-zápis)
4. [PHP základy – syntaxe, funkce, OOP](#4-php-základy--syntaxe-funkce-oop)
5. [Sessions, cookies, přihlášení](#5-sessions-cookies-přihlášení)
6. [PHP a MySQL (PDO)](#6-php-a-mysql-pdo)
7. [Bezpečnost – SQL injection, XSS, hesla](#7-bezpečnost--sql-injection-xss-hesla)
8. [REST API v PHP](#8-rest-api-v-php)
9. [Ukázková úloha IV.1 – XML zápisník](#9-ukázková-úloha-iv1--xml-zápisník)
10. [Ukázková úloha IV.2 – Skladový systém](#10-ukázková-úloha-iv2--skladový-systém)

---

## 1. XML – základy a struktura

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Kořenový element – každý XML soubor musí mít právě jeden -->
<library>
  <book id="1">
    <title>Stopařův průvodce po galaxii</title>
    <author>Douglas Adams</author>
    <genre>sci-fi</genre>
    <year>1979</year>
    <available>true</available>
  </book>
  <book id="2">
    <title>Pán much</title>
    <author>William Golding</author>
    <genre>drama</genre>
    <year>1954</year>
    <available>false</available>
  </book>
</library>
```

### Pravidla well-formed XML
```
✅ Jeden kořenový element
✅ Všechny tagy uzavřeny (<tag></tag> nebo <tag/>)
✅ Správné vnořování (<a><b></b></a>, NE <a><b></a></b>)
✅ Atributy v uvozovkách (id="1", ne id=1)
✅ Speciální znaky escapovány:
   &amp;   →  &
   &lt;    →  <
   &gt;    →  >
   &quot;  →  "
   &apos;  →  '
```

### HTML DOM vs XML DOM
```
HTML DOM:  document.getElementById(), querySelector() – pro HTML v prohlížeči
XML DOM:   načtení přes DOMParser nebo PHP DOMDocument – pro XML data

// JS: parsování XML v prohlížeči
const parser = new DOMParser();
const xmlDoc = parser.parseFromString(xmlString, "text/xml");
const books  = xmlDoc.getElementsByTagName("book");
console.log(books[0].getAttribute("id"));                    // "1"
console.log(books[0].querySelector("title").textContent);    // "Stopařův průvodce po galaxii"
```

---

## 2. XSD – validace XML

```xml
<!-- library.xsd – schéma pro validaci XML s knihami -->
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

  <xs:element name="library">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="book" type="BookType"
                    minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>

  <xs:complexType name="BookType">
    <xs:sequence>
      <xs:element name="title"     type="xs:string"/>
      <xs:element name="author"    type="xs:string"/>
      <xs:element name="genre"     type="GenreEnum"/>
      <xs:element name="year"      type="xs:gYear"/>
      <xs:element name="available" type="xs:boolean"/>
    </xs:sequence>
    <xs:attribute name="id" type="xs:positiveInteger" use="required"/>
  </xs:complexType>

  <!-- Enum pro žánr -->
  <xs:simpleType name="GenreEnum">
    <xs:restriction base="xs:string">
      <xs:enumeration value="sci-fi"/>
      <xs:enumeration value="drama"/>
      <xs:enumeration value="thriller"/>
      <xs:enumeration value="romance"/>
      <xs:enumeration value="non-fiction"/>
    </xs:restriction>
  </xs:simpleType>

</xs:schema>
```

### Validace XSD v PHP
```php
$dom = new DOMDocument();
$dom->load('library.xml');

if ($dom->schemaValidate('library.xsd')) {
    echo "XML je validní.";
} else {
    echo "XML není validní!";
}
```

---

## 3. PHP a XML – čtení a zápis

### SimpleXML – nejjednodušší přístup
```php
// Načtení XML souboru
$xml = simplexml_load_file('library.xml');

// Procházení elementů
foreach ($xml->book as $book) {
    echo $book->title . " – " . $book->author . "\n";
    echo "ID: " . $book['id'] . "\n";   // atribut
}

// Filtrování – XPath
$available = $xml->xpath("//book[available='true']");
foreach ($available as $book) {
    echo $book->title . "\n";
}

// Přidání nové knihy
$newBook = $xml->addChild('book');
$newBook->addAttribute('id', '3');
$newBook->addChild('title', 'Malý princ');
$newBook->addChild('author', 'Antoine de Saint-Exupéry');
$newBook->addChild('genre', 'drama');
$newBook->addChild('year', '1943');
$newBook->addChild('available', 'true');

// Uložení zpět do souboru
$xml->asXML('library.xml');
```

### DOMDocument – více kontroly
```php
$dom = new DOMDocument('1.0', 'UTF-8');
$dom->formatOutput = true;    // hezké odsazení
$dom->load('library.xml');

$root = $dom->documentElement;   // <library>

// Vytvoření nového elementu
$book = $dom->createElement('book');
$book->setAttribute('id', '4');

$title = $dom->createElement('title', htmlspecialchars('Duna'));
$book->appendChild($title);

$author = $dom->createElement('author', 'Frank Herbert');
$book->appendChild($author);

$available = $dom->createElement('available', 'true');
$book->appendChild($available);

$root->appendChild($book);
$dom->save('library.xml');

// Smazání elementu (XPath hledání + removeChild)
$xpath   = new DOMXPath($dom);
$bookDel = $xpath->query("//book[@id='2']")->item(0);
if ($bookDel) {
    $bookDel->parentNode->removeChild($bookDel);
    $dom->save('library.xml');
}
```

---

## 4. PHP základy – syntaxe, funkce, OOP

### Syntaxe
```php
<?php
// Proměnné – vždy $
$name   = "Jan";
$age    = 25;
$active = true;
$arr    = [1, 2, 3];
$assoc  = ["klic" => "hodnota", "jmeno" => "Jan"];

// Podmínky
if ($age >= 18) {
    echo "Dospělý";
} elseif ($age >= 15) {
    echo "Teenager";
} else {
    echo "Dítě";
}

// Smyčky
foreach ($assoc as $key => $value) {
    echo "$key: $value\n";
}

for ($i = 0; $i < 3; $i++) {
    echo $i;
}

// Funkce
function greet(string $name, string $greeting = "Ahoj"): string {
    return "$greeting, $name!";
}
echo greet("Jan");           // "Ahoj, Jan!"
echo greet("Eva", "Čau");   // "Čau, Eva!"

// Null coalescing
$value = $_GET['id'] ?? 'default';

// String funkce
strlen($str), strtolower($str), strtoupper($str)
trim($str), str_replace('a', 'b', $str)
explode(',', $str)   // string → array
implode(',', $arr)   // array → string
htmlspecialchars($str)  // escapování pro výstup do HTML!
```

### OOP v PHP
```php
class Task {
    // Konstruktor s promoted properties (PHP 8+)
    public function __construct(
        private int    $id,
        private string $title,
        private string $status = 'nezahajeno',
        private string $category = 'osobni'
    ) {}

    // Getter
    public function getId(): int      { return $this->id; }
    public function getTitle(): string { return $this->title; }
    public function getStatus(): string { return $this->status; }

    // Metoda
    public function complete(): void  { $this->status = 'dokonceno'; }

    // Statická metoda (bez instance)
    public static function fromXml(SimpleXMLElement $el): self {
        return new self(
            (int)$el['id'],
            (string)$el->title,
            (string)$el->status,
            (string)$el->category
        );
    }

    // Serializace do pole (pro JSON/výstup)
    public function toArray(): array {
        return [
            'id'       => $this->id,
            'title'    => $this->title,
            'status'   => $this->status,
            'category' => $this->category,
        ];
    }
}

// Rozhraní
interface Repository {
    public function findAll(): array;
    public function findById(int $id): ?Task;
    public function save(Task $task): void;
    public function delete(int $id): void;
}

// Dědičnost
class UrgentTask extends Task {
    public function __construct(int $id, string $title, private string $deadline) {
        parent::__construct($id, $title, 'zahajeno');
    }
    public function getDeadline(): string { return $this->deadline; }
}
```

---

## 5. Sessions, cookies, přihlášení

```php
// Sessions – data na serveru, identifikace přes cookie PHPSESSID
session_start();   // MUSÍ být před jakýmkoli výstupem!

// Uložení do session
$_SESSION['user_id']   = 42;
$_SESSION['username']  = 'jan.novak';
$_SESSION['role']      = 'admin';

// Čtení ze session
if (isset($_SESSION['user_id'])) {
    echo "Přihlášen: " . $_SESSION['username'];
}

// Odhlášení
session_destroy();
unset($_SESSION);

// Cookies – data v prohlížeči
setcookie('theme', 'dark', time() + 30*24*3600, '/');  // platnost 30 dní
echo $_COOKIE['theme'] ?? 'light';
```

### Přihlašovací systém (bezpečný)
```php
// register.php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';

    // Hashování hesla – NIKDY neukládej plaintext!
    $hash = password_hash($password, PASSWORD_BCRYPT);

    // Ulož do DB nebo XML...
    $pdo->prepare("INSERT INTO users (username, password_hash) VALUES (?,?)")
        ->execute([$username, $hash]);
}

// login.php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';

    $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
    $stmt->execute([$username]);
    $user = $stmt->fetch();

    // Ověření hesla
    if ($user && password_verify($password, $user['password_hash'])) {
        session_start();
        session_regenerate_id(true);   // prevence session fixation!
        $_SESSION['user_id']  = $user['id'];
        $_SESSION['username'] = $user['username'];
        header('Location: /dashboard.php');
        exit;
    } else {
        $error = "Nesprávné přihlašovací údaje.";
    }
}

// Ochrana stránky – na začátek každé chráněné stránky
function requireLogin(): void {
    session_start();
    if (!isset($_SESSION['user_id'])) {
        header('Location: /login.php');
        exit;
    }
}
```

---

## 6. PHP a MySQL (PDO)

### Připojení
```php
// db.php – připojení přes PDO (bezpečnější než mysqli)
function getDb(): PDO {
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO(
            'mysql:host=localhost;dbname=sklad;charset=utf8mb4',
            'root',
            'heslo',
            [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]
        );
    }
    return $pdo;
}
```

### CRUD operace
```php
$pdo = getDb();

// CREATE
$stmt = $pdo->prepare(
    "INSERT INTO products (name, quantity, price, category) VALUES (?,?,?,?)"
);
$stmt->execute(['Šroub M8', 500, 0.50, 'spojovaci_material']);
$newId = $pdo->lastInsertId();

// READ – všechny
$products = $pdo->query("SELECT * FROM products ORDER BY name")->fetchAll();

// READ – filtrované (VŽDY prepared statements!)
$stmt = $pdo->prepare("SELECT * FROM products WHERE category = ? AND quantity > ?");
$stmt->execute([$category, 0]);
$products = $stmt->fetchAll();

// READ – jeden záznam
$stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
$stmt->execute([$id]);
$product = $stmt->fetch();   // null pokud nenalezeno

// UPDATE
$stmt = $pdo->prepare("UPDATE products SET quantity = ?, price = ? WHERE id = ?");
$stmt->execute([600, 0.55, $id]);
echo $stmt->rowCount();   // počet ovlivněných řádků

// DELETE
$pdo->prepare("DELETE FROM products WHERE id = ?")->execute([$id]);
```

### Schéma DB pro skladový systém
```sql
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','skladnik') DEFAULT 'skladnik',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    category      VARCHAR(50),
    quantity      INT NOT NULL DEFAULT 0,
    min_quantity  INT NOT NULL DEFAULT 10,   -- práh pro upozornění
    price         DECIMAL(10,2),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    product_id    INT NOT NULL,
    quantity      INT NOT NULL,
    status        ENUM('pending','completed','cancelled') DEFAULT 'pending',
    created_by    INT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

---

## 7. Bezpečnost – SQL injection, XSS, hesla

```php
// ❌ SQL injection – NIKDY takto!
$id = $_GET['id'];
$pdo->query("SELECT * FROM products WHERE id = $id");
// Útočník zadá: ?id=1 OR 1=1 → vrátí vše

// ✅ Prepared statements – vždy
$stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
$stmt->execute([$_GET['id']]);

// ❌ XSS – výstup bez escapování
echo "<p>" . $_GET['search'] . "</p>";
// Útočník zadá: <script>document.cookie</script>

// ✅ Escapování výstupu – vždy
echo "<p>" . htmlspecialchars($_GET['search'] ?? '', ENT_QUOTES, 'UTF-8') . "</p>";

// ❌ Ukládání plaintext hesla
$pdo->execute([$username, $password]);  // NIKDY!

// ✅ Hashování
$hash = password_hash($password, PASSWORD_BCRYPT);
// Ověření:
password_verify($inputPassword, $hash);  // true/false

// CSRF ochrana – token ve formuláři
session_start();
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// Ve formuláři:
// <input type="hidden" name="csrf" value="<?= $_SESSION['csrf_token'] ?>">

// Při zpracování:
if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf'] ?? '')) {
    die('CSRF útok detekován!');
}
```

---

## 8. REST API v PHP

```php
// api/products.php – jednoduchý REST endpoint
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');   // CORS

$pdo    = getDb();
$method = $_SERVER['REQUEST_METHOD'];
$id     = $_GET['id'] ?? null;

switch ($method) {
    case 'GET':
        if ($id) {
            $stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
            $stmt->execute([$id]);
            $product = $stmt->fetch();
            echo json_encode($product ?: ['error' => 'Nenalezeno'], JSON_UNESCAPED_UNICODE);
        } else {
            $products = $pdo->query("SELECT * FROM products")->fetchAll();
            echo json_encode($products, JSON_UNESCAPED_UNICODE);
        }
        break;

    case 'POST':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare(
            "INSERT INTO products (name, quantity, price) VALUES (?,?,?)"
        );
        $stmt->execute([$data['name'], $data['quantity'], $data['price']]);
        http_response_code(201);
        echo json_encode(['id' => $pdo->lastInsertId()]);
        break;

    case 'PUT':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare("UPDATE products SET quantity=?, price=? WHERE id=?");
        $stmt->execute([$data['quantity'], $data['price'], $id]);
        echo json_encode(['updated' => $stmt->rowCount()]);
        break;

    case 'DELETE':
        $pdo->prepare("DELETE FROM products WHERE id=?")->execute([$id]);
        http_response_code(204);
        break;

    default:
        http_response_code(405);
        echo json_encode(['error' => 'Metoda nepodporována']);
}
```

### Volání API z JS (fetch)
```js
// GET
const products = await fetch('/api/products.php').then(r => r.json());

// POST
await fetch('/api/products.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Šroub', quantity: 100, price: 0.5 })
});

// DELETE
await fetch(`/api/products.php?id=${id}`, { method: 'DELETE' });
```

---

## 9. Ukázková úloha IV.1 – XML zápisník

### Struktura projektu
```
todo-xml/
├── data/
│   ├── tasks.xml          ← data
│   ├── users.xml          ← uživatelé
│   └── tasks.xsd          ← validační schéma
├── index.php              ← seznam úkolů (vyžaduje přihlášení)
├── login.php              ← přihlašovací formulář
├── register.php           ← registrace
├── add.php                ← přidání úkolu
├── edit.php               ← editace úkolu
├── delete.php             ← smazání úkolu
├── import.php             ← import XML souboru
└── logout.php
```

### users.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<users>
  <user id="1">
    <username>jan</username>
    <!-- password_hash = password_hash('tajne', PASSWORD_BCRYPT) -->
    <password_hash>$2y$10$abc...</password_hash>
  </user>
</users>
```

### index.php – seznam s filtrováním
```php
<?php
requireLogin();
$xml = simplexml_load_file('data/tasks.xml');

$filterCat    = $_GET['category'] ?? '';
$filterStatus = $_GET['status']   ?? '';

// XPath filtrování
if ($filterCat && $filterStatus) {
    $tasks = $xml->xpath("//task[category='$filterCat'][status='$filterStatus']");
} elseif ($filterCat) {
    $tasks = $xml->xpath("//task[category='$filterCat']");
} elseif ($filterStatus) {
    $tasks = $xml->xpath("//task[status='$filterStatus']");
} else {
    $tasks = $xml->task;
}
?>
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>Zápisník úkolů</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
</head>
<body class="container py-4">
<h1>Moje úkoly</h1>

<!-- Filtr -->
<form method="get" class="row g-2 mb-3">
    <div class="col-auto">
        <select name="category" class="form-select">
            <option value="">Všechny kategorie</option>
            <option value="prace" <?= $filterCat==='prace'?'selected':'' ?>>Práce</option>
            <option value="osobni" <?= $filterCat==='osobni'?'selected':'' ?>>Osobní</option>
            <option value="studium" <?= $filterCat==='studium'?'selected':'' ?>>Studium</option>
        </select>
    </div>
    <div class="col-auto">
        <select name="status" class="form-select">
            <option value="">Všechny stavy</option>
            <option value="nezahajeno">Nezahájeno</option>
            <option value="zahajeno">Zahájeno</option>
            <option value="dokonceno">Dokončeno</option>
        </select>
    </div>
    <div class="col-auto">
        <button class="btn btn-primary">Filtrovat</button>
        <a href="index.php" class="btn btn-secondary">Reset</a>
    </div>
</form>

<!-- Seznam -->
<table class="table table-striped">
<thead><tr><th>Název</th><th>Kategorie</th><th>Stav</th><th>Akce</th></tr></thead>
<tbody>
<?php foreach ($tasks as $task): ?>
<tr>
    <td><?= htmlspecialchars((string)$task->title) ?></td>
    <td><?= htmlspecialchars((string)$task->category) ?></td>
    <td><?= htmlspecialchars((string)$task->status) ?></td>
    <td>
        <a href="edit.php?id=<?= $task['id'] ?>" class="btn btn-sm btn-warning">Upravit</a>
        <a href="delete.php?id=<?= $task['id'] ?>"
           onclick="return confirm('Smazat?')"
           class="btn btn-sm btn-danger">Smazat</a>
    </td>
</tr>
<?php endforeach; ?>
</tbody>
</table>

<a href="add.php" class="btn btn-success">+ Přidat úkol</a>
<a href="import.php" class="btn btn-outline-secondary">Importovat XML</a>
<a href="logout.php" class="btn btn-outline-danger float-end">Odhlásit</a>
</body>
</html>
```

### import.php – validace přes XSD
```php
<?php
requireLogin();
$error = $success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['xmlfile'])) {
    $tmpFile = $_FILES['xmlfile']['tmp_name'];

    // 1. Zkontroluj příponu
    $ext = strtolower(pathinfo($_FILES['xmlfile']['name'], PATHINFO_EXTENSION));
    if ($ext !== 'xml') {
        $error = "Soubor musí být XML.";
    } else {
        // 2. Validace proti XSD
        $dom = new DOMDocument();
        $dom->load($tmpFile);
        if (!$dom->schemaValidate('data/tasks.xsd')) {
            $error = "XML soubor není validní podle schématu.";
        } else {
            // 3. Import do tasks.xml
            $existing = simplexml_load_file('data/tasks.xml');
            $imported = simplexml_load_file($tmpFile);
            foreach ($imported->task as $task) {
                $new = $existing->addChild('task');
                $new->addAttribute('id', time() . rand(1,99));
                $new->addChild('title',    (string)$task->title);
                $new->addChild('category', (string)$task->category);
                $new->addChild('status',   (string)$task->status);
                $new->addChild('created',  date('Y-m-d'));
            }
            $existing->asXML('data/tasks.xml');
            $success = "Import proběhl úspěšně.";
        }
    }
}
?>
<!-- HTML formulář pro upload souboru -->
<form method="post" enctype="multipart/form-data">
    <input type="file" name="xmlfile" accept=".xml" required>
    <button type="submit">Importovat</button>
</form>
```

---

## 10. Ukázková úloha IV.2 – Skladový systém

### Struktura projektu
```
sklad/
├── api/
│   └── products.php       ← REST API endpoint
├── includes/
│   ├── db.php             ← PDO připojení
│   ├── auth.php           ← requireLogin(), requireRole()
│   └── functions.php      ← pomocné funkce
├── index.php              ← přehled produktů
├── product_add.php
├── product_edit.php
├── orders.php
├── login.php
└── logout.php
```

### auth.php – role
```php
function requireLogin(): void {
    session_start();
    if (!isset($_SESSION['user_id'])) {
        header('Location: /login.php'); exit;
    }
}

function requireRole(string $role): void {
    requireLogin();
    if ($_SESSION['role'] !== $role) {
        http_response_code(403);
        die('<h1>403 Přístup odepřen</h1>');
    }
}

// Použití:
// requireRole('admin');   // jen admin
// requireLogin();         // jakýkoli přihlášený
```

### Upozornění na nízké zásoby
```php
// Vyhledání produktů pod minimem
$stmt = $pdo->query(
    "SELECT * FROM products WHERE quantity <= min_quantity ORDER BY quantity ASC"
);
$lowStock = $stmt->fetchAll();

if (!empty($lowStock)) {
    echo '<div class="alert alert-warning">';
    echo '<strong>Nízké zásoby:</strong><ul>';
    foreach ($lowStock as $p) {
        echo "<li>" . htmlspecialchars($p['name'])
           . " – pouze " . $p['quantity'] . " ks (min: " . $p['min_quantity'] . ")</li>";
    }
    echo '</ul></div>';
}
```

### index.php – přehled produktů
```php
<?php
require 'includes/db.php';
require 'includes/auth.php';
requireLogin();
$pdo = getDb();

$products = $pdo->query("SELECT * FROM products ORDER BY name")->fetchAll();
$lowStock = $pdo->query(
    "SELECT * FROM products WHERE quantity <= min_quantity"
)->fetchAll();
?>
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>Skladový systém</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
</head>
<body class="container py-4">

<div class="d-flex justify-content-between mb-3">
    <h1>Sklad</h1>
    <div>
        Přihlášen: <strong><?= htmlspecialchars($_SESSION['username']) ?></strong>
        (<?= $_SESSION['role'] ?>)
        <a href="logout.php" class="btn btn-sm btn-outline-danger ms-2">Odhlásit</a>
    </div>
</div>

<?php if (!empty($lowStock)): ?>
<div class="alert alert-warning">
    <strong>⚠ Nízké zásoby:</strong>
    <?= implode(', ', array_column($lowStock, 'name')) ?>
</div>
<?php endif; ?>

<table class="table table-hover">
<thead><tr>
    <th>Název</th><th>Kategorie</th>
    <th>Množství</th><th>Cena</th><th>Akce</th>
</tr></thead>
<tbody>
<?php foreach ($products as $p): ?>
<tr class="<?= $p['quantity'] <= $p['min_quantity'] ? 'table-danger' : '' ?>">
    <td><?= htmlspecialchars($p['name']) ?></td>
    <td><?= htmlspecialchars($p['category']) ?></td>
    <td><?= $p['quantity'] ?> ks</td>
    <td><?= number_format($p['price'], 2) ?> Kč</td>
    <td>
        <a href="product_edit.php?id=<?= $p['id'] ?>" class="btn btn-sm btn-warning">Upravit</a>
        <?php if ($_SESSION['role'] === 'admin'): ?>
        <a href="product_delete.php?id=<?= $p['id'] ?>"
           onclick="return confirm('Smazat produkt?')"
           class="btn btn-sm btn-danger">Smazat</a>
        <?php endif; ?>
    </td>
</tr>
<?php endforeach; ?>
</tbody>
</table>

<?php if ($_SESSION['role'] === 'admin'): ?>
<a href="product_add.php" class="btn btn-success">+ Přidat produkt</a>
<?php endif; ?>
<a href="orders.php" class="btn btn-primary">Objednávky</a>

</body>
</html>
```

---

## Rychlá reference – časté chyby PHP

```php
// ❌ session_start() po výstupu
echo "něco";
session_start();    // CHYBA: headers already sent

// ✅ session_start() jako úplně první věc
<?php session_start(); ?>

// ❌ Výstup bez escapování
echo $_GET['name'];  // XSS!

// ✅ Vždy escapovat
echo htmlspecialchars($_GET['name'] ?? '', ENT_QUOTES, 'UTF-8');

// ❌ Zápis do XML bez uzamčení souboru
$xml->asXML('tasks.xml');  // při souběžném přístupu může dojít ke corrupted souboru

// ✅ S file lock
$fp = fopen('tasks.xml', 'c');
flock($fp, LOCK_EX);
$xml->asXML('tasks.xml');
flock($fp, LOCK_UN);
fclose($fp);

// ❌ Zobrazení chyb v produkci
ini_set('display_errors', 1);   // útočník vidí strukturu kódu

// ✅ Logy místo zobrazení
ini_set('display_errors', 0);
ini_set('log_errors', 1);
```

---

*PHP 8 · SimpleXML · DOMDocument · PDO/MySQL · Bootstrap 5 · REST API*