import { ApiProperty } from '@nestjs/swagger';
import { Transform } from 'class-transformer';
import { IsNotEmpty, IsString, Matches } from 'class-validator';
import { normalizePhoneNumber } from '../../common/utils/phone-number';

export class LoginDto {
  @ApiProperty({ example: '+60123456789' })
  @Transform(({ value }) => normalizePhoneNumber(String(value)))
  @Matches(/^(?:\+?[0-9]{9,15})$/)
  phone_number!: string;

  @ApiProperty({ example: 'secret123' })
  @IsString()
  @IsNotEmpty()
  password!: string;
}
