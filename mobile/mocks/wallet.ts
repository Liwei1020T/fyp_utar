import type { WalletBalance, WalletTransaction } from '../types/domain';

export const MOCK_WALLETS: WalletBalance[] = [
  {
    userId: 'player-001',
    availableBalance: 48,
    pendingTopUp: 0,
    lifetimeTopUps: 240,
  },
  {
    userId: 'player-002',
    availableBalance: 18,
    pendingTopUp: 0,
    lifetimeTopUps: 140,
  },
  {
    userId: 'player-003',
    availableBalance: 0,
    pendingTopUp: 0,
    lifetimeTopUps: 40,
  },
];

export const MOCK_WALLET_TRANSACTIONS: WalletTransaction[] = [
  {
    id: 'wallet-001',
    userId: 'player-001',
    type: 'top_up',
    direction: 'credit',
    status: 'completed',
    amount: 80,
    description: 'Mock wallet top-up for future bookings',
    createdAt: '2026-03-27T20:12:00.000Z',
    methodLabel: 'Online banking',
  },
  {
    id: 'wallet-002',
    userId: 'player-002',
    type: 'booking_payment',
    direction: 'debit',
    status: 'completed',
    amount: 8,
    description: 'Wallet used during booking payment BK-2398',
    createdAt: '2026-03-28T11:09:00.000Z',
    relatedBookingId: 'BK-2398',
    methodLabel: 'Wallet balance',
  },
];
