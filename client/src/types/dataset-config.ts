export type PerformanceType = "Mortality A/E Analysis";

export interface ApiColumnMapping {
    policy_number_column: string | null;
    face_amount_column: string | null;
    mac_column: string;
    mec_column: string;
    man_column: string;
    men_column: string;
    moc_column: string | null;
    cola_m1_column: string | null;
}

export interface ApiDatasetConfig {
    id: string;
    dataset_name: string;
    performance_type: PerformanceType;
    file_path: string;
    column_mapping: ApiColumnMapping;
    created_date: string;  // ISO format datetime string
}

export interface ApiCreateDatasetConfigRequest {
    dataset_name: string;
    performance_type: PerformanceType;
    file_path: string;
    column_mapping: ApiColumnMapping;
}

export interface ApiListDatasetConfigsResults {
    configs: ApiDatasetConfig[];
}
