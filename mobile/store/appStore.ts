import { create } from 'zustand';
import {
  MOCK_ADMIN_SETTINGS,
  MOCK_BOOKINGS,
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
import { getRoleHome } from '../lib/navigation';
import {
  clearBackendAccessToken,
  persistBackendAccessToken,
} from '../services/backendSessionStorage';
import type {
  AppUser,
  AdminProfile,
  Booking,
  BookingDraft,
  RecommendationMatch,
  BookingStatus,
  BusinessHours,
  ChatConversation,
  ChatMessage,
  NotificationItem,
  NotificationPreferences,
  Payment,
  PaymentMethod,
  PaymentStatus,
  PlayerProfile,
  RacketPassport,
  StringItem,
  UserRole,
  AdminSettings,
  WalletBalance,
  WalletTransaction,
} from '../types/domain';

function titleize(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function buildTimeline(status: BookingStatus, dropOffDate: string, dropOffTime: string) {
  const now = new Date().toISOString();
  const steps: Booking['timeline'] = [
    {
      status: 'pending_payment',
      title: 'Waiting for payment',
      note: 'Booking draft created and waiting for full payment.',
      at: now,
    },
  ];

  if (status === 'pending_payment' || status === 'cancelled') {
    if (status === 'cancelled') {
      steps.push({
        status: 'cancelled',
        title: 'Booking cancelled',
        note: 'The unpaid booking was released back into the schedule.',
        at: now,
      });
    }
    return steps;
  }

  steps.push({
    status: 'confirmed',
    title: 'Booking confirmed',
    note: 'Full payment succeeded and the drop-off slot is secured.',
    at: now,
  });

  if (
    status === 'awaiting_dropoff' ||
    status === 'in_progress' ||
    status === 'ready_for_collection' ||
    status === 'completed'
  ) {
    steps.push({
      status: 'awaiting_dropoff',
      title: 'Awaiting drop-off',
      note: `Bring your racket on ${dropOffDate} at ${dropOffTime}.`,
      at: now,
    });
  }

  if (status === 'in_progress' || status === 'ready_for_collection' || status === 'completed') {
    steps.push({
      status: 'in_progress',
      title: 'Stringing in progress',
      note: 'The admin desk has started the live service work.',
      at: now,
    });
  }

  if (status === 'ready_for_collection' || status === 'completed') {
    steps.push({
      status: 'ready_for_collection',
      title: 'Ready for collection',
      note: 'Final checks passed and the pickup message is ready.',
      at: now,
    });
  }

  if (status === 'completed') {
    steps.push({
      status: 'completed',
      title: 'Completed',
      note: 'The racket has been collected and the service is closed.',
      at: now,
    });
  }

  return steps;
}

function buildConversationMeta(mode: ChatConversation['mode']) {
  switch (mode) {
    case 'waiting_admin':
      return 'Waiting for Admin';
    case 'admin_joined':
      return 'Admin Joined';
    case 'resolved':
      return 'Resolved';
    case 'closed':
      return 'Closed';
    case 'ai_only':
    default:
      return 'AI Reply';
  }
}

interface RegisterPlayerInput {
  username: string;
  email: string;
}

interface AppStoreState {
  hasHydrated: boolean;
  sessionSource: 'mock' | 'backend' | null;
  backendAccessToken: string | null;
  currentUserId: string | null;
  livePlayerProfile: PlayerProfile | null;
  liveAdminProfile: AdminProfile | null;
  liveStrings: StringItem[];
  liveBookings: Booking[];
  liveRecommendationResults: RecommendationMatch[];
  users: AppUser[];
  strings: StringItem[];
  bookings: Booking[];
  payments: Payment[];
  conversations: ChatConversation[];
  notifications: NotificationItem[];
  businessHours: BusinessHours[];
  rackets: RacketPassport[];
  wallets: WalletBalance[];
  walletTransactions: WalletTransaction[];
  adminSettings: AdminSettings[];
  notificationPreferences: NotificationPreferences[];
  compareSelection: string[];
  bookingDraft: BookingDraft | null;
  lastPaymentOutcome: PaymentStatus | null;
  login: (email: string) => UserRole | null;
  loginAsUser: (userId: string) => UserRole | null;
  registerPlayer: (input: RegisterPlayerInput) => string;
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
  prependLiveBooking: (booking: Booking) => void;
  setLiveRecommendationResults: (items: RecommendationMatch[]) => void;
  clearLiveRecommendationResults: () => void;
  logout: () => void;
  updatePlayerProfile: (playerId: string, patch: Partial<PlayerProfile>) => void;
  setBookingDraft: (draft: BookingDraft) => void;
  clearBookingDraft: () => void;
  submitBookingPayment: (
    method: PaymentMethod,
    status: PaymentStatus,
    bookingId?: string
  ) => { bookingId: string | null; paymentId: string | null };
  cancelBooking: (bookingId: string) => void;
  updateBookingStatus: (
    bookingId: string,
    status: BookingStatus,
    options?: { expectedCompletionAt?: string | null }
  ) => void;
  toggleCompareSelection: (stringId: string) => void;
  clearCompareSelection: () => void;
  appendChatMessage: (conversationId: string, message: Omit<ChatMessage, 'id' | 'sentAt'>) => void;
  requestAdminSupport: (conversationId: string) => void;
  resolveConversation: (conversationId: string) => void;
  updateBusinessHours: (adminId: string, nextHours: BusinessHours) => void;
  updateStringItem: (stringId: string, patch: Partial<StringItem>) => void;
  markNotificationRead: (notificationId: string) => void;
  topUpWallet: (userId: string, amount: number, methodLabel: string) => string;
  updateNotificationPreferences: (
    userId: string,
    patch: Partial<NotificationPreferences>
  ) => void;
  updateAdminSettings: (adminId: string, patch: Partial<AdminSettings>) => void;
}

type PersistedAppState = Pick<
  AppStoreState,
  | 'sessionSource'
  | 'currentUserId'
  | 'businessHours'
  | 'adminSettings'
>;

const APP_STORE_KEY = 'stringsense-app-store';

function readPersistedState(): Partial<PersistedAppState> {
  if (typeof localStorage === 'undefined') {
    return {};
  }

  try {
    const raw = localStorage.getItem(APP_STORE_KEY);
    return raw ? (JSON.parse(raw) as PersistedAppState) : {};
  } catch {
    return {};
  }
}

function clearPersistedSessionIdentity() {
  if (typeof localStorage === 'undefined') {
    return;
  }

  const stored = normalizePersistedState(readPersistedState());
  try {
    localStorage.setItem(
      APP_STORE_KEY,
      JSON.stringify({
        sessionSource: null,
        currentUserId: null,
        businessHours: stored.businessHours ?? MOCK_BUSINESS_HOURS,
        adminSettings: stored.adminSettings ?? MOCK_ADMIN_SETTINGS,
      } satisfies PersistedAppState),
    );
  } catch {
    // Browser persistence is optional; the backend token still stays memory-only.
  }
}

function extractPersistedState(state: AppStoreState): PersistedAppState {
  return {
    sessionSource: state.sessionSource,
    currentUserId: state.currentUserId,
    businessHours: state.businessHours,
    adminSettings: state.adminSettings,
  };
}

function normalizePersistedState(
  state: Partial<PersistedAppState>,
): Partial<PersistedAppState> {
  if (state.sessionSource !== 'backend') {
    return state;
  }

  const mockBusinessHoursIds = new Set(
    MOCK_BUSINESS_HOURS.map((item) => item.adminId),
  );
  const mockAdminSettingsIds = new Set(
    MOCK_ADMIN_SETTINGS.map((item) => item.adminId),
  );

  return {
    sessionSource: null,
    currentUserId: null,
    businessHours: state.businessHours?.filter((item) =>
      mockBusinessHoursIds.has(item.adminId),
    ),
    adminSettings: state.adminSettings?.filter((item) =>
      mockAdminSettingsIds.has(item.adminId),
    ),
  };
}

const persistedState = normalizePersistedState(readPersistedState());

export const useAppStore = create<AppStoreState>((set, get) => ({
  hasHydrated: false,
  sessionSource: persistedState.sessionSource ?? null,
  backendAccessToken: null,
  currentUserId: persistedState.currentUserId ?? null,
  livePlayerProfile: null,
  liveAdminProfile: null,
  liveStrings: [],
  liveBookings: [],
  liveRecommendationResults: [],
  users: MOCK_USERS,
  strings: MOCK_STRINGS,
  bookings: MOCK_BOOKINGS,
  payments: MOCK_PAYMENTS,
  conversations: MOCK_CHAT_CONVERSATIONS,
  notifications: MOCK_NOTIFICATIONS,
  businessHours: persistedState.businessHours ?? MOCK_BUSINESS_HOURS,
  rackets: MOCK_RACKETS,
  wallets: MOCK_WALLETS,
  walletTransactions: MOCK_WALLET_TRANSACTIONS,
  adminSettings: persistedState.adminSettings ?? MOCK_ADMIN_SETTINGS,
  notificationPreferences: MOCK_NOTIFICATION_PREFERENCES,
  compareSelection: [],
  bookingDraft: null,
  lastPaymentOutcome: null,
  markHydrated: () => set({ hasHydrated: true }),
  login: (email) => {
    const user = get().users.find((item) => item.email.toLowerCase() === email.toLowerCase());

    if (!user) {
      return null;
    }

    void clearBackendAccessToken();
    set({
      hasHydrated: true,
      currentUserId: user.id,
      sessionSource: 'mock',
      backendAccessToken: null,
      livePlayerProfile: null,
      liveAdminProfile: null,
      liveStrings: [],
      liveBookings: [],
      liveRecommendationResults: [],
    });
    return user.role;
  },
  loginAsUser: (userId) => {
    const user = get().users.find((item) => item.id === userId);

    if (!user) {
      return null;
    }

    void clearBackendAccessToken();
    set({
      hasHydrated: true,
      currentUserId: user.id,
      sessionSource: 'mock',
      backendAccessToken: null,
      livePlayerProfile: null,
      liveAdminProfile: null,
      liveStrings: [],
      liveBookings: [],
      liveRecommendationResults: [],
    });
    return user.role;
  },
  registerPlayer: ({ username, email }) => {
    const state = get();
    const playerId = `player-${String(
      state.users.filter((item) => item.role === 'player').length + 1
    ).padStart(3, '0')}`;
    const newPlayer: PlayerProfile = {
      id: playerId,
      role: 'player',
      name: username,
      email,
      avatarLabel: username
        .split(' ')
        .map((item) => item[0])
        .join('')
        .slice(0, 2)
        .toUpperCase(),
      phone: '+60 12-000 0000',
      skillLevel: 'Beginner',
      playingStyle: 'Balanced',
      playFrequency: 'Weekly',
      budgetRange: 'RM30–RM50',
      preferredFeel: 'Balanced',
      preferredTension: 24,
      priorities: {
        power: 6,
        control: 6,
        durability: 6,
        comfort: 7,
        sound: 5,
      },
      advancedPreferences: {
        elasticity: 6,
        tensionRetention: 6,
        stringMovement: 7,
      },
      homeVenue: 'Klang Valley',
      preferredAdminId: 'admin-001',
      recentGoal: 'Dial in a setup that feels balanced and confidence-building.',
    };

    void clearBackendAccessToken();
    set({
      hasHydrated: true,
      users: [newPlayer, ...state.users],
      currentUserId: newPlayer.id,
      sessionSource: 'mock',
      backendAccessToken: null,
      livePlayerProfile: null,
      liveAdminProfile: null,
      liveStrings: [],
      liveBookings: [],
      liveRecommendationResults: [],
      wallets: [
        { userId: newPlayer.id, availableBalance: 0, pendingTopUp: 0, lifetimeTopUps: 0 },
        ...state.wallets,
      ],
      notificationPreferences: [
        {
          userId: newPlayer.id,
          booking: true,
          payment: true,
          service: true,
          chat: true,
          recommendation: true,
        },
        ...state.notificationPreferences,
      ],
    });

    return newPlayer.id;
  },
  setBackendPlayerSession: ({ accessToken, player }) => {
    clearPersistedSessionIdentity();
    void persistBackendAccessToken(accessToken);
    set({
      hasHydrated: true,
      sessionSource: 'backend',
      backendAccessToken: accessToken,
      currentUserId: player.id,
      livePlayerProfile: player,
      liveAdminProfile: null,
      liveRecommendationResults: [],
    });
  },
  setBackendAdminSession: ({ accessToken, admin }) => {
    clearPersistedSessionIdentity();
    void persistBackendAccessToken(accessToken);
    set({
      hasHydrated: true,
      sessionSource: 'backend',
      backendAccessToken: accessToken,
      currentUserId: admin.id,
      liveAdminProfile: admin,
      livePlayerProfile: null,
      liveRecommendationResults: [],
    });
  },
  setLiveStrings: (liveStrings) => set({ liveStrings }),
  setLiveBookings: (liveBookings) => set({ liveBookings }),
  prependLiveBooking: (booking) =>
    set((state) => ({
      liveBookings: [booking, ...state.liveBookings.filter((item) => item.id !== booking.id)],
    })),
  setLiveRecommendationResults: (liveRecommendationResults) =>
    set({ liveRecommendationResults }),
  clearLiveRecommendationResults: () => set({ liveRecommendationResults: [] }),
  logout: () => {
    const restoredMockState = normalizePersistedState(readPersistedState());
    void clearBackendAccessToken();
    set({
      hasHydrated: true,
      sessionSource: null,
      backendAccessToken: null,
      currentUserId: null,
      livePlayerProfile: null,
      liveAdminProfile: null,
      liveStrings: [],
      liveBookings: [],
      liveRecommendationResults: [],
      bookingDraft: null,
      compareSelection: [],
      lastPaymentOutcome: null,
      businessHours:
        restoredMockState.businessHours ?? MOCK_BUSINESS_HOURS,
      adminSettings:
        restoredMockState.adminSettings ?? MOCK_ADMIN_SETTINGS,
    });
  },
  updatePlayerProfile: (playerId, patch) =>
    set((state) => {
      if (
        state.sessionSource === 'backend' &&
        state.livePlayerProfile &&
        state.livePlayerProfile.id === playerId
      ) {
        return {
          livePlayerProfile: {
            ...state.livePlayerProfile,
            ...patch,
          },
        };
      }

      return {
        users: state.users.map((item) =>
          item.id === playerId && item.role === 'player'
            ? ({ ...item, ...patch } as PlayerProfile)
            : item
        ),
      };
    }),
  setBookingDraft: (draft) => set({ bookingDraft: draft }),
  clearBookingDraft: () => set({ bookingDraft: null }),
  submitBookingPayment: (method, status, bookingId) => {
    const state = get();
    const currentUser = state.users.find(
      (item) => item.id === state.currentUserId && item.role === 'player'
    );
    const userId = currentUser?.id;

    if (!userId) {
      return { bookingId: null, paymentId: null };
    }

    const createdAt = new Date().toISOString();
    const nextPaymentId = `PAY-${5100 + state.payments.length + 1}`;
    const wallet = state.wallets.find((item) => item.userId === userId);

    const persistWalletUsage = (
      amount: number,
      description: string,
      relatedBookingId?: string
    ) => {
      set((current) => ({
        wallets: current.wallets.map((item) =>
          item.userId === userId
            ? {
                ...item,
                availableBalance: Math.max(0, item.availableBalance - amount),
              }
            : item
        ),
        walletTransactions: [
          {
            id: `wallet-${current.walletTransactions.length + 1}`,
            userId,
            type: 'booking_payment',
            direction: 'debit',
            status: 'completed',
            amount,
            description,
            createdAt,
            relatedBookingId,
            methodLabel: 'Wallet balance',
          },
          ...current.walletTransactions,
        ],
      }));
    };

    if (bookingId) {
      const existingBooking = state.bookings.find((item) => item.id === bookingId);

      if (!existingBooking) {
        return { bookingId: null, paymentId: null };
      }

      const walletUsed =
        status === 'paid' && method === 'wallet_balance'
          ? Math.min(wallet?.availableBalance ?? 0, existingBooking.totalAmount)
          : 0;
      const payment: Payment = {
        id: nextPaymentId,
        bookingId: existingBooking.id,
        playerId: existingBooking.playerId,
        adminId: existingBooking.adminId,
        method,
        status,
        amount: existingBooking.totalAmount,
        type: 'booking_payment',
        createdAt,
        reference: `MOCK-${method.toUpperCase()}-${nextPaymentId}`,
        note:
          status === 'paid'
            ? 'Full payment confirmed inside the mock checkout.'
            : 'Mock payment attempt did not complete successfully.',
      };

      const nextBooking: Booking = {
        ...existingBooking,
        paymentStatus: status === 'paid' ? 'paid' : status,
        status: status === 'paid' ? 'confirmed' : existingBooking.status,
        amountPaid: status === 'paid' ? existingBooking.totalAmount : 0,
        walletUsed,
        timeline:
          status === 'paid'
            ? buildTimeline('confirmed', existingBooking.dropOffDate, existingBooking.dropOffTime)
            : existingBooking.timeline,
      };

      if (walletUsed > 0) {
        persistWalletUsage(walletUsed, `Wallet used for ${existingBooking.id}`, existingBooking.id);
      }

      set((current) => ({
        bookings: current.bookings.map((item) =>
          item.id === existingBooking.id ? nextBooking : item
        ),
        payments: [payment, ...current.payments],
        notifications: [
          {
            id: `notif-${current.notifications.length + 20}`,
            userId,
            category: status === 'paid' ? 'payment' : 'booking',
            title: status === 'paid' ? 'Payment successful' : 'Payment needs attention',
            body:
              status === 'paid'
                ? `${existingBooking.id} is now confirmed for drop-off.`
                : `You can retry payment for ${existingBooking.id} or cancel the booking while it remains unpaid.`,
            createdAt,
            read: false,
            route:
              status === 'paid'
                ? `/player/bookings/${existingBooking.id}`
                : `/player/payments/${existingBooking.id}`,
          },
          ...current.notifications,
        ],
        lastPaymentOutcome: status,
      }));

      return { bookingId: existingBooking.id, paymentId: payment.id };
    }

    const draft = state.bookingDraft;

    if (!draft) {
      return { bookingId: null, paymentId: null };
    }

    const stringItem = state.strings.find((item) => item.id === draft.stringId);
    const stringFee = stringItem?.price ?? 36;
    const serviceFee = 18;
    const totalAmount = stringFee + serviceFee;
    const nextBookingId = `BK-${2400 + state.bookings.length + 1}`;
    const walletUsed =
      status === 'paid' && method === 'wallet_balance'
        ? Math.min(wallet?.availableBalance ?? 0, totalAmount)
        : 0;

    const bookingStatus: BookingStatus = status === 'paid' ? 'confirmed' : 'pending_payment';

    const booking: Booking = {
      id: nextBookingId,
      playerId: userId,
      adminId: draft.adminId,
      stringId: draft.stringId,
      status: bookingStatus,
      paymentStatus: status === 'paid' ? 'paid' : status,
      racketId: draft.racketId ?? undefined,
      racketBrand: draft.racketBrand,
      racketModel: draft.racketModel,
      requestedTension: draft.requestedTension,
      dropOffDate: draft.dropOffDate,
      dropOffTime: draft.dropOffTime,
      createdAt,
      notes: draft.notes,
      serviceFee,
      stringFee,
      totalAmount,
      amountPaid: status === 'paid' ? totalAmount : 0,
      walletUsed,
      bookingToken: `DROP-OFF-${nextBookingId}`,
      checkInReference: `SS-${nextBookingId}-${draft.racketBrand.toUpperCase().slice(0, 4)}`,
      queuePosition: 8,
      paymentRuleNote:
        'Full payment confirms the booking. Reschedule or cancel stays available only before payment completes.',
      timeline: buildTimeline(bookingStatus, draft.dropOffDate, draft.dropOffTime),
      updates: [],
    };

    const payment: Payment = {
      id: nextPaymentId,
      bookingId: nextBookingId,
      playerId: userId,
      adminId: draft.adminId,
      method,
      status,
      amount: totalAmount,
      type: 'booking_payment',
      createdAt,
      reference: `MOCK-${method.toUpperCase()}-${nextPaymentId}`,
      note:
        status === 'paid'
          ? 'Mock full payment completed from the checkout flow.'
          : 'Payment result returned a non-success outcome in the prototype.',
    };

    const nextRackets =
      draft.saveRacket && !draft.racketId
        ? [
            {
              id: `racket-${state.rackets.length + 1}`,
              playerId: userId,
              nickname: `${draft.racketBrand} ${draft.racketModel}`,
              brand: draft.racketBrand,
              model: draft.racketModel,
              weightClass: '4U',
              balancePoint: 'Balanced',
              gripSize: 'G5',
              preferredUse: 'Saved from booking flow',
              notes: 'Created from the frontend-only booking summary.',
              serviceCount: 1,
              currentStringId: draft.stringId,
              currentTension: draft.requestedTension,
              preferredRange: [Math.max(20, draft.requestedTension - 1), draft.requestedTension + 1],
              lastServicedAt: createdAt,
              stringHistory: [
                {
                  bookingId: nextBookingId,
                  stringId: draft.stringId,
                  tension: draft.requestedTension,
                  installedAt: createdAt,
                  feelRating: 0,
                  durabilityNote: 'Awaiting post-service feedback.',
                },
              ],
            } as RacketPassport,
            ...state.rackets,
          ]
        : state.rackets;

    if (walletUsed > 0) {
      persistWalletUsage(walletUsed, `Wallet used for ${nextBookingId}`, nextBookingId);
    }

    set((current) => ({
      bookings: [booking, ...current.bookings],
      payments: [payment, ...current.payments],
      notifications: [
        {
          id: `notif-${current.notifications.length + 20}`,
          userId,
          category: status === 'paid' ? 'booking' : 'payment',
          title: status === 'paid' ? 'Booking confirmed' : 'Payment not completed',
          body:
            status === 'paid'
              ? `${nextBookingId} is confirmed for ${draft.dropOffDate} at ${draft.dropOffTime}.`
              : `You can retry payment, reschedule, or cancel ${nextBookingId} before payment is completed.`,
          createdAt,
          read: false,
          route:
            status === 'paid'
              ? `/player/bookings/${nextBookingId}`
              : `/player/payments/${nextBookingId}`,
        },
        ...current.notifications,
      ],
      rackets: nextRackets,
      bookingDraft: draft,
      lastPaymentOutcome: status,
    }));

    return { bookingId: nextBookingId, paymentId: payment.id };
  },
  cancelBooking: (bookingId) =>
    set((state) => ({
      bookings: state.bookings.map((item) =>
        item.id === bookingId && item.paymentStatus !== 'paid'
          ? {
              ...item,
              status: 'cancelled',
              paymentStatus: 'cancelled',
              timeline: buildTimeline('cancelled', item.dropOffDate, item.dropOffTime),
            }
          : item
      ),
    })),
  updateBookingStatus: (bookingId, status, options) =>
    set((state) => ({
      bookings: state.bookings.map((item) =>
        item.id === bookingId
          ? {
              ...item,
              status,
              expectedCompletionAt:
                options && 'expectedCompletionAt' in options
                  ? options.expectedCompletionAt ?? undefined
                  : item.expectedCompletionAt,
              timeline: [
                ...item.timeline,
                {
                  status,
                  title: titleize(status),
                  note: 'Updated from the frontend-only admin operations workspace.',
                  at: new Date().toISOString(),
                },
              ],
            }
          : item
      ),
    })),
  toggleCompareSelection: (stringId) =>
    set((state) => {
      const exists = state.compareSelection.includes(stringId);

      if (exists) {
        return {
          compareSelection: state.compareSelection.filter((item) => item !== stringId),
        };
      }

      if (state.compareSelection.length >= 2) {
        if (typeof window !== 'undefined') {
          alert('Comparison limit reached. You can only compare up to 2 strings at once.');
        }
        return { compareSelection: state.compareSelection };
      }

      const next = [...state.compareSelection, stringId];
      return { compareSelection: next };
    }),
  clearCompareSelection: () => set({ compareSelection: [] }),
  appendChatMessage: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              updatedAt: new Date().toISOString(),
              mode:
                message.role === 'admin'
                  ? 'admin_joined'
                  : conversation.mode,
              statusLabel:
                message.role === 'admin'
                  ? buildConversationMeta('admin_joined')
                  : conversation.statusLabel,
              messages: [
                ...conversation.messages,
                {
                  ...message,
                  id: `msg-${conversation.messages.length + 300}`,
                  sentAt: new Date().toISOString(),
                },
              ],
            }
          : conversation
      ),
    })),
  requestAdminSupport: (conversationId) =>
    set((state) => ({
      conversations: state.conversations.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              mode: 'waiting_admin',
              statusLabel: buildConversationMeta('waiting_admin'),
              updatedAt: new Date().toISOString(),
              messages: [
                ...conversation.messages,
                {
                  id: `msg-${conversation.messages.length + 300}`,
                  role: 'system',
                  senderName: 'System',
                  body: 'Admin support requested. The shop will respond in this thread.',
                  sentAt: new Date().toISOString(),
                },
              ],
            }
          : conversation
      ),
    })),
  resolveConversation: (conversationId) =>
    set((state) => ({
      conversations: state.conversations.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              mode: 'resolved',
              statusLabel: buildConversationMeta('resolved'),
              updatedAt: new Date().toISOString(),
            }
          : conversation
      ),
    })),
  updateBusinessHours: (adminId, nextHours) =>
    set((state) => ({
      businessHours: state.businessHours.some((item) => item.adminId === adminId)
        ? state.businessHours.map((item) =>
            item.adminId === adminId ? nextHours : item
          )
        : [nextHours, ...state.businessHours],
    })),
  updateStringItem: (stringId, patch) =>
    set((state) => {
      if (state.sessionSource === 'backend') {
        return {
          liveStrings: state.liveStrings.map((item) =>
            item.id === stringId ? { ...item, ...patch } : item
          ),
        };
      }

      return {
        strings: state.strings.map((item) =>
          item.id === stringId ? { ...item, ...patch } : item
        ),
      };
    }),
  markNotificationRead: (notificationId) =>
    set((state) => ({
      notifications: state.notifications.map((item) =>
        item.id === notificationId ? { ...item, read: true } : item
      ),
    })),
  topUpWallet: (userId, amount, methodLabel) => {
    const reference = `TOPUP-${Date.now()}`;
    set((state) => ({
      wallets: state.wallets.map((item) =>
        item.userId === userId
          ? {
              ...item,
              availableBalance: item.availableBalance + amount,
              lifetimeTopUps: item.lifetimeTopUps + amount,
            }
          : item
      ),
      walletTransactions: [
        {
          id: `wallet-${state.walletTransactions.length + 1}`,
          userId,
          type: 'top_up',
          direction: 'credit',
          status: 'completed',
          amount,
          description: 'Wallet balance topped up from the frontend-only flow.',
          createdAt: new Date().toISOString(),
          methodLabel,
        },
        ...state.walletTransactions,
      ],
    }));
    return reference;
  },
  updateNotificationPreferences: (userId, patch) =>
    set((state) => ({
      notificationPreferences: state.notificationPreferences.map((item) =>
        item.userId === userId ? { ...item, ...patch } : item
      ),
    })),
  updateAdminSettings: (adminId, patch) =>
    set((state) => ({
      adminSettings: state.adminSettings.some((item) => item.adminId === adminId)
        ? state.adminSettings.map((item) =>
            item.adminId === adminId ? { ...item, ...patch } : item
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

if (typeof localStorage !== 'undefined') {
  useAppStore.subscribe((state) => {
    if (state.sessionSource === 'backend') {
      return;
    }

    try {
      localStorage.setItem(APP_STORE_KEY, JSON.stringify(extractPersistedState(state)));
    } catch {
      // Ignore local persistence failures and keep runtime state usable.
    }
  });
}

export function useCurrentUser() {
  const sessionSource = useAppStore((state) => state.sessionSource);
  const livePlayerProfile = useAppStore((state) => state.livePlayerProfile);
  const liveAdminProfile = useAppStore((state) => state.liveAdminProfile);
  const currentUserId = useAppStore((state) => state.currentUserId);
  const users = useAppStore((state) => state.users);
  if (sessionSource === 'backend') {
    return livePlayerProfile ?? liveAdminProfile;
  }
  return users.find((item) => item.id === currentUserId) ?? null;
}

export function useRoleHome() {
  const user = useCurrentUser();
  return user ? getRoleHome(user.role) : '/auth/welcome';
}

export function usePreferredAdminId() {
  const user = useCurrentUser();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const adminSettings = useAppStore((state) => state.adminSettings);

  if (!user) {
    return null;
  }

  if (user.role === 'admin') {
    return user.id;
  }

  if (sessionSource === 'backend') {
    return adminSettings.find((item) => item.adminId === 'main')?.adminId
      ?? adminSettings[0]?.adminId
      ?? user.preferredAdminId;
  }

  const matchingSetting = adminSettings.find((item) => item.adminId === user.preferredAdminId);
  if (matchingSetting) {
    return matchingSetting.adminId;
  }

  return user.preferredAdminId;
}

export function useBookings() {
  const sessionSource = useAppStore((state) => state.sessionSource);
  const liveBookings = useAppStore((state) => state.liveBookings);
  const bookings = useAppStore((state) => state.bookings);
  return sessionSource === 'backend' ? liveBookings : bookings;
}

export function usePayments() {
  return useAppStore((state) => state.payments);
}

export function useConversations() {
  return useAppStore((state) => state.conversations);
}

export function useNotifications() {
  return useAppStore((state) => state.notifications);
}

export function useBusinessHoursState() {
  return useAppStore((state) => state.businessHours);
}

export function useStrings() {
  const sessionSource = useAppStore((state) => state.sessionSource);
  const liveStrings = useAppStore((state) => state.liveStrings);
  const strings = useAppStore((state) => state.strings);
  return sessionSource === 'backend' ? liveStrings : strings;
}

export function useRackets() {
  return useAppStore((state) => state.rackets);
}

export function useWallets() {
  return useAppStore((state) => state.wallets);
}

export function useBackendAccessToken() {
  return useAppStore((state) => state.backendAccessToken);
}

export function useLiveRecommendationResults() {
  return useAppStore((state) => state.liveRecommendationResults);
}
