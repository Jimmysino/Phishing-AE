import { Body, Controller, HttpCode, HttpStatus, Post } from '@nestjs/common';
import { AnalisisWebService } from './analisis-web.service';
import { AnalizarUrlDto } from './dto/analizar-url.dto';
import { FastApiPredictResponse } from './interfaces/fastapi-response.interface';

@Controller('api')
export class AnalisisWebController {
  constructor(private readonly analisisWebService: AnalisisWebService) {}

  @Post('analyze')
  @HttpCode(HttpStatus.OK)
  async analyze(@Body() body: AnalizarUrlDto): Promise<FastApiPredictResponse> {
    return this.analisisWebService.predict(body.url);
  }
}
