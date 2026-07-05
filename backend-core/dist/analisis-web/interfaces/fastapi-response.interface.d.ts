export interface FastApiPredictResponse {
    is_phishing: boolean;
    confidence: number;
    message: string;
}
