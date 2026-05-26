import { View, Text, FlatList, Button, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { useNews } from '../hooks/useNews';
import { TouchableOpacity } from 'react-native';

export default function HomeScreen() {
  const router = useRouter();
  const { news, loading, error, refresh } = useNews();

  useEffect(() => {
    refresh();
  }, []);

  return (
    <View style={styles.container}>
      {error   && <Text style={styles.error}>{error}</Text>}
      {loading && <Text style={styles.info}>Načítám zprávy...</Text>}

      <FlatList
        data={news}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.item}
            onPress={() => router.push({ pathname: '/detail', params: { id: item.id } })}
          >
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.date}>{item.pubDate}</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text style={styles.info}>Žádné zprávy. Klikni Obnovit.</Text>
        }
        refreshing={loading}
        onRefresh={refresh}
      />

      <View style={styles.button}>
        <Button title="Obnovit zprávy" onPress={refresh} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  error:     { padding: 8, backgroundColor: '#ffcccc', color: 'red' },
  info:      { padding: 16, textAlign: 'center', color: '#888' },
  button:    { padding: 12 },
  item:      { padding: 12, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
  title:     { fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  date:      { fontSize: 12, color: '#888' },
});