import { AnalisisWebService } from './analisis-web.service';
import { AnalizarUrlDto } from './dto/analizar-url.dto';
import { FastApiPredictResponse } from './interfaces/fastapi-response.interface';
export declare class AnalisisWebController {
    private readonly analisisWebService;
    constructor(analisisWebService: AnalisisWebService);
    analyze(body: AnalizarUrlDto): Promise<FastApiPredictResponse>;
}
