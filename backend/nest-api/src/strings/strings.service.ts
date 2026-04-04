import { Injectable, NotFoundException, OnModuleInit, BadRequestException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Prisma } from '@prisma/client';
import { approvedNormalizedNames, approvedRowsToDtos, normalizeCatalogName } from './approved-catalog';
import { toIsoString, toNullableNumber } from '../common/utils/serialization';
import { QueryStringsDto } from './dto/query-strings.dto';
import { UpsertStringDto } from './dto/upsert-string.dto';
import { PrismaService } from '../database/prisma.service';

const STRING_SORT_FIELD_MAP: Record<
  string,
  keyof Prisma.StringCatalogItemOrderByWithRelationInput
> = {
  brand: 'brand',
  model_name: 'modelName',
  price_rm: 'priceRm',
  attack: 'attack',
  comfort: 'comfort',
  control: 'control',
  durability: 'durability',
  elasticity: 'elasticity',
  sound: 'sound',
  tension_retention: 'tensionRetention',
  value_for_money: 'valueForMoney',
  created_at: 'createdAt',
  updated_at: 'updatedAt',
};

@Injectable()
export class StringsService implements OnModuleInit {
  private approvedCatalogNames?: Set<string>;

  constructor(
    private readonly prisma: PrismaService,
    private readonly configService: ConfigService,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.ensureApprovedCatalogSeeded();
  }

  async ensureApprovedCatalogSeeded(): Promise<void> {
    const count = await this.prisma.stringCatalogItem.count();
    if (count > 0) {
      return;
    }

    const approvedRows = approvedRowsToDtos(this.getApprovedCatalogSourcePath());
    for (const row of approvedRows) {
      await this.prisma.stringCatalogItem.create({
        data: this.toPersistence(row),
      });
    }
  }

  async listActive(query: QueryStringsDto) {
    return this.listStrings({
      ...query,
      is_active: true,
    });
  }

  async listAdmin(query: QueryStringsDto) {
    return this.listStrings(query);
  }

  async getById(stringId: string, includeInactive = false) {
    const item = await this.findStringOrThrow(stringId);
    if (!item || (!includeInactive && !item.isActive)) {
      throw new NotFoundException('String not found');
    }

    return this.serializeString(item);
  }

  async create(dto: UpsertStringDto) {
    this.assertApprovedCatalogEntry(dto);
    const item = await this.prisma.stringCatalogItem.create({
      data: this.toPersistence(dto),
    });
    return this.serializeString(item);
  }

  async update(stringId: string, dto: UpsertStringDto) {
    await this.findStringOrThrow(stringId);

    this.assertApprovedCatalogEntry(dto);
    const item = await this.prisma.stringCatalogItem.update({
      where: { id: stringId },
      data: this.toPersistence(dto),
    });
    return this.serializeString(item);
  }

  async deactivate(stringId: string) {
    await this.findStringOrThrow(stringId);

    const item = await this.prisma.stringCatalogItem.update({
      where: { id: stringId },
      data: { isActive: false },
    });
    return this.serializeString(item);
  }

  serializeString(item: Prisma.StringCatalogItemGetPayload<Record<string, never>>) {
    return {
      id: item.id,
      brand: item.brand,
      model_name: item.modelName,
      normalized_name: item.normalizedName,
      price_rm: toNullableNumber(item.priceRm),
      attack: toNullableNumber(item.attack),
      comfort: toNullableNumber(item.comfort),
      control: toNullableNumber(item.control),
      durability: toNullableNumber(item.durability),
      elasticity: toNullableNumber(item.elasticity),
      sound: toNullableNumber(item.sound),
      string_movement: toNullableNumber(item.stringMovement),
      tension_retention: toNullableNumber(item.tensionRetention),
      value_for_money: toNullableNumber(item.valueForMoney),
      beginner_fit_score: toNullableNumber(item.beginnerFitScore),
      stability_score: toNullableNumber(item.stabilityScore),
      all_round_score: toNullableNumber(item.allRoundScore),
      source_item_id: item.sourceItemId,
      source_url: item.sourceUrl,
      is_active: item.isActive,
      created_at: toIsoString(item.createdAt),
      updated_at: toIsoString(item.updatedAt),
    };
  }

  async listStrings(query: QueryStringsDto) {
    const where: Prisma.StringCatalogItemWhereInput = {
      ...(query.is_active !== undefined ? { isActive: query.is_active } : {}),
      ...(query.brand
        ? {
            brand: {
              contains: query.brand,
            },
          }
        : {}),
      ...(query.search
        ? {
            OR: [
              { brand: { contains: query.search } },
              { modelName: { contains: query.search } },
              { normalizedName: { contains: query.search.toLowerCase() } },
            ],
          }
        : {}),
    };

    const sortBy = STRING_SORT_FIELD_MAP[query.sort_by ?? 'brand'] ?? 'brand';
    const sortOrder = query.sort_order ?? 'asc';

    const [items, total] = await this.prisma.$transaction([
      this.prisma.stringCatalogItem.findMany({
        where,
        orderBy: [{ [sortBy]: sortOrder }, { modelName: 'asc' }],
        skip: query.offset,
        ...(query.limit !== undefined ? { take: query.limit } : {}),
      }),
      this.prisma.stringCatalogItem.count({ where }),
    ]);

    return {
      items: items.map((item) => this.serializeString(item)),
      total,
    };
  }

  private assertApprovedCatalogEntry(dto: UpsertStringDto): void {
    const normalizedName =
      dto.normalized_name ?? normalizeCatalogName(dto.brand, dto.model_name);

    if (!this.getApprovedCatalogNames().has(normalizedName)) {
      throw new BadRequestException(
        'Only strings from the approved real catalog source can be created or updated',
      );
    }
  }

  private async findStringOrThrow(stringId: string) {
    const item = await this.prisma.stringCatalogItem.findUnique({
      where: { id: stringId },
    });
    if (!item) {
      throw new NotFoundException('String not found');
    }

    return item;
  }

  private getApprovedCatalogNames(): Set<string> {
    if (!this.approvedCatalogNames) {
      this.approvedCatalogNames = approvedNormalizedNames(this.getApprovedCatalogSourcePath());
    }

    return this.approvedCatalogNames;
  }

  private getApprovedCatalogSourcePath(): string {
    return this.configService.getOrThrow<string>('catalog.approvedSourcePath');
  }

  private toPersistence(dto: UpsertStringDto): Prisma.StringCatalogItemUncheckedCreateInput {
    return {
      brand: dto.brand.trim(),
      modelName: dto.model_name.trim(),
      normalizedName:
        dto.normalized_name ?? normalizeCatalogName(dto.brand, dto.model_name),
      priceRm: dto.price_rm,
      attack: dto.attack,
      comfort: dto.comfort,
      control: dto.control,
      durability: dto.durability,
      elasticity: dto.elasticity,
      sound: dto.sound,
      stringMovement: dto.string_movement,
      tensionRetention: dto.tension_retention,
      valueForMoney: dto.value_for_money,
      beginnerFitScore: dto.beginner_fit_score,
      stabilityScore: dto.stability_score,
      allRoundScore: dto.all_round_score,
      sourceItemId: dto.source_item_id,
      sourceUrl: dto.source_url,
      isActive: dto.is_active ?? true,
    };
  }
}
