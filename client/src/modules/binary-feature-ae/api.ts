import { postJson } from '@/core/http';
import type {
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
} from '@/types/binary-feature-ae';

export async function postBinaryFeatureCalculate(
    params: ApiBinaryFeatureCalculateRequest,
    signal?: AbortSignal,
): Promise<ApiBinaryFeatureCalculateResponse> {
    return postJson<ApiBinaryFeatureCalculateResponse>(
        '/api/binary-feature-ae/calculate',
        params,
        signal,
    );
}
