export interface BackendAuthUser {
  id: string;
  username: string;
  phone_number: string;
  role: string;
  auth_provider: string;
  external_auth_id: string | null;
  is_active: boolean;
}

export interface BackendAuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  phone_number: string;
  user_id: string;
  user: BackendAuthUser;
}

export interface BackendMessageResponse {
  message: string;
}

export type BackendAgentSurface =
  | 'chatbot'
  | 'recommendation_explanation'
  | 'admin_assistant';

export interface BackendAgentMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface BackendAgentQuery {
  message: string;
  context: {
    surface: BackendAgentSurface;
    run_id?: string | null;
    catalog_id?: string | null;
    booking_id?: string | null;
  };
  conversation_history?: BackendAgentMessage[];
}

export interface BackendAgentSource {
  source_type: string;
  source_id: string;
  label: string;
  version?: string | null;
}

export interface BackendAgentAction {
  action:
    | 'open_string'
    | 'open_recommendation'
    | 'open_booking'
    | 'request_human_handoff'
    | 'open_admin_booking'
    | 'open_admin_inventory'
    | 'open_admin_conversation'
    | 'open_admin_payments'
    | 'update_booking_status'
    | 'update_inventory_stock'
    | 'send_admin_message';
  label: string;
  parameters: Record<string, string>;
}

export interface BackendAgentResponse {
  answer: string;
  summary: string;
  evidence: string[];
  sources: BackendAgentSource[];
  evidence_status: 'complete' | 'partial' | 'insufficient_evidence';
  suggested_questions: string[];
  suggested_actions: BackendAgentAction[];
  handoff?: {
    recommended: boolean;
    reason?: string | null;
    booking_id?: string | null;
  } | null;
  model: string;
  response_id?: string | null;
}

export interface BackendNotificationPreferences {
  booking: boolean;
  payment: boolean;
  service: boolean;
  chat: boolean;
  recommendation: boolean;
  system: boolean;
}

export interface BackendNotificationPreferencesPayload {
  booking?: boolean;
  payment?: boolean;
  service?: boolean;
  chat?: boolean;
  recommendation?: boolean;
  system?: boolean;
}

export interface BackendPrivacySettings {
  analytics_consent: boolean;
  personalization_consent: boolean;
  marketing_consent: boolean;
}

export interface BackendDeviceToken {
  id: string;
  user_id: string;
  token_preview: string;
  platform: 'ios' | 'android' | 'web';
  device_name: string | null;
  enabled: boolean;
  last_seen_at: string;
}

export type BackendNotificationCategory =
  | 'booking'
  | 'payment'
  | 'service'
  | 'chat'
  | 'recommendation'
  | 'system';

export interface BackendNotification {
  id: string;
  user_id: string;
  category: BackendNotificationCategory;
  title: string;
  body: string;
  created_at: string;
  read: boolean;
  route: string;
}

export interface BackendMarkNotificationsReadPayload {
  event_ids: string[];
}

export interface BackendMarkNotificationsReadResponse {
  marked_count: number;
  marked_read_ids: string[];
}

export interface BackendForgotPasswordRequestResponse
  extends BackendMessageResponse {
  dev_code_preview: string | null;
}

