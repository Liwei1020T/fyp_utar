import type {
  AdminProfile,
  Booking,
  BookingStatus,
  BookingStatusEntry,
  PlayerProfile,
  PlayFrequency,
  PlayingStyle,
  RecommendationMatch,
  SkillLevel,
  StringItem,
} from '../types/domain';
import type {
  BackendAdminInventoryString,
  BackendAuthUser,
  BackendBooking,
  BackendBookingStatusHistory,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationPayload,
  BackendRecommendationResponse,
  BackendString,
} from '../types/backend';

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

function toFiveScale(value: number, fallback = 3) {
  return Math.max(1, Math.min(5, Math.round(value / 2) || fallback));
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
    preferredTension: profile?.preferred_tension ?? 24,
    priorities: {
      power: toTenScale(profile?.pref_attack),
      control: toTenScale(profile?.pref_control),
      durability: toTenScale(profile?.pref_durability),
      comfort: toTenScale(profile?.pref_comfort),
      sound: toTenScale(profile?.pref_sound),
    },
    homeVenue: 'Klang Valley',
    preferredAdminId: 'admin-001',
    recentGoal:
      'Use your saved profile to generate a grounded shortlist for the next restring.',
  };
}

export function mapBackendUserToAdminProfile(user: BackendAuthUser): AdminProfile {
  return {
    id: user.id,
    role: 'admin',
    name: user.username,
    email: user.phone_number,
    avatarLabel: initials(user.username),
    businessName: 'Apex String Lab',
    city: 'Kuala Lumpur',
    branchCode: 'LIVE-BACKEND',
    averageTurnaroundHours: 24,
    queueCapacity: 24,
    rating: 4.8,
    specialties: ['Booking operations', 'Inventory control', 'String setup support'],
    escalationEmail: user.phone_number,
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
  if (item.comfort >= 0.7) {
    return [22, 27];
  }
  if (item.stability_score >= 0.7 || item.durability >= 0.7) {
    return [24, 29];
  }
  return [23, 28];
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

export function mapBackendStringToStringItem(item: BackendString): StringItem {
  const strengths = deriveStrengthLabels(item);
  const category = deriveCategory(item);
  const recommendedTension = deriveRecommendedTension(item);

  return {
    id: item.id,
    brand: item.brand,
    model: item.model_name,
    category,
    gauge:
      category === 'repulsion'
        ? '0.65-0.68 mm'
        : category === 'durable'
          ? '0.68-0.70 mm'
          : '0.66-0.69 mm',
    material: 'Performance multifilament',
    price: item.price_rm ?? 0,
    recommendedTension,
    ratings: {
      power: Math.max(1, Math.round(((item.attack + item.elasticity) / 2) * 10)),
      control: Math.max(1, Math.round(item.control * 10)),
      durability: Math.max(
        1,
        Math.round(((item.durability + item.tension_retention) / 2) * 10),
      ),
      comfort: Math.max(1, Math.round(item.comfort * 10)),
      sound: Math.max(1, Math.round(item.sound * 10)),
    },
    tensionNote: `Suggested range ${recommendedTension[0]}-${recommendedTension[1]} lbs based on the current backend profile.`,
    description: `Built around ${strengths
      .slice(0, 2)
      .map((label) => label.toLowerCase())
      .join(' and ')} with a ${titleCase(category)} leaning setup.`,
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
    inventoryTags: [titleCase(category), ...strengths.slice(0, 2)],
    stockLevel: item.is_active ? 8 : 0,
    availability: item.is_active ? 'in_stock' : 'out_of_stock',
    adminNote: item.source_url ?? undefined,
  };
}

export function mapBackendInventoryStringToStringItem(
  item: BackendAdminInventoryString,
): StringItem {
  return {
    ...mapBackendStringToStringItem(item),
    stockLevel: item.stock_level,
    availability: item.availability,
    adminNote: item.admin_note ?? undefined,
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
    case 'rejected':
      return 'cancelled';
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
        title: titleCase(currentStatus),
        note: 'Booking created in the live backend.',
        at: createdAt,
      },
    ];
  }

  return entries.map((entry) => {
    const status = mapBackendStatus(entry.new_status);
    return {
      status,
      title:
        entry.old_status == null
          ? 'Booking created'
          : `Moved to ${titleCase(status)}`,
      note:
        entry.note && entry.note.trim()
          ? entry.note
          : entry.old_status == null
          ? 'Initial booking submitted through the live backend.'
          : `Status updated from ${titleCase(mapBackendStatus(entry.old_status))}.`,
      at: entry.changed_at ?? createdAt,
    };
  });
}

