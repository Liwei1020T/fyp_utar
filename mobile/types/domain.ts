export type UserRole = 'player' | 'admin';

export type SkillLevel = 'Beginner' | 'Intermediate' | 'Advanced' | 'Competitive';
export type PlayingStyle = 'Attacking' | 'Balanced' | 'Control' | 'Defensive';
export type PlayFrequency = 'Social' | 'Weekly' | 'Tournament';
export type BudgetRange = 'Below RM30' | 'RM30–RM50' | 'RM50+';
export type PreferredFeel = 'Soft' | 'Balanced' | 'Crisp' | 'Hard';
export type PriorityKey = 'power' | 'control' | 'durability' | 'comfort' | 'sound';
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
  budgetRange: BudgetRange;
  preferredFeel: PreferredFeel;
  preferredTension: number;
  priorities: Record<PriorityKey, number>;
  advancedPreferences: Record<AdvancedPreferenceKey, number>;
  homeVenue: string;
  preferredAdminId: string;
  recentGoal: string;
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
  | 'card'
  | 'online_banking'
  | 'e_wallet'
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
  serviceFee: number;
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
  generatedAt?: string | null;
  suggestedTensionRange: string;
}

export interface RecommendationScoreBreakdown {
  preferenceMatch?: number;
  ruleFit?: number;
  budgetFit?: number;
  nlpReviewScore?: number;
  confidenceScore?: number;
  finalScore?: number;
}

export interface RecommendationRationalePayload {
  score_breakdown?: {
    preference_match?: number;
    rule_fit?: number;
    budget_fit?: number;
    confidence_score?: number;
    nlp_review_score?: number;
    final_score?: number;
  };
  algorithm_family?: string;
  collaborative_filtering_used?: boolean;
  matrix_version?: string | null;
  feature_source_version?: string | null;
  feature_source_generated_at?: string | null;
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
    nlp_confidence?: number | null;
    nlp_influence?: number | null;
    fusion_confidence?: number | null;
    source_version?: string | null;
    source_generated_at?: string | null;
    source_ref?: string | null;
    review_count_snapshot?: number | null;
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
  budget?: {
    price_rm?: number | null;
    budget_tier?: 'below_30' | 'between_30_50' | 'above_50';
    item_price_tier?: 'low' | 'mid' | 'high' | 'unknown';
    budget_tier_bounds_rm?: {
      min_rm?: number;
      max_rm?: number;
    };
  };
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

export type FeedbackSentimentTag =
  | 'crisp_feel'
  | 'good_communication'
  | 'fast_turnaround'
  | 'would_book_again';

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
  durability?: number;
  wouldUseAgain?: boolean;
  comment?: string;
  stringFeedback?: string;
  serviceFeedback?: string;
  sentimentTags: FeedbackSentimentTag[];
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
  durabilityNote: string;
  feedback?: BookingFeedback;
}

export interface RacketPassport {
  id: string;
  playerId: string;
  nickname: string;
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

export interface AdminSettings {
  adminId: string;
  storeName: string;
  storeContact: string;
  supportText: string;
  paymentNotes: string;
  bookingNotes: string;
  storePolicyText: string;
  address: string;
  trendingStringIds: string[];
  defaultServicePrice: number;
  notificationSettings: Record<
    string,
    { enabled?: boolean; title?: string; body?: string }
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
