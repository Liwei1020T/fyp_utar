import type {
  AdminProfile,
  Booking,
  BookingFeedback,
  BookingStatus,
  BookingStatusEntry,
  BookingUpdate,
  BookingSlot,
  BusinessHours,
  ChatConversation,
  NotificationItem,
  Payment,
  PlayerProfile,
  PlayFrequency,
  PlayingStyle,
  PreferredFeel,
  PreferredGauge,
  RecentGoal,
  RecommendationMatch,
  RecommendationScoreBreakdown,
  RacketPassport,
  SkillLevel,
  StringItem,
  WalletBalance,
  WalletTransaction,
} from '../types/domain';
import type {
  BackendAdminInventoryString,
  BackendAuthUser,
  BackendBooking,
  BackendBookingConversation,
  BackendBookingStatusHistory,
  BackendBookingUpdate,
  BackendInventoryAvailability,
  BackendFeedback,
  BackendNotification,
  BackendOfficialPerformance,
  BackendPayment,
  BackendPricingMode,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationResponse,
  BackendRacket,
  BackendRacketDetail,
  BackendString,
  BackendSlot,
  BackendStoreBusinessHours,
  BackendWallet,
  BackendWalletTransaction,
} from '../types/backend';
import {
  formatBookingOrderCode,
  formatConversationMode,
  formatLocalDateInputValue,
  formatLocalTimeValue,
} from '../lib/formatters';
import {
  deriveAvailabilityStatus,
  derivePriceStatus,
  formatGaugeRange,
  formatTensionRange,
  sanitizePerformanceScores,
} from '../lib/inventory';
import { resolveBackendMediaUrl } from './backendApi';

