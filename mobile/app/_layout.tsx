import '../global.css';

import { Component, useEffect, type ReactNode } from 'react';
import { Stack } from 'expo-router';
import { HeroUINativeProvider } from 'heroui-native';
import { StatusBar } from 'expo-status-bar';
import { Text, View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { appChromeColors } from '../components/ui/theme';
import { useAppStore } from '../store/appStore';
import {
  backendApi,
  isBackendAuthError,
  setBackendSessionExpiredHandler,
} from '../services/backendApi';
import {
  mapBackendUserToAdminProfile,
  mapBackendUserToPlayerProfile,
} from '../services/backendMappers';
import { loadBackendAccessToken } from '../services/backendSessionStorage';

class RootErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error('Root render failed', error);
  }

  render() {
    if (this.state.error) {
      return (
        <View
          style={{
            flex: 1,
            justifyContent: 'center',
            padding: 24,
            backgroundColor: appChromeColors.pageAuth,
          }}
        >
          <Text style={{ color: appChromeColors.danger, fontSize: 18, fontWeight: '700' }}>
            StringSense could not start
          </Text>
          <Text style={{ marginTop: 12, color: appChromeColors.textPrimary, lineHeight: 22 }}>
            {this.state.error.message}
          </Text>
        </View>
      );
    }

    return this.props.children;
  }
}

function BackendSessionBootstrap() {
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const markHydrated = useAppStore((state) => state.markHydrated);
  const logout = useAppStore((state) => state.logout);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );

  useEffect(
    () => setBackendSessionExpiredHandler(logout),
    [logout],
  );

  useEffect(() => {
    if (hasHydrated) {
      return;
    }

    let cancelled = false;

    const bootstrapSession = async () => {
      try {
        const token = await loadBackendAccessToken();
        if (!token) {
          return;
        }
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

        const profile = await backendApi.fetchProfile(token);

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
    setBackendAdminSession,
    setBackendPlayerSession,
  ]);

  return null;
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: appChromeColors.page }}>
      <View style={{ flex: 1, backgroundColor: appChromeColors.page }}>
        <RootErrorBoundary>
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
        </RootErrorBoundary>
      </View>
    </GestureHandlerRootView>
  );
}
