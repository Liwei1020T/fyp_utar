import { Module } from '@nestjs/common';
import { AdminBookingsController } from './admin-bookings.controller';
import { AdminStringsController } from './admin-strings.controller';
import { AdminRecommendationLogsController } from './admin-recommendation-logs.controller';
import { BookingsModule } from '../bookings/bookings.module';
import { StringsModule } from '../strings/strings.module';
import { RecommendationsModule } from '../recommendations/recommendations.module';

@Module({
  imports: [BookingsModule, StringsModule, RecommendationsModule],
  controllers: [
    AdminBookingsController,
    AdminStringsController,
    AdminRecommendationLogsController,
  ],
})
export class AdminModule {}
