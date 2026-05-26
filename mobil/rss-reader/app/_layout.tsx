import { Stack } from 'expo-router';
import { useEffect } from 'react';

export default function RootLayout() {

  return (
    <Stack>
      <Stack.Screen name="index"  options={{ title: 'RSS Čtečka' }} />
      <Stack.Screen name="detail" options={{ title: 'Detail zprávy' }} />
    </Stack>
  );
}