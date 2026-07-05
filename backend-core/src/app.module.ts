import { Module } from '@nestjs/common';
import { AnalisisWebModule } from './analisis-web/analisis-web.module';

@Module({
  imports: [AnalisisWebModule],
})
export class AppModule {}