export function mapBackendBookingToBooking(
  booking: BackendBooking,
  priceByStringId: Map<string, number>,
  adminId = 'admin-001',
): Booking {
  const status = mapBackendStatus(booking.status);
  const dropOffDateTime = booking.drop_off_datetime
    ? new Date(booking.drop_off_datetime)
    : null;
  const stringFee = priceByStringId.get(booking.string_id) ?? 0;

  return {
    id: booking.id,
    playerId: booking.user_id,
    adminId,
    stringId: booking.string_id,
    status,
    paymentStatus: 'paid',
    racketBrand: booking.racket_brand ?? 'Unknown',
    racketModel: booking.racket_model ?? 'Unknown',
    requestedTension: booking.requested_tension ?? 24,
    dropOffDate: dropOffDateTime
      ? dropOffDateTime.toISOString().slice(0, 10)
      : booking.created_at?.slice(0, 10) ?? 'TBD',
    dropOffTime: dropOffDateTime
      ? dropOffDateTime.toISOString().slice(11, 16)
      : 'TBD',
    createdAt: booking.created_at ?? new Date().toISOString(),
    notes: booking.notes ?? undefined,
    serviceFee: 0,
    stringFee,
    totalAmount: stringFee,
    amountPaid: stringFee,
    walletUsed: 0,
    bookingToken: booking.id,
    checkInReference:
      booking.check_in_reference ?? `LIVE-${booking.id.slice(0, 8).toUpperCase()}`,
    queuePosition: 0,
    paymentRuleNote:
      'Payment flow is still mocked. This live booking only covers the core service request flow.',
    timeline: historyToTimeline(
      booking.status_history,
      status,
      booking.created_at ?? new Date().toISOString(),
    ),
  };
}

export function buildBackendProfilePayload(
  player: Pick<
    PlayerProfile,
    'skillLevel' | 'playingStyle' | 'playFrequency' | 'preferredTension' | 'priorities'
  >,
): BackendProfilePayload {
  return {
    skill_level: mapFrontendSkillLevel(player.skillLevel),
    playing_style: mapFrontendPlayingStyle(player.playingStyle),
    budget_min: 0,
    budget_max: 999,
    preferred_tension: player.preferredTension,
    game_type: 'doubles',
    frequency_per_week: mapPlayFrequencyToBackend(player.playFrequency),
    pref_attack: toFiveScale(player.priorities.power),
    pref_comfort: toFiveScale(player.priorities.comfort),
    pref_control: toFiveScale(player.priorities.control),
    pref_durability: toFiveScale(player.priorities.durability),
    pref_elasticity: toFiveScale(player.priorities.power),
    pref_sound: toFiveScale(player.priorities.sound),
    pref_string_movement: 3,
    pref_tension_retention: toFiveScale(
      Math.round((player.priorities.control + player.priorities.durability) / 2),
    ),
    pref_value_for_money: 3,
  };
}

export function buildRecommendationPayload(input: {
  userId: string;
  skillLevel: SkillLevel;
  playingStyle: PlayingStyle;
  preferredTension: number;
  playFrequency: PlayFrequency;
  priorities: PlayerProfile['priorities'];
  gameType?: string;
  budgetMin?: number;
  budgetMax?: number;
}): BackendRecommendationPayload {
  return {
    user_id: input.userId,
    skill_level: mapFrontendSkillLevel(input.skillLevel),
    playing_style: mapFrontendPlayingStyle(input.playingStyle),
    budget_min: input.budgetMin ?? 0,
    budget_max: input.budgetMax ?? 999,
    preferred_tension: input.preferredTension,
    game_type: input.gameType ?? 'doubles',
    frequency_per_week: mapPlayFrequencyToBackend(input.playFrequency),
    pref_attack: toFiveScale(input.priorities.power),
    pref_comfort: toFiveScale(input.priorities.comfort),
    pref_control: toFiveScale(input.priorities.control),
    pref_durability: toFiveScale(input.priorities.durability),
    pref_elasticity: toFiveScale(input.priorities.power),
    pref_sound: toFiveScale(input.priorities.sound),
    pref_string_movement: 3,
    pref_tension_retention: toFiveScale(
      Math.round((input.priorities.control + input.priorities.durability) / 2),
    ),
    pref_value_for_money: 3,
    top_n: 3,
  };
}

export function mapRecommendationResponse(
  response: BackendRecommendationResponse,
  strings: StringItem[],
): RecommendationMatch[] {
  return response.results.map((item) => {
    const matched =
      strings.find(
        (candidate) =>
          `${candidate.brand} ${candidate.model}`.toLowerCase() ===
          item.string_name.toLowerCase(),
      ) ??
      strings.find((candidate) => candidate.brand === item.brand);

    return {
      id: matched?.id ?? `${item.brand}-${item.rank}`,
      stringId: matched?.id ?? null,
      brand: item.brand,
      modelName: matched?.model ?? item.string_name.replace(`${item.brand} `, ''),
      stringName: item.string_name,
      price: item.price_rm ?? matched?.price ?? 0,
      matchScore: Math.round(item.score * 100),
      reasons: item.reasons,
      aspectScores: item.aspect_scores,
      suggestedTensionRange: matched
        ? `${matched.recommendedTension[0]}-${matched.recommendedTension[1]} lbs`
        : '23-28 lbs',
    };
  });
}
