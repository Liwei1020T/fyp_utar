import { Injectable } from '@nestjs/common';
import { PrismaService } from '../database/prisma.service';

@Injectable()
export class HealthService {
  constructor(private readonly prisma: PrismaService) {}

  async getHealth(): Promise<{ status: 'ok'; database: 'ok' }> {
    await this.prisma.$queryRaw`SELECT 1`;
    return {
      status: 'ok',
      database: 'ok',
    };
  }
}
