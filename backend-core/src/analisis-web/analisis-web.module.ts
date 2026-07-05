import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { AnalisisWebController } from './analisis-web.controller';
import { AnalisisWebService } from './analisis-web.service';

@Module({
  imports: [
    HttpModule.register({
      timeout: 10000,
      maxRedirects: 3,
    }),
  ],
  controllers: [AnalisisWebController],
  providers: [AnalisisWebService],
})
export class AnalisisWebModule {}
