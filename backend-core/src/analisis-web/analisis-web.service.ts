import { HttpException, HttpStatus, Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom, TimeoutError } from 'rxjs';
import { timeout } from 'rxjs/operators';
import { AxiosError } from 'axios';
import { FastApiPredictResponse } from './interfaces/fastapi-response.interface';

const FASTAPI_URL = 'http://localhost:8000/predict';
const REQUEST_TIMEOUT_MS = 10_000;

@Injectable()
export class AnalisisWebService {
  private readonly logger = new Logger(AnalisisWebService.name);

  constructor(private readonly httpService: HttpService) {}

  async predict(url: string): Promise<FastApiPredictResponse> {
    const payload = { url };

    try {
      const response = await firstValueFrom(
        this.httpService
          .post<FastApiPredictResponse>(FASTAPI_URL, payload)
          .pipe(timeout(REQUEST_TIMEOUT_MS)),
      );

      return response.data;
    } catch (error) {
      if (error instanceof TimeoutError) {
        this.logger.warn('FastAPI request timed out');
        throw new HttpException(
          'El servicio de predicción no respondió a tiempo.',
          HttpStatus.GATEWAY_TIMEOUT,
        );
      }

      const axiosError = error as AxiosError;

      if (axiosError.code === 'ECONNREFUSED') {
        this.logger.error('FastAPI is not reachable at ' + FASTAPI_URL);
        throw new HttpException(
          'El servicio de predicción no está disponible. Verifica que FastAPI esté corriendo en el puerto 8000.',
          HttpStatus.SERVICE_UNAVAILABLE,
        );
      }

      if (axiosError.response) {
        this.logger.error(
          `FastAPI responded with ${axiosError.response.status}`,
          axiosError.response.data,
        );
        throw new HttpException(
          axiosError.response.data ?? 'Error en el servicio de predicción.',
          axiosError.response.status,
        );
      }

      this.logger.error('Unexpected error calling FastAPI', error);
      throw new HttpException(
        'Error interno al comunicarse con el servicio de predicción.',
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }
}
