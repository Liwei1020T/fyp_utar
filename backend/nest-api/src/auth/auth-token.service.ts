import { Injectable, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { USER_ROLES, UserRoleValue } from '../common/domain';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';

@Injectable()
export class AuthTokenService {
  constructor(
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  signToken(payload: {
    subject: string;
    role: UserRoleValue;
    phoneNumber: string;
  }): string {
    return this.jwtService.sign({
      sub: payload.subject,
      role: payload.role,
      phone_number: payload.phoneNumber,
      type: 'access',
      iss: this.configService.getOrThrow<string>('auth.jwtIssuer'),
    });
  }

  verifyToken(token: string): AuthenticatedUser {
    try {
      const payload = this.jwtService.verify(token, {
        secret: this.configService.getOrThrow<string>('auth.jwtSecret'),
        issuer: this.configService.getOrThrow<string>('auth.jwtIssuer'),
      }) as Record<string, unknown>;

      if (
        payload.type !== 'access' ||
        typeof payload.sub !== 'string' ||
        typeof payload.phone_number !== 'string' ||
        typeof payload.role !== 'string' ||
        !USER_ROLES.includes(payload.role as UserRoleValue)
      ) {
        throw new UnauthorizedException('Invalid access token');
      }

      return {
        sub: payload.sub,
        userId: payload.sub,
        phoneNumber: payload.phone_number,
        role: payload.role as UserRoleValue,
      };
    } catch {
      throw new UnauthorizedException('Invalid access token');
    }
  }
}
