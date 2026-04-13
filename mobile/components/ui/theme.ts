import type { BookingStatus, PaymentStatus } from '../../types/domain';
import type { AppChipVariant } from './AppChip';

export const appChromeColors = {
  page: '#F5F5F7',
  pageAuth: '#F5F5F7',
  pageAdmin: '#F5F5F7',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceMuted: '#F5F5F7',
  hero: '#1D1D1F',
  heroForeground: '#FFFFFF',
  heroMuted: '#D2D2D7',
  tabBar: 'rgba(255, 255, 255, 0.96)',
  tabBarBorder: 'rgba(210, 210, 215, 0.72)',
  primary: '#0071E3',
  primarySoft: '#EAF4FF',
  primarySoftBorder: '#BBD7F4',
  secondary: '#0066CC',
  secondarySoft: '#EAF4FF',
  secondarySoftBorder: '#BBD7F4',
  accent: '#0071E3',
  accentSoft: '#EAF4FF',
  accentSoftBorder: '#BBD7F4',
  success: '#248A3D',
  successSoft: '#ECF8EF',
  warning: '#BF7A00',
  warningSoft: '#FFF7E8',
  complete: '#6E6E73',
  completeSoft: '#F5F5F7',
  danger: '#D70015',
  dangerSoft: '#FFF2F4',
  textPrimary: '#1D1D1F',
  textSecondary: 'rgba(29, 29, 31, 0.72)',
  border: '#D2D2D7',
  inactive: 'rgba(29, 29, 31, 0.48)',
} as const;

export const appLayoutMetrics = {
  contentMaxWidth: 820,
  pagePadding: 16,
  headerTopSpacing: 8,
  sectionGap: 24,
} as const;

export const performanceThemes = {
  power: {
    accent: appChromeColors.primary,
    softClassName: 'bg-primary-50 border-primary-100',
    textClassName: 'text-primary-700',
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
    accent: appChromeColors.primary,
    softClassName: 'bg-primary-50 border-primary-100',
    textClassName: 'text-primary-700',
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
