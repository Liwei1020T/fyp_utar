import { Redirect } from 'expo-router';
import { useCurrentUser } from '../store/appStore';
import { getRoleHome } from '../lib/navigation';

export default function IndexScreen() {
  const user = useCurrentUser();

  return <Redirect href={(user ? getRoleHome(user.role) : '/auth/welcome') as never} />;
}
