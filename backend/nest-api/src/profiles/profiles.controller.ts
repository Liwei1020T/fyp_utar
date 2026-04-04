import { Body, Controller, Get, Put } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { successResponse } from '../common/api-response';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';
import { UpsertProfileDto } from './dto/upsert-profile.dto';
import { ProfilesService } from './profiles.service';

@ApiTags('Profiles')
@ApiBearerAuth('access-token')
@Controller('profiles')
export class ProfilesController {
  constructor(private readonly profilesService: ProfilesService) {}

  @Get('me')
  async getMyProfile(@CurrentUser() user: AuthenticatedUser) {
    const data = await this.profilesService.getByUserId(user.sub);
    return successResponse('Profile fetched successfully', data);
  }

  @Put('me')
  async updateMyProfile(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: UpsertProfileDto,
  ) {
    const data = await this.profilesService.upsert(user.sub, dto);
    return successResponse('Profile updated successfully', data);
  }
}
