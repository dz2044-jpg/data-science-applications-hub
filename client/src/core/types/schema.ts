export type ApiCoreColumnKind = 'numeric' | 'categorical' | 'date';

export interface ApiCoreDatasetColumnInfo {
    name: string;
    kind: ApiCoreColumnKind;
    unique_values?: string[] | null;
    unique_count?: number | null;
    numeric_min?: number | null;
    numeric_max?: number | null;
    date_min?: string | null;
    date_max?: string | null;
}

export interface ApiCoreDatasetSchemaResults {
    dataset_name: string;
    columns: ApiCoreDatasetColumnInfo[];
    max_unique_values: number;
}

