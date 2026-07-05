"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var AnalisisWebService_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnalisisWebService = void 0;
const common_1 = require("@nestjs/common");
const axios_1 = require("@nestjs/axios");
const rxjs_1 = require("rxjs");
const operators_1 = require("rxjs/operators");
const FASTAPI_URL = 'http://localhost:8000/predict';
const REQUEST_TIMEOUT_MS = 10_000;
let AnalisisWebService = AnalisisWebService_1 = class AnalisisWebService {
    constructor(httpService) {
        this.httpService = httpService;
        this.logger = new common_1.Logger(AnalisisWebService_1.name);
    }
    async predict(url) {
        const payload = { url };
        try {
            const response = await (0, rxjs_1.firstValueFrom)(this.httpService
                .post(FASTAPI_URL, payload)
                .pipe((0, operators_1.timeout)(REQUEST_TIMEOUT_MS)));
            return response.data;
        }
        catch (error) {
            if (error instanceof rxjs_1.TimeoutError) {
                this.logger.warn('FastAPI request timed out');
                throw new common_1.HttpException('El servicio de predicción no respondió a tiempo.', common_1.HttpStatus.GATEWAY_TIMEOUT);
            }
            const axiosError = error;
            if (axiosError.code === 'ECONNREFUSED') {
                this.logger.error('FastAPI is not reachable at ' + FASTAPI_URL);
                throw new common_1.HttpException('El servicio de predicción no está disponible. Verifica que FastAPI esté corriendo en el puerto 8000.', common_1.HttpStatus.SERVICE_UNAVAILABLE);
            }
            if (axiosError.response) {
                this.logger.error(`FastAPI responded with ${axiosError.response.status}`, axiosError.response.data);
                throw new common_1.HttpException(axiosError.response.data ?? 'Error en el servicio de predicción.', axiosError.response.status);
            }
            this.logger.error('Unexpected error calling FastAPI', error);
            throw new common_1.HttpException('Error interno al comunicarse con el servicio de predicción.', common_1.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
};
exports.AnalisisWebService = AnalisisWebService;
exports.AnalisisWebService = AnalisisWebService = AnalisisWebService_1 = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [axios_1.HttpService])
], AnalisisWebService);
//# sourceMappingURL=analisis-web.service.js.map