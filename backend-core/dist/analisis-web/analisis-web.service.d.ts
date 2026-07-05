import { HttpService } from '@nestjs/axios';
import { FastApiPredictResponse } from './interfaces/fastapi-response.interface';
export declare class AnalisisWebService {
    private readonly httpService;
    private readonly logger;
    constructor(httpService: HttpService);
    predict(url: string): Promise<FastApiPredictResponse>;
}
