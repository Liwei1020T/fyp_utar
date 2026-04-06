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

export interface BackendString {
  id: string;
  brand: string;
  model_name: string;
  normalized_name: string;
  price_rm: number | null;
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
  stability_score: number;
  all_round_score: number;
  source_item_id: string | null;
  source_url: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export type BackendInventoryAvailability =
  | 'in_stock'
  | 'low_stock'
  | 'out_of_stock';

export interface BackendAdminInventoryString extends BackendString {
  stock_level: number;
  availability: BackendInventoryAvailability;
  admin_note: string | null;
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

export interface BackendBooking {
  id: string;
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
  string_name: string;
  brand: string;
  score: number;
  price_rm: number | null;
  aspect_scores: Record<string, number>;
  reasons: string[];
}

export interface BackendRecommendationResponse {
  algorithm_version: string;
  results: BackendRecommendationResult[];
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
