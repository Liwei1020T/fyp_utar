import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsIn, IsInt, IsNumber, IsOptional, Max, Min } from 'class-validator';
import { GAME_TYPES, PLAYING_STYLES, SKILL_LEVELS } from '../../common/domain';

export class GenerateRecommendationDto {
  @ApiPropertyOptional({ enum: SKILL_LEVELS, example: 'intermediate' })
  @IsOptional()
  @IsIn(SKILL_LEVELS)
  skill_level?: string;

  @ApiPropertyOptional({ enum: PLAYING_STYLES, example: 'attacking' })
  @IsOptional()
  @IsIn(PLAYING_STYLES)
  playing_style?: string;

  @ApiPropertyOptional({ example: 40, minimum: 0, maximum: 999 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(999)
  budget_min?: number;

  @ApiPropertyOptional({ example: 80, minimum: 0, maximum: 999 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(999)
  budget_max?: number;

  @ApiPropertyOptional({ example: 25, minimum: 16, maximum: 35 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 1 })
  @Min(16)
  @Max(35)
  preferred_tension?: number;

  @ApiPropertyOptional({ enum: GAME_TYPES, example: 'doubles' })
  @IsOptional()
  @IsIn(GAME_TYPES)
  game_type?: string;

  @ApiPropertyOptional({ example: 3, minimum: 0, maximum: 14 })
  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(14)
  frequency_per_week?: number;

  @ApiPropertyOptional({ example: 5, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_attack?: number;

  @ApiPropertyOptional({ example: 3, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_comfort?: number;

  @ApiPropertyOptional({ example: 4, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_control?: number;

  @ApiPropertyOptional({ example: 4, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_durability?: number;

  @ApiPropertyOptional({ example: 5, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_elasticity?: number;

  @ApiPropertyOptional({ example: 3, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_sound?: number;

  @ApiPropertyOptional({ example: 4, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_string_movement?: number;

  @ApiPropertyOptional({ example: 4, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_tension_retention?: number;

  @ApiPropertyOptional({ example: 3, minimum: 1, maximum: 5 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  pref_value_for_money?: number;

  @ApiPropertyOptional({ example: 5, minimum: 1, maximum: 10 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(10)
  top_n?: number;
}
