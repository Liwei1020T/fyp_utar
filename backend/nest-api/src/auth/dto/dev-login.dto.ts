import { IsIn } from 'class-validator';

export class DevLoginDto {
  @IsIn(['customer', 'admin'])
  role!: 'customer' | 'admin';
}
