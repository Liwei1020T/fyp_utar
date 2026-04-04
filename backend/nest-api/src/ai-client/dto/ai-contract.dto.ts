import { GAME_TYPES, PLAYING_STYLES, SKILL_LEVELS } from '../../common/domain';

export interface AiRecommendRequest {
  user_id?: string;
  skill_level: (typeof SKILL_LEVELS)[number];
  playing_style: (typeof PLAYING_STYLES)[number];
  budget_min: number;
  budget_max: number;
  preferred_tension: number;
  game_type: (typeof GAME_TYPES)[number];
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

export interface AiRecommendationResult {
  rank: number;
  string_name: string;
  brand: string;
  score: number;
  price_rm: number | null;
  aspect_scores: Record<string, number>;
  reasons: string[];
}

export interface AiRecommendResponse {
  algorithm_version: string;
  results: AiRecommendationResult[];
}
