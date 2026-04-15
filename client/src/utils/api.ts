import type {
    ApiMonitorFromCsvParameters,
    ApiMonitorFromCsvResults,
    ApiMonitorFromDatasetParameters,
} from '@/types/monitor';
import type {
    ApiDatasetColaResults,
    ApiDatasetSchemaResults,
    ApiListDatasetsResults,
} from '@/types/datasets';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';
import type {
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateParameters,
    ApiAeUnivariateResults,
    ApiAeVariableLabelsParameters,
    ApiAeVariableLabelsResults,
} from '@/types/ae';
import type { ApiAeInsightsResults } from '@/types/insights';

const API_BASE = 'http://localhost:8000';

export async function getDatasets(): Promise<ApiListDatasetsResults> {
    const res = await fetch(`${API_BASE}/api/datasets`);
    if (!res.ok) {
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiListDatasetsResults;
}

export async function getDatasetSchema(
    datasetName: string,
): Promise<ApiDatasetSchemaResults> {
    const res = await fetch(
        `${API_BASE}/api/datasets/${encodeURIComponent(datasetName)}/schema`,
    );
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetSchemaResults;
}

export async function getDatasetCola(
    datasetName: string,
): Promise<ApiDatasetColaResults> {
    const res = await fetch(
        `${API_BASE}/api/datasets/${encodeURIComponent(datasetName)}/cola`,
    );
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetColaResults;
}

export async function postMonitorFromCsv(
    file: File,
    params: ApiMonitorFromCsvParameters,
): Promise<ApiMonitorFromCsvResults> {
    const form = new FormData();
    form.append('file', file);
    form.append('params', JSON.stringify(params ?? {}));

    const res = await fetch(`${API_BASE}/api/monitor/from-csv`, {
        method: 'POST',
        body: form,
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiMonitorFromCsvResults;
}

export async function postMonitorFromDataset(
    params: ApiMonitorFromDatasetParameters,
): Promise<ApiMonitorFromCsvResults> {
    const res = await fetch(`${API_BASE}/api/monitor/from-dataset`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiMonitorFromCsvResults;
}

export async function postAeUnivariate(
    params: ApiAeUnivariateParameters,
): Promise<ApiAeUnivariateResults> {
    const res = await fetch(`${API_BASE}/api/ae/univariate`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiAeUnivariateResults;
}

export async function postAeUnivariateFromConfig(
    params: ApiAeUnivariateFromConfigParameters,
): Promise<ApiAeUnivariateResults> {
    const res = await fetch(`${API_BASE}/api/ae/univariate-from-config`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiAeUnivariateResults;
}

export async function postAeVariableLabels(
    params: ApiAeVariableLabelsParameters,
): Promise<ApiAeVariableLabelsResults> {
    const res = await fetch(`${API_BASE}/api/ae/variable-labels`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiAeVariableLabelsResults;
}

export async function postAeUploadSchema(
    file: File,
): Promise<ApiDatasetSchemaResults> {
    // For schema detection, only upload first 10MB for CSV/Excel to improve performance
    // Parquet files cannot be sliced because metadata is in the footer at the end
    const maxBytes = 10 * 1024 * 1024; // 10MB
    const isParquet = file.name.toLowerCase().endsWith('.parquet');
    const fileSlice = !isParquet && file.size > maxBytes ? file.slice(0, maxBytes) : file;
    const slicedFile = fileSlice === file ? file : new File([fileSlice], file.name, { type: file.type });
    
    const form = new FormData();
    form.append('file', slicedFile);

    const res = await fetch(`${API_BASE}/api/ae/upload-schema`, {
        method: 'POST',
        body: form,
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetSchemaResults;
}

export async function postCoreUploadSchema(
    file: File,
): Promise<ApiCoreDatasetSchemaResults> {
    const maxBytes = 10 * 1024 * 1024;
    const isParquet = file.name.toLowerCase().endsWith('.parquet');
    const fileSlice = !isParquet && file.size > maxBytes ? file.slice(0, maxBytes) : file;
    const slicedFile =
        fileSlice === file ? file : new File([fileSlice], file.name, { type: file.type });

    const form = new FormData();
    form.append('file', slicedFile);

    const res = await fetch(`${API_BASE}/api/core/upload-schema`, {
        method: 'POST',
        body: form,
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiCoreDatasetSchemaResults;
}

export async function postAeUnivariateFromCsv(
    file: File,
    params: ApiAeUnivariateParameters,
): Promise<ApiAeUnivariateResults> {
    const form = new FormData();
    form.append('file', file);
    form.append('params', JSON.stringify(params));

    const res = await fetch(`${API_BASE}/api/ae/univariate-from-csv`, {
        method: 'POST',
        body: form,
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiAeUnivariateResults;
}

// Dataset Config API
import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
} from '@/types/dataset-config';

export async function getDatasetConfigs(): Promise<ApiListDatasetConfigsResults> {
    const res = await fetch(`${API_BASE}/api/dataset-configs`);
    if (!res.ok) {
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiListDatasetConfigsResults;
}

export async function createDatasetConfig(
    request: ApiCreateDatasetConfigRequest,
    file: File,
): Promise<ApiDatasetConfig> {
    const formData = new FormData();
    formData.append('dataset_name', request.dataset_name);
    formData.append('performance_type', request.performance_type);
    formData.append('column_mapping_json', JSON.stringify(request.column_mapping));
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE}/api/dataset-configs`, {
        method: 'POST',
        body: formData,
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetConfig;
}

export async function getDatasetConfig(configId: string): Promise<ApiDatasetConfig> {
    const res = await fetch(`${API_BASE}/api/dataset-configs/${encodeURIComponent(configId)}`);
    if (!res.ok) {
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetConfig;
}

export async function getDatasetConfigSchema(
    configId: string,
): Promise<ApiDatasetSchemaResults> {
    const res = await fetch(
        `${API_BASE}/api/dataset-configs/${encodeURIComponent(configId)}/schema`,
    );
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiDatasetSchemaResults;
}

export async function deleteDatasetConfig(configId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/dataset-configs/${encodeURIComponent(configId)}`, {
        method: 'DELETE',
    });
    if (!res.ok) {
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
}

export async function getDatasetConfigFile(configId: string): Promise<File> {
    // First get the config to extract the original filename as fallback
    const config = await getDatasetConfig(configId);
    const fallbackFilename = config.file_path;
    
    const res = await fetch(
        `${API_BASE}/api/dataset-configs/${encodeURIComponent(configId)}/file`,
    );
    if (!res.ok) {
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    
    const blob = await res.blob();
    const contentDisposition = res.headers.get('content-disposition');
    let filename = fallbackFilename; // Use fallback by default
    
    if (contentDisposition) {
        // Try multiple patterns for extracting filename
        const patterns = [
            /filename[*]?=["']?([^"'\n;]+)["']?/i,
            /filename="([^"]+)"/i,
            /filename='([^']+)'/i,
            /filename=([^;\n]+)/i,
        ];
        
        for (const pattern of patterns) {
            const match = pattern.exec(contentDisposition);
            if (match && match[1]) {
                filename = match[1].trim();
                console.log('Extracted filename from content-disposition:', filename);
                break;
            }
        }
    }
    
    console.log('Using filename:', filename, 'for File object');
    
    // Infer MIME type from extension
    const getMimeType = (fname: string): string => {
        const ext = fname.toLowerCase().split('.').pop();
        switch (ext) {
            case 'csv': return 'text/csv';
            case 'xlsx': return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
            case 'xls': return 'application/vnd.ms-excel';
            case 'parquet': return 'application/octet-stream';
            default: return blob.type || 'application/octet-stream';
        }
    };
    
    return new File([blob], filename, { type: getMimeType(filename) });
}

export async function getAeInsightsFromConfig(
    configId: string,
    maxResultsPerMetric = 25,
): Promise<ApiAeInsightsResults> {
    const res = await fetch(`${API_BASE}/api/ae/insights/from-config`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
            config_id: configId,
            max_results_per_metric: maxResultsPerMetric,
        }),
    });
    if (!res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('application/json')) {
            const body = (await res.json()) as { detail?: unknown };
            throw new Error(
                typeof body.detail === 'string'
                    ? body.detail
                    : `HTTP ${res.status}`,
            );
        }
        throw new Error((await res.text()) || `HTTP ${res.status}`);
    }
    return (await res.json()) as ApiAeInsightsResults;
}
