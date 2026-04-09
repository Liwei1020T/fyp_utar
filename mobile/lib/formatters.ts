import type {
  BookingStatus,
  ChatMessageRole,
  ConversationMode,
  InventoryAvailability,
  PaymentMethod,
  PaymentStatus,
  UserRole,
} from '../types/domain';

const SPECIAL_LABEL_TOKENS: Record<string, string> = {
  ai: 'AI',
  qr: 'QR',
};

export function formatLabel(value: string) {
  return value
    .split(/[_-\s]+/)
    .filter(Boolean)
    .map((segment) => {
      const normalized = segment.toLowerCase();
      return SPECIAL_LABEL_TOKENS[normalized]
        ?? `${normalized.charAt(0).toUpperCase()}${normalized.slice(1)}`;
    })
    .join(' ');
}

export function formatRole(role: UserRole) {
  return formatLabel(role);
}

export function formatBookingStatus(status: BookingStatus) {
  return formatLabel(status);
}

export function formatPaymentStatus(status: PaymentStatus) {
  return formatLabel(status);
}

export function formatPaymentMethod(method: PaymentMethod) {
  return formatLabel(method);
}

export function formatConversationMode(mode: ConversationMode) {
  return formatLabel(mode);
}

export function formatPlayFrequency(value: string) {
  switch (value) {
    case 'Social':
      return '1 day / week';
    case 'Weekly':
      return '2-3 days / week';
    case 'Tournament':
      return '4+ days / week';
    default:
      return value;
  }
}

export function formatAvailability(availability: InventoryAvailability) {
  return formatLabel(availability);
}

export function formatCurrency(amount: number) {
  return `RM ${amount.toFixed(2)}`;
}

export function formatLocalDateInputValue(value: Date | string) {
  const date = typeof value === 'string' ? new Date(value) : value;

  if (Number.isNaN(date.getTime())) {
    return typeof value === 'string' ? value : '';
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatLocalTimeValue(value: Date | string) {
  const date = typeof value === 'string' ? new Date(value) : value;

  if (Number.isNaN(date.getTime())) {
    return typeof value === 'string' ? value : '';
  }

  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

export function formatDateLabel(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString('en-MY', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

export function formatDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('en-MY', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}
