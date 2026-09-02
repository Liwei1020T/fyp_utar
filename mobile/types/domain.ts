export type UserRole = 'player' | 'admin';

export type SkillLevel = 'Beginner' | 'Intermediate' | 'Advanced' | 'Competitive';
export type PlayingStyle = 'Attacking' | 'Balanced' | 'Control' | 'Defensive';
export type PlayFrequency = 'Social' | 'Weekly' | 'Tournament';
export type PreferredFeel = 'Soft' | 'Medium' | 'Hard';
export type PreferredGauge = 'No preference' | 'Thin' | 'Medium' | 'Thick';
export type RecentGoal =
  | 'Balanced setup'
  | 'More power'
  | 'Better control'
  | 'More durability'
  | 'More comfort'
  | 'Hold tension longer'
  | 'Better value';
export type PriorityKey =
  | 'power'
  | 'control'
  | 'durability'
  | 'comfort'
  | 'sound'
  | 'value';
export type AdvancedPreferenceKey =
  | 'elasticity'
  | 'tensionRetention'
  | 'stringMovement';
export type StringCategory = 'repulsion' | 'balanced' | 'control' | 'durable';
export type InventoryPriceStatus = 'priced' | 'pending' | 'quoted_at_shop';

export interface UserIdentity {
  id: string;
  role: UserRole;
  name: string;
  email: string;
  avatarLabel: string;
}

export interface PlayerProfile extends UserIdentity {
  role: 'player';
  phone: string;
  skillLevel: SkillLevel;
  playingStyle: PlayingStyle;
  playFrequency: PlayFrequency;
  preferredFeel: PreferredFeel;
  preferredGauge: PreferredGauge;
  preferredTension: number;
  priorities: Record<PriorityKey, number>;
  advancedPreferences: Record<AdvancedPreferenceKey, number>;
  homeVenue: string;
  preferredAdminId: string;
  recentGoal: RecentGoal;
}

export interface AdminProfile extends UserIdentity {
  role: 'admin';
}

export type AppUser = PlayerProfile | AdminProfile;

export type InventoryAvailability = 'in_stock' | 'low_stock' | 'out_of_stock';

export interface StringPerformanceScores {
  power: number;
  control: number;
  durability: number;
  comfort: number;
  sound: number;
}

