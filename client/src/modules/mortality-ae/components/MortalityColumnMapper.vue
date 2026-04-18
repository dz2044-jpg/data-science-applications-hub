<template>
    <q-card flat bordered class="q-mt-md">
        <q-card-section class="q-pb-sm">
            <div class="text-h6">Experience Study Mortality A/E Mapping</div>
            <div class="text-body2 text-grey-7">
                Select which columns correspond to the required mortality fields.
            </div>
        </q-card-section>

        <q-card-section v-if="schema" class="q-pt-none">
            <div class="row items-center q-col-gutter-md q-mb-md">
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.policy_number_column"
                        :options="columnMappingOptions.policy_number"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="Policy Number Column [Optional]"
                        clearable
                        :error="Boolean(errorsByField.policy_number_column)"
                        :error-message="errorsByField.policy_number_column"
                        @update:model-value="updateField('policy_number_column', $event)"
                    />
                </div>
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.face_amount_column"
                        :options="columnMappingOptions.face_amount"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="Face Amount Column [Optional]"
                        clearable
                        :error="Boolean(errorsByField.face_amount_column)"
                        :error-message="errorsByField.face_amount_column"
                        @update:model-value="updateField('face_amount_column', $event)"
                    />
                </div>
            </div>
            <div class="row items-center q-col-gutter-md q-mb-md">
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.mac_column"
                        :options="columnMappingOptions.mac"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="MAC Column (Actual Deaths Count) *"
                        clearable
                        :error="Boolean(errorsByField.mac_column)"
                        :error-message="errorsByField.mac_column"
                        @update:model-value="updateField('mac_column', $event)"
                    />
                </div>
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.mec_column"
                        :options="columnMappingOptions.mec"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="MEC Column (Expected Deaths Count) *"
                        clearable
                        :error="Boolean(errorsByField.mec_column)"
                        :error-message="errorsByField.mec_column"
                        @update:model-value="updateField('mec_column', $event)"
                    />
                </div>
            </div>
            <div class="row items-center q-col-gutter-md q-mb-md">
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.man_column"
                        :options="columnMappingOptions.man"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="MAN Column (Actual Deaths Amount) *"
                        clearable
                        :error="Boolean(errorsByField.man_column)"
                        :error-message="errorsByField.man_column"
                        @update:model-value="updateField('man_column', $event)"
                    />
                </div>
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.men_column"
                        :options="columnMappingOptions.men"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="MEN Column (Expected Deaths Amount) *"
                        clearable
                        :error="Boolean(errorsByField.men_column)"
                        :error-message="errorsByField.men_column"
                        @update:model-value="updateField('men_column', $event)"
                    />
                </div>
            </div>
            <div class="row items-center q-col-gutter-md">
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.moc_column"
                        :options="columnMappingOptions.moc"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="MOC Column (Exposure Count) [Optional]"
                        clearable
                        :error="Boolean(errorsByField.moc_column)"
                        :error-message="errorsByField.moc_column"
                        @update:model-value="updateField('moc_column', $event)"
                    />
                </div>
                <div class="col-12 col-md-6">
                    <q-select
                        :model-value="setupState.cola_m1_column"
                        :options="columnMappingOptions.cola_m1"
                        emit-value
                        map-options
                        outlined
                        dense
                        options-dense
                        label="COLA Column (Cause of Death) [Optional]"
                        clearable
                        :error="Boolean(errorsByField.cola_m1_column)"
                        :error-message="errorsByField.cola_m1_column"
                        @update:model-value="updateField('cola_m1_column', $event)"
                    />
                </div>
            </div>
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';

import type { ApiDatasetSchemaResults } from '@/types/datasets';
import type { ModuleFieldError } from '@/core/registry';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';
import type { MortalityAeSetupState } from '@/modules/mortality-ae/definition';

const props = defineProps<{
    schema: ApiCoreDatasetSchemaResults | null;
    setupState: MortalityAeSetupState;
    setupErrors?: ModuleFieldError[] | null;
    setupContext?: ApiDatasetSchemaResults | null;
}>();

const emit = defineEmits<{
    'update:setupState': [value: MortalityAeSetupState];
}>();

const errorsByField = computed<Record<string, string>>(() => {
    const next: Record<string, string> = {};
    for (const error of props.setupErrors ?? []) {
        next[error.field] = error.message;
    }
    return next;
});

const fallbackOptions = computed(() => {
    return (props.schema?.columns ?? []).map((column) => ({
        label: column.name,
        value: column.name,
    }));
});

const columnMappingOptions = computed(() => {
    const suggestions = props.setupContext?.column_suggestions;
    if (!suggestions) {
        return {
            policy_number: fallbackOptions.value,
            face_amount: fallbackOptions.value,
            mac: fallbackOptions.value,
            mec: fallbackOptions.value,
            man: fallbackOptions.value,
            men: fallbackOptions.value,
            moc: fallbackOptions.value,
            cola_m1: fallbackOptions.value,
        };
    }

    return {
        policy_number: suggestions.policy_number_candidates.map((value) => ({
            label: value,
            value,
        })),
        face_amount: suggestions.face_amount_candidates.map((value) => ({
            label: value,
            value,
        })),
        mac: suggestions.mac_candidates.map((value) => ({
            label: value,
            value,
        })),
        mec: suggestions.mec_candidates.map((value) => ({
            label: value,
            value,
        })),
        man: suggestions.man_candidates.map((value) => ({
            label: value,
            value,
        })),
        men: suggestions.men_candidates.map((value) => ({
            label: value,
            value,
        })),
        moc: suggestions.moc_candidates.map((value) => ({
            label: value,
            value,
        })),
        cola_m1: suggestions.cola_m1_candidates.map((value) => ({
            label: value,
            value,
        })),
    };
});

function hasAnySetupValue(state: MortalityAeSetupState): boolean {
    return Object.values(state).some((value) => Boolean(value));
}

function updateField(
    field: keyof MortalityAeSetupState,
    value: string | null,
) {
    emit('update:setupState', {
        ...props.setupState,
        [field]: value,
    });
}

watch(
    () => props.setupContext,
    (context) => {
        if (!context || hasAnySetupValue(props.setupState)) {
            return;
        }
        const suggestions = context.column_suggestions;
        if (!suggestions) {
            return;
        }
        emit('update:setupState', {
            policy_number_column: suggestions.policy_number_candidates[0] || null,
            face_amount_column: suggestions.face_amount_candidates[0] || null,
            mac_column: suggestions.mac_candidates[0] || context.mac_column,
            mec_column: suggestions.mec_candidates[0] || context.mec_column,
            man_column: suggestions.man_candidates[0] || null,
            men_column: suggestions.men_candidates[0] || null,
            moc_column: suggestions.moc_candidates[0] || null,
            cola_m1_column: suggestions.cola_m1_candidates[0] || null,
        });
    },
    { immediate: true },
);
</script>
