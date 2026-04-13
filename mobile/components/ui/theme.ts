import type { BookingStatus, PaymentStatus } from '../../types/domain';
import type { AppChipVariant } from './AppChip';

export const appChromeColors = {
  page: '#F7F9FC',
  pageAuth: '#FAFBFD',
  pageAdmin: '#F6FAF8',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceMuted: '#EEF3F7',
  hero: '#2757A4',
  heroForeground: '#F7FAFF',
  heroMuted: '#CFE0F7',
  tabBar: 'rgba(255, 255, 255, 0.96)',
  tabBarBorder: 'rgba(220, 229, 240, 0.92)',
  primary: '#2563EB',
  primarySoft: '#EAF1FF',
  primarySoftBorder: '#C8D9FA',
  secondary: '#0F9F8F',
  secondarySoft: '#E8F8F5',
  secondarySoftBorder: '#BCE7E0',
  accent: '#D48A12',
  accentSoft: '#FFF5DF',
  accentSoftBorder: '#F3DBA7',
  success: '#168A5B',
  successSoft: '#EAF8F1',
  warning: '#B7791F',
  warningSoft: '#FFF7E6',
  complete: '#5F756B',
  completeSoft: '#F0F5F2',
  danger: '#D94848',
  dangerSoft: '#FFF0F0',
  textPrimary: '#14181F',
  textSecondary: '#566579',
  border: '#DDE6F0',
  inactive: '#8291A6',
} as const;

export const appLayoutMetrics = {
  contentMaxWidth: 820,
  pagePadding: 16,
  headerTopSpacing: 8,
  sectionGap: 24,
} as const;

export const performanceThemes = {
  power: {
    accent: appChromeColors.accent,
    softClassName: 'bg-accent-50 border-accent-100',
    textClassName: 'text-accent-700',
    label: 'Power',
  },
  durability: {
    accent: appChromeColors.success,
    softClassName: 'bg-success-50 border-success-100',
    textClassName: 'text-success-700',
    label: 'Durability',
  },
  control: {
    accent: appChromeColors.primary,
    softClassName: 'bg-primary-50 border-primary-100',
    textClassName: 'text-primary-700',
    label: 'Control',
  },
  sound: {
    accent: appChromeColors.secondary,
    softClassName: 'bg-secondary-50 border-secondary-100',
    textClassName: 'text-secondary-700',
    label: 'Sound',
  },
} as const;

export function getBookingStatusVariant(status: BookingStatus): AppChipVariant {
  switch (status) {
    case 'pending':
    case 'pending_payment':
      return 'warning';
    case 'awaiting_dropoff':
      return 'warning'; // Amber / warm neutral
    case 'in_progress':
      return 'primary'; // Blue
    case 'ready_for_collection':
      return 'success'; // Green
    case 'completed':
      return 'complete'; // Muted grey/green
    case 'confirmed':
      return 'primary';
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
