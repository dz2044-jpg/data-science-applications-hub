import type { Component } from 'vue';

import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    PerformanceType,
} from '@/types/dataset-config';
import type { ApiDatasetSchemaResults } from '@/types/datasets';
import { postAeUploadSchema } from '@/utils/api';

import type { ApiCoreDatasetSchemaResults } from './types/schema';

export type ModuleId = 'mortality_ae';

export type ModuleFieldError = {
    field: string;
    message: string;
};

export type ModuleValidationResult = {
    summary: string[];
    fieldErrors: ModuleFieldError[];
} | null;

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

export type AsyncSetupComponent = () => Promise<{ default: Component }>;

export type AnalysisModuleDefinition<TSetupState = unknown, TSetupContext = unknown> = {
    id: ModuleId;
    label: string;
    status: 'active' | 'planned' | 'hidden';
    analysisRoute: string;
    setupComponent: AsyncSetupComponent;
    createInitialSetupState: () => TSetupState;
    validateSetupState: (state: TSetupState) => ModuleValidationResult;
    buildCreateRequest: (args: {
        datasetName: string;
        uploadedFileName: string;
        setupState: TSetupState;
    }) => ApiCreateDatasetConfigRequest;
    loadSetupStateFromExistingConfig?: (config: ApiDatasetConfig) => TSetupState;
    loadSetupContext?: (
        file: File,
        schema: ApiCoreDatasetSchemaResults,
    ) => Promise<TSetupContext>;
    performanceTypes?: PerformanceType[];
};

export type AnyAnalysisModuleDefinition = AnalysisModuleDefinition<any, any>;

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
            fieldErrors.push({
                field,
                message: 'Required',
            });
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
        column_mapping: {
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
    return {
        policy_number_column: config.column_mapping.policy_number_column,
        face_amount_column: config.column_mapping.face_amount_column,
        mac_column: config.column_mapping.mac_column,
        mec_column: config.column_mapping.mec_column,
        man_column: config.column_mapping.man_column,
        men_column: config.column_mapping.men_column,
        moc_column: config.column_mapping.moc_column,
        cola_m1_column: config.column_mapping.cola_m1_column,
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
    setupComponent: () =>
        import('@/modules/mortality-ae/components/MortalityColumnMapper.vue'),
    createInitialSetupState: createInitialMortalitySetupState,
    validateSetupState: validateMortalitySetupState,
    buildCreateRequest: buildMortalityCreateRequest,
    loadSetupStateFromExistingConfig: loadMortalitySetupStateFromConfig,
    loadSetupContext: async (file: File) => postAeUploadSchema(file),
    performanceTypes: ['Mortality A/E Analysis'],
};

export const analysisModules: AnyAnalysisModuleDefinition[] = [mortalityAeModule];

export const activeAnalysisModules = analysisModules.filter(
    (module) => module.status === 'active',
);

export function getAnalysisModuleById(
    moduleId: ModuleId | null,
): AnyAnalysisModuleDefinition | null {
    if (!moduleId) {
        return null;
    }
    return analysisModules.find((module) => module.id === moduleId) ?? null;
}

export function getAnalysisModuleForConfig(
    config: ApiDatasetConfig,
): AnyAnalysisModuleDefinition | null {
    return (
        analysisModules.find((module) =>
            module.performanceTypes?.includes(config.performance_type),
        ) ?? null
    );
}

