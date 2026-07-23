import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const BACKEND_ACCESS_TOKEN_KEY = 'stringsense.backend-access-token';
let pendingWrite: Promise<void> = Promise.resolve();

function enqueueWrite(operation: () => Promise<void>) {
  pendingWrite = pendingWrite.then(operation, operation).catch(() => undefined);
  return pendingWrite;
}

export async function loadBackendAccessToken() {
  if (Platform.OS === 'web') {
    return null;
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
    return;
  }

  await enqueueWrite(() => SecureStore.deleteItemAsync(BACKEND_ACCESS_TOKEN_KEY));
}
