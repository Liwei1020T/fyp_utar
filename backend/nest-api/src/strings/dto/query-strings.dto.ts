import { ApiPropertyOptional } from '@nestjs/swagger';
import { Transform } from 'class-transformer';
import { IsBoolean, IsIn, IsInt, IsOptional, Max, Min } from 'class-validator';

export class QueryStringsDto {
  @ApiPropertyOptional({ example: 'Yonex' })
  @IsOptional()
  search?: string;

  @ApiPropertyOptional({ example: 'Yonex' })
  @IsOptional()
  brand?: string;

  @ApiPropertyOptional({
    enum: [
      'brand',
      'model_name',
      'price_rm',
      'attack',
      'comfort',
      'control',
      'durability',
      'elasticity',
      'sound',
      'tension_retention',
      'value_for_money',
      'created_at',
      'updated_at',
    ],
  })
  @IsOptional()
  @IsIn([
    'brand',
    'model_name',
    'price_rm',
    'attack',
    'comfort',
    'control',
    'durability',
    'elasticity',
    'sound',
    'tension_retention',
    'value_for_money',
    'created_at',
    'updated_at',
  ])
  sort_by?: string;

  @ApiPropertyOptional({ enum: ['asc', 'desc'] })
  @IsOptional()
  @IsIn(['asc', 'desc'])
  sort_order?: 'asc' | 'desc';

  @ApiPropertyOptional({ minimum: 1, maximum: 100, example: 20 })
  @IsOptional()
  @Transform(({ value }) => (value === undefined ? undefined : Number(value)))
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number;

  @ApiPropertyOptional({ minimum: 0, example: 0, default: 0 })
  @Transform(({ value }) => (value === undefined ? 0 : Number(value)))
  @IsInt()
  @Min(0)
  offset = 0;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @Transform(({ value }) =>
    value === undefined ? undefined : value === true || value === 'true',
  )
  @IsBoolean()
  is_active?: boolean;
}
