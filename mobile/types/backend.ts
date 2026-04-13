export interface BackendAuthUser {
  id: string;
  username: string;
  phone_number: string;
  role: string;
  auth_provider: string;
  external_auth_id: string | null;
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

export interface BackendForgotPasswordRequestResponse
  extends BackendMessageResponse {
  dev_code_preview: string | null;
}

export interface BackendProfile {
  skill_level: string | null;
  playing_style: string | null;
  budget_min: number | null;
  budget_max: number | null;
  preferred_tension: number | null;
  game_type: string | null;
  frequency_per_week: number | null;
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
  order_code?: string | null;
  user_id: string;
  string_id: string;
  string_name: string;
  customer_phone_number: string | null;
  customer_username: string | null;
  racket_brand: string | null;
  racket_model: string | null;
  requested_tension: number | null;
  drop_off_datetime: string | null;
  notes: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  check_in_reference?: string | null;
  latest_admin_note: string | null;
  status_history: BackendBookingStatusHistory[] | null;
  updates: BackendBookingUpdate[] | null;
}

export interface BackendCheckInLookupResponse {
  matched_by: 'booking_id' | 'check_in_reference';
  booking: BackendBooking;
}

export interface BackendCheckInRequest {
  booking_id?: string | null;
  reference?: string | null;
  note?: string | null;
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
  booking_notes: string;
  store_policy_text: string;
  address: string;
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
}

export interface BackendAnalyticsWorkloadEntry {
  label: string;
  value: number;
}

export interface BackendAnalyticsSummary {
  weekly_bookings: number;
  pending_payment_count: number;
  awaiting_dropoff_count: number;
  in_progress_count: number;
  ready_for_collection_count: number;
  completed_today: number;
  low_stock_count: number;
  unread_chats: number;
  today_revenue: number;
  busy_slots: string[];
  popular_string_ids: string[];
  workload_mix: BackendAnalyticsWorkloadEntry[];
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
  generated_at?: string | null;
}

export interface BackendRecommendationDetailResponse {
  algorithm_version: string;
  result: BackendRecommendationResult;
  generated_at?: string | null;
}

export interface BackendRecommendationScoreBreakdown {
  preference_match?: number;
  rule_fit?: number;
  budget_fit?: number;
  nlp_review_score?: number;
  final_score?: number;
}

export interface BackendRecommendationRationale {
  score_breakdown?: BackendRecommendationScoreBreakdown;
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
    budget_min?: number;
    budget_max?: number;
  };
  rule_events?: Array<{
    rule?: string;
    delta?: number;
    reason?: string;
  }>;
  profile_context?: Record<string, string | number | null>;
  top_reasons?: string[];
}

export interface BackendProfilePayload {
  skill_level?: string;
  playing_style?: string;
  budget_min?: number;
  budget_max?: number;
  preferred_tension?: number;
  game_type?: string;
  frequency_per_week?: number;
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

export interface BackendRecommendationPayload {
  user_id: string;
  skill_level: string;
  playing_style: string;
  budget_min: number;
  budget_max: number;
  preferred_tension: number;
  game_type: string;
  frequency_per_week: number;
  pref_attack: number;
  pref_comfort: number;
  pref_control: number;
  pref_durability: number;
  pref_elasticity: number;
  pref_sound: number;
  pref_string_movement: number;
  pref_tension_retention: number;
  pref_value_for_money: number;
  top_n?: number;
}
