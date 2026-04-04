import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { paginatedResponse, successResponse } from '../common/api-response';
import { QueryStringsDto } from './dto/query-strings.dto';
import { StringsService } from './strings.service';

@ApiTags('Strings')
@ApiBearerAuth('access-token')
@Controller('strings')
export class StringsController {
  constructor(private readonly stringsService: StringsService) {}

  @Get()
  async list(@Query() query: QueryStringsDto) {
    const result = await this.stringsService.listActive(query);
    return paginatedResponse(
      'Strings fetched successfully',
      result.items,
      result.total,
      query.limit ?? null,
      query.offset,
    );
  }

  @Get(':stringId')
  async detail(@Param('stringId') stringId: string) {
    const item = await this.stringsService.getById(stringId);
    return successResponse('String fetched successfully', item);
  }
}
