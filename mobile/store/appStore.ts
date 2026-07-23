import { create } from 'zustand';
import { getRoleHome } from '../lib/navigation';
import {
  clearBackendAccessToken,
  persistBackendAccessToken,
} from '../services/backendSessionStorage';
import type {
  AdminProfile,
  AdminSettings,
  Booking,
  BookingDraft,
  BusinessHours,
  ChatConversation,
  NotificationItem,
  Payment,
  PlayerProfile,
  RacketPassport,
  RecommendationMatch,
  StringItem,
  WalletBalance,
  WalletTransaction,
} from '../types/domain';

function reconcileBookingPayments(
  bookings: Booking[],
  payments: Payment[],
): Booking[] {
  const latestByBookingId = new Map<string, Payment>();
  payments.forEach((payment) => {
    if (payment.type !== 'booking_payment' || !payment.bookingId) {
      return;
    }
    const current = latestByBookingId.get(payment.bookingId);
    if (!current || payment.createdAt > current.createdAt) {
      latestByBookingId.set(payment.bookingId, payment);
    }
  });

  return bookings.map((booking) => {
    const payment = latestByBookingId.get(booking.id);
    if (!payment) {
      return booking;
    }
    const isPaid = payment.status === 'paid';
    return {
      ...booking,
      paymentStatus: payment.status,
      totalAmount: payment.amount,
      amountPaid: isPaid ? payment.amount : 0,
      walletUsed:
        isPaid && payment.method === 'wallet_balance' ? payment.amount : 0,
    };
  });
}

interface AppStoreState {
  hasHydrated: boolean;
  backendAccessToken: string | null;
  livePlayerProfile: PlayerProfile | null;
  liveAdminProfile: AdminProfile | null;
  liveStrings: StringItem[];
  liveBookings: Booking[];
  liveConversations: ChatConversation[];
  liveNotifications: NotificationItem[];
  liveRackets: RacketPassport[];
  livePayments: Payment[];
  liveWallets: WalletBalance[];
  liveWalletTransactions: WalletTransaction[];
  liveRecommendationResults: RecommendationMatch[];
  businessHours: BusinessHours[];
  adminSettings: AdminSettings[];
  compareSelection: string[];
  bookingDraft: BookingDraft | null;
  markHydrated: () => void;
  setBackendPlayerSession: (input: {
    accessToken: string;
    player: PlayerProfile;
  }) => void;
  setBackendAdminSession: (input: {
    accessToken: string;
    admin: AdminProfile;
  }) => void;
  setLiveStrings: (strings: StringItem[]) => void;
  setLiveBookings: (bookings: Booking[]) => void;
  setLiveConversations: (conversations: ChatConversation[]) => void;
  setLiveNotifications: (notifications: NotificationItem[]) => void;
  setLiveRackets: (rackets: RacketPassport[]) => void;
  setLivePayments: (payments: Payment[]) => void;
  setLiveWallet: (
    balance: WalletBalance,
    transactions: WalletTransaction[],
  ) => void;
  prependLiveBooking: (booking: Booking) => void;
  setLiveRecommendationResults: (items: RecommendationMatch[]) => void;
  clearLiveRecommendationResults: () => void;
  logout: () => void;
  updatePlayerProfile: (
    playerId: string,
    patch: Partial<PlayerProfile>,
  ) => void;
  setBookingDraft: (draft: BookingDraft) => void;
  clearBookingDraft: () => void;
  toggleCompareSelection: (stringId: string) => void;
  clearCompareSelection: () => void;
  updateBusinessHours: (adminId: string, nextHours: BusinessHours) => void;
  updateStringItem: (stringId: string, patch: Partial<StringItem>) => void;
  updateAdminSettings: (
    adminId: string,
    patch: Partial<AdminSettings>,
  ) => void;
}

