import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsBoolean, IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';

export class UpsertStringDto {
  @ApiProperty({ example: 'Yonex' })
  @IsString()
  brand!: string;

  @ApiProperty({ example: 'BG80' })
  @IsString()
  model_name!: string;

  @ApiPropertyOptional({ example: 'yonex bg80' })
  @IsOptional()
  @IsString()
  normalized_name?: string;

  @ApiPropertyOptional({ example: 45, minimum: 0, maximum: 999 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(999)
  price_rm?: number;

  @ApiPropertyOptional({ example: 0.81, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  attack?: number;

  @ApiPropertyOptional({ example: 0.58, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  comfort?: number;

  @ApiPropertyOptional({ example: 0.72, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  control?: number;

  @ApiPropertyOptional({ example: 0.61, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  durability?: number;

  @ApiPropertyOptional({ example: 0.79, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  elasticity?: number;

  @ApiPropertyOptional({ example: 0.84, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  sound?: number;

  @ApiPropertyOptional({ example: 0.67, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  string_movement?: number;

  @ApiPropertyOptional({ example: 0.63, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  tension_retention?: number;

  @ApiPropertyOptional({ example: 0.59, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  value_for_money?: number;

  @ApiPropertyOptional({ example: 0.7, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  beginner_fit_score?: number;

  @ApiPropertyOptional({ example: 0.66, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  stability_score?: number;

  @ApiPropertyOptional({ example: 0.74, minimum: 0, maximum: 1 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(1)
  all_round_score?: number;

  @ApiPropertyOptional({ example: 'source-123' })
  @IsOptional()
  @IsString()
  source_item_id?: string;

  @ApiPropertyOptional({ example: 'https://example.com/catalog/bg80' })
  @IsOptional()
  @IsString()
  source_url?: string;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @IsBoolean()
  is_active?: boolean;
}
