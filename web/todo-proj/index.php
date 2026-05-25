<?php
define('TASKS_FILE', __DIR__ . '/data/tasks.xml');

function loadXml(): SimpleXMLElement {
    if (!file_exists(TASKS_FILE))
        file_put_contents(TASKS_FILE, '<?xml version="1.0" encoding="UTF-8"?><tasks/>');
    return simplexml_load_file(TASKS_FILE);
}

function saveXml(SimpleXMLElement $xml): void {
    $xml->asXML(TASKS_FILE);
}

function uid(): string { return uniqid('', true); }
function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }

$page   = $_GET['page']   ?? 'list';
$action = $_POST['action'] ?? '';

if ($action === 'add') {
    $title = trim($_POST['title'] ?? '');
    if ($title) {
        $xml  = loadXml();
        $task = $xml->addChild('task');
        $task->addAttribute('id', uid());
        $task->addChild('title',    h($title));
        $task->addChild('category', $_POST['category'] ?? 'osobni');
        $task->addChild('status',   $_POST['status']   ?? 'nezahajeno');
        $task->addChild('desc',     h(trim($_POST['desc'] ?? '')));
        $task->addChild('created',  date('Y-m-d'));
        saveXml($xml);
    }
    header('Location: ?page=list'); exit;
}

if ($action === 'edit') {
    $id  = $_POST['id'] ?? '';
    $xml = loadXml();
    $res = $xml->xpath("//task[@id='$id']");
    if ($res) {
        $res[0]->title    = h(trim($_POST['title'] ?? ''));
        $res[0]->category = $_POST['category'] ?? 'osobni';
        $res[0]->status   = $_POST['status']   ?? 'nezahajeno';
        $res[0]->desc     = h(trim($_POST['desc'] ?? ''));
        saveXml($xml);
    }
    header('Location: ?page=list'); exit;
}

if ($page === 'delete') {
    $id  = $_GET['id'] ?? '';
    $xml = loadXml();
    $res = $xml->xpath("//task[@id='$id']");
    if ($res) {
        $dom = dom_import_simplexml($res[0]);
        $dom->parentNode->removeChild($dom);
        saveXml($xml);
    }
    header('Location: ?page=list'); exit;
}

if ($action === 'import') {
    $tmp = $_FILES['xmlfile']['tmp_name'] ?? '';
    if ($tmp) {
        $dom = new DOMDocument();
        $dom->load($tmp);
        libxml_use_internal_errors(true);
        $importErr = '';
        if ($dom->schemaValidate(__DIR__ . '/data/tasks.xsd')) {
            $existing = loadXml();
            $imported = simplexml_load_file($tmp);
            foreach ($imported->task as $t) {
                $new = $existing->addChild('task');
                $new->addAttribute('id', uid());
                $new->addChild('title',    h((string)$t->title));
                $new->addChild('category', (string)$t->category);
                $new->addChild('status',   (string)$t->status);
                $new->addChild('desc',     h((string)$t->desc));
                $new->addChild('created',  date('Y-m-d'));
            }
            saveXml($existing);
        } else {
            $importErr = 'XML není validní.';
        }
        libxml_clear_errors();
    }
    header('Location: ?page=list'); exit;
}

$xml      = loadXml();
$cat      = $_GET['category'] ?? '';
$stat     = $_GET['status']   ?? '';
$xp       = '//task'
          . ($cat  ? "[category='$cat']"  : '')
          . ($stat ? "[status='$stat']"   : '');
$tasks    = $xml->xpath($xp);
$editTask = null;
if ($page === 'edit' && isset($_GET['id'])) {
    $res = $xml->xpath("//task[@id='{$_GET['id']}']");
    if ($res) $editTask = $res[0];
}
?>
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Zápisník úkolů</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
</head>
<body class="container py-4" style="max-width:800px">

<div class="d-flex justify-content-between align-items-center mb-3">
    <h2 class="mb-0">Zápisník úkolů</h2>
    <a href="?page=import" class="btn btn-sm btn-outline-secondary">Import XML</a>
</div>

<?php if ($page === 'import'): ?>

<h5>Importovat XML</h5>
<div class="alert alert-info"><pre class="mb-0">&lt;tasks&gt;
  &lt;task&gt;
    &lt;title&gt;Název&lt;/title&gt;
    &lt;category&gt;prace|osobni|studium&lt;/category&gt;
    &lt;status&gt;nezahajeno|zahajeno|dokonceno&lt;/status&gt;
    &lt;desc&gt;Volitelný popis&lt;/desc&gt;
  &lt;/task&gt;
