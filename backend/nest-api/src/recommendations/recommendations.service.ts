import { Injectable, NotFoundException } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { AiRecommendRequest, AiRecommendResponse } from '../ai-client/dto/ai-contract.dto';
import { toIsoString } from '../common/utils/serialization';
import { PrismaService } from '../database/prisma.service';
import { ProfilesService } from '../profiles/profiles.service';
import { AiClientService } from '../ai-client/ai-client.service';
import { GenerateRecommendationDto } from './dto/generate-recommendation.dto';
import { ProfileRecommendationDto } from './dto/profile-recommendation.dto';
import { normalizeRecommendationInput } from './recommendation-normalizer';

@Injectable()
export class RecommendationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly profilesService: ProfilesService,
    private readonly aiClientService: AiClientService,
  ) {}

  async generateForProfile(userId: string, dto: ProfileRecommendationDto) {
    const profile = await this.profilesService.getByUserId(userId);
    if (!profile) {
      throw new NotFoundException('Profile not found');
    }

    const aiPayload = normalizeRecommendationInput({
      ...(profile as Record<string, number | string | undefined>),
      user_id: userId,
      top_n: dto.top_n,
    } as Partial<AiRecommendRequest>);

    const aiResponse = await this.aiClientService.recommend(aiPayload);
    await this.logRecommendation(userId, profile, aiResponse);
    return aiResponse;
  }

  async generateDirect(dto: GenerateRecommendationDto, userId?: string) {
    const aiPayload = normalizeRecommendationInput({
      ...(dto as unknown as Record<string, string | number | undefined>),
      user_id: userId,
    } as Partial<AiRecommendRequest>);

    const aiResponse = await this.aiClientService.recommend(aiPayload);
    await this.logRecommendation(
      userId ?? null,
      dto as unknown as Record<string, unknown>,
      aiResponse,
    );
    return aiResponse;
  }

  async listLogs(query: {
    phone_number?: string;
    algorithm_version?: string;
    limit?: number;
    offset: number;
  }) {
    const where = {
      ...(query.algorithm_version ? { algorithmVersion: query.algorithm_version } : {}),
      ...(query.phone_number
        ? {
            user: {
              phoneNumber: {
                contains: query.phone_number,
              },
            },
          }
        : {}),
    };

    const [items, total] = await this.prisma.$transaction([
      this.prisma.recommendationLog.findMany({
        where,
        include: {
          user: true,
        },
        orderBy: { createdAt: 'desc' },
        skip: query.offset,
        ...(query.limit !== undefined ? { take: query.limit } : {}),
      }),
      this.prisma.recommendationLog.count({ where }),
    ]);

    return {
      items: items.map((item) => ({
        user_id: item.userId,
        phone_number: item.user?.phoneNumber ?? null,
        username: item.user?.username ?? null,
        profile_snapshot_json: item.profileSnapshotJson,
        recommendation_result_json: item.recommendationResultJson,
        algorithm_version: item.algorithmVersion,
        created_at: toIsoString(item.createdAt),
      })),
      total,
    };
  }

  private async logRecommendation(
    userId: string | null,
    profileSnapshot: Record<string, unknown>,
    result: AiRecommendResponse,
  ) {
    await this.prisma.recommendationLog.create({
      data: {
        userId,
        profileSnapshotJson: profileSnapshot as Prisma.InputJsonObject,
        recommendationResultJson: result as unknown as Prisma.InputJsonObject,
        algorithmVersion: result.algorithm_version,
      },
    });
  }
}
