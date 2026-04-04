import { ApiProperty } from '@nestjs/swagger';
import { IsIn } from 'class-validator';

export class UpdateBookingStatusDto {
  @ApiProperty({
    enum: [
      'pending',
      'confirmed',
      'in_progress',
      'ready_for_pickup',
      'picked_up',
      'cancelled',
      'rejected',
    ],
  })
  @IsIn([
    'pending',
    'confirmed',
    'in_progress',
    'ready_for_pickup',
    'picked_up',
    'cancelled',
    'rejected',
  ])
  status!: 'pending' | 'confirmed' | 'in_progress' | 'ready_for_pickup' | 'picked_up' | 'cancelled' | 'rejected';
}
