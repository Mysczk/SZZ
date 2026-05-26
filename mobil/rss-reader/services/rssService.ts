import type { NewsItem } from './database';

const RSS_URL = 'https://servis.idnes.cz/rss.aspx?c=zpravodaj';

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim();
}

function extractTag(xml: string, tag: string): string {
  const match = xml.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i'));
  return match ? stripHtml(match[1]) : '';
}

function extractCdata(xml: string, tag: string): string {
  const match = xml.match(new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>`, 'i'));
  return match ? match[1].trim() : extractTag(xml, tag);
}

export async function fetchRSS(): Promise<NewsItem[]> {
  try {
    const response = await fetch(RSS_URL);
    console.log('Status:', response.status);
    const xml = await response.text();
    console.log('XML délka:', xml.length);
    console.log('XML začátek:', xml.substring(0, 200));

    const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/gi) ?? [];
    console.log('Počet položek:', itemMatches.length);

    return itemMatches.map((item) => ({
      id:          extractCdata(item, 'guid') || extractCdata(item, 'link'),
      title:       extractCdata(item, 'title'),
      description: extractCdata(item, 'description'),
      pubDate:     extractTag(item, 'pubDate'),
      link:        extractCdata(item, 'link'),
    }));
  } catch (e) {
    console.error('Chyba fetchRSS:', e);
    throw e;
  }
}
