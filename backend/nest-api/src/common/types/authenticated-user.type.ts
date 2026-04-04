export interface AuthenticatedUser {
  sub: string;
  userId: string;
  phoneNumber: string;
  role: 'customer' | 'admin' | 'vendor';
}