export interface StringCatalogRecord {
  id: string;
  brand: string;
  modelName: string;
  localizedName?: string;
  isHybrid: boolean;
  gaugeMinMm: number | null;
  gaugeMaxMm: number | null;
  material: string;
  description: string;
  mainTrait: string;
  category: StringCategory;
  tensionMinLbs: number | null;
  tensionMaxLbs: number | null;
  performanceScores: StringPerformanceScores;
  imageUrl?: string;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface VendorInventoryRecord {
  id: string;
  vendorId?: string;
  stringId: string;
  stockQty: number;
  price: number | null;
  priceStatus: InventoryPriceStatus;
  availabilityStatus: InventoryAvailability;
  shopNote?: string;
  updatedAt?: string;
}

export interface StringItem {
  id: string;
  brand: string;
  model: string;
  localizedName?: string;
  category: StringCategory;
  mainTrait: string;
  gauge: string;
  gaugeMinMm: number | null;
  gaugeMaxMm: number | null;
  material: string;
  price: number;
  priceStatus: InventoryPriceStatus;
  recommendedTension: [number, number];
  tensionMinLbs: number | null;
  tensionMaxLbs: number | null;
  ratings: StringPerformanceScores;
  tensionNote: string;
  description: string;
  imageUrl?: string;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
  inventoryUpdatedAt?: string;
  bestFor: string[];
  strengths: string[];
  tradeOffs: string[];
  reviewHighlight: string;
  inventoryTags: string[];
  stockLevel: number;
  availability: InventoryAvailability;
  adminNote?: string;
  catalog: StringCatalogRecord;
  inventory: VendorInventoryRecord;
}

export type BookingStatus =
  | 'pending'
  | 'pending_payment'
  | 'confirmed'
  | 'awaiting_dropoff'
  | 'in_progress'
  | 'ready_for_collection'
  | 'completed'
  | 'cancelled'
  | 'rejected';

export type PaymentStatus =
  | 'unpaid'
  | 'pending'
  | 'paid'
  | 'failed'
  | 'cancelled';

export type PaymentMethod =
  | 'qr_transfer'
  | 'cash'
  | 'wallet_balance';

export interface BookingStatusEntry {
  status: BookingStatus;
  title: string;
  note: string;
  at: string;
}

export interface BookingUpdate {
  id: string;
  bookingId: string;
  authorUserId: string;
  authorRole: UserRole;
  authorPhoneNumber?: string;
  comment?: string;
  photoUrl?: string;
  photoOriginalName?: string;
  photoContentType?: string;
  photoType?: 'racket' | 'service_progress' | 'other';
  createdAt: string;
}

export interface Booking {
  id: string;
  orderCode?: string;
  playerId: string;
  adminId: string;
  stringId: string;
  status: BookingStatus;
  paymentStatus: PaymentStatus;
  racketId?: string;
  racketBrand: string;
  racketModel: string;
  requestedTension: number;
  customerName?: string;
  customerPhone?: string;
  dropOffDate: string;
  dropOffTime: string;
  expectedCompletionAt?: string;
  collectionAt?: string;
  createdAt: string;
  notes?: string;
  serviceMethod: 'counter_dropoff' | 'pickup_request';
  cancellationReason?: string;
  completionSummary?: string;
  stringFee: number;
  totalAmount: number;
  amountPaid: number;
  walletUsed: number;
  bookingToken: string;
  checkInReference: string;
  queuePosition: number;
  paymentRuleNote: string;
  timeline: BookingStatusEntry[];
  updates: BookingUpdate[];
}

export interface RecommendationMatch {
  id: string;
  stringId: string | null;
  catalogId: string | null;
  stringName: string;
  brand: string;
  modelName: string;
  price: number | null;
  matchScore: number;
  reasons: string[];
  aspectScores: Record<string, number>;
  scoreBreakdown?: RecommendationScoreBreakdown;
  rationalePayload?: RecommendationRationalePayload | null;
  fitAngle?: string;
  tradeOffSummary?: string;
  algorithmVersion?: string;
  runId?: string | null;
  generatedAt?: string | null;
  suggestedTensionRange: string;
}

export interface RecommendationScoreBreakdown {
  preferenceMatch?: number;
  ruleFit?: number;
  valueForMoney?: number;
  nlpReviewScore?: number;
  personalHistoryScore?: number;
  personalHistoryWeight?: number;
  personalizedBaseScore?: number;
  finalScore?: number;
}

export interface PersonalHistoryEvidence {
  mode?: string;
  normalized_score?: number | null;
  feedback_count?: number;
  string_satisfaction?: number | null;
  would_use_again_ratio?: number | null;
  confidence?: number;
  weight?: number;
  evidence_scope?: string | null;
  racket_id?: string | null;
  racket_model_key?: string | null;
  source_version?: string | null;
  snapshot_version?: string | null;
  base_score?: number;
  final_score?: number;
}

export interface RecommendationRationalePayload {
  score_breakdown?: {
    preference_match?: number;
    rule_fit?: number;
    value_for_money?: number;
    nlp_review_score?: number;
    personal_history_score?: number;
    personal_history_weight?: number;
    personalized_base_score?: number;
    final_score?: number;
  };
  algorithm_family?: string;
  collaborative_filtering_used?: boolean;
  personal_history_used?: boolean;
  feedback_calibration_used?: boolean;
  feedback_snapshot_version?: string | null;
  personal_history_snapshot_version?: string | null;
  personal_history?: PersonalHistoryEvidence | null;
  racket_context?: Record<string, string | number | null> | null;
  cf_shadow?: Record<string, string | number | boolean | null>;
  primary_fit_angle?: string;
  trade_off_summary?: string;
  feature_sources?: Record<string, string>;
  feature_evidence?: Array<{
    feature_key?: string;
    display_label?: string;
    effective_score?: number | null;
    preference_weight?: number | null;
    source?: string;
    official_score?: number | null;
    nlp_review_score?: number | null;
    nlp_influence?: number | null;
    feedback_score?: number | null;
    feedback_booking_count?: number | null;
    feedback_weight?: number | null;
    feedback_evidence_scope?: string | null;
  }>;
  effective_feature_scores?: Record<string, number>;
  fused_feature_scores?: Record<string, number>;
  nlp_review_scores?: Record<string, number>;
  nlp_review_signal_count?: number;
  nlp_review_summary?: string | null;
  auxiliary_scores?: Record<string, number>;
  user_preference_vector?: Array<{
    feature_key?: string;
    raw_score?: number | null;
    preference_weight?: number | null;
  }>;
  price_rm?: number | null;
  rule_events?: Array<{
    rule?: string;
    delta?: number;
    reason?: string;
  }>;
  profile_context?: Record<string, string | number | null>;
  top_reasons?: string[];
}

export interface Payment {
  id: string;
  bookingId?: string;
  playerId: string;
  adminId?: string;
  method: PaymentMethod;
  status: PaymentStatus;
  amount: number;
  type: 'booking_payment' | 'wallet_top_up';
  createdAt: string;
  reference: string;
  note?: string;
  proofUrl?: string;
}

export type ChatMessageRole = 'user' | 'ai' | 'admin' | 'system';

export type ConversationMode =
  | 'ai_only'
  | 'waiting_admin'
  | 'admin_joined'
  | 'resolved'
  | 'closed';

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  senderName: string;
  body: string;
  sentAt: string;
}

