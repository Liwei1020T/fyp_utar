import { Redirect } from 'expo-router';
import { useAppStore, useCurrentUser } from '../store/appStore';
import { getRoleHome } from '../lib/navigation';
import { View } from 'react-native';

export default function IndexScreen() {
  const user = useCurrentUser();
  const hasHydrated = useAppStore((state) => state.hasHydrated);

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: 'white' }} />;
  }

  return <Redirect href={(user ? getRoleHome(user.role) : '/auth/welcome') as never} />;
}
