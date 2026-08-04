import type { BookingStatus, PaymentStatus } from '../../types/domain';
import type { AppChipVariant } from './AppChip';

export const appChromeColors = {
  page: '#F7F8FA',
  pageAuth: '#F7F8FA',
  pageAdmin: '#F5F7FA',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceMuted: '#F3F6FA',
  surfaceTint: '#EEF4FF',
  hero: '#163B7A',
  heroDeep: '#102F63',
  heroForeground: '#FFFFFF',
  heroMuted: '#D6E4FF',
  tabBar: '#FFFFFF',
  tabBarBorder: '#D8E0EA',
  primary: '#2563EB',
  primaryPressed: '#1D4ED8',
  primarySoft: '#DBEAFE',
  primarySoftest: '#EFF6FF',
  primarySoftBorder: '#BFDBFE',
  secondary: '#163B7A',
  secondarySoft: '#EEF4FF',
  secondarySoftBorder: '#D6E4FF',
  accent: '#D4A72C',
  accentSoft: '#FEF3C7',
  accentSoftBorder: '#F5D67A',
  success: '#059669',
  successSoft: '#D1FAE5',
  warning: '#D97706',
  warningSoft: '#FEF3C7',
  complete: '#64748B',
  completeSoft: '#E2E8F0',
  danger: '#DC2626',
  dangerSoft: '#FEE2E2',
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',
  textOnDark: '#FFFFFF',
  textOnDarkSecondary: '#D6E4FF',
  border: '#D8E0EA',
  borderSoft: '#E7ECF2',
  divider: '#E2E8F0',
  inactive: '#94A3B8',
} as const;

export const appLayoutMetrics = {
  contentMaxWidth: 960,
  pagePadding: 16,
  tabletPagePadding: 24,
  desktopPagePadding: 32,
  headerTopSpacing: 12,
  sectionGap: 24,
} as const;

export const performanceThemes = {
  power: {
    accent: appChromeColors.primary,
    softClassName: 'bg-primary-50 border-primary-200',
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
    softClassName: 'bg-primary-50 border-primary-200',
    textClassName: 'text-primary-700',
    label: 'Control',
  },
  sound: {
    accent: appChromeColors.primary,
    softClassName: 'bg-primary-50 border-primary-200',
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
    case 'rejected':
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
