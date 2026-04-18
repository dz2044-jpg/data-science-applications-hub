import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
} from '@/types/dataset-config';
import { isBinaryFeatureDatasetConfig } from '@/types/dataset-config';

import type {
    AnalysisModuleDefinition,
    ModuleFieldError,
    ModuleValidationResult,
} from '@/core/registry';

export type BinaryFeatureAeSetupState = {
    rule: string | null;
    RuleName: string | null;
    first_date: string | null;
    category: string | null;
    hit_count: string | null;
    hit_rate: string | null;
    claim_count: string | null;
    mec_sum: string | null;
    ae_ratio: string | null;
    ci_lower_95: string | null;
    ci_upper_95: string | null;
    ci_lower_90: string | null;
    ci_upper_90: string | null;
    ci_lower_80: string | null;
    ci_upper_80: string | null;
    cola_cancer_pct: string | null;
    cola_heart_pct: string | null;
    cola_nervous_system_pct: string | null;
    cola_non_natural_pct: string | null;
    cola_other_medical_pct: string | null;
    cola_respiratory_pct: string | null;
    cola_others_pct: string | null;
};

function createInitialBinaryFeatureSetupState(): BinaryFeatureAeSetupState {
    return {
        rule: null,
        RuleName: null,
        first_date: null,
        category: null,
        hit_count: null,
        hit_rate: null,
        claim_count: null,
        mec_sum: null,
        ae_ratio: null,
        ci_lower_95: null,
        ci_upper_95: null,
        ci_lower_90: null,
        ci_upper_90: null,
        ci_lower_80: null,
        ci_upper_80: null,
        cola_cancer_pct: null,
        cola_heart_pct: null,
        cola_nervous_system_pct: null,
        cola_non_natural_pct: null,
        cola_other_medical_pct: null,
        cola_respiratory_pct: null,
        cola_others_pct: null,
    };
}

const requiredFields: Array<keyof BinaryFeatureAeSetupState> = [
    'rule',
    'RuleName',
    'first_date',
    'category',
    'hit_count',
    'hit_rate',
    'claim_count',
    'mec_sum',
    'ae_ratio',
    'ci_lower_95',
    'ci_upper_95',
    'ci_lower_90',
    'ci_upper_90',
    'ci_lower_80',
    'ci_upper_80',
    'cola_cancer_pct',
    'cola_heart_pct',
    'cola_nervous_system_pct',
    'cola_non_natural_pct',
    'cola_other_medical_pct',
    'cola_respiratory_pct',
    'cola_others_pct',
];

function validateBinaryFeatureSetupState(
    state: BinaryFeatureAeSetupState,
): ModuleValidationResult {
    const fieldErrors: ModuleFieldError[] = [];

    for (const field of requiredFields) {
        if (!state[field]) {
            fieldErrors.push({ field, message: 'Required' });
        }
    }

    const selectedColumns = Object.entries(state)
        .filter(([, value]) => Boolean(value))
        .map(([field, value]) => ({
            field,
            value: value as string,
        }));
    const seenColumns = new Map<string, string>();
    for (const entry of selectedColumns) {
        const existing = seenColumns.get(entry.value);
        if (existing) {
            fieldErrors.push({
                field: entry.field,
                message: `Already assigned to ${existing}`,
            });
        } else {
            seenColumns.set(entry.value, entry.field);
        }
    }

    if (fieldErrors.length === 0) {
        return null;
    }

    return {
        summary: ['Complete all required binary feature mappings with unique columns.'],
        fieldErrors,
    };
}

function buildBinaryFeatureCreateRequest(args: {
    datasetName: string;
    uploadedFileName: string;
    setupState: BinaryFeatureAeSetupState;
}): ApiCreateDatasetConfigRequest {
    return {
        dataset_name: args.datasetName,
        performance_type: 'Binary Feature Mortality A/E',
        file_path: args.uploadedFileName,
        module_id: 'binary_feature_ae',
        module_config: {
            rule: args.setupState.rule ?? '',
            RuleName: args.setupState.RuleName ?? '',
            first_date: args.setupState.first_date ?? '',
            category: args.setupState.category ?? '',
            hit_count: args.setupState.hit_count ?? '',
            hit_rate: args.setupState.hit_rate ?? '',
            claim_count: args.setupState.claim_count ?? '',
            mec_sum: args.setupState.mec_sum ?? '',
            ae_ratio: args.setupState.ae_ratio ?? '',
            ci_lower_95: args.setupState.ci_lower_95 ?? '',
            ci_upper_95: args.setupState.ci_upper_95 ?? '',
            ci_lower_90: args.setupState.ci_lower_90 ?? '',
            ci_upper_90: args.setupState.ci_upper_90 ?? '',
            ci_lower_80: args.setupState.ci_lower_80 ?? '',
            ci_upper_80: args.setupState.ci_upper_80 ?? '',
            cola_cancer_pct: args.setupState.cola_cancer_pct ?? '',
            cola_heart_pct: args.setupState.cola_heart_pct ?? '',
            cola_nervous_system_pct: args.setupState.cola_nervous_system_pct ?? '',
            cola_non_natural_pct: args.setupState.cola_non_natural_pct ?? '',
            cola_other_medical_pct: args.setupState.cola_other_medical_pct ?? '',
            cola_respiratory_pct: args.setupState.cola_respiratory_pct ?? '',
            cola_others_pct: args.setupState.cola_others_pct ?? '',
        },
    };
}

function loadBinaryFeatureSetupStateFromConfig(
    config: ApiDatasetConfig,
): BinaryFeatureAeSetupState {
    if (!isBinaryFeatureDatasetConfig(config)) {
        return createInitialBinaryFeatureSetupState();
    }

    return {
        ...config.module_config,
    };
}

export const binaryFeatureAeModule: AnalysisModuleDefinition<BinaryFeatureAeSetupState> = {
    id: 'binary_feature_ae',
    label: 'Binary Feature Mortality A/E',
    status: 'active',
    analysisRoute: '/binary-feature-ae/analysis',
    performanceType: 'Binary Feature Mortality A/E',
    setupComponent: () =>
        import('@/modules/binary-feature-ae/components/BinaryFeatureMapper.vue'),
    createInitialSetupState: createInitialBinaryFeatureSetupState,
    validateSetupState: validateBinaryFeatureSetupState,
    buildCreateRequest: buildBinaryFeatureCreateRequest,
    loadSetupStateFromExistingConfig: loadBinaryFeatureSetupStateFromConfig,
};
