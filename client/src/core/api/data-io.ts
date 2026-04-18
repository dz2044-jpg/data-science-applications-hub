import {
    createSlicedUploadFile,
    postFormData,
} from '@/core/http';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';

export async function postCoreUploadSchema(
    file: File,
): Promise<ApiCoreDatasetSchemaResults> {
    const form = new FormData();
    form.append('file', createSlicedUploadFile(file));
    return postFormData<ApiCoreDatasetSchemaResults>('/api/core/upload-schema', form);
}
