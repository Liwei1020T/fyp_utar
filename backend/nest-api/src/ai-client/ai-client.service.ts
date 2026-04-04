import { HttpService } from '@nestjs/axios';
import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { AiRecommendRequest, AiRecommendResponse } from './dto/ai-contract.dto';

@Injectable()
export class AiClientService {
  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {}

  async recommend(payload: AiRecommendRequest): Promise<AiRecommendResponse> {
    return this.post<AiRecommendResponse>('/internal/ai/recommend', payload);
  }

  async explain(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.post<Record<string, unknown>>('/internal/ai/explain', payload);
  }

  async analyzeReviews(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.post<Record<string, unknown>>('/internal/ai/reviews/analyze', payload);
  }

  async queryRag(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.post<Record<string, unknown>>('/internal/ai/rag/query', payload);
  }

  private async post<T>(path: string, payload: unknown): Promise<T> {
    const baseUrl = this.configService.getOrThrow<string>('aiService.baseUrl');
    const internalApiKey =
      this.configService.getOrThrow<string>('aiService.internalApiKey');

    try {
      const response = await firstValueFrom(
        this.httpService.post<T>(`${baseUrl}${path}`, payload, {
          headers: {
            'x-internal-api-key': internalApiKey,
          },
          timeout: this.configService.get<number>('aiService.timeoutMs') ?? 8000,
        }),
      );
      return response.data;
    } catch (error) {
      throw new ServiceUnavailableException(
        `AI service request failed for ${path}: ${String(error)}`,
      );
    }
  }
}
