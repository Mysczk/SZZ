import { useState, useEffect, useCallback } from 'react';
import { fetchRSS } from '../services/rssService';
import { saveNews, loadNews, initDatabase } from '../services/database';
import type { NewsItem } from '../services/database';

export function useNews() {
  const [news, setNews]       = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    initDatabase();
    setNews(loadNews());
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fresh = await fetchRSS();
      saveNews(fresh);
      setNews(loadNews());
    } catch (e) {
      setError('Nepodařilo se načíst zprávy. Zobrazuji offline data.');
    } finally {
      setLoading(false);
    }
  }, []);

  return { news, loading, error, refresh };
}