export const useAppStore = create<AppStoreState>((set) => ({
  hasHydrated: false,
  backendAccessToken: null,
  livePlayerProfile: null,
  liveAdminProfile: null,
  liveStrings: [],
  liveBookings: [],
  liveConversations: [],
  liveNotifications: [],
  liveRackets: [],
  livePayments: [],
  liveWallets: [],
  liveWalletTransactions: [],
  liveRecommendationResults: [],
  businessHours: [],
  adminSettings: [],
  compareSelection: [],
  bookingDraft: null,
  markHydrated: () => set({ hasHydrated: true }),
  setBackendPlayerSession: ({ accessToken, player }) => {
    void persistBackendAccessToken(accessToken);
    set({
      hasHydrated: true,
      backendAccessToken: accessToken,
      livePlayerProfile: player,
      liveAdminProfile: null,
      liveConversations: [],
      liveNotifications: [],
      liveRackets: [],
      liveRecommendationResults: [],
      livePayments: [],
      liveWallets: [],
      liveWalletTransactions: [],
      businessHours: [],
      adminSettings: [],
    });
  },
  setBackendAdminSession: ({ accessToken, admin }) => {
    void persistBackendAccessToken(accessToken);
    set({
      hasHydrated: true,
      backendAccessToken: accessToken,
      liveAdminProfile: admin,
      livePlayerProfile: null,
      liveConversations: [],
      liveNotifications: [],
      liveRackets: [],
      liveRecommendationResults: [],
      livePayments: [],
      liveWallets: [],
      liveWalletTransactions: [],
      businessHours: [],
      adminSettings: [],
    });
  },
  setLiveStrings: (liveStrings) => set({ liveStrings }),
  setLiveBookings: (liveBookings) =>
    set((state) => ({
      liveBookings: reconcileBookingPayments(
        liveBookings,
        state.livePayments,
      ),
    })),
  setLiveConversations: (liveConversations) => set({ liveConversations }),
  setLiveNotifications: (liveNotifications) => set({ liveNotifications }),
  setLiveRackets: (liveRackets) => set({ liveRackets }),
  setLivePayments: (livePayments) =>
    set((state) => ({
      livePayments,
      liveBookings: reconcileBookingPayments(
        state.liveBookings,
        livePayments,
      ),
    })),
  setLiveWallet: (balance, liveWalletTransactions) =>
    set({ liveWallets: [balance], liveWalletTransactions }),
  prependLiveBooking: (booking) =>
    set((state) => ({
      liveBookings: [
        booking,
        ...state.liveBookings.filter((item) => item.id !== booking.id),
      ],
    })),
  setLiveRecommendationResults: (liveRecommendationResults) =>
    set({ liveRecommendationResults }),
  clearLiveRecommendationResults: () =>
    set({ liveRecommendationResults: [] }),
  logout: () => {
    void clearBackendAccessToken();
    set({
      hasHydrated: true,
      backendAccessToken: null,
      livePlayerProfile: null,
      liveAdminProfile: null,
      liveStrings: [],
      liveBookings: [],
      liveConversations: [],
      liveNotifications: [],
      liveRackets: [],
      livePayments: [],
      liveWallets: [],
      liveWalletTransactions: [],
      liveRecommendationResults: [],
      bookingDraft: null,
      compareSelection: [],
      businessHours: [],
      adminSettings: [],
    });
  },
  updatePlayerProfile: (playerId, patch) =>
    set((state) => {
      if (state.livePlayerProfile?.id !== playerId) {
        return {};
      }

      return {
        livePlayerProfile: {
          ...state.livePlayerProfile,
          ...patch,
        },
      };
    }),
  setBookingDraft: (draft) => set({ bookingDraft: draft }),
  clearBookingDraft: () => set({ bookingDraft: null }),
  toggleCompareSelection: (stringId) =>
    set((state) => {
      const exists = state.compareSelection.includes(stringId);

      if (exists) {
        return {
          compareSelection: state.compareSelection.filter(
            (item) => item !== stringId,
          ),
        };
      }

      if (state.compareSelection.length >= 2) {
        if (typeof window !== 'undefined') {
          alert(
            'Comparison limit reached. You can only compare up to 2 strings at once.',
          );
        }
        return {};
      }

      return {
        compareSelection: [...state.compareSelection, stringId],
      };
    }),
  clearCompareSelection: () => set({ compareSelection: [] }),
  updateBusinessHours: (adminId, nextHours) =>
    set((state) => ({
      businessHours: state.businessHours.some(
        (item) => item.adminId === adminId,
      )
        ? state.businessHours.map((item) =>
            item.adminId === adminId ? nextHours : item,
          )
        : [nextHours, ...state.businessHours],
    })),
  updateStringItem: (stringId, patch) =>
    set((state) => ({
      liveStrings: state.liveStrings.map((item) =>
        item.id === stringId ? { ...item, ...patch } : item,
      ),
    })),
  updateAdminSettings: (adminId, patch) =>
    set((state) => ({
      adminSettings: state.adminSettings.some(
        (item) => item.adminId === adminId,
      )
        ? state.adminSettings.map((item) =>
            item.adminId === adminId ? { ...item, ...patch } : item,
          )
        : [
            {
              adminId,
              storeName: '',
              storeContact: '',
              supportText: '',
              paymentNotes: '',
              bookingNotes: '',
              storePolicyText: '',
              address: '',
              trendingStringIds: [],
              ...patch,
            },
            ...state.adminSettings,
          ],
    })),
}));

export function useCurrentUser() {
  const livePlayerProfile = useAppStore((state) => state.livePlayerProfile);
  const liveAdminProfile = useAppStore((state) => state.liveAdminProfile);
  return livePlayerProfile ?? liveAdminProfile;
}

export function useRoleHome() {
  const user = useCurrentUser();
  return user ? getRoleHome(user.role) : '/auth/welcome';
}

export function usePreferredAdminId() {
  const user = useCurrentUser();

  if (!user) {
    return null;
  }

  return user.role === 'admin' ? user.id : 'main';
}

export function useBookings() {
  return useAppStore((state) => state.liveBookings);
}

export function usePayments() {
  return useAppStore((state) => state.livePayments);
}

export function useConversations() {
  return useAppStore((state) => state.liveConversations);
}

export function useNotifications() {
  return useAppStore((state) => state.liveNotifications);
}

export function useBusinessHoursState() {
  return useAppStore((state) => state.businessHours);
}

export function useStrings() {
  return useAppStore((state) => state.liveStrings);
}

export function useRackets() {
  return useAppStore((state) => state.liveRackets);
}

export function useWallets() {
  return useAppStore((state) => state.liveWallets);
}

export function useWalletTransactions() {
  return useAppStore((state) => state.liveWalletTransactions);
}

export function useBackendAccessToken() {
  return useAppStore((state) => state.backendAccessToken);
}

export function useLiveRecommendationResults() {
  return useAppStore((state) => state.liveRecommendationResults);
}
