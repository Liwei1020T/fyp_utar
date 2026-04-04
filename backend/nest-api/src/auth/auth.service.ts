import {
  ConflictException,
  Injectable,
  NotFoundException,
  OnModuleInit,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AuthProvider, UserRole } from '@prisma/client';
import { hashPassword, verifyPassword } from '../common/utils/password-hash';
import { PrismaService } from '../database/prisma.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { AuthTokenService } from './auth-token.service';

type SerializableUser = {
  id: string;
  username: string;
  phoneNumber: string;
  role: UserRole;
  authProvider: AuthProvider;
  externalAuthId: string | null;
};

type SeedRole = 'admin' | 'vendor';

type SeedUserConfig = {
  authRole: 'admin' | 'vendor';
  enabledConfigKey: 'auth.seedAdminEnabled' | 'auth.seedVendorEnabled';
  phoneNumberConfigKey: 'auth.seedAdminPhoneNumber' | 'auth.seedVendorPhoneNumber';
  usernameConfigKey: 'auth.seedAdminUsername' | 'auth.seedVendorUsername';
  passwordConfigKey: 'auth.seedAdminPassword' | 'auth.seedVendorPassword';
  role: SeedRole;
};

const SEED_USER_CONFIG: Record<SeedRole, SeedUserConfig> = {
  admin: {
    authRole: UserRole.admin,
    enabledConfigKey: 'auth.seedAdminEnabled',
    phoneNumberConfigKey: 'auth.seedAdminPhoneNumber',
    usernameConfigKey: 'auth.seedAdminUsername',
    passwordConfigKey: 'auth.seedAdminPassword',
    role: 'admin',
  },
  vendor: {
    authRole: UserRole.vendor,
    enabledConfigKey: 'auth.seedVendorEnabled',
    phoneNumberConfigKey: 'auth.seedVendorPhoneNumber',
    usernameConfigKey: 'auth.seedVendorUsername',
    passwordConfigKey: 'auth.seedVendorPassword',
    role: 'vendor',
  },
};

@Injectable()
export class AuthService implements OnModuleInit {
  constructor(
    private readonly prisma: PrismaService,
    private readonly configService: ConfigService,
    private readonly authTokenService: AuthTokenService,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.ensureSeedUser('admin');
    await this.ensureSeedUser('vendor');
  }

  async getCurrentUser(userId: string): Promise<Record<string, unknown>> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    return this.serializeUser(user);
  }

  async registerCustomer(dto: RegisterDto): Promise<Record<string, unknown>> {
    const existingUser = await this.prisma.user.findUnique({
      where: { phoneNumber: dto.phone_number },
    });
    if (existingUser) {
      throw new ConflictException('Phone number already registered');
    }

    const user = await this.prisma.user.create({
      data: {
        username: dto.username.trim(),
        phoneNumber: dto.phone_number,
        passwordHash: hashPassword(dto.password),
        role: UserRole.customer,
        authProvider: AuthProvider.local,
      },
    });

    return this.loginResponse(user);
  }

  async login(dto: LoginDto): Promise<Record<string, unknown>> {
    const user = await this.prisma.user.findUnique({
      where: { phoneNumber: dto.phone_number },
    });
    if (!user || !verifyPassword(dto.password, user.passwordHash)) {
      throw new UnauthorizedException('Invalid credentials');
    }

    return this.loginResponse(user);
  }

  private async ensureSeedUser(role: SeedRole): Promise<void> {
    const seedConfig = SEED_USER_CONFIG[role];
    if (this.configService.get<boolean>(seedConfig.enabledConfigKey) !== true) {
      return;
    }

    const phoneNumber = this.configService.getOrThrow<string>(
      seedConfig.phoneNumberConfigKey,
    );
    const username = this.configService.getOrThrow<string>(
      seedConfig.usernameConfigKey,
    );
    const password = this.configService.getOrThrow<string>(
      seedConfig.passwordConfigKey,
    );

    const existing = await this.prisma.user.findUnique({
      where: { phoneNumber },
    });
    if (existing) {
      if (existing.role !== seedConfig.authRole) {
        throw new ConflictException(
          `Seed ${seedConfig.role} phone number is already assigned to a different role`,
        );
      }
      return;
    }

    await this.prisma.user.create({
      data: {
        username,
        phoneNumber,
        passwordHash: hashPassword(password),
        role: seedConfig.authRole,
        authProvider: AuthProvider.local,
      },
    });
  }

  private loginResponse(user: SerializableUser & { id: string }) {
    return {
      access_token: this.authTokenService.signToken({
        subject: user.id,
        role: user.role,
        phoneNumber: user.phoneNumber,
      }),
      token_type: 'bearer',
      role: user.role,
      phone_number: user.phoneNumber,
      user_id: user.id,
      user: this.serializeUser(user),
    };
  }

  private serializeUser(user: SerializableUser): Record<string, unknown> {
    return {
      id: user.id,
      username: user.username,
      phone_number: user.phoneNumber,
      role: user.role,
      auth_provider: user.authProvider,
      external_auth_id: user.externalAuthId,
    };
  }
}
