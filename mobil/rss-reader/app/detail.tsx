import { View, Text, ScrollView, Linking, Button, StyleSheet } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { loadNewsById } from '../services/database';
import type { NewsItem } from '../services/database';

export default function DetailScreen() {
  const { id }          = useLocalSearchParams<{ id: string }>();
  const [item, setItem] = useState<NewsItem | null>(null);

  useEffect(() => {
    if (id) setItem(loadNewsById(id));
  }, [id]);

  if (!item) return <Text style={{ padding: 16 }}>Zpráva nenalezena.</Text>;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.date}>{item.pubDate}</Text>
      <Text style={styles.body}>{item.description}</Text>
      <Button
        title="Otevřít v prohlížeči"
        onPress={() => Linking.openURL(item.link)}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title:     { fontSize: 20, fontWeight: 'bold', marginBottom: 8 },
  date:      { color: '#888', marginBottom: 12 },
  body:      { fontSize: 15, lineHeight: 22, marginBottom: 16 },
});