import '../global.css';

import { Stack } from 'expo-router';
import { HeroUINativeProvider } from 'heroui-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { appChromeColors } from '../components/ui/theme';

const queryClient = new QueryClient();

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: appChromeColors.page }}>
      <View style={{ flex: 1, backgroundColor: appChromeColors.page }}>
        <QueryClientProvider client={queryClient}>
          <HeroUINativeProvider>
            <Stack
              screenOptions={{
                headerShown: false,
                contentStyle: { backgroundColor: appChromeColors.page },
              }}
            />
            <StatusBar style="dark" />
          </HeroUINativeProvider>
        </QueryClientProvider>
      </View>
    </GestureHandlerRootView>
  );
}
