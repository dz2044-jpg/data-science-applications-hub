export type ApiColumnKind = 'numeric' | 'categorical' | 'date';

export interface ApiDatasetColumnInfo {
    name: string;
    kind: ApiColumnKind;
    unique_values?: string[] | null;
    unique_count?: number | null;
    numeric_min?: number | null;
    numeric_max?: number | null;
    date_min?: string | null;
    date_max?: string | null;
}

export interface ApiColumnMappingSuggestions {
    policy_number_candidates: string[];
    face_amount_candidates: string[];
    mac_candidates: string[];
    mec_candidates: string[];
    man_candidates: string[];
    men_candidates: string[];
    moc_candidates: string[];
    cola_m1_candidates: string[];
}

export interface ApiDatasetSchemaResults {
    dataset_name: string;
    columns: ApiDatasetColumnInfo[];
    mec_column: string;
    mac_column: string;
    max_unique_values: number;
    column_suggestions?: ApiColumnMappingSuggestions | null;
}