function titleCase(value: string) {
  return value
    .split(/[_-\s]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

function initials(value: string) {
  const parts = value
    .split(' ')
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 2);
  return (parts.length > 0 ? parts : [value])
    .map((item) => item[0] ?? '')
    .join('')
    .toUpperCase();
}

function toTenScale(value: number | null | undefined, fallback = 6) {
  if (value == null) {
    return fallback;
  }
  return Math.max(1, Math.min(10, Math.round(value * 2)));
}

function toTenPreference(value: number, fallback = 5) {
  return Math.max(1, Math.min(10, Math.round(value) || fallback));
}

function mapBackendPreference(value: number | null | undefined, fallback = 6) {
  if (value == null) {
    return fallback;
  }
  return Math.max(1, Math.min(10, Math.round(value)));
}

export function deriveAdvancedPreferences(
  priorities: PlayerProfile['priorities'],
): PlayerProfile['advancedPreferences'] {
  return {
    elasticity: derivedElasticityPreference(priorities),
    tensionRetention: derivedTensionRetentionPreference(priorities),
    stringMovement: derivedStringMovementPreference(priorities),
  };
}

function advancedPreferencesForPayload(
  player: Pick<PlayerProfile, 'priorities'> &
    Partial<Pick<PlayerProfile, 'advancedPreferences'>>,
) {
  return player.advancedPreferences ?? deriveAdvancedPreferences(player.priorities);
}

function derivedElasticityPreference(priorities: PlayerProfile['priorities']) {
  return toTenPreference(Math.round((priorities.power + priorities.sound) / 2));
}

function derivedStringMovementPreference(
  priorities: PlayerProfile['priorities'],
) {
  return toTenPreference(Math.round((priorities.control + priorities.comfort) / 2));
}

function derivedTensionRetentionPreference(
  priorities: PlayerProfile['priorities'],
) {
  return toTenPreference(
    Math.round((priorities.control + priorities.durability) / 2),
  );
}

export function mapBackendSkillLevel(
  value: string | null | undefined,
): SkillLevel {
  switch (value) {
    case 'beginner':
      return 'Beginner';
    case 'advanced':
      return 'Advanced';
    case 'competitive':
      return 'Competitive';
    case 'intermediate':
    default:
      return 'Intermediate';
  }
}

function mapFrontendSkillLevel(
  value: SkillLevel,
): 'beginner' | 'intermediate' | 'advanced' {
  switch (value) {
    case 'Beginner':
      return 'beginner';
    case 'Advanced':
    case 'Competitive':
      return 'advanced';
    case 'Intermediate':
    default:
      return 'intermediate';
  }
}

export function mapBackendPlayingStyle(
  value: string | null | undefined,
): PlayingStyle {
  switch (value) {
    case 'attacking':
      return 'Attacking';
    case 'control_defensive':
      return 'Control';
    case 'balanced':
    default:
      return 'Balanced';
  }
}

export function mapFrontendPlayingStyle(
  value: PlayingStyle,
): 'attacking' | 'balanced' | 'control_defensive' {
  switch (value) {
    case 'Attacking':
      return 'attacking';
    case 'Balanced':
      return 'balanced';
    case 'Control':
    case 'Defensive':
    default:
      return 'control_defensive';
  }
}

export function mapFrequencyToPlayFrequency(
  value: number | null | undefined,
): PlayFrequency {
  if (value == null || value <= 1) {
    return 'Social';
  }
  if (value <= 3) {
    return 'Weekly';
  }
  return 'Tournament';
}

export function mapPlayFrequencyToBackend(value: PlayFrequency): number {
  switch (value) {
    case 'Social':
      return 1;
    case 'Tournament':
      return 5;
    case 'Weekly':
    default:
      return 3;
  }
}

function mapPreferredFeelToBackend(value: PreferredFeel) {
  return value.toLowerCase() as 'soft' | 'medium' | 'hard';
}

export function mapBackendPreferredFeel(profile?: BackendProfile | null): PreferredFeel {
  if (profile?.preferred_feel === 'soft') {
    return 'Soft';
  }
  if (profile?.preferred_feel === 'hard') {
    return 'Hard';
  }
  return 'Medium';
}

function mapPreferredGaugeToBackend(value: PreferredGauge) {
  return value.toLowerCase().replace(' ', '_') as
    | 'no_preference'
    | 'thin'
    | 'medium'
    | 'thick';
}

function mapBackendPreferredGauge(
  value: BackendProfile['preferred_gauge'] | undefined,
): PreferredGauge {
  if (value === 'thin') return 'Thin';
  if (value === 'medium') return 'Medium';
  if (value === 'thick') return 'Thick';
  return 'No preference';
}

const recentGoalToBackend = {
  'Balanced setup': 'balanced',
  'More power': 'power',
  'Better control': 'control',
  'More durability': 'durability',
  'More comfort': 'comfort',
  'Hold tension longer': 'tension_retention',
  'Better value': 'value_for_money',
} as const;

function mapBackendRecentGoal(value?: BackendProfile['recent_goal']): RecentGoal {
  const match = Object.entries(recentGoalToBackend).find(
    ([, backendValue]) => backendValue === value,
  );
  return (match?.[0] as RecentGoal | undefined) ?? 'Balanced setup';
}

export function mapBackendUserToPlayerProfile(
  user: BackendAuthUser,
  profile?: BackendProfile | null,
): PlayerProfile {
  return {
    id: user.id,
    role: 'player',
    name: user.username,
    email: user.phone_number,
    avatarLabel: initials(user.username),
    phone: user.phone_number,
    skillLevel: mapBackendSkillLevel(profile?.skill_level),
    playingStyle: mapBackendPlayingStyle(profile?.playing_style),
    playFrequency: mapFrequencyToPlayFrequency(profile?.frequency_per_week),
    preferredFeel: mapBackendPreferredFeel(profile),
    preferredGauge: mapBackendPreferredGauge(profile?.preferred_gauge),
    preferredTension: profile?.preferred_tension ?? 24,
    priorities: {
      power: mapBackendPreference(profile?.pref_attack),
      control: mapBackendPreference(profile?.pref_control),
      durability: mapBackendPreference(profile?.pref_durability),
      comfort: mapBackendPreference(profile?.pref_comfort),
      sound: mapBackendPreference(profile?.pref_sound),
      value: mapBackendPreference(profile?.pref_value_for_money),
    },
    advancedPreferences: {
      elasticity: mapBackendPreference(profile?.pref_elasticity),
      tensionRetention: mapBackendPreference(profile?.pref_tension_retention),
      stringMovement: mapBackendPreference(profile?.pref_string_movement),
    },
    homeVenue: 'Klang Valley',
    preferredAdminId: 'main',
    recentGoal: mapBackendRecentGoal(profile?.recent_goal),
  };
}

export function mapBackendUserToAdminProfile(user: BackendAuthUser): AdminProfile {
  return {
    id: user.id,
    role: 'admin',
    name: user.username,
    email: user.phone_number,
    avatarLabel: initials(user.username),
  };
}

function deriveCategory(item: BackendString): StringItem['category'] {
  const ranked = [
    ['repulsion', item.attack + item.elasticity] as const,
    ['control', item.control] as const,
    ['durable', item.durability + item.tension_retention] as const,
    ['balanced', item.all_round_score] as const,
  ].sort((left, right) => right[1] - left[1]);
  return ranked[0]?.[0] ?? 'balanced';
}

function deriveRecommendedTension(item: BackendString): [number, number] {
  let derived: [number, number];
  if (item.comfort >= 0.7) {
    derived = [22, 27];
  } else if (item.stability_score >= 0.7 || item.durability >= 0.7) {
    derived = [24, 29];
  } else {
    derived = [23, 28];
  }

  return [
    item.tension_min_lbs ?? derived[0],
    item.tension_max_lbs ?? derived[1],
  ];
}

function deriveStrengthLabels(item: BackendString) {
  return [
    ['Power', item.attack + item.elasticity] as const,
    ['Control', item.control] as const,
    ['Durability', item.durability] as const,
    ['Comfort', item.comfort] as const,
    ['Sound', item.sound] as const,
  ]
    .sort((left, right) => right[1] - left[1])
    .map(([label]) => label);
}

function normalizeCategory(item: BackendString): StringItem['category'] {
  const rawCategory = item.category?.trim().toLowerCase();
  if (
    rawCategory === 'repulsion' ||
    rawCategory === 'balanced' ||
    rawCategory === 'control' ||
    rawCategory === 'durable'
  ) {
    return rawCategory;
  }
  const normalizedTags = item.tags
    .map((tag) => tag.tag_key.trim().toLowerCase())
    .filter(Boolean);

  if (normalizedTags.includes('control')) {
    return 'control';
  }
  if (normalizedTags.includes('durability') || normalizedTags.includes('durable')) {
    return 'durable';
  }
  if (normalizedTags.includes('repulsion') || normalizedTags.includes('attack')) {
    return 'repulsion';
  }
  return deriveCategory(item);
}

function deriveGaugeBounds(
  item: BackendString,
  category: StringItem['category'],
) {
  if (item.gauge_main_mm != null || item.gauge_cross_mm != null) {
    return {
      min: item.gauge_main_mm ?? item.gauge_cross_mm ?? null,
      max: item.gauge_cross_mm ?? item.gauge_main_mm ?? null,
    };
  }

  switch (category) {
    case 'repulsion':
      return { min: 0.65, max: 0.68 };
    case 'durable':
      return { min: 0.68, max: 0.7 };
    case 'control':
      return { min: 0.65, max: 0.67 };
    case 'balanced':
    default:
      return { min: 0.66, max: 0.69 };
  }
}

function deriveMainTrait(
  item: BackendString,
  category: StringItem['category'],
  strengths: string[],
) {
  if (item.main_trait?.trim()) {
    return item.main_trait.trim();
  }
  const highlightedTag = item.tags
    .map((tag) => tag.tag_label?.trim())
    .find((value) =>
      value != null && ['Repulsion', 'Control', 'Durability', 'Balanced'].includes(value),
    );
  if (highlightedTag) {
    return highlightedTag;
  }

  switch (category) {
    case 'repulsion':
      return 'Repulsion';
    case 'control':
      return 'Control';
    case 'durable':
      return 'Durable';
    case 'balanced':
    default:
      return strengths[0] ?? 'Balanced';
  }
}

function mapBackendPricingModeToPriceStatus(
  pricingMode: BackendPricingMode | null | undefined,
  price: number | null | undefined,
) {
  switch (pricingMode) {
    case 'fixed_price':
      return price == null ? 'pending' : 'priced';
    case 'quoted_at_shop':
      return 'quoted_at_shop';
    case 'price_pending':
      return 'pending';
    default:
      return derivePriceStatus(price);
  }
}

function resolveAvailabilityStatus(
  value: BackendInventoryAvailability | null | undefined,
  fallbackStock: number,
) {
  return value ?? deriveAvailabilityStatus(fallbackStock);
}

function deriveMaterial(item: BackendString) {
  return item.material_summary_en?.trim() || 'Performance multifilament';
}

function deriveScores(item: BackendString) {
  return sanitizePerformanceScores(
    {
      power: Math.round(((item.attack + item.elasticity) / 2) * 10),
      control: Math.round(item.control * 10),
      durability: Math.round(((item.durability + item.tension_retention) / 2) * 10),
      comfort: Math.round(item.comfort * 10),
      sound: Math.round(item.sound * 10),
    },
    {
      power: 6,
      control: 6,
      durability: 6,
      comfort: 6,
      sound: 6,
    },
  );
}

export function mapOfficialPerformanceToPerformanceScores(
  official: BackendOfficialPerformance | null | undefined,
  fallback: StringItem['ratings'],
) {
  if (!official) {
    return fallback;
  }

  return sanitizePerformanceScores(
    {
      power: official.repulsion_power ?? fallback.power,
      control: official.control ?? fallback.control,
      durability: official.durability ?? fallback.durability,
      comfort: official.shock_absorption ?? fallback.comfort,
      sound: official.hitting_sound ?? fallback.sound,
    },
    fallback,
  );
}

export function mapBackendStringToStringItem(item: BackendString): StringItem {
  const strengths = deriveStrengthLabels(item);
  const category = normalizeCategory(item);
  const recommendedTension = deriveRecommendedTension(item);
  const gaugeBounds = deriveGaugeBounds(item, category);
  const ratings = deriveScores(item);
  const mainTrait = deriveMainTrait(item, category, strengths);
  const tensionMinLbs = item.tension_min_lbs;
  const tensionMaxLbs = item.tension_max_lbs;
  const gauge = formatGaugeRange(gaugeBounds.min, gaugeBounds.max);
  const priceStatus = derivePriceStatus(item.price_rm);
  const stockQty = Math.max(0, item.available_stock);
  const availability = deriveAvailabilityStatus(
    stockQty,
    item.availability_status,
  );
  const imageUrl = resolveBackendMediaUrl(item.image_url);
  const catalog = {
    id: item.id,
    brand: item.brand,
    modelName: item.model_name,
    localizedName: item.original_name ?? undefined,
    isHybrid: item.is_hybrid,
    gaugeMinMm: gaugeBounds.min,
    gaugeMaxMm: gaugeBounds.max,
    material: deriveMaterial(item),
    description:
      item.full_description?.trim()
      || item.short_description?.trim()
      || `Built around ${strengths
        .slice(0, 2)
        .map((label) => label.toLowerCase())
        .join(' and ')} with a ${titleCase(category)} leaning setup.`,
    mainTrait,
    category,
    tensionMinLbs,
    tensionMaxLbs,
    performanceScores: ratings,
    imageUrl,
    isActive: item.is_active,
    createdAt: item.created_at ?? undefined,
    updatedAt: item.updated_at ?? undefined,
  };
  const inventory = {
    id: item.id,
    stringId: item.id,
    stockQty,
    price: item.price_rm ?? null,
    priceStatus,
    availabilityStatus: availability,
    shopNote: undefined,
    updatedAt: item.updated_at ?? undefined,
  };

  return {
    id: item.id,
    brand: item.brand,
    model: item.model_name,
    localizedName: catalog.localizedName,
    category,
    mainTrait,
    gauge,
    gaugeMinMm: gaugeBounds.min,
    gaugeMaxMm: gaugeBounds.max,
    material: catalog.material,
    price: item.price_rm ?? 0,
    priceStatus,
    recommendedTension,
    tensionMinLbs: catalog.tensionMinLbs,
    tensionMaxLbs: catalog.tensionMaxLbs,
    ratings,
    tensionNote:
      tensionMinLbs != null || tensionMaxLbs != null
        ? `Recorded catalog range: ${formatTensionRange(tensionMinLbs, tensionMaxLbs)}.`
        : 'No catalog tension range is recorded for this string.',
    description: catalog.description,
    imageUrl,
    isActive: catalog.isActive,
    createdAt: catalog.createdAt,
    updatedAt: catalog.updatedAt,
    inventoryUpdatedAt: inventory.updatedAt,
    bestFor: [
      category === 'repulsion'
        ? 'Players chasing faster rebound'
        : category === 'control'
          ? 'Players prioritizing placement'
          : category === 'durable'
            ? 'Players restringing less often'
            : 'Players wanting an all-round setup',
      item.price_rm != null && item.price_rm <= 60
        ? 'Value-conscious setups'
        : 'Premium restring sessions',
    ],
    strengths: strengths.slice(0, 3).map((label) => `${label}-focused response`),
    tradeOffs: strengths
      .slice(-2)
      .map((label) => `Lower emphasis on ${label.toLowerCase()} than the top-matched options.`),
    reviewHighlight: `Current rules engine highlights ${strengths[0].toLowerCase()} as the lead fit.`,
    inventoryTags: [titleCase(mainTrait), titleCase(category), ...strengths.slice(0, 1)],
    stockLevel: inventory.stockQty,
    availability,
    adminNote: inventory.shopNote,
    catalog,
    inventory,
  };
}

export function mapBackendInventoryStringToStringItem(
  item: BackendAdminInventoryString,
): StringItem {
  const mapped = mapBackendStringToStringItem(item);
  const availability = resolveAvailabilityStatus(
    item.availability_status ?? item.availability,
    item.stock_level,
  );
  const resolvedPrice = item.selling_price ?? item.price_rm;
  const priceStatus = mapBackendPricingModeToPriceStatus(item.pricing_mode, resolvedPrice);
  const inventory = {
    ...mapped.inventory,
    id: mapped.inventory.id,
    stockQty: item.stock_level,
    price: resolvedPrice ?? null,
    priceStatus,
    availabilityStatus: availability,
    shopNote: item.admin_note ?? undefined,
    updatedAt: item.updated_at ?? undefined,
  };

  return {
    ...mapped,
    price: inventory.price ?? 0,
    priceStatus,
    stockLevel: inventory.stockQty,
    availability,
    adminNote: inventory.shopNote,
    inventoryUpdatedAt: inventory.updatedAt,
    inventory,
  };
}

export function mapBackendBusinessHoursToBusinessHours(
  item: BackendStoreBusinessHours,
  adminId: string,
): BusinessHours {
  return {
    adminId,
    days: item.days.map((day) => ({
      day: day.day,
      isOpen: day.is_open,
      openTime: day.open_time,
      closeTime: day.close_time,
      breakStart: day.break_start ?? undefined,
      breakEnd: day.break_end ?? undefined,
      slotDurationMinutes: day.slot_duration_minutes,
      maxBookingsPerSlot: day.max_bookings_per_slot,
    })),
    specialClosedDates: item.special_closed_dates,
  };
}

export function mapBusinessHoursToBackendPayload(item: BusinessHours) {
  return {
    days: item.days.map((day) => ({
      day: day.day,
      is_open: day.isOpen,
      open_time: day.openTime,
      close_time: day.closeTime,
      break_start: day.breakStart ?? null,
      break_end: day.breakEnd ?? null,
      slot_duration_minutes: day.slotDurationMinutes,
      max_bookings_per_slot: day.maxBookingsPerSlot,
    })),
    special_closed_dates: item.specialClosedDates,
  };
}

export function mapBackendSlotToBookingSlot(
  item: BackendSlot,
  adminId: string,
): BookingSlot {
  return {
    id: item.id,
    adminId,
    date: item.date,
    time: item.time,
    capacity: item.capacity,
    availableSpots: item.available_spots,
    label: item.label,
    dayLabel: item.day_label,
  };
}

function mapBackendStatus(value: string): BookingStatus {
  switch (value) {
    case 'awaiting_dropoff':
    case 'pending':
    case 'confirmed':
      return 'awaiting_dropoff';
    case 'in_progress':
      return 'in_progress';
    case 'ready_for_collection':
    case 'ready_for_pickup':
      return 'ready_for_collection';
    case 'completed':
    case 'picked_up':
      return 'completed';
    case 'cancelled':
      return 'cancelled';
    case 'rejected':
      return 'rejected';
    default:
      return 'awaiting_dropoff';
  }
}

function historyToTimeline(
  entries: BackendBookingStatusHistory[] | null,
  currentStatus: BookingStatus,
  createdAt: string,
): BookingStatusEntry[] {
  if (!entries || entries.length === 0) {
    return [
      {
        status: currentStatus,
        title: 'Booking created',
        note: 'Initial booking submitted through the live backend.',
        at: createdAt,
      },
    ];
  }

  return entries.map((entry, index) => {
    const status = mapBackendStatus(entry.new_status);
    const isInitialEntry = index === 0;
    return {
      status,
      title: isInitialEntry ? 'Booking created' : `Moved to ${titleCase(status)}`,
      note:
        entry.note && entry.note.trim()
          ? entry.note
          : isInitialEntry
          ? 'Initial booking submitted through the live backend.'
          : 'Service status updated by the shop.',
      at: entry.changed_at ?? createdAt,
    };
  });
}

function mapBackendBookingUpdateToBookingUpdate(
  item: BackendBookingUpdate,
): BookingUpdate {
  return {
    id: item.id,
    bookingId: item.booking_id,
    authorUserId: item.author_user_id,
    authorRole: item.author_role === 'admin' ? 'admin' : 'player',
    authorPhoneNumber: item.author_phone_number ?? undefined,
    comment: item.comment ?? undefined,
    photoUrl: resolveBackendMediaUrl(item.photo_url),
    photoOriginalName: item.photo_original_name ?? undefined,
    photoContentType: item.photo_content_type ?? undefined,
    photoType: item.photo_type ?? undefined,
    createdAt: item.created_at ?? new Date().toISOString(),
  };
}

export function mapBackendBookingToBooking(
  booking: BackendBooking,
  adminId = 'main',
): Booking {
  const status = mapBackendStatus(booking.status);
  const slotMatch = booking.slot_id?.match(
    /^slot-(\d{4}-\d{2}-\d{2})-(\d{2}:\d{2})$/,
  );
  const slotDate = slotMatch?.[1];
  const slotTime = slotMatch?.[2];
  const dropOffDateTime = booking.drop_off_datetime
    ? new Date(booking.drop_off_datetime)
    : null;

  return {
    id: booking.id,
    orderCode: booking.order_code,
    playerId: booking.user_id,
    adminId,
    stringId: booking.string_id,
    status,
    paymentStatus: 'unpaid',
    racketId: booking.racket_id ?? undefined,
    racketBrand: booking.racket_brand ?? 'Unknown',
    racketModel: booking.racket_model ?? 'Unknown',
    requestedTension: booking.requested_tension ?? 24,
    customerName: booking.customer_username ?? undefined,
    customerPhone: booking.customer_phone_number ?? undefined,
    dropOffDate:
      slotDate
      ?? (dropOffDateTime
        ? formatLocalDateInputValue(dropOffDateTime)
        : booking.created_at?.slice(0, 10) ?? 'TBD'),
    dropOffTime:
      slotTime ?? (dropOffDateTime ? formatLocalTimeValue(dropOffDateTime) : 'TBD'),
    expectedCompletionAt: booking.expected_completion_datetime ?? undefined,
    collectionAt: booking.collection_datetime ?? undefined,
    createdAt: booking.created_at ?? new Date().toISOString(),
    notes: booking.notes ?? undefined,
    serviceMethod: booking.service_method,
    cancellationReason: booking.cancellation_reason ?? undefined,
    completionSummary: booking.completion_summary ?? undefined,
    stringFee: 0,
    totalAmount: 0,
    amountPaid: 0,
    walletUsed: 0,
    bookingToken: booking.id,
    checkInReference: booking.check_in_reference,
    queuePosition: 0,
    paymentRuleNote:
      'Payment status and totals come from the server payment quote and ledger.',
    timeline: historyToTimeline(
      booking.status_history,
      status,
      booking.created_at ?? new Date().toISOString(),
    ),
    updates: (booking.updates ?? []).map(mapBackendBookingUpdateToBookingUpdate),
  };
}

export function mapBackendNotificationToNotification(
  notification: BackendNotification,
): NotificationItem {
  return {
    id: notification.id,
    userId: notification.user_id,
    category: notification.category,
    title: notification.title,
    body: notification.body,
    createdAt: notification.created_at,
    read: notification.read,
    route: notification.route,
  };
}

export function mapBackendConversationToConversation(
  conversation: BackendBookingConversation,
  booking?: Booking,
  adminId?: string,
): ChatConversation {
  const updatedAt =
    conversation.updated_at ??
    conversation.created_at ??
    conversation.support_requested_at;
  const messages = conversation.messages.map((message) => {
    const isAdmin = message.author_role === 'admin';
    return {
      id: message.id,
      role: isAdmin ? 'admin' : 'user',
      senderName:
        isAdmin
          ? 'Shop admin'
          : booking?.customerName ?? 'Player',
      body: message.body,
      sentAt: message.created_at ?? updatedAt,
    } satisfies ChatConversation['messages'][number];
  });
  const isGeneralSupport = conversation.booking_id == null;

  return {
    id: conversation.id,
    playerId: conversation.player_id,
    adminId: booking?.adminId ?? adminId,
    bookingId: conversation.booking_id ?? undefined,
    stringId: booking?.stringId,
    title: isGeneralSupport
      ? 'General support'
      : `Booking ${booking?.orderCode ?? formatBookingOrderCode(conversation.booking_id ?? '')}`,
    mode: conversation.state,
    statusLabel: formatConversationMode(conversation.state),
    summary:
      messages.at(-1)?.body ??
      (isGeneralSupport
        ? 'General support requested.'
        : 'Support requested for this booking.'),
    updatedAt,
    quickPrompts: [
      'Can you confirm my drop-off time?',
      'I need to update my service note.',
      'When will my racket be ready?',
    ],
    messages,
  };
}

export function mapBackendFeedbackToBookingFeedback(
  feedback: BackendFeedback,
): BookingFeedback {
  return {
    id: feedback.id,
    bookingId: feedback.booking_id,
    userId: feedback.user_id,
    rating: feedback.rating,
    recommendationRelevance: feedback.recommendation_relevance ?? undefined,
    stringSatisfaction: feedback.string_satisfaction ?? undefined,
    tensionSatisfaction: feedback.tension_satisfaction ?? undefined,
    comfort: feedback.comfort ?? undefined,
    control: feedback.control ?? undefined,
    repulsion: feedback.repulsion ?? undefined,
    wouldUseAgain: feedback.would_use_again ?? undefined,
    comment: feedback.comment ?? undefined,
    stringFeedback: feedback.string_feedback ?? undefined,
    serviceFeedback: feedback.service_feedback ?? undefined,
    createdAt: feedback.created_at,
    updatedAt: feedback.updated_at,
  };
}

export function mapBackendRacketToRacketPassport(
  racket: BackendRacket | BackendRacketDetail,
): RacketPassport {
  const serviceHistory =
    'service_history' in racket ? racket.service_history : [];
  const stringHistory = serviceHistory.map((entry) => {
    const feedback = entry.feedback
      ? mapBackendFeedbackToBookingFeedback(entry.feedback)
      : undefined;
    return {
      bookingId: entry.booking_id,
      stringId: entry.string_id,
      stringName: entry.string_name,
      tension: entry.requested_tension ?? 0,
      installedAt: entry.serviced_at,
      feelRating: feedback ? feedback.rating * 2 : 0,
      feedback,
    };
  });
  const summaryTension = racket.current_tension ?? undefined;
  const tensions = serviceHistory.flatMap((entry) =>
    entry.requested_tension == null ? [] : [entry.requested_tension],
  );
  if (tensions.length === 0 && summaryTension != null) {
    tensions.push(summaryTension);
  }
  const preferredRange: [number, number] =
    tensions.length > 0
      ? [Math.min(...tensions), Math.max(...tensions)]
      : [0, 0];
  const currentService = serviceHistory[0];

  return {
    id: racket.id,
    playerId: racket.user_id,
    nickname: racket.nickname,
    modelKey: racket.model_key,
    brand: racket.brand,
    model: racket.model,
    weightClass: racket.weight_class ?? 'Not recorded',
    balancePoint: racket.balance_point ?? 'Not recorded',
    gripSize: racket.grip_size ?? 'Not recorded',
    preferredUse: racket.preferred_use ?? 'Not recorded',
    notes: racket.notes ?? '',
    serviceCount: racket.service_count ?? serviceHistory.length,
    currentStringId:
      currentService?.string_id ?? racket.current_string_id ?? '',
    currentTension: currentService?.requested_tension ?? summaryTension ?? 0,
    preferredRange,
    lastServicedAt:
      currentService?.serviced_at ?? racket.last_serviced_at ?? racket.updated_at,
    stringHistory,
  };
}

export function mapBackendPaymentToPayment(
  payment: BackendPayment,
): Payment {
  return {
    id: payment.id,
    bookingId: payment.booking_id ?? undefined,
    playerId: payment.user_id,
    method: payment.method,
    status: payment.status,
    amount: payment.amount,
    type: payment.type,
    createdAt: payment.created_at,
    reference: payment.reference,
    note: payment.note ?? undefined,
    proofUrl: resolveBackendMediaUrl(payment.proof_url),
  };
}

export function mapBackendWalletTransaction(
  transaction: BackendWalletTransaction,
): WalletTransaction {
  return {
    id: transaction.id,
    userId: transaction.user_id,
    type: transaction.type,
    direction: transaction.direction,
    status: transaction.status,
    amount: transaction.amount,
    description: transaction.description,
    createdAt: transaction.created_at,
    relatedBookingId: transaction.related_booking_id ?? undefined,
    methodLabel: transaction.method_label ?? undefined,
  };
}

export function mapBackendWallet(wallet: BackendWallet): {
  balance: WalletBalance;
  transactions: WalletTransaction[];
} {
  return {
    balance: {
      userId: wallet.user_id,
      availableBalance: wallet.available_balance,
      pendingTopUp: wallet.pending_top_up,
      lifetimeTopUps: wallet.lifetime_top_ups,
    },
    transactions: wallet.transactions.map(mapBackendWalletTransaction),
  };
}

export function buildBackendProfilePayload(
  player: Pick<
    PlayerProfile,
    | 'skillLevel'
    | 'name'
    | 'playingStyle'
    | 'playFrequency'
    | 'preferredTension'
    | 'preferredFeel'
    | 'preferredGauge'
    | 'recentGoal'
    | 'priorities'
  > &
    Partial<Pick<PlayerProfile, 'advancedPreferences'>>,
): BackendProfilePayload {
  const advanced = advancedPreferencesForPayload(player);

  return {
    username: player.name,
    skill_level: mapFrontendSkillLevel(player.skillLevel),
    playing_style: mapFrontendPlayingStyle(player.playingStyle),
    preferred_tension: player.preferredTension,
    frequency_per_week: mapPlayFrequencyToBackend(player.playFrequency),
    preferred_feel: mapPreferredFeelToBackend(player.preferredFeel ?? 'Medium'),
    preferred_gauge: mapPreferredGaugeToBackend(player.preferredGauge),
    recent_goal: recentGoalToBackend[player.recentGoal],
    pref_attack: toTenPreference(player.priorities.power),
    pref_comfort: toTenPreference(player.priorities.comfort),
    pref_control: toTenPreference(player.priorities.control),
    pref_durability: toTenPreference(player.priorities.durability),
    pref_elasticity: toTenPreference(advanced.elasticity),
    pref_sound: toTenPreference(player.priorities.sound),
    pref_string_movement: toTenPreference(advanced.stringMovement),
    pref_tension_retention: toTenPreference(advanced.tensionRetention),
    pref_value_for_money: toTenPreference(player.priorities.value),
  };
}

export function mapRecommendationResponse(
  response: BackendRecommendationResponse,
  strings: StringItem[],
): RecommendationMatch[] {
  return response.results.map((item) => {
    const matched =
      strings.find((candidate) => candidate.id === item.catalog_id) ??
      strings.find(
        (candidate) =>
          `${candidate.brand} ${candidate.model}`.toLowerCase() ===
          item.string_name.toLowerCase(),
      ) ??
      strings.find((candidate) => candidate.brand === item.brand);
    const catalogId = item.catalog_id ?? matched?.id ?? null;

    return {
      id: catalogId ?? `${item.brand}-${item.rank}`,
      stringId: matched?.id ?? catalogId,
      catalogId,
      brand: item.brand,
      modelName:
        matched?.model ??
        item.model_name ??
        item.string_name.replace(`${item.brand} `, ''),
      stringName: item.string_name,
      price: item.price_rm ?? matched?.inventory.price ?? null,
      matchScore: Math.round(item.score * 100),
      reasons: item.reasons,
      aspectScores: item.aspect_scores,
      scoreBreakdown: mapRecommendationScoreBreakdown(item.score_breakdown),
      rationalePayload: item.rationale_payload ?? null,
      fitAngle: item.rationale_payload?.primary_fit_angle,
      tradeOffSummary: item.rationale_payload?.trade_off_summary,
      algorithmVersion: response.algorithm_version,
      runId: response.run_id ?? null,
      generatedAt: item.generated_at ?? response.generated_at ?? null,
      suggestedTensionRange: matched
        ? formatTensionRange(
            matched.tensionMinLbs,
            matched.tensionMaxLbs,
            'Tension guidance unavailable',
          )
        : 'Tension guidance unavailable',
    };
  });
}

function mapRecommendationScoreBreakdown(
  value: BackendRecommendationResponse['results'][number]['score_breakdown'],
): RecommendationScoreBreakdown | undefined {
  if (!value) {
    return undefined;
  }
  return {
    preferenceMatch: value.preference_match,
    ruleFit: value.rule_fit,
    valueForMoney: value.value_for_money,
    nlpReviewScore: value.nlp_review_score,
    personalHistoryScore: value.personal_history_score,
    personalHistoryWeight: value.personal_history_weight,
    personalizedBaseScore: value.personalized_base_score,
    finalScore: value.final_score,
  };
}
