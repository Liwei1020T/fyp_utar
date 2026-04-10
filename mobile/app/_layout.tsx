import '../global.css';

import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { HeroUINativeProvider } from 'heroui-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { appChromeColors } from '../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
} from '../store/appStore';
import {
  backendApi,
  isBackendAuthError,
} from '../services/backendApi';
import {
  mapBackendUserToAdminProfile,
  mapBackendUserToPlayerProfile,
} from '../services/backendMappers';

const queryClient = new QueryClient();

function BackendSessionBootstrap() {
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const sessionSource = useAppStore((state) => state.sessionSource);
  const token = useBackendAccessToken();
  const markHydrated = useAppStore((state) => state.markHydrated);
  const logout = useAppStore((state) => state.logout);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );

  useEffect(() => {
    if (hasHydrated) {
      return;
    }

    if (sessionSource !== 'backend' || !token) {
      markHydrated();
      return;
    }

    let cancelled = false;

    const bootstrapSession = async () => {
      try {
        const currentUser = await backendApi.fetchCurrentUser(token);

        if (cancelled) {
          return;
        }

        if (currentUser.role === 'admin') {
          setBackendAdminSession({
            accessToken: token,
            admin: mapBackendUserToAdminProfile(currentUser),
          });
          return;
        }

        const profile = await backendApi.fetchProfile(token).catch(() => null);

        if (cancelled) {
          return;
        }

        setBackendPlayerSession({
          accessToken: token,
          player: mapBackendUserToPlayerProfile(currentUser, profile),
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (isBackendAuthError(error)) {
          logout();
          return;
        }

        console.warn('Failed to restore persisted backend session', error);
      } finally {
        if (!cancelled) {
          markHydrated();
        }
      }
    };

    void bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, [
    hasHydrated,
    logout,
    markHydrated,
    sessionSource,
    setBackendAdminSession,
    setBackendPlayerSession,
    token,
  ]);

  return null;
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: appChromeColors.page }}>
      <View style={{ flex: 1, backgroundColor: appChromeColors.page }}>
        <QueryClientProvider client={queryClient}>
          <HeroUINativeProvider>
            <BackendSessionBootstrap />
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
