import { Module } from '@nestjs/common';
import { StringsController } from './strings.controller';
import { StringsService } from './strings.service';
import { StringsImportService } from './strings-import.service';

@Module({
  controllers: [StringsController],
  providers: [StringsService, StringsImportService],
  exports: [StringsService, StringsImportService],
})
export class StringsModule {}
