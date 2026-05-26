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
  const response = await fetch(RSS_URL);
  const xml = await response.text();

  const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/gi) ?? [];

  return itemMatches.map((item) => ({
    id:          extractCdata(item, 'guid') || extractCdata(item, 'link'),
    title:       extractCdata(item, 'title'),
    description: extractCdata(item, 'description'),
    pubDate:     extractTag(item, 'pubDate'),
    link:        extractCdata(item, 'link'),
  }));
}