import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
} from '@/types/dataset-config';
import { isMortalityDatasetConfig } from '@/types/dataset-config';
import type { ApiDatasetSchemaResults } from '@/types/datasets';

import type {
    AnalysisModuleDefinition,
    ModuleFieldError,
    ModuleValidationResult,
} from '@/core/registry';
import { postAeUploadSchema } from '@/modules/mortality-ae/api';

export type MortalityAeSetupState = {
    policy_number_column: string | null;
    face_amount_column: string | null;
    mac_column: string | null;
    mec_column: string | null;
    man_column: string | null;
    men_column: string | null;
    moc_column: string | null;
    cola_m1_column: string | null;
};

function createInitialMortalitySetupState(): MortalityAeSetupState {
    return {
        policy_number_column: null,
        face_amount_column: null,
        mac_column: null,
        mec_column: null,
        man_column: null,
        men_column: null,
        moc_column: null,
        cola_m1_column: null,
    };
}

function validateMortalitySetupState(
    state: MortalityAeSetupState,
): ModuleValidationResult {
    const fieldErrors: ModuleFieldError[] = [];
    const requiredFields: Array<keyof MortalityAeSetupState> = [
        'mac_column',
        'mec_column',
        'man_column',
        'men_column',
    ];

    for (const field of requiredFields) {
        if (!state[field]) {
            fieldErrors.push({ field, message: 'Required' });
        }
    }

    if (fieldErrors.length === 0) {
        return null;
    }

    return {
        summary: ['Complete the required mortality column mappings.'],
        fieldErrors,
    };
}

function buildMortalityCreateRequest(args: {
    datasetName: string;
    uploadedFileName: string;
    setupState: MortalityAeSetupState;
}): ApiCreateDatasetConfigRequest {
    return {
        dataset_name: args.datasetName,
        performance_type: 'Mortality A/E Analysis',
        file_path: args.uploadedFileName,
        module_id: 'mortality_ae',
        module_config: {
            policy_number_column: args.setupState.policy_number_column,
            face_amount_column: args.setupState.face_amount_column,
            mac_column: args.setupState.mac_column ?? '',
            mec_column: args.setupState.mec_column ?? '',
            man_column: args.setupState.man_column ?? '',
            men_column: args.setupState.men_column ?? '',
            moc_column: args.setupState.moc_column,
            cola_m1_column: args.setupState.cola_m1_column,
        },
    };
}

function loadMortalitySetupStateFromConfig(
    config: ApiDatasetConfig,
): MortalityAeSetupState {
    if (!isMortalityDatasetConfig(config)) {
        return createInitialMortalitySetupState();
    }

    return {
        policy_number_column: config.module_config.policy_number_column,
        face_amount_column: config.module_config.face_amount_column,
        mac_column: config.module_config.mac_column,
        mec_column: config.module_config.mec_column,
        man_column: config.module_config.man_column,
        men_column: config.module_config.men_column,
        moc_column: config.module_config.moc_column,
        cola_m1_column: config.module_config.cola_m1_column,
    };
}

export const mortalityAeModule: AnalysisModuleDefinition<
    MortalityAeSetupState,
    ApiDatasetSchemaResults
> = {
    id: 'mortality_ae',
    label: 'Experience Study Mortality A/E',
    status: 'active',
    analysisRoute: '/mortality-ae/analysis',
    performanceType: 'Mortality A/E Analysis',
    setupComponent: () =>
        import('@/modules/mortality-ae/components/MortalityColumnMapper.vue'),
    createInitialSetupState: createInitialMortalitySetupState,
    validateSetupState: validateMortalitySetupState,
    buildCreateRequest: buildMortalityCreateRequest,
    loadSetupStateFromExistingConfig: loadMortalitySetupStateFromConfig,
    loadSetupContext: async (file: File) => postAeUploadSchema(file),
};
