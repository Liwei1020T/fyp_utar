import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const BACKEND_ACCESS_TOKEN_KEY = 'stringsense.backend-access-token';
let pendingWrite: Promise<void> = Promise.resolve();

function getWebSessionStorage() {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function enqueueWrite(operation: () => Promise<void>) {
  pendingWrite = pendingWrite.then(operation, operation).catch(() => undefined);
  return pendingWrite;
}

export async function loadBackendAccessToken() {
  if (Platform.OS === 'web') {
    try {
      return getWebSessionStorage()?.getItem(BACKEND_ACCESS_TOKEN_KEY) ?? null;
    } catch {
      return null;
    }
  }

  try {
    await pendingWrite;
    return await SecureStore.getItemAsync(BACKEND_ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export async function persistBackendAccessToken(accessToken: string) {
  if (Platform.OS === 'web') {
    try {
      getWebSessionStorage()?.setItem(BACKEND_ACCESS_TOKEN_KEY, accessToken);
    } catch {
      // The in-memory session remains usable when browser storage is unavailable.
    }
    return;
  }

  await enqueueWrite(() =>
    SecureStore.setItemAsync(BACKEND_ACCESS_TOKEN_KEY, accessToken, {
      keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
    }),
  );
}

export async function clearBackendAccessToken() {
  if (Platform.OS === 'web') {
    try {
      getWebSessionStorage()?.removeItem(BACKEND_ACCESS_TOKEN_KEY);
    } catch {
      // Nothing else is required once the in-memory session has been cleared.
    }
    return;
  }

  await enqueueWrite(() => SecureStore.deleteItemAsync(BACKEND_ACCESS_TOKEN_KEY));
}
