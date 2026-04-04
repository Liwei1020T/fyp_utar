import { Module } from '@nestjs/common';
import { RecommendationsController } from './recommendations.controller';
import { RecommendationsService } from './recommendations.service';
import { ProfilesModule } from '../profiles/profiles.module';
import { AiClientModule } from '../ai-client/ai-client.module';

@Module({
  imports: [ProfilesModule, AiClientModule],
  controllers: [RecommendationsController],
  providers: [RecommendationsService],
  exports: [RecommendationsService],
})
export class RecommendationsModule {}
