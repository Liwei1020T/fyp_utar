import { Body, Controller, Get, Param, Patch, Query } from '@nestjs/common';
import { BookingStatus } from '@prisma/client';
import { ApiBearerAuth, ApiQuery, ApiTags } from '@nestjs/swagger';
import { paginatedResponse, successResponse } from '../common/api-response';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { Roles } from '../common/decorators/roles.decorator';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';
import { BookingsService } from '../bookings/bookings.service';
import { UpdateBookingStatusDto } from '../bookings/dto/update-booking-status.dto';

@ApiTags('Admin Bookings')
@ApiBearerAuth('access-token')
@Roles('admin', 'vendor')
@Controller('admin/bookings')
export class AdminBookingsController {
  constructor(private readonly bookingsService: BookingsService) {}

  @Get()
  @ApiQuery({ name: 'status', enum: BookingStatus, required: false })
  @ApiQuery({ name: 'search', type: String, required: false })
  @ApiQuery({ name: 'sort_by', type: String, required: false })
  @ApiQuery({ name: 'sort_order', enum: ['asc', 'desc'], required: false })
  @ApiQuery({ name: 'limit', type: Number, required: false, example: 20 })
  @ApiQuery({ name: 'offset', type: Number, required: false, example: 0 })
  async list(
    @Query('status') status: BookingStatus | undefined,
    @Query('search') search: string | undefined,
    @Query('sort_by') sortBy: string | undefined,
    @Query('sort_order') sortOrder: 'asc' | 'desc' | undefined,
    @Query('limit') limit: string | undefined,
    @Query('offset') offset = '0',
  ) {
    const result = await this.bookingsService.listAll({
      status,
      search,
      sort_by: sortBy,
      sort_order: sortOrder,
      limit: limit ? Number(limit) : undefined,
      offset: Number(offset),
    });

    return paginatedResponse(
      'Admin bookings fetched successfully',
      result.items,
      result.total,
      limit ? Number(limit) : null,
      Number(offset),
    );
  }

  @Get(':bookingId')
  async detail(
    @Param('bookingId') bookingId: string,
    @CurrentUser() user: AuthenticatedUser,
  ) {
    const data = await this.bookingsService.getAccessibleBooking(
      bookingId,
      user.sub,
      user.role,
    );
    return successResponse('Admin booking fetched successfully', data);
  }

  @Patch(':bookingId/status')
  async updateStatus(
    @Param('bookingId') bookingId: string,
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: UpdateBookingStatusDto,
  ) {
    const data = await this.bookingsService.updateStatus(
      bookingId,
      dto.status as BookingStatus,
      user.sub,
    );
    return successResponse('Booking updated successfully', data);
  }
}
