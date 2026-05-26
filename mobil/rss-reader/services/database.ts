import * as SQLite from 'expo-sqlite';

const db = SQLite.openDatabaseSync('rss.db');

export type NewsItem = {
  id: string;
  title: string;
  description: string;
  pubDate: string;
  link: string;
};

export function initDatabase() {
  db.execSync(`
    CREATE TABLE IF NOT EXISTS news (
      id          TEXT PRIMARY KEY,
      title       TEXT NOT NULL,
      description TEXT,
      pubDate     TEXT,
      link        TEXT,
      fetchedAt   INTEGER DEFAULT (strftime('%s','now'))
    );
  `);
}

export function saveNews(items: NewsItem[]) {
  for (const item of items) {
    db.runSync(
      `INSERT OR REPLACE INTO news (id, title, description, pubDate, link)
       VALUES (?, ?, ?, ?, ?)`,
      [item.id, item.title, item.description, item.pubDate, item.link]
    );
  }
}

export function loadNews(): NewsItem[] {
  return db.getAllSync<NewsItem>(
    `SELECT * FROM news ORDER BY fetchedAt DESC`
  );
}

export function loadNewsById(id: string): NewsItem | null {
  return db.getFirstSync<NewsItem>(
    `SELECT * FROM news WHERE id = ?`, [id]
  ) ?? null;
}