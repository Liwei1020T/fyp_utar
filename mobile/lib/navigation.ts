import type { UserRole } from '../types/domain';

export const ROLE_HOME: Record<UserRole, string> = {
  player: '/player',
  admin: '/admin',
};

export function getRoleHome(role: UserRole) {
  return ROLE_HOME[role];
}
