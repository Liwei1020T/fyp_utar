import { Controller, Get, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiQuery, ApiTags } from '@nestjs/swagger';
import { paginatedResponse } from '../common/api-response';
import { Roles } from '../common/decorators/roles.decorator';
import { RecommendationsService } from '../recommendations/recommendations.service';

@ApiTags('Admin Recommendation Logs')
@ApiBearerAuth('access-token')
@Roles('admin')
@Controller('admin/recommendation-logs')
export class AdminRecommendationLogsController {
  constructor(private readonly recommendationsService: RecommendationsService) {}

  @Get()
  @ApiQuery({ name: 'phone_number', type: String, required: false })
  @ApiQuery({ name: 'algorithm_version', type: String, required: false })
  @ApiQuery({ name: 'limit', type: Number, required: false, example: 20 })
  @ApiQuery({ name: 'offset', type: Number, required: false, example: 0 })
  async list(
    @Query('phone_number') phoneNumber: string | undefined,
    @Query('algorithm_version') algorithmVersion: string | undefined,
    @Query('limit') limit: string | undefined,
    @Query('offset') offset = '0',
  ) {
    const result = await this.recommendationsService.listLogs({
      phone_number: phoneNumber,
      algorithm_version: algorithmVersion,
      limit: limit ? Number(limit) : undefined,
      offset: Number(offset),
    });

    return paginatedResponse(
      'Recommendation logs fetched successfully',
      result.items,
      result.total,
      limit ? Number(limit) : null,
      Number(offset),
    );
  }
}
