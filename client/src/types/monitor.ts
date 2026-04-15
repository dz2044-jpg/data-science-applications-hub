import type { ApiChartTable } from './chart';

export interface ApiMonitorFromCsvParameters {
    date_column?: string;
    value_column?: string;
    group_column?: string | null;
    date_format?: string | null;
    min_date?: string | null;
    max_date?: string | null;
    rolling_window_days?: number;
    baseline_window_days?: number;
    zscore_threshold?: number;
}

export interface ApiMonitorFromDatasetParameters extends ApiMonitorFromCsvParameters {
    dataset_name: string;
}

export interface ApiDatasetSummary {
    rows: number;
    days: number;
    series: string[];
}

export interface ApiAnomalyEvent {
    time_s: number;
    series: string;
    value: number;
    zscore: number;
}

export interface ApiMonitorFromCsvResults {
    summary: ApiDatasetSummary;
    chart_data: Record<string, ApiChartTable>;
    anomalies: ApiAnomalyEvent[];
}
