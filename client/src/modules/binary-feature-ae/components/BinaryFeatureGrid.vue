<template>
    <q-table
        v-model:selected="selectedRowsModel"
        dense
        flat
        bordered
        row-key="row_id"
        selection="multiple"
        :rows="rows"
        :columns="columns"
        :pagination="{ rowsPerPage: 10 }"
        :rows-per-page-options="[10, 25, 50, 100]"
        @row-click="onRowClick"
    />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { QTableColumn } from 'quasar';

import type { ApiBinaryFeatureRow } from '@/types/binary-feature-ae';
import {
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';

const props = defineProps<{
    rows: ApiBinaryFeatureRow[];
    selectedRowIds: string[];
}>();

const emit = defineEmits<{
    'update:selectedRowIds': [value: string[]];
    'focus-row': [rowId: string];
}>();

const columns: QTableColumn<ApiBinaryFeatureRow>[] = [
    {
        name: 'rule',
        label: 'Rule',
        field: 'rule',
        align: 'left',
        sortable: true,
    },
    {
        name: 'RuleName',
        label: 'Rule Name',
        field: 'RuleName',
        align: 'left',
        sortable: true,
    },
    {
        name: 'category',
        label: 'Category',
        field: 'category',
        align: 'left',
        sortable: true,
    },
    {
        name: 'hit_count',
        label: 'Hit Count',
        field: 'hit_count',
        align: 'right',
        sortable: true,
        format: (value: number) => formatWholeNumber(value),
    },
    {
        name: 'hit_rate',
        label: 'Hit Rate',
        field: 'hit_rate',
        align: 'right',
        sortable: true,
        format: (value: number) => formatPercentFromRatio(value),
    },
    {
        name: 'claim_count',
        label: 'Claim Count',
        field: 'claim_count',
        align: 'right',
        sortable: true,
        format: (value: number) => formatWholeNumber(value),
    },
    {
        name: 'mec_sum',
        label: 'MEC Sum',
        field: 'mec_sum',
        align: 'right',
        sortable: true,
        format: (value: number) => value.toFixed(2),
    },
    {
        name: 'ae_ratio',
        label: 'A/E Ratio',
        field: 'ae_ratio',
        align: 'right',
        sortable: true,
        format: (value: number) => value.toFixed(4),
    },
    {
        name: 'ci_lower',
        label: 'CI Lower',
        field: 'ci_lower',
        align: 'right',
        sortable: true,
        format: (value: number) => value.toFixed(4),
    },
    {
        name: 'ci_upper',
        label: 'CI Upper',
        field: 'ci_upper',
        align: 'right',
        sortable: true,
        format: (value: number) => value.toFixed(4),
    },
    {
        name: 'significance_class',
        label: 'Significance',
        field: 'significance_class',
        align: 'left',
        sortable: true,
    },
    {
        name: 'dominant_cola',
        label: 'Dominant Mix',
        field: 'dominant_cola',
        align: 'left',
        sortable: true,
    },
    {
        name: 'impact_score',
        label: 'Impact Score',
        field: 'impact_score',
        align: 'right',
        sortable: true,
        format: (value: number) => value.toFixed(4),
    },
];

const selectedRowsModel = computed<ApiBinaryFeatureRow[]>({
    get() {
        return props.rows.filter((row) => props.selectedRowIds.includes(row.row_id));
    },
    set(rows) {
        emit(
            'update:selectedRowIds',
            rows.map((row) => row.row_id),
        );
    },
});

function onRowClick(_event: Event, row: ApiBinaryFeatureRow) {
    emit('focus-row', row.row_id);
}
</script>
