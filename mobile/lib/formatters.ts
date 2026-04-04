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

export function formatMessageRole(role: ChatMessageRole) {
  return role === 'ai' ? 'AI' : role.charAt(0).toUpperCase() + role.slice(1);
}

export function formatAvailability(availability: InventoryAvailability) {
  return formatLabel(availability);
}

export function formatCurrency(amount: number) {
  return `RM ${amount.toFixed(2)}`;
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
