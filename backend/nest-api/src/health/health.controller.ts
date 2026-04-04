import { Controller, Get } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { Public } from '../common/decorators/public.decorator';
import { successResponse } from '../common/api-response';
import { HealthService } from './health.service';

@ApiTags('Health')
@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Public()
  @Get()
  async getHealth(): Promise<ReturnType<typeof successResponse>> {
    const payload = await this.healthService.getHealth();
    return successResponse('Health fetched successfully', payload);
  }
}
