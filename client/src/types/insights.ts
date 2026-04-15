import type { ApiAeAtomicVariable } from '@/types/ae';

export interface ApiAeInsightDrill {
    x_variable: ApiAeAtomicVariable;
    split_variable?: ApiAeAtomicVariable | null;
}

export interface ApiAeInsightResult {
    dimensions: string[];
    segment_label: string;
    segment_filters: Record<string, string>;
    sample_size: number;
    exposure_count: number;
    actual_count: number;
    expected_count: number;
    variance_count: number;
    ae_count: number | null;
    actual_amount: number;
    expected_amount: number;
    variance_amount: number;
    ae_amount: number | null;
    drill: ApiAeInsightDrill;
}

export interface ApiAeInsightsResults {
    config_id: string;
    count_insights: ApiAeInsightResult[];
    amount_insights: ApiAeInsightResult[];
}
