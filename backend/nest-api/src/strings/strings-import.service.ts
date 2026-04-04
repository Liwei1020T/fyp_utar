import { Injectable } from '@nestjs/common';
import { approvedRowToDto } from './approved-catalog';
import { StringsService } from './strings.service';

@Injectable()
export class StringsImportService {
  constructor(private readonly stringsService: StringsService) {}

  async importRows(rows: Record<string, unknown>[]) {
    let createdCount = 0;
    let updatedCount = 0;
    let errorCount = 0;

    for (const row of rows) {
      try {
        const dto = approvedRowToDto(row);
        const existing = await this.findExistingByNormalizedName(dto.normalized_name!);
        if (existing) {
          await this.stringsService.update(existing.id, dto);
          updatedCount += 1;
        } else {
          await this.stringsService.create(dto);
          createdCount += 1;
        }
      } catch {
        errorCount += 1;
      }
    }

    return {
      imported_count: createdCount + updatedCount,
      created_count: createdCount,
      updated_count: updatedCount,
      error_count: errorCount,
    };
  }

  private async findExistingByNormalizedName(normalizedName: string) {
    const result = await this.stringsService.listAdmin({
      search: normalizedName,
      offset: 0,
    });

    return result.items.find(
      (item) => item.normalized_name === normalizedName,
    ) as { id: string; normalized_name: string } | undefined;
  }
}
