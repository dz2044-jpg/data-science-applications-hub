import type {
    ApiBinaryFeatureAeModuleConfig,
    PerformanceType,
} from '@/types/dataset-config';
import type {
    BinaryFeatureCiLevel,
    BinaryFeatureSignificance,
} from '@/types/binary-feature-ae';

export const BINARY_FEATURE_PERFORMANCE_TYPE: PerformanceType =
    'Binary Feature Mortality A/E';

export const SIGNIFICANCE_OPTIONS: BinaryFeatureSignificance[] = [
    'Elevated',
    'Uncertain',
    'Below Expected',
];

export const CI_LEVEL_OPTIONS: BinaryFeatureCiLevel[] = ['95', '90', '80'];

export const CONFIDENCE_BAND_ORDER = [
    'Elevated 95%',
    'Elevated 90%',
    'Elevated 80%',
    'Uncertain',
    'Below Expected 80%',
    'Below Expected 90%',
    'Below Expected 95%',
] as const;

export const CONFIDENCE_BAND_COLORS: Record<string, string> = {
    'Elevated 95%': '#d62728',
    'Elevated 90%': '#ff7f0e',
    'Elevated 80%': '#ffbb78',
    Uncertain: '#aec7e8',
    'Below Expected 80%': '#c5e0b4',
    'Below Expected 90%': '#70ad47',
    'Below Expected 95%': '#375623',
};

export const COLA_DEFINITIONS: Array<{
    key: keyof Pick<
        ApiBinaryFeatureAeModuleConfig,
        | 'cola_cancer_pct'
        | 'cola_heart_pct'
        | 'cola_nervous_system_pct'
        | 'cola_non_natural_pct'
        | 'cola_other_medical_pct'
        | 'cola_respiratory_pct'
        | 'cola_others_pct'
    >;
    label: string;
}> = [
    { key: 'cola_cancer_pct', label: 'Cancer' },
    { key: 'cola_heart_pct', label: 'Heart' },
    { key: 'cola_nervous_system_pct', label: 'Nervous System' },
    { key: 'cola_non_natural_pct', label: 'Non-natural' },
    { key: 'cola_other_medical_pct', label: 'Other Medical' },
    { key: 'cola_respiratory_pct', label: 'Respiratory' },
    { key: 'cola_others_pct', label: 'Others' },
];

export const BINARY_FEATURE_FIELD_DEFINITIONS: Array<{
    key: keyof ApiBinaryFeatureAeModuleConfig;
    label: string;
    sourceName: string;
}> = [
    { key: 'rule', label: 'Rule', sourceName: 'rule' },
    { key: 'RuleName', label: 'Rule Name', sourceName: 'RuleName' },
    { key: 'first_date', label: 'First Date', sourceName: 'first_date' },
    { key: 'category', label: 'Category', sourceName: 'category' },
    { key: 'hit_count', label: 'Hit Count', sourceName: 'hit_count' },
    { key: 'hit_rate', label: 'Hit Rate', sourceName: 'hit_rate' },
    { key: 'claim_count', label: 'Claim Count', sourceName: 'claim_count' },
    { key: 'mec_sum', label: 'MEC Sum', sourceName: 'mec_sum' },
    { key: 'ae_ratio', label: 'A/E Ratio', sourceName: 'ae_ratio' },
    { key: 'ci_lower_95', label: 'CI Lower 95', sourceName: 'ci_lower_95' },
    { key: 'ci_upper_95', label: 'CI Upper 95', sourceName: 'ci_upper_95' },
    { key: 'ci_lower_90', label: 'CI Lower 90', sourceName: 'ci_lower_90' },
    { key: 'ci_upper_90', label: 'CI Upper 90', sourceName: 'ci_upper_90' },
    { key: 'ci_lower_80', label: 'CI Lower 80', sourceName: 'ci_lower_80' },
    { key: 'ci_upper_80', label: 'CI Upper 80', sourceName: 'ci_upper_80' },
    {
        key: 'cola_cancer_pct',
        label: 'COLA Cancer %',
        sourceName: 'cola_cancer_pct',
    },
    {
        key: 'cola_heart_pct',
        label: 'COLA Heart %',
        sourceName: 'cola_heart_pct',
    },
    {
        key: 'cola_nervous_system_pct',
        label: 'COLA Nervous System %',
        sourceName: 'cola_nervous_system_pct',
    },
    {
        key: 'cola_non_natural_pct',
        label: 'COLA Non-natural %',
        sourceName: 'cola_non-natural_pct',
    },
    {
        key: 'cola_other_medical_pct',
        label: 'COLA Other Medical %',
        sourceName: 'cola_other_medical_pct',
    },
    {
        key: 'cola_respiratory_pct',
        label: 'COLA Respiratory %',
        sourceName: 'cola_respiratory_pct',
    },
    {
        key: 'cola_others_pct',
        label: 'COLA Others %',
        sourceName: 'cola_others_pct',
    },
];