export interface ChatConversation {
  id: string;
  playerId: string;
  adminId?: string;
  bookingId?: string;
  stringId?: string;
  title: string;
  mode: ConversationMode;
  statusLabel: string;
  summary: string;
  updatedAt: string;
  quickPrompts: string[];
  messages: ChatMessage[];
}

export type NotificationCategory =
  | 'booking'
  | 'payment'
  | 'service'
  | 'chat'
  | 'recommendation'
  | 'system';

export interface NotificationItem {
  id: string;
  userId: string;
  category: NotificationCategory;
  title: string;
  body: string;
  createdAt: string;
  read: boolean;
  route: string;
}

export interface BookingFeedback {
  id: string;
  bookingId: string;
  userId: string;
  rating: number;
  recommendationRelevance?: number;
  stringSatisfaction?: number;
  tensionSatisfaction?: number;
  comfort?: number;
  control?: number;
  repulsion?: number;
  wouldUseAgain?: boolean;
  comment?: string;
  stringFeedback?: string;
  serviceFeedback?: string;
  createdAt: string;
  updatedAt: string;
}

export interface RacketStringLog {
  bookingId: string;
  stringId: string;
  stringName?: string;
  tension: number;
  installedAt: string;
  feelRating: number;
  feedback?: BookingFeedback;
}

export interface RacketPassport {
  id: string;
  playerId: string;
  nickname: string;
  modelKey: string | null;
  brand: string;
  model: string;
  weightClass: string;
  balancePoint: string;
  gripSize: string;
  preferredUse: string;
  notes: string;
  serviceCount: number;
  currentStringId: string;
  currentTension: number;
  preferredRange: [number, number];
  lastServicedAt: string;
  stringHistory: RacketStringLog[];
}

export interface BusinessHoursDay {
  day: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
  isOpen: boolean;
  openTime: string;
  closeTime: string;
  breakStart?: string;
  breakEnd?: string;
  slotDurationMinutes: number;
  maxBookingsPerSlot: number;
}

export interface BusinessHours {
  adminId: string;
  days: BusinessHoursDay[];
  specialClosedDates: string[];
}

export interface BookingSlot {
  id: string;
  adminId: string;
  date: string;
  time: string;
  capacity: number;
  availableSpots: number;
  label: string;
  dayLabel: string;
}

export interface AdminAnalyticsSummary {
  adminId: string;
  weeklyBookings: number;
  pendingPaymentCount: number;
  awaitingDropoffCount: number;
  inProgressCount: number;
  readyForCollectionCount: number;
  completedToday: number;
  lowStockCount: number;
  unreadChats: number;
  todayRevenue: number;
  repeatCustomerCount: number;
  pendingFeedbackCount: number;
  averageFeedbackScore?: number;
  averageCompletionHours?: number;
  tensionDistribution: Record<string, number>;
  busySlots: string[];
  popularStringIds: string[];
  workloadMix: Array<{ label: string; value: number }>;
}

export interface WalletBalance {
  userId: string;
  availableBalance: number;
  pendingTopUp: number;
  lifetimeTopUps: number;
}

export interface WalletTransaction {
  id: string;
  userId: string;
  type: 'top_up' | 'booking_payment' | 'refund' | 'adjustment';
  direction: 'credit' | 'debit';
  status: 'completed' | 'pending' | 'failed';
  amount: number;
  description: string;
  createdAt: string;
  relatedBookingId?: string;
  methodLabel?: string;
}

export interface NotificationPreferences {
  userId: string;
  booking: boolean;
  payment: boolean;
  service: boolean;
  chat: boolean;
  recommendation: boolean;
  system: boolean;
}

export interface StoreSettings {
  storeName: string;
  storeContact: string;
  supportText: string;
  paymentNotes: string;
  paymentQrUrl?: string;
  bookingNotes: string;
  storePolicyText: string;
  address: string;
  trendingStringIds: string[];
  notificationSettings: Record<
    string,
    { enabled?: boolean }
  >;
}

export interface BookingDraft {
  stringId: string;
  adminId: string;
  racketId?: string | null;
  racketBrand: string;
  racketModel: string;
  requestedTension: number;
  notes: string;
  serviceMethod: 'counter_dropoff' | 'pickup_request';
  slotId: string;
  dropOffDate: string;
  dropOffTime: string;
  photoUri?: string;
  photoName?: string;
  photoContentType?: string;
  saveRacket?: boolean;
}
