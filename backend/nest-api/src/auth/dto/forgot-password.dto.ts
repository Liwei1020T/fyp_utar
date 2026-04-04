import { Transform } from 'class-transformer';
import { IsString, Matches, MinLength } from 'class-validator';
import { normalizePhoneNumber } from '../../common/utils/phone-number';

export class ForgotPasswordRequestDto {
  @Transform(({ value }) => normalizePhoneNumber(String(value)))
  @Matches(/^(?:\+?[0-9]{9,15})$/)
  phone_number!: string;
}

export class ForgotPasswordResetDto {
  @Transform(({ value }) => normalizePhoneNumber(String(value)))
  @Matches(/^(?:\+?[0-9]{9,15})$/)
  phone_number!: string;

  @Matches(/^\d{6}$/)
  verification_code!: string;

  @IsString()
  @MinLength(8)
  @Matches(/[A-Za-z]/, { message: 'new_password must contain at least one letter' })
  @Matches(/[0-9]/, { message: 'new_password must contain at least one digit' })
  new_password!: string;
}
