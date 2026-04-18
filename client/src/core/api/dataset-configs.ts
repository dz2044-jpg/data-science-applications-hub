import {
    deleteRequest,
    getJson,
    postFormData,
} from '@/core/http';
import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
} from '@/types/dataset-config';
import type { ApiDatasetSchemaResults } from '@/types/datasets';

export async function getDatasetConfigs(): Promise<ApiListDatasetConfigsResults> {
    return getJson<ApiListDatasetConfigsResults>('/api/dataset-configs');
}

export async function createDatasetConfig(
    request: ApiCreateDatasetConfigRequest,
    file: File,
): Promise<ApiDatasetConfig> {
    const formData = new FormData();
    formData.append('dataset_name', request.dataset_name);
    formData.append('performance_type', request.performance_type);
    formData.append('module_id', request.module_id);
    formData.append('module_config_json', JSON.stringify(request.module_config));
    formData.append('file', file);

    return postFormData<ApiDatasetConfig>('/api/dataset-configs', formData);
}

export async function getDatasetConfig(configId: string): Promise<ApiDatasetConfig> {
    return getJson<ApiDatasetConfig>(
        `/api/dataset-configs/${encodeURIComponent(configId)}`,
    );
}

export async function getDatasetConfigSchema(
    configId: string,
): Promise<ApiDatasetSchemaResults> {
    return getJson<ApiDatasetSchemaResults>(
        `/api/dataset-configs/${encodeURIComponent(configId)}/schema`,
    );
}

export async function deleteDatasetConfig(configId: string): Promise<void> {
    await deleteRequest(`/api/dataset-configs/${encodeURIComponent(configId)}`);
}
