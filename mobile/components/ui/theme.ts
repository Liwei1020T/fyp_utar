import type { BookingStatus, PaymentStatus } from '../../types/domain';
import type { AppChipVariant } from './AppChip';

export const appChromeColors = {
  page: '#F4F7FB',
  pageAuth: '#F7FAFD',
  pageAdmin: '#F2F8F8',
  surface: '#FFFFFF',
  surfaceElevated: '#FBFDFF',
  surfaceMuted: '#EEF4FA',
  hero: '#214C80',
  heroForeground: '#F7FAFF',
  heroMuted: '#D7E6F8',
  tabBar: 'rgba(244, 248, 252, 0.96)',
  tabBarBorder: 'rgba(255, 255, 255, 0.92)',
  primary: '#2F64B6',
  inactive: '#8EA0B8',
} as const;

export const appLayoutMetrics = {
  contentMaxWidth: 820,
  pagePadding: 20,
  headerTopSpacing: 16,
  sectionGap: 28,
} as const;

export const performanceThemes = {
  power: {
    accent: '#EA580C',
    softClassName: 'bg-power-50 border-power-100',
    textClassName: 'text-power-700',
    label: 'Power',
  },
  durability: {
    accent: '#1E8058',
    softClassName: 'bg-durability-50 border-durability-100',
    textClassName: 'text-durability-700',
    label: 'Durability',
  },
  control: {
    accent: '#22766D',
    softClassName: 'bg-control-50 border-control-100',
    textClassName: 'text-control-700',
    label: 'Control',
  },
  sound: {
    accent: '#6550B8',
    softClassName: 'bg-sound-50 border-sound-100',
    textClassName: 'text-sound-700',
    label: 'Sound',
  },
} as const;

export function getBookingStatusVariant(status: BookingStatus): AppChipVariant {
  switch (status) {
    case 'pending':
      return 'warning';
    case 'ready_for_collection':
    case 'completed':
      return 'success';
    case 'confirmed':
    case 'awaiting_dropoff':
    case 'in_progress':
      return 'primary';
    case 'pending_payment':
      return 'warning';
    case 'cancelled':
      return 'danger';
    default:
      return 'neutral';
  }
}

export function getPaymentStatusVariant(status: PaymentStatus): AppChipVariant {
  switch (status) {
    case 'paid':
      return 'success';
    case 'failed':
    case 'cancelled':
      return 'danger';
    case 'unpaid':
    default:
      return 'warning';
  }
}
