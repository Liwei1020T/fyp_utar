import { Controller, Get, Param, Post, Body } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { successResponse } from '../common/api-response';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';
import { CreateBookingDto } from './dto/create-booking.dto';
import { BookingsService } from './bookings.service';

@ApiTags('Bookings')
@ApiBearerAuth('access-token')
@Controller('bookings')
export class BookingsController {
  constructor(private readonly bookingsService: BookingsService) {}

  @Post()
  async create(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: CreateBookingDto,
  ) {
    const data = await this.bookingsService.create(user.sub, dto);
    return successResponse('Booking created successfully', data);
  }

  @Get('me')
  async mine(@CurrentUser() user: AuthenticatedUser) {
    const data = await this.bookingsService.listForUser(user.sub);
    return successResponse('Bookings fetched successfully', data);
  }

  @Get(':bookingId')
  async detail(
    @CurrentUser() user: AuthenticatedUser,
    @Param('bookingId') bookingId: string,
  ) {
    const data = await this.bookingsService.getAccessibleBooking(
      bookingId,
      user.sub,
      user.role,
    );
    return successResponse('Booking fetched successfully', data);
  }
}
