import type { UserRole } from '../types/domain';

export const ROLE_HOME: Record<UserRole, string> = {
  player: '/player',
  vendor: '/vendor',
};

export function getRoleHome(role: UserRole) {
  return ROLE_HOME[role];
}
