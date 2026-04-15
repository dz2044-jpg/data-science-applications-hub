<template>
    <q-table
        dense
        flat
        :rows="tableRows"
        :columns="tableColumns"
        row-key="time_s"
        :rows-per-page-options="[10, 25, 50]"
    />
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { ApiChartTable } from '@/types/chart';

const props = defineProps<{
    table: ApiChartTable;
}>();

const tableColumns = computed(() => {
    return props.table.columns.map((c) => ({
        name: c.name,
        label: c.name,
        field: c.name,
        align: 'left' as const,
        sortable: false,
    }));
});

const tableRows = computed(() => {
    return props.table.rows.map((row) => {
        const obj: Record<string, number | null> = {};
        props.table.columns.forEach((c, idx) => {
            obj[c.name] = row[idx] ?? null;
        });
        return obj;
    });
});
</script>

