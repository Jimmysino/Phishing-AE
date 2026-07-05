"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnalisisWebModule = void 0;
const common_1 = require("@nestjs/common");
const axios_1 = require("@nestjs/axios");
const analisis_web_controller_1 = require("./analisis-web.controller");
const analisis_web_service_1 = require("./analisis-web.service");
let AnalisisWebModule = class AnalisisWebModule {
};
exports.AnalisisWebModule = AnalisisWebModule;
exports.AnalisisWebModule = AnalisisWebModule = __decorate([
    (0, common_1.Module)({
        imports: [
            axios_1.HttpModule.register({
                timeout: 10000,
                maxRedirects: 3,
            }),
        ],
        controllers: [analisis_web_controller_1.AnalisisWebController],
        providers: [analisis_web_service_1.AnalisisWebService],
    })
], AnalisisWebModule);
//# sourceMappingURL=analisis-web.module.js.map