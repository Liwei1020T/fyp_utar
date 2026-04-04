import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration, { resolveBackendPath } from './config/configuration';
import { validateEnvironment } from './config/env.validation';
import { DatabaseModule } from './database/database.module';
import { AuthModule } from './auth/auth.module';
import { ProfilesModule } from './profiles/profiles.module';
import { StringsModule } from './strings/strings.module';
import { BookingsModule } from './bookings/bookings.module';
import { AdminModule } from './admin/admin.module';
import { RecommendationsModule } from './recommendations/recommendations.module';
import { HealthModule } from './health/health.module';
import { AiClientModule } from './ai-client/ai-client.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: [resolveBackendPath('.env')],
      load: [configuration],
      validate: validateEnvironment,
    }),
    DatabaseModule,
    AiClientModule,
    HealthModule,
    AuthModule,
    UsersModule,
    ProfilesModule,
    StringsModule,
    BookingsModule,
    AdminModule,
    RecommendationsModule,
  ],
})
export class AppModule {}
