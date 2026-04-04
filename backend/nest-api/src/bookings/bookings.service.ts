import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { BookingStatus, Prisma, UserRole } from '@prisma/client';
import {
  toIsoString,
  toNullableIsoString,
  toNullableNumber,
} from '../common/utils/serialization';
import { PrismaService } from '../database/prisma.service';
import { CreateBookingDto } from './dto/create-booking.dto';
import { assertBookingStatusTransition } from './booking-status';

@Injectable()
export class BookingsService {
  constructor(private readonly prisma: PrismaService) {}

  async create(userId: string, dto: CreateBookingDto) {
    const stringItem = await this.prisma.stringCatalogItem.findUnique({
      where: { id: dto.string_id },
    });
    if (!stringItem || !stringItem.isActive) {
      throw new NotFoundException('String not found');
    }

    const booking = await this.prisma.booking.create({
      data: {
        userId,
        stringId: dto.string_id,
        racketBrand: dto.racket_brand,
        racketModel: dto.racket_model,
        requestedTension: dto.requested_tension,
        dropOffDatetime: dto.drop_off_datetime
          ? new Date(dto.drop_off_datetime)
          : undefined,
        notes: dto.notes,
        status: BookingStatus.pending,
        statusHistory: {
          create: {
            oldStatus: null,
            newStatus: BookingStatus.pending,
            changedByUserId: userId,
          },
        },
      },
      include: {
        string: true,
        statusHistory: {
          orderBy: { changedAt: 'asc' },
        },
      },
    });

    return this.serializeBooking(booking);
  }

  async listForUser(userId: string) {
    const bookings = await this.prisma.booking.findMany({
      where: { userId },
      include: {
        string: true,
        statusHistory: {
          orderBy: { changedAt: 'asc' },
        },
      },
      orderBy: { createdAt: 'desc' },
    });
    return bookings.map((booking) => this.serializeBooking(booking));
  }

  async getAccessibleBooking(bookingId: string, userId: string, role: UserRole) {
    const booking = await this.prisma.booking.findUnique({
      where: { id: bookingId },
      include: {
        string: true,
        user: true,
        statusHistory: {
          orderBy: { changedAt: 'asc' },
          include: { changedBy: true },
        },
      },
    });
    if (!booking) {
      throw new NotFoundException('Booking not found');
    }
    if (role === UserRole.customer && booking.userId !== userId) {
      throw new NotFoundException('Booking not found');
    }
    return this.serializeBooking(booking);
  }

  async listAll(query: {
    status?: BookingStatus;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset: number;
  }) {
    const where: Prisma.BookingWhereInput = {
      ...(query.status ? { status: query.status } : {}),
      ...(query.search
        ? {
            OR: [
              { racketBrand: { contains: query.search } },
              { racketModel: { contains: query.search } },
              { string: { brand: { contains: query.search } } },
              { string: { modelName: { contains: query.search } } },
              { user: { phoneNumber: { contains: query.search } } },
              { user: { username: { contains: query.search } } },
            ],
          }
        : {}),
    };

    const orderField: keyof Prisma.BookingOrderByWithRelationInput =
      query.sort_by === 'drop_off_datetime'
        ? 'dropOffDatetime'
        : query.sort_by === 'status'
          ? 'status'
          : query.sort_by === 'updated_at'
            ? 'updatedAt'
            : 'createdAt';

    const [items, total] = await this.prisma.$transaction([
      this.prisma.booking.findMany({
        where,
        include: {
          string: true,
          user: true,
          statusHistory: {
            orderBy: { changedAt: 'asc' },
          },
        },
        orderBy: [{ [orderField]: query.sort_order ?? 'desc' }, { createdAt: 'desc' }],
        skip: query.offset,
        ...(query.limit !== undefined ? { take: query.limit } : {}),
      }),
      this.prisma.booking.count({ where }),
    ]);

    return {
      items: items.map((item) => this.serializeBooking(item)),
      total,
    };
  }

  async updateStatus(bookingId: string, status: BookingStatus, changedByUserId: string) {
    const booking = await this.prisma.booking.findUnique({
      where: { id: bookingId },
      include: { string: true },
    });
    if (!booking) {
      throw new NotFoundException('Booking not found');
    }

    assertBookingStatusTransition(booking.status, status);

    const updated = await this.prisma.booking.update({
      where: { id: bookingId },
      data: {
        status,
        statusHistory: {
          create: {
            oldStatus: booking.status,
            newStatus: status,
            changedByUserId,
          },
        },
      },
      include: {
        string: true,
        user: true,
        statusHistory: {
          orderBy: { changedAt: 'asc' },
          include: { changedBy: true },
        },
      },
    });

    return this.serializeBooking(updated);
  }

  serializeBooking(
    booking: {
      id: string;
      userId: string;
      stringId: string;
      racketBrand: string | null;
      racketModel: string | null;
      requestedTension: Prisma.Decimal | null;
      dropOffDatetime: Date | null;
      notes: string | null;
      status: BookingStatus;
      createdAt: Date;
      updatedAt: Date;
      string: { brand: string; modelName: string };
      user?: { phoneNumber: string; username: string } | null;
      statusHistory?: Array<{
        oldStatus: BookingStatus | null;
        newStatus: BookingStatus;
        changedByUserId: string | null;
        changedAt: Date;
        changedBy?: { phoneNumber: string } | null;
      }>;
    },
  ) {
    return {
      id: booking.id,
      user_id: booking.userId,
      string_id: booking.stringId,
      string_name: `${booking.string.brand} ${booking.string.modelName}`,
      customer_phone_number:
        'user' in booking && booking.user ? booking.user.phoneNumber : undefined,
      customer_username: 'user' in booking && booking.user ? booking.user.username : undefined,
      racket_brand: booking.racketBrand,
      racket_model: booking.racketModel,
      requested_tension: toNullableNumber(booking.requestedTension),
      drop_off_datetime: toNullableIsoString(booking.dropOffDatetime),
      notes: booking.notes,
      status: booking.status,
      created_at: toIsoString(booking.createdAt),
      updated_at: toIsoString(booking.updatedAt),
      status_history:
        'statusHistory' in booking && Array.isArray(booking.statusHistory)
          ? booking.statusHistory.map((entry) => ({
              old_status: entry.oldStatus,
              new_status: entry.newStatus,
              changed_by_user_id: entry.changedByUserId,
              changed_by_phone_number: entry.changedBy?.phoneNumber ?? null,
              changed_at: toIsoString(entry.changedAt),
            }))
          : undefined,
    };
  }
}
