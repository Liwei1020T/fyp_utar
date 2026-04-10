import type { BookingStatus, PaymentStatus } from '../../types/domain';
import type { AppChipVariant } from './AppChip';

export const appChromeColors = {
  page: '#F5F7FB',
  pageAuth: '#F8FAFD',
  pageAdmin: '#F5F8FC',
  surface: '#FFFFFF',
  surfaceElevated: '#FBFCFE',
  surfaceMuted: '#EEF4FA',
  hero: '#2F64B6',
  heroForeground: '#F7FAFF',
  heroMuted: '#D7E6F8',
  tabBar: 'rgba(244, 248, 252, 0.96)',
  tabBarBorder: 'rgba(255, 255, 255, 0.92)',
  primary: '#2F64B6',
  primarySoft: '#EAF2FF',
  primarySoftBorder: '#CFE0F8',
  accent: '#C7922B',
  accentSoft: '#FFF3D8',
  accentSoftBorder: '#F0DEB4',
  success: '#2F7A58',
  successSoft: '#EEF8F4',
  warning: '#B67D21',
  warningSoft: '#FFF7E8',
  complete: '#6D8477',
  completeSoft: '#F1F5F3',
  danger: '#D94C4C',
  dangerSoft: '#FFF1F1',
  textPrimary: '#1D1D1F',
  textSecondary: '#64748B',
  border: '#E3EBF4',
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
    accent: appChromeColors.primary,
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
