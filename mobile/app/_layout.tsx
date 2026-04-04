import '../global.css';

import { Stack } from 'expo-router';
import { HeroUINativeProvider } from 'heroui-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { appChromeColors } from '../components/ui/theme';

const queryClient = new QueryClient();

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({
    // Add custom fonts if needed, otherwise use system
  });

  useEffect(() => {
    if (loaded) {
      SplashScreen.hideAsync();
    }
  }, [loaded]);

  if (!loaded) {
    return null;
  }

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
