import { BadRequestException, Injectable } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { toIsoString, toNullableNumber } from '../common/utils/serialization';
import { PrismaService } from '../database/prisma.service';
import { UpsertProfileDto } from './dto/upsert-profile.dto';

@Injectable()
export class ProfilesService {
  constructor(private readonly prisma: PrismaService) {}

  async getByUserId(userId: string): Promise<Record<string, unknown> | null> {
    const profile = await this.prisma.userProfile.findUnique({
      where: { userId },
    });
    return profile ? this.serializeProfile(profile) : null;
  }

  async upsert(userId: string, dto: UpsertProfileDto): Promise<Record<string, unknown>> {
    this.assertBudgetRange(dto.budget_min, dto.budget_max);
    const data = this.toPersistence(userId, dto);

    const profile = await this.prisma.userProfile.upsert({
      where: { userId },
      create: data,
      update: data,
    });

    return this.serializeProfile(profile);
  }

  serializeProfile(profile: Prisma.UserProfileGetPayload<Record<string, never>>) {
    return {
      skill_level: profile.skillLevel,
      playing_style: profile.playingStyle,
      budget_min: toNullableNumber(profile.budgetMin),
      budget_max: toNullableNumber(profile.budgetMax),
      preferred_tension: toNullableNumber(profile.preferredTension),
      game_type: profile.gameType,
      frequency_per_week: profile.frequencyPerWeek,
      pref_attack: profile.prefAttack,
      pref_comfort: profile.prefComfort,
      pref_control: profile.prefControl,
      pref_durability: profile.prefDurability,
      pref_elasticity: profile.prefElasticity,
      pref_sound: profile.prefSound,
      pref_string_movement: profile.prefStringMovement,
      pref_tension_retention: profile.prefTensionRetention,
      pref_value_for_money: profile.prefValueForMoney,
      created_at: toIsoString(profile.createdAt),
      updated_at: toIsoString(profile.updatedAt),
    };
  }

  private toPersistence(
    userId: string,
    dto: UpsertProfileDto,
  ): Prisma.UserProfileUncheckedCreateInput {
    return {
      userId,
      skillLevel: dto.skill_level,
      playingStyle: dto.playing_style,
      budgetMin: dto.budget_min,
      budgetMax: dto.budget_max,
      preferredTension: dto.preferred_tension,
      gameType: dto.game_type,
      frequencyPerWeek: dto.frequency_per_week,
      prefAttack: dto.pref_attack,
      prefComfort: dto.pref_comfort,
      prefControl: dto.pref_control,
      prefDurability: dto.pref_durability,
      prefElasticity: dto.pref_elasticity,
      prefSound: dto.pref_sound,
      prefStringMovement: dto.pref_string_movement,
      prefTensionRetention: dto.pref_tension_retention,
      prefValueForMoney: dto.pref_value_for_money,
    };
  }

  private assertBudgetRange(min?: number, max?: number): void {
    if (min !== undefined && max !== undefined && min > max) {
      throw new BadRequestException('budget_min must be less than or equal to budget_max');
    }
  }
}
