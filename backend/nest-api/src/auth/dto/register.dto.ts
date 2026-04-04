import { ApiProperty } from '@nestjs/swagger';
import { Transform } from 'class-transformer';
import {
  IsNotEmpty,
  IsString,
  Matches,
  MaxLength,
  MinLength,
} from 'class-validator';
import { normalizePhoneNumber } from '../../common/utils/phone-number';

export class RegisterDto {
  @ApiProperty({ example: 'tanweijie', maxLength: 64 })
  @IsString()
  @IsNotEmpty()
  @MaxLength(64)
  username!: string;

  @ApiProperty({ example: '+60123456789' })
  @Transform(({ value }) => normalizePhoneNumber(String(value)))
  @Matches(/^(?:\+?[0-9]{9,15})$/)
  phone_number!: string;

  @ApiProperty({ example: 'secret123', minLength: 8, maxLength: 128 })
  @IsString()
  @MinLength(8)
  @MaxLength(128)
  @Matches(/[A-Za-z]/, { message: 'password must contain at least one letter' })
  @Matches(/[0-9]/, { message: 'password must contain at least one digit' })
  password!: string;
}
