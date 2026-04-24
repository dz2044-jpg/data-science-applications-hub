<template>
    <div v-if="hasBanners" class="q-mb-md">
        <q-banner
            v-if="isStale"
            rounded
            dense
            class="ai-state-banner ai-state-banner--stale q-mb-sm"
        >
            <template #avatar>
                <q-icon name="warning" />
            </template>
            This explanation is stale. The visible view or focused rule changed after
            the AI response was generated.
        </q-banner>

        <q-banner
            v-if="isFallback"
            rounded
            dense
            class="ai-state-banner ai-state-banner--fallback q-mb-sm"
        >
            <template #avatar>
                <q-icon name="shield" />
            </template>
            Deterministic fallback response shown.
        </q-banner>

        <q-banner
            v-if="!usedReferenceContext"
            rounded
            dense
            class="ai-state-banner ai-state-banner--info q-mb-sm"
        >
            <template #avatar>
                <q-icon name="info" />
            </template>
            No optional reference context was attached to this explanation.
        </q-banner>

        <q-banner
            v-if="showReferenceSources"
            rounded
            dense
            class="ai-state-banner ai-state-banner--reference q-mb-sm"
        >
            <template #avatar>
                <q-icon name="library_books" />
            </template>
            Reference context used: {{ referenceSources.join(', ') }}
        </q-banner>

        <q-banner
            v-if="validationNotes.length"
            rounded
            dense
            class="ai-state-banner ai-state-banner--validation"
        >
            <template #avatar>
                <q-icon name="fact_check" />
            </template>
            <div class="text-weight-medium">Validation Notes</div>
            <ul class="ai-state-banner__list">
                <li v-for="note in validationNotes" :key="note">
                    {{ note }}
                </li>
            </ul>
        </q-banner>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
    isStale: boolean;
    isFallback: boolean;
    usedReferenceContext: boolean;
    referenceSources: string[];
    validationNotes: string[];
}>();

const showReferenceSources = computed(
    () => props.usedReferenceContext && props.referenceSources.length > 0,
);

const hasBanners = computed(() => {
    return (
        props.isStale ||
        props.isFallback ||
        !props.usedReferenceContext ||
        showReferenceSources.value ||
        props.validationNotes.length > 0
    );
});
</script>

<style scoped>
.ai-state-banner {
    border: 1px solid transparent;
}

.ai-state-banner--stale {
    background: #fff3cd;
    border-color: #f2c46d;
    color: #6c4c00;
}

.ai-state-banner--fallback {
    background: #fdeaea;
    border-color: #f1b7bf;
    color: #8a0013;
}

.ai-state-banner--info {
    background: #f5f6f7;
    border-color: #d6d9dd;
    color: #4f5b66;
}

.ai-state-banner--reference {
    background: #ecf8f3;
    border-color: #9dd3b5;
    color: #136642;
}

.ai-state-banner--validation {
    background: #eef6ff;
    border-color: #9fc3e7;
    color: #164b7a;
}

.ai-state-banner__list {
    margin: 6px 0 0;
    padding-left: 18px;
}

.ai-state-banner__list li + li {
    margin-top: 4px;
}
</style>
