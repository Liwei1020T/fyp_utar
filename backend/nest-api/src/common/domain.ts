export const USER_ROLES = ['customer', 'admin', 'vendor'] as const;
export type UserRoleValue = (typeof USER_ROLES)[number];

export const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
export type SkillLevelValue = (typeof SKILL_LEVELS)[number];

export const PLAYING_STYLES = [
  'attacking',
  'balanced',
  'control_defensive',
] as const;
export type PlayingStyleValue = (typeof PLAYING_STYLES)[number];

export const GAME_TYPES = ['singles', 'doubles'] as const;
export type GameTypeValue = (typeof GAME_TYPES)[number];

export const AUTH_PROVIDERS = ['local', 'firebase_future_ready'] as const;
export type AuthProviderValue = (typeof AUTH_PROVIDERS)[number];

export const BOOKING_STATUSES = [
  'pending',
  'confirmed',
  'in_progress',
  'ready_for_pickup',
  'picked_up',
  'cancelled',
  'rejected',
] as const;
export type BookingStatusValue = (typeof BOOKING_STATUSES)[number];