export interface BackendProfile {
  username: string;
  skill_level: string | null;
  playing_style: string | null;
  preferred_tension: number | null;
  frequency_per_week: number | null;
  preferred_feel: 'soft' | 'medium' | 'hard' | null;
  preferred_gauge: 'no_preference' | 'thin' | 'medium' | 'thick' | null;
  recent_goal:
    | 'balanced'
    | 'power'
    | 'control'
    | 'durability'
    | 'comfort'
    | 'tension_retention'
    | 'value_for_money'
    | null;
  pref_attack: number | null;
  pref_comfort: number | null;
  pref_control: number | null;
  pref_durability: number | null;
  pref_elasticity: number | null;
  pref_sound: number | null;
  pref_string_movement: number | null;
  pref_tension_retention: number | null;
  pref_value_for_money: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface BackendCatalogTag {
  tag_key: string;
  tag_label: string;
  tag_count: number;
}

export interface BackendOfficialPerformance {
  catalog_id: string;
  source_type: string | null;
  source_name: string | null;
  source_url: string | null;
  source_region: string | null;
  category: number | null;
  feature: number | null;
  feel: number | null;
  repulsion_power: number | null;
  durability: number | null;
  hitting_sound: number | null;
  shock_absorption: number | null;
  control: number | null;
  notes: string | null;
  status: string;
  updated_at: string | null;
}

export interface BackendString {
  id: string;
  brand: string;
  brand_code: string;
  display_name: string;
  model_name: string;
  normalized_name: string;
  price_rm: number | null;
  available_stock: number;
  availability_status: BackendInventoryAvailability;
  series_key: string | null;
  series_label: string | null;
  is_hybrid: boolean;
  gauge_main_mm: number | null;
  gauge_cross_mm: number | null;
  gauge_label: string | null;
  category: string | null;
  main_trait: string | null;
  tension_min_lbs: number | null;
  tension_max_lbs: number | null;
  material_summary_en: string | null;
  image_url: string | null;
  color_options_en: string[];
  short_description: string;
  full_description: string;
  official_performance_status: string;
  source_item_id: string | null;
  source_url: string | null;
  source_language: string | null;
  original_name: string | null;
  original_brand_label: string | null;
  original_series: string | null;
  original_material: string | null;
  original_color: string | null;
  community_rating: number | null;
  want_count: number;
  used_count: number;
  review_count: number;
  tags: BackendCatalogTag[];
  aspect_scores: Record<string, number>;
  attack: number;
  comfort: number;
  control: number;
  durability: number;
  elasticity: number;
  sound: number;
  string_movement: number;
  tension_retention: number;
  value_for_money: number;
  beginner_fit_score: number;
  attacking_fit_score: number;
  control_fit_score: number;
  stability_score: number;
  all_round_score: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export type BackendInventoryAvailability = 'in_stock' | 'low_stock' | 'out_of_stock';
export type BackendPricingMode = 'fixed_price' | 'quoted_at_shop' | 'price_pending';

export interface BackendAdminInventoryString extends BackendString {
  stock_level: number;
  current_stock: number;
  reserved_stock: number;
  available_stock: number;
  reorder_level: number;
  reorder_quantity: number;
  cost_price: number | null;
  selling_price: number | null;
  pricing_mode: BackendPricingMode;
  availability_status: BackendInventoryAvailability;
  availability: BackendInventoryAvailability;
  admin_note: string | null;
}

export interface BackendStringWritePayload {
  brand: string;
  model_name: string;
  price_rm?: number | null;
  display_name?: string | null;
  series_key?: string | null;
  series_label?: string | null;
  is_hybrid?: boolean | null;
  gauge_main_mm?: number | null;
  gauge_cross_mm?: number | null;
  gauge_label?: string | null;
  category?: string | null;
  main_trait?: string | null;
  tension_min_lbs?: number | null;
  tension_max_lbs?: number | null;
  material_summary_en?: string | null;
  image_url?: string | null;
  color_options_en?: string[] | null;
  short_description?: string | null;
  full_description?: string | null;
  source_language?: string | null;
  original_name?: string | null;
  original_brand_label?: string | null;
  original_series?: string | null;
  original_material?: string | null;
  original_color?: string | null;
  is_active?: boolean | null;
}

export interface BackendOfficialPerformancePayload {
  source_type?: string | null;
  source_name?: string | null;
  source_url?: string | null;
  source_region?: string | null;
  category?: number | null;
  feature?: number | null;
  feel?: number | null;
  repulsion_power?: number | null;
  durability?: number | null;
  hitting_sound?: number | null;
  shock_absorption?: number | null;
  control?: number | null;
  notes?: string | null;
  status?: string | null;
}

export interface BackendInventoryUpdatePayload {
  price_rm?: number | null;
  stock_level?: number | null;
  current_stock?: number | null;
  reserved_stock?: number | null;
  reorder_level?: number | null;
  reorder_quantity?: number | null;
  cost_price?: number | null;
  selling_price?: number | null;
  pricing_mode?: BackendPricingMode | null;
  availability_status?: BackendInventoryAvailability | null;
  is_active?: boolean | null;
  admin_note?: string | null;
  movement_type?: string | null;
  reference_type?: string | null;
  reference_id?: string | null;
}

export interface BackendStringEditorUpdatePayload {
  catalog?: BackendStringWritePayload;
  inventory?: BackendInventoryUpdatePayload;
  official_performance?: BackendOfficialPerformancePayload;
}

export interface BackendStoreBusinessHoursDay {
  day:
    | 'Monday'
    | 'Tuesday'
    | 'Wednesday'
    | 'Thursday'
    | 'Friday'
    | 'Saturday'
    | 'Sunday';
  is_open: boolean;
  open_time: string;
  close_time: string;
  break_start: string | null;
  break_end: string | null;
  slot_duration_minutes: number;
  max_bookings_per_slot: number;
}

export interface BackendStoreBusinessHours {
  id: string;
  days: BackendStoreBusinessHoursDay[];
  special_closed_dates: string[];
  updated_at: string | null;
}

export interface BackendStoreBusinessHoursPayload {
  days: BackendStoreBusinessHoursDay[];
  special_closed_dates: string[];
}

export interface BackendSlot {
  id: string;
  date: string;
  time: string;
  capacity: number;
  booked_count: number;
  available_spots: number;
  label: string;
  day_label: string;
}

export interface BackendBookingStatusHistory {
  old_status: string | null;
  new_status: string;
  changed_by_user_id: string | null;
  changed_by_phone_number: string | null;
  note: string | null;
  changed_at: string | null;
}

export interface BackendBookingUpdate {
  id: string;
  booking_id: string;
  author_user_id: string;
  author_role: string;
  author_phone_number: string | null;
  comment: string | null;
  photo_url: string | null;
  photo_original_name: string | null;
  photo_content_type: string | null;
  photo_type: 'racket' | 'service_progress' | 'other' | null;
  created_at: string | null;
}

export interface BackendBooking {
  id: string;
  order_code: string;
  user_id: string;
  string_id: string;
  string_name: string;
  racket_id: string | null;
  customer_phone_number: string | null;
  customer_username: string | null;
  racket_brand: string | null;
  racket_model: string | null;
  requested_tension: number | null;
  slot_id: string | null;
  drop_off_datetime: string | null;
  expected_completion_datetime: string | null;
  collection_datetime: string | null;
  notes: string | null;
  service_method: 'counter_dropoff' | 'pickup_request';
  cancellation_reason: string | null;
  completion_summary: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  check_in_reference: string;
  latest_admin_note: string | null;
  status_history: BackendBookingStatusHistory[] | null;
  updates: BackendBookingUpdate[] | null;
}

export type BackendConversationState =
  | 'waiting_admin'
  | 'admin_joined'
  | 'resolved'
  | 'closed';

export interface BackendSendConversationMessagePayload {
  body: string;
}

export interface BackendBookingConversationMessage {
  id: string;
  author_user_id: string;
  author_role: string;
  body: string;
  created_at: string | null;
}

export interface BackendBookingConversation {
  id: string;
  booking_id: string | null;
  player_id: string;
  state: BackendConversationState;
  support_requested_at: string;
  player_last_read_at: string | null;
  admin_last_read_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  messages: BackendBookingConversationMessage[];
}

export interface BackendCreateRacketPayload {
  nickname: string;
  model_key?: string | null;
  brand: string;
  model: string;
  weight_class?: string | null;
  balance_point?: string | null;
  grip_size?: string | null;
  preferred_use?: string | null;
  notes?: string | null;
}

export interface BackendUpdateRacketPayload {
  nickname?: string;
  model_key?: string | null;
  brand?: string;
  model?: string;
  weight_class?: string | null;
  balance_point?: string | null;
  grip_size?: string | null;
  preferred_use?: string | null;
  notes?: string | null;
}

export interface BackendRacket {
  id: string;
  user_id: string;
  nickname: string;
  model_key: string | null;
  brand: string;
  model: string;
  weight_class: string | null;
  balance_point: string | null;
  grip_size: string | null;
  preferred_use: string | null;
  notes: string | null;
  service_count?: number;
  current_string_id?: string | null;
  current_tension?: number | null;
  last_serviced_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendRacketModelOption {
  key: string;
  brand: string;
  model: string;
}

export type BackendFeedbackSentimentTag =
  | 'crisp_feel'
  | 'good_communication'
  | 'fast_turnaround'
  | 'would_book_again';

export interface BackendCreateFeedbackPayload {
  rating: number;
  recommendation_relevance?: number | null;
  string_satisfaction?: number | null;
  tension_satisfaction?: number | null;
  comfort?: number | null;
  control?: number | null;
  repulsion?: number | null;
  durability?: number | null;
  would_use_again?: boolean | null;
  comment?: string | null;
  string_feedback?: string | null;
  service_feedback?: string | null;
  sentiment_tags?: BackendFeedbackSentimentTag[];
}

export type BackendUpdateFeedbackPayload = Partial<BackendCreateFeedbackPayload>;

export interface BackendFeedbackEligibility {
  durability_available_at: string | null;
  can_rate_durability: boolean;
}

export interface BackendFeedback {
  id: string;
  booking_id: string;
  user_id: string;
  rating: number;
  recommendation_relevance: number | null;
  string_satisfaction: number | null;
  tension_satisfaction: number | null;
  comfort: number | null;
  control: number | null;
  repulsion: number | null;
  durability: number | null;
  durability_available_at: string | null;
  can_rate_durability: boolean;
  durability_rated_at: string | null;
  structured_field_confirmed_at: Record<string, string>;
  would_use_again: boolean | null;
  comment: string | null;
  string_feedback: string | null;
  service_feedback: string | null;
  sentiment_tags: BackendFeedbackSentimentTag[];
  created_at: string;
  updated_at: string;
}

export interface BackendRacketServiceHistory {
  booking_id: string;
  string_id: string;
  string_name: string;
  requested_tension: number | null;
  serviced_at: string;
  feedback: BackendFeedback | null;
}

export interface BackendRacketDetail extends BackendRacket {
  service_history: BackendRacketServiceHistory[];
}

export interface BackendCheckInLookupResponse {
  matched_by: 'booking_id' | 'check_in_reference' | 'qr_token';
  booking: BackendBooking;
}

export interface BackendCheckInToken {
  token: string;
  expires_at: string;
  status: 'active' | 'used' | 'expired' | 'revoked';
}

export interface BackendCheckInRequest {
  booking_id?: string | null;
  reference?: string | null;
  note?: string | null;
}

export interface BackendPayment {
  id: string;
  booking_id: string | null;
  user_id: string;
  method:
    | 'card'
    | 'online_banking'
    | 'e_wallet'
    | 'qr_transfer'
    | 'cash'
    | 'wallet_balance';
  status: 'pending' | 'paid' | 'failed' | 'cancelled';
  amount: number;
  type: 'booking_payment' | 'wallet_top_up';
  reference: string;
  note: string | null;
  proof_url: string | null;
  created_at: string;
}

export interface BackendBookingPaymentQuote {
  booking_id: string;
  string_fee: number;
  service_fee: number;
  total_amount: number;
  wallet_balance: number;
  active_payment: BackendPayment | null;
}

export interface BackendWalletTransaction {
  id: string;
  user_id: string;
  type: 'top_up' | 'booking_payment';
  direction: 'credit' | 'debit';
  status: 'completed';
  amount: number;
  description: string;
  created_at: string;
  related_booking_id: string | null;
  method_label: string | null;
}

export interface BackendWallet {
  user_id: string;
  available_balance: number;
  pending_top_up: number;
  lifetime_top_ups: number;
  transactions: BackendWalletTransaction[];
}

export interface BackendServiceQueueItem {
  queue_position: number;
  booking: BackendBooking;
}

export interface BackendServiceQueueLane {
  status: string;
  title: string;
  items: BackendServiceQueueItem[];
}

export interface BackendServiceQueue {
  generated_at: string;
  lanes: BackendServiceQueueLane[];
}

export interface BackendStoreSettings {
  id: string;
  store_name: string;
  store_contact: string;
  support_text: string;
  payment_notes: string;
  payment_qr_url: string | null;
  booking_notes: string;
  store_policy_text: string;
  address: string;
  trending_string_ids: string[];
  default_service_price: number;
  notification_settings: Record<
    string,
    { enabled?: boolean; title?: string; body?: string }
  >;
  updated_at: string | null;
}

export interface BackendStoreSettingsPayload {
  store_name: string;
  store_contact: string;
  support_text: string;
  payment_notes: string;
  booking_notes: string;
  store_policy_text: string;
  address: string;
  trending_string_ids: string[];
  default_service_price: number;
  notification_settings: Record<
    string,
    { enabled?: boolean; title?: string; body?: string }
  >;
}

export interface BackendAnalyticsWorkloadEntry {
  label: string;
  value: number;
}

export interface BackendAnalyticsSummary {
  weekly_bookings: number;
  today_bookings: number;
  pending_payment_count: number;
  awaiting_dropoff_count: number;
  in_progress_count: number;
  ready_for_collection_count: number;
  completed_today: number;
  low_stock_count: number;
  unread_chats: number;
  today_revenue: number;
  repeat_customer_count: number;
  pending_feedback_count: number;
  average_feedback_score: number | null;
  average_completion_hours: number | null;
  tension_distribution: Record<string, number>;
  busy_slots: string[];
  popular_string_ids: string[];
  workload_mix: BackendAnalyticsWorkloadEntry[];
}

export interface BackendAdminFeedback extends BackendFeedback {
  order_code: string;
  string_id: string;
  string_name: string;
  customer_username: string;
  customer_phone_number: string;
}

export interface BackendCommunityFeatureSummary {
  score: number;
  distinct_users: number;
  booking_count: number;
  confidence: number;
  weight: number;
  evidence_scope: 'global_string' | 'exact_racket_model';
  source_version: string;
}

export interface BackendCommunityStringSummary {
  string_id: string;
  features: Record<string, BackendCommunityFeatureSummary>;
}

export interface BackendCommunitySummary {
  policy_version: string;
  snapshot_version: string;
  racket_model_key: string | null;
  strings: BackendCommunityStringSummary[];
}

export interface BackendAdminCommunitySummary {
  global: BackendCommunitySummary;
  racket_contexts: BackendCommunitySummary[];
}

export interface BackendAdminNotification {
  id: string;
  user_id: string;
  customer_username: string;
  customer_phone_number: string;
  token_preview: string | null;
  category: BackendNotificationCategory;
  title: string;
  body: string;
  route: string | null;
  status: string;
  provider_message: string | null;
  attempts: number;
  created_at: string;
  last_attempt_at: string | null;
}

export interface BackendAdminDeviceToken extends BackendDeviceToken {
  customer_username: string;
  customer_phone_number: string;
}

export interface BackendPopularString {
  string_id: string;
  brand: string;
  model_name: string;
  booking_count: number;
}

export interface BackendPage<T> {
  items: T[];
  total: number;
  limit: number | null;
  offset: number;
}

export interface BackendRecommendationResult {
  rank: number;
  catalog_id?: string | null;
  string_name: string;
  brand: string;
  model_name?: string | null;
  score: number;
  price_rm: number | null;
  aspect_scores: Record<string, number>;
  reasons: string[];
  score_breakdown?: BackendRecommendationScoreBreakdown | null;
  rationale_payload?: BackendRecommendationRationale | null;
  generated_at?: string | null;
}

export interface BackendRecommendationResponse {
  algorithm_version: string;
  results: BackendRecommendationResult[];
  run_id?: string | null;
  generated_at?: string | null;
}

export interface BackendRecommendationDetailResponse {
  algorithm_version: string;
  result: BackendRecommendationResult;
  run_id?: string | null;
  generated_at?: string | null;
}

export interface BackendRecommendationRunItem {
  id: string;
  catalog_id: string;
  rank_position: number;
  final_score: number;
  preference_match_score?: number | null;
  rule_fit_score?: number | null;
  value_for_money_score?: number | null;
  nlp_review_score?: number | null;
  score_breakdown: Record<string, unknown>;
  rationale: Record<string, unknown>;
}

export interface BackendRecommendationRun {
  id: string;
  user_id?: string | null;
  phone_number?: string | null;
  username?: string | null;
  algorithm_version: string;
  request_snapshot: Record<string, unknown>;
  profile_snapshot: Record<string, unknown>;
  generated_at?: string | null;
  items: BackendRecommendationRunItem[];
}

export interface BackendRecommendationScoreBreakdown {
  preference_match?: number;
  rule_fit?: number;
  value_for_money?: number;
  nlp_review_score?: number;
  final_score?: number;
}

export interface BackendRecommendationRationale {
  score_breakdown?: BackendRecommendationScoreBreakdown;
  algorithm_family?: string;
  collaborative_filtering_used?: boolean;
  community_calibration_used?: boolean;
  community_snapshot_version?: string | null;
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
    baseline_score?: number | null;
    community_score?: number | null;
    community_distinct_users?: number | null;
    community_booking_count?: number | null;
    community_confidence?: number | null;
    community_weight?: number | null;
    community_evidence_scope?: string | null;
    community_racket_model_key?: string | null;
    community_source_version?: string | null;
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

export interface BackendProfilePayload {
  username?: string;
  skill_level?: string;
  playing_style?: string;
  preferred_tension?: number;
  frequency_per_week?: number;
  preferred_feel?: 'soft' | 'medium' | 'hard';
  preferred_gauge?: 'no_preference' | 'thin' | 'medium' | 'thick';
  recent_goal?:
    | 'balanced'
    | 'power'
    | 'control'
    | 'durability'
    | 'comfort'
    | 'tension_retention'
    | 'value_for_money';
  pref_attack?: number;
  pref_comfort?: number;
  pref_control?: number;
  pref_durability?: number;
  pref_elasticity?: number;
  pref_sound?: number;
  pref_string_movement?: number;
  pref_tension_retention?: number;
  pref_value_for_money?: number;
}
