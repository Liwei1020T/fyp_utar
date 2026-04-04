import { Body, Controller, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { successResponse } from '../common/api-response';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';
import { GenerateRecommendationDto } from './dto/generate-recommendation.dto';
import { ProfileRecommendationDto } from './dto/profile-recommendation.dto';
import { RecommendationsService } from './recommendations.service';

@ApiTags('Recommendations')
@ApiBearerAuth('access-token')
@Controller('recommendations')
export class RecommendationsController {
  constructor(private readonly recommendationsService: RecommendationsService) {}

  @Post('me')
  async generateForCurrentUser(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: ProfileRecommendationDto,
  ) {
    const data = await this.recommendationsService.generateForProfile(user.sub, dto);
    return successResponse('Recommendations generated successfully', data);
  }

  @Post('direct')
  async generateDirect(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: GenerateRecommendationDto,
  ) {
    const data = await this.recommendationsService.generateDirect(dto, user.sub);
    return successResponse('Recommendations generated successfully', data);
  }
}
