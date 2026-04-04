import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsDateString, IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';

export class CreateBookingDto {
  @ApiProperty({ example: '9cc5df5e-63d4-4608-b84e-ec40798a4321' })
  @IsString()
  string_id!: string;

  @ApiPropertyOptional({ example: 'Yonex' })
  @IsOptional()
  @IsString()
  racket_brand?: string;

  @ApiPropertyOptional({ example: 'Astrox 88D' })
  @IsOptional()
  @IsString()
  racket_model?: string;

  @ApiPropertyOptional({ example: 25, minimum: 16, maximum: 35 })
  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 1 })
  @Min(16)
  @Max(35)
  requested_tension?: number;

  @ApiPropertyOptional({ example: '2026-04-03T10:00:00Z' })
  @IsOptional()
  @IsDateString()
  drop_off_datetime?: string;

  @ApiPropertyOptional({ example: 'Customer prefers a crisp feel.' })
  @IsOptional()
  @IsString()
  notes?: string;
}
