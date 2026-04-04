import { Body, Controller, Delete, Get, Param, Post, Put, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { paginatedResponse, successResponse } from '../common/api-response';
import { Roles } from '../common/decorators/roles.decorator';
import { QueryStringsDto } from '../strings/dto/query-strings.dto';
import { UpsertStringDto } from '../strings/dto/upsert-string.dto';
import { StringsService } from '../strings/strings.service';

@ApiTags('Admin Strings')
@ApiBearerAuth('access-token')
@Roles('admin', 'vendor')
@Controller('admin/strings')
export class AdminStringsController {
  constructor(private readonly stringsService: StringsService) {}

  @Get()
  async list(@Query() query: QueryStringsDto) {
    const result = await this.stringsService.listAdmin(query);
    return paginatedResponse(
      'Admin strings fetched successfully',
      result.items,
      result.total,
      query.limit ?? null,
      query.offset,
    );
  }

  @Post()
  async create(@Body() dto: UpsertStringDto) {
    const data = await this.stringsService.create(dto);
    return successResponse('String created successfully', data);
  }

  @Put(':stringId')
  async update(@Param('stringId') stringId: string, @Body() dto: UpsertStringDto) {
    const data = await this.stringsService.update(stringId, dto);
    return successResponse('String updated successfully', data);
  }

  @Delete(':stringId')
  async deactivate(@Param('stringId') stringId: string) {
    const data = await this.stringsService.deactivate(stringId);
    return successResponse('String deactivated successfully', data);
  }
}
