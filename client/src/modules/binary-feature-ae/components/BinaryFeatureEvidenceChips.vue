<template>
    <div v-if="evidenceRefs.length">
        <div class="text-subtitle2 q-mb-sm">Evidence</div>
        <div class="row q-col-gutter-sm q-row-gutter-sm">
            <div
                v-for="evidence in evidenceRefs"
                :key="`${evidence.row_id}-${evidence.reason_type}-${evidence.reason_label}`"
                class="col-auto"
            >
                <q-chip
                    clickable
                    dense
                    class="evidence-chip"
                    :class="`evidence-chip--${evidence.severity}`"
                    @click="emit('focus-row', evidence.row_id)"
                >
                    {{ evidence.reason_label }}
                    <q-tooltip class="bg-grey-9 text-body2">
                        <div class="text-weight-medium">{{ evidence.rule_label }}</div>
                        <div class="text-caption">{{ evidence.reason_type }}</div>
                    </q-tooltip>
                </q-chip>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { ApiBinaryFeatureAiEvidenceRef } from '@/types/binary-feature-ae';

defineProps<{
    evidenceRefs: ApiBinaryFeatureAiEvidenceRef[];
}>();

const emit = defineEmits<{
    'focus-row': [rowId: string];
}>();
</script>

<style scoped>
.evidence-chip {
    border: 1px solid transparent;
    font-weight: 600;
}

.evidence-chip--high {
    background: #fdeaea;
    border-color: #f1b7bf;
    color: #8a0013;
}

.evidence-chip--medium {
    background: #fff4dd;
    border-color: #f2c46d;
    color: #8a5400;
}

.evidence-chip--low {
    background: #ecf5ff;
    border-color: #8eb7e0;
    color: #135487;
}

.evidence-chip--neutral {
    background: #f1f3f5;
    border-color: #cfd4da;
    color: #495057;
}
</style>