&lt;/tasks&gt;</pre></div>
<form method="post" enctype="multipart/form-data">
    <input type="hidden" name="action" value="import">
    <input type="file" name="xmlfile" class="form-control mb-2" accept=".xml" required>
    <button class="btn btn-primary">Importovat</button>
    <a href="?page=list" class="btn btn-secondary ms-2">Zpět</a>
</form>

<?php else: ?>

<!-- Formulář přidat / upravit -->
<div class="card mb-4"><div class="card-body">
<form method="post">
    <input type="hidden" name="action" value="<?= $editTask ? 'edit' : 'add' ?>">
    <?php if ($editTask): ?><input type="hidden" name="id" value="<?= $editTask['id'] ?>"><?php endif; ?>
    <div class="row g-2">
        <div class="col-md-4">
            <input type="text" name="title" class="form-control" placeholder="Název *"
                   value="<?= $editTask ? h((string)$editTask->title) : '' ?>" required autofocus>
        </div>
        <div class="col-md-2">
            <select name="category" class="form-select">
                <?php foreach (['osobni'=>'Osobní','prace'=>'Práce','studium'=>'Studium'] as $v=>$l): ?>
                <option value="<?= $v ?>" <?= ($editTask && (string)$editTask->category===$v)?'selected':'' ?>><?= $l ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <select name="status" class="form-select">
                <?php foreach (['nezahajeno'=>'Nezahájeno','zahajeno'=>'Zahájeno','dokonceno'=>'Dokončeno'] as $v=>$l): ?>
                <option value="<?= $v ?>" <?= ($editTask && (string)$editTask->status===$v)?'selected':'' ?>><?= $l ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-3">
            <input type="text" name="desc" class="form-control" placeholder="Popis"
                   value="<?= $editTask ? h((string)$editTask->desc) : '' ?>">
        </div>
        <div class="col-md-1">
            <button class="btn btn-<?= $editTask ? 'warning' : 'success' ?> w-100"><?= $editTask ? '✎' : '+' ?></button>
        </div>
    </div>
</form>
</div></div>

<!-- Filtr -->
<form method="get" class="row g-2 mb-3">
    <input type="hidden" name="page" value="list">
    <div class="col-auto">
        <select name="category" class="form-select form-select-sm">
            <option value="">Všechny kategorie</option>
            <?php foreach (['osobni','prace','studium'] as $v): ?>
            <option value="<?= $v ?>" <?= ($_GET['category']??'')===$v?'selected':'' ?>><?= ucfirst($v) ?></option>
            <?php endforeach; ?>
        </select>
    </div>
    <div class="col-auto">
        <select name="status" class="form-select form-select-sm">
            <option value="">Všechny stavy</option>
            <?php foreach (['nezahajeno','zahajeno','dokonceno'] as $v): ?>
            <option value="<?= $v ?>" <?= ($_GET['status']??'')===$v?'selected':'' ?>><?= ucfirst($v) ?></option>
            <?php endforeach; ?>
        </select>
    </div>
    <div class="col-auto">
        <button class="btn btn-sm btn-primary">Filtrovat</button>
        <a href="?page=list" class="btn btn-sm btn-secondary">Reset</a>
    </div>
</form>

<!-- Seznam -->
<?php if (empty($tasks)): ?>
    <div class="alert alert-info">Žádné úkoly. Přidej první!</div>
<?php else: ?>
<table class="table table-striped table-sm">
<thead class="table-dark"><tr><th>Název</th><th>Kategorie</th><th>Stav</th><th>Datum</th><th></th></tr></thead>
<tbody>
<?php foreach ($tasks as $t):
    $bc = ['prace'=>'primary','osobni'=>'success','studium'=>'warning'];
    $bs = ['nezahajeno'=>'secondary','zahajeno'=>'info','dokonceno'=>'success'];
?>
<tr>
    <td title="<?= h((string)$t->desc) ?>"><?= h((string)$t->title) ?></td>
    <td><span class="badge bg-<?= $bc[(string)$t->category]??'secondary' ?>"><?= h((string)$t->category) ?></span></td>
    <td><span class="badge bg-<?= $bs[(string)$t->status]??'secondary' ?>"><?= h((string)$t->status) ?></span></td>
    <td><?= h((string)$t->created) ?></td>
    <td>
        <a href="?page=edit&id=<?= $t['id'] ?>" class="btn btn-sm btn-warning py-0">✎</a>
        <a href="?page=delete&id=<?= $t['id'] ?>" onclick="return confirm('Smazat?')"
           class="btn btn-sm btn-danger py-0">✕</a>
    </td>
</tr>
<?php endforeach; ?>
</tbody>
</table>
<?php endif; ?>

<?php endif; ?>
</body>
</html>