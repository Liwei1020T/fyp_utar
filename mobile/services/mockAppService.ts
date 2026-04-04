import {
  MOCK_ADMINS,
  MOCK_ADMIN_ANALYTICS,
  MOCK_ADMIN_SETTINGS,
  MOCK_BOOKINGS,
  MOCK_BOOKING_SLOTS,
  MOCK_BUSINESS_HOURS,
  MOCK_CHAT_CONVERSATIONS,
  MOCK_NOTIFICATION_PREFERENCES,
  MOCK_NOTIFICATIONS,
  MOCK_PAYMENTS,
  MOCK_PLAYERS,
  MOCK_RACKETS,
  MOCK_STRINGS,
  MOCK_USERS,
  MOCK_WALLETS,
  MOCK_WALLET_TRANSACTIONS,
} from '../mocks';
import { useAppStore } from '../store/appStore';
import type {
  AppUser,
  AdminAnalyticsSummary,
  AdminProfile,
  AdminSettings,
  Booking,
  BookingSlot,
  BusinessHours,
  ChatConversation,
  NotificationItem,
  NotificationPreferences,
  Payment,
  PlayerProfile,
  RacketPassport,
  StringItem,
  WalletBalance,
  WalletTransaction,
} from '../types/domain';

export function getUserById(id?: string | null): AppUser | undefined {
  const state = useAppStore.getState();
  if (
    state.sessionSource === 'backend' &&
    state.livePlayerProfile &&
    state.livePlayerProfile.id === id
  ) {
    return state.livePlayerProfile;
  }
  return MOCK_USERS.find((item) => item.id === id);
}

export function getUserByEmail(email: string) {
  return MOCK_USERS.find((item) => item.email.toLowerCase() === email.toLowerCase());
}

export function getPlayerById(id?: string | null): PlayerProfile | undefined {
  const state = useAppStore.getState();
  if (
    state.sessionSource === 'backend' &&
    state.livePlayerProfile &&
    state.livePlayerProfile.id === id
  ) {
    return state.livePlayerProfile;
  }
  return MOCK_PLAYERS.find((item) => item.id === id);
}

export function getAdminById(id?: string | null): AdminProfile | undefined {
  return MOCK_ADMINS.find((item) => item.id === id);
}

export function getStringById(id?: string | null): StringItem | undefined {
  const state = useAppStore.getState();
  if (state.sessionSource === 'backend') {
    return state.liveStrings.find((item) => item.id === id);
  }
  return MOCK_STRINGS.find((item) => item.id === id);
}

export function getBookingById(id?: string | null): Booking | undefined {
  const state = useAppStore.getState();
  if (state.sessionSource === 'backend') {
    return state.liveBookings.find((item) => item.id === id);
  }
  return MOCK_BOOKINGS.find((item) => item.id === id);
}

export function getPaymentsForBooking(bookingId: string): Payment[] {
  return MOCK_PAYMENTS.filter((item) => item.bookingId === bookingId);
}

export function getBookingsForPlayer(playerId: string): Booking[] {
  const state = useAppStore.getState();
  if (state.sessionSource === 'backend') {
    return state.liveBookings.filter((item) => item.playerId === playerId);
  }
  return MOCK_BOOKINGS.filter((item) => item.playerId === playerId);
}

export function getBookingsForAdmin(adminId: string): Booking[] {
  return MOCK_BOOKINGS.filter((item) => item.adminId === adminId);
}

export function getNotificationsForUser(userId: string): NotificationItem[] {
  return MOCK_NOTIFICATIONS.filter((item) => item.userId === userId);
}

export function getRacketsForPlayer(playerId: string): RacketPassport[] {
  return MOCK_RACKETS.filter((item) => item.playerId === playerId);
}

export function getBusinessHoursForAdmin(adminId: string): BusinessHours | undefined {
  return MOCK_BUSINESS_HOURS.find((item) => item.adminId === adminId);
}

export function getSlotsForAdmin(adminId: string, date?: string): BookingSlot[] {
  return MOCK_BOOKING_SLOTS.filter(
    (item) => item.adminId === adminId && (!date || item.date === date)
  );
}

export function getConversationsForPlayer(playerId: string): ChatConversation[] {
  return MOCK_CHAT_CONVERSATIONS.filter((item) => item.playerId === playerId);
}

export function getConversationsForAdmin(adminId: string): ChatConversation[] {
  return MOCK_CHAT_CONVERSATIONS.filter((item) => item.adminId === adminId);
}

export function getConversationById(id?: string | null) {
  return MOCK_CHAT_CONVERSATIONS.find((item) => item.id === id);
}

export function getAdminAnalytics(adminId: string): AdminAnalyticsSummary | undefined {
  return MOCK_ADMIN_ANALYTICS.find((item) => item.adminId === adminId);
}

export function getWalletByUserId(userId: string): WalletBalance | undefined {
  return MOCK_WALLETS.find((item) => item.userId === userId);
}

export function getWalletTransactions(userId: string): WalletTransaction[] {
  return MOCK_WALLET_TRANSACTIONS.filter((item) => item.userId === userId);
}

export function getNotificationPreferences(userId: string): NotificationPreferences | undefined {
  return MOCK_NOTIFICATION_PREFERENCES.find((item) => item.userId === userId);
}

export function getAdminSettings(adminId: string): AdminSettings | undefined {
  return MOCK_ADMIN_SETTINGS.find((item) => item.adminId === adminId);
}

export function getRecommendedStringsForPlayer(playerId: string) {
  const player = getPlayerById(playerId);
  const state = useAppStore.getState();
  const sourceStrings =
    state.sessionSource === 'backend' && state.liveStrings.length > 0
      ? state.liveStrings
      : MOCK_STRINGS;

  if (!player) {
    return sourceStrings.slice(0, 3);
  }

  const ranked = [...sourceStrings].sort((left, right) => {
    const leftScore =
      left.ratings.power * player.priorities.power +
      left.ratings.control * player.priorities.control +
      left.ratings.durability * player.priorities.durability +
      left.ratings.comfort * player.priorities.comfort +
      left.ratings.sound * player.priorities.sound;
    const rightScore =
      right.ratings.power * player.priorities.power +
      right.ratings.control * player.priorities.control +
      right.ratings.durability * player.priorities.durability +
      right.ratings.comfort * player.priorities.comfort +
      right.ratings.sound * player.priorities.sound;

    return rightScore - leftScore;
  });

  return ranked.slice(0, 3);
}

export function getOperationalSummary() {
  return {
    players: MOCK_PLAYERS.length,
    strings: MOCK_STRINGS.length,
    bookings: MOCK_BOOKINGS.length,
    chats: MOCK_CHAT_CONVERSATIONS.length,
    lowStock: MOCK_STRINGS.filter((item) => item.availability === 'low_stock').length,
  };
}
