import type { Component } from 'vue';

import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ModuleId,
    PerformanceType,
} from '@/types/dataset-config';
import { binaryFeatureAeModule } from '@/modules/binary-feature-ae/definition';
import { mortalityAeModule } from '@/modules/mortality-ae/definition';

import type { ApiCoreDatasetSchemaResults } from './types/schema';

export type ModuleFieldError = {
    field: string;
    message: string;
};

export type ModuleValidationResult = {
    summary: string[];
    fieldErrors: ModuleFieldError[];
} | null;

export type AsyncSetupComponent = () => Promise<{ default: Component }>;

export type AnalysisModuleDefinition<TSetupState = unknown, TSetupContext = unknown> = {
    id: ModuleId;
    label: string;
    status: 'active' | 'planned' | 'hidden';
    analysisRoute: string;
    performanceType: PerformanceType;
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
};

export type AnyAnalysisModuleDefinition = AnalysisModuleDefinition<any, any>;

export const analysisModules: AnyAnalysisModuleDefinition[] = [
    mortalityAeModule,
    binaryFeatureAeModule,
];

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
    return getAnalysisModuleById(config.module_id);
}
