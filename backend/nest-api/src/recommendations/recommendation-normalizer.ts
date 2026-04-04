import { BadRequestException } from '@nestjs/common';
import { AiRecommendRequest } from '../ai-client/dto/ai-contract.dto';

type RecommendationInput = Partial<AiRecommendRequest>;

export function normalizeRecommendationInput(
  input: RecommendationInput,
): AiRecommendRequest {
  const budgetMin = input.budget_min ?? 0;
  const budgetMax = input.budget_max ?? budgetMin;
  if (budgetMin > budgetMax) {
    throw new BadRequestException('budget_min must be less than or equal to budget_max');
  }

  const requiredFields: Array<keyof AiRecommendRequest> = [
    'skill_level',
    'playing_style',
    'preferred_tension',
    'game_type',
    'frequency_per_week',
    'pref_attack',
    'pref_comfort',
    'pref_control',
    'pref_durability',
    'pref_elasticity',
    'pref_sound',
    'pref_string_movement',
    'pref_tension_retention',
    'pref_value_for_money',
  ];

  for (const field of requiredFields) {
    if (input[field] === undefined || input[field] === null) {
      throw new BadRequestException(`${field} is required for recommendation`);
    }
  }

  return {
    user_id: input.user_id,
    skill_level: input.skill_level!,
    playing_style: input.playing_style!,
    budget_min: budgetMin,
    budget_max: budgetMax,
    preferred_tension: input.preferred_tension!,
    game_type: input.game_type!,
    frequency_per_week: input.frequency_per_week!,
    pref_attack: input.pref_attack!,
    pref_comfort: input.pref_comfort!,
    pref_control: input.pref_control!,
    pref_durability: input.pref_durability!,
    pref_elasticity: input.pref_elasticity!,
    pref_sound: input.pref_sound!,
    pref_string_movement: input.pref_string_movement!,
    pref_tension_retention: input.pref_tension_retention!,
    pref_value_for_money: input.pref_value_for_money!,
    top_n: input.top_n ?? 5,
  };
}
