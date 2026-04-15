<template>
    <q-page class="q-pa-md">
        <div class="main-container">
            <q-banner class="q-px-md q-pt-md q-pb-sm">
                <div class="row items-center q-gutter-x-sm">
                    <span class="text-h4">Experience Study Mortality A/E</span>
                </div>
                <div class="text-body2 text-grey-7 q-mt-xs">
                    Load a saved mortality configuration and run the Experience Study
                    Mortality A/E workflow.
                </div>
            </q-banner>

            <q-card class="q-mt-md">
                <q-expansion-item
                    switch-toggle-side
                    label="About"
                    header-class="text-primary"
                >
                    <div class="q-pa-md">
                        This tool runs locally and analyzes uploaded data files (CSV, Excel, Parquet). It computes A/E 
                        (Actual vs Expected) ratios across x-axis groups and can optionally 
                        overlay split results on the same chart.
                    </div>
                </q-expansion-item>
            </q-card>

            <q-card class="q-pa-md q-mt-md">
                <q-banner class="q-pa-sm">
                    <span class="text-h5">Inputs</span>
                </q-banner>

                <form class="q-mt-sm" @submit.prevent="onAnalyze">
                    <!-- Dataset Config Selector -->
                    <div class="row items-center q-col-gutter-md q-mb-md">
                        <div class="col-12">
                            <q-select
                                v-model="selectedConfigId"
                                :options="configOptions"
                                emit-value
                                map-options
                                outlined
                                dense
                                label="Select Saved Dataset Configuration"
                                class="input-600"
                                clearable
                                :loading="configsLoading"
                                hint="Choose a previously configured dataset from the Data Input page"
                            >
                                <template v-slot:prepend>
                                    <q-icon name="folder_open" />
                                </template>
                            </q-select>
                        </div>
                    </div>

                    <!-- Show config info when selected -->
                    <div v-if="selectedConfig" class="q-mb-md">
                        <q-banner class="bg-green-1" dense>
                            <template v-slot:avatar>
                                <q-icon name="check_circle" color="positive" />
                            </template>
                            <strong>{{ selectedConfig.dataset_name }}</strong> loaded successfully
                            <br />File and column mappings loaded automatically from saved configuration
                        </q-banner>
                    </div>

                    <!-- Message when no config selected -->
                    <div v-if="!selectedConfig" class="q-mb-md">
                        <q-banner class="bg-grey-3" dense>
                            <template v-slot:avatar>
                                <q-icon name="info" color="grey-7" />
                            </template>
                            Please select a saved dataset configuration above, or go to the <strong>Central Setup</strong> page to create a new one.
                        </q-banner>
                    </div>

                    <AeInsightBanner
                        v-if="selectedConfig"
                        class="q-mb-md"
                        :insights="insightResults"
                        :loading="insightsLoading"
                        :error="insightsError"
                        @apply="applyInsightDrill"
                    />

                    <q-card flat bordered class="q-mt-md">
                        <q-card-section class="q-pb-sm">
                            <div class="text-h6">X-axis Variable</div>
                            <div class="text-body2 text-grey-7">
                                Choose the variable to plot on the x-axis. Numeric variables can
                                be binned; date variables can be binned; categorical variables can
                                be grouped.
                            </div>
                        </q-card-section>

                        <q-card-section class="q-pt-none">
                            <div class="row items-center q-gutter-md">
                                <q-select
                                    v-model="xVarName"
                                    :options="xVariableOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="X variable"
                                    class="input-200"
                                    :disable="!schema || schemaLoading"
                                    clearable
                                />

                                <template
                                    v-if="
                                        !isXCross &&
                                        (xVarInfo?.kind === 'numeric' || xVarInfo?.kind === 'date')
                                    "
                                >
                                    <q-select
                                        v-model="xNumericBinning"
                                        :options="numericBinningOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="Binning"
                                        class="input-200"
                                    />
                                    <q-select
                                        v-if="xNumericBinning !== 'custom'"
                                        v-model="xNumericBinCount"
                                        :options="binCountOptions"
                                        outlined
                                        dense
                                        options-dense
                                        emit-value
                                        map-options
                                        label="Bins"
                                        class="input-200"
                                    />
                                    <q-input
                                        v-else
                                        v-model="xNumericCustomEdgesRaw"
                                        outlined
                                        dense
                                        label="Custom edges"
                                        class="input-200"
                                    />
                                </template>

                                <template v-else-if="!isXCross && xVarInfo?.kind === 'categorical'">
                                    <q-select
                                        v-model="xCatGroupCount"
                                        :options="categoricalGroupCountOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="Groups"
                                        class="input-200"
                                    />
                                </template>

                                <template v-else-if="isXCross">
                                    <q-select
                                        v-model="xCrossAName"
                                        :options="baseVariableOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="Variable A"
                                        class="input-200"
                                        :disable="!schema || schemaLoading"
                                        clearable
                                    />
                                    <template
                                        v-if="
                                            xCrossAVarInfo?.kind === 'numeric' ||
                                            xCrossAVarInfo?.kind === 'date'
                                        "
                                    >
                                        <q-select
                                            v-model="xCrossANumericBinning"
                                            :options="numericBinningOptions"
                                            emit-value
                                            map-options
                                            outlined
                                            dense
                                            options-dense
                                            label="A binning"
                                            class="input-200"
                                        />
                                        <q-select
                                            v-if="xCrossANumericBinning !== 'custom'"
                                            v-model="xCrossANumericBinCount"
                                            :options="binCountOptions"
                                            outlined
                                            dense
                                            options-dense
                                            emit-value
                                            map-options
                                            label="A bins"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-else
                                            v-model="xCrossANumericCustomEdgesRaw"
                                            outlined
                                            dense
                                            label="A edges"
                                            class="input-200"
                                        />
                                    </template>

                                    <q-select
                                        v-model="xCrossBName"
                                        :options="baseVariableOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="Variable B"
                                        class="input-200"
                                        :disable="!schema || schemaLoading"
                                        clearable
                                    />
                                    <template
                                        v-if="
                                            xCrossBVarInfo?.kind === 'numeric' ||
                                            xCrossBVarInfo?.kind === 'date'
                                        "
                                    >
                                        <q-select
                                            v-model="xCrossBNumericBinning"
                                            :options="numericBinningOptions"
                                            emit-value
                                            map-options
                                            outlined
                                            dense
                                            options-dense
                                            label="B binning"
                                            class="input-200"
                                        />
                                        <q-select
                                            v-if="xCrossBNumericBinning !== 'custom'"
                                            v-model="xCrossBNumericBinCount"
                                            :options="binCountOptions"
                                            outlined
                                            dense
                                            options-dense
                                            emit-value
                                            map-options
                                            label="B bins"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-else
                                            v-model="xCrossBNumericCustomEdgesRaw"
                                            outlined
                                            dense
                                            label="B edges"
                                            class="input-200"
                                        />
                                    </template>

                                    <q-select
                                        v-model="xCrossGroupCount"
                                        :options="crossGroupCountOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="Groups"
                                        class="input-200"
                                        :disable="!xCrossAName || !xCrossBName"
                                    />
                                </template>

                                <q-space />
                                <div v-if="!isXCross && xVarInfo" class="text-caption text-grey-7">
                                    <span class="text-weight-medium">Type:</span>
                                    {{ xVarInfo.kind }}
                                    <template v-if="xVarInfo.kind === 'numeric'">
                                         <span class="text-weight-medium">Range:</span>
                                        {{ xVarInfo.numeric_min ?? '-' }} ->
                                        {{ xVarInfo.numeric_max ?? '-' }}
                                    </template>
                                    <template v-else-if="xVarInfo.kind === 'date'">
                                         <span class="text-weight-medium">Range:</span>
                                        {{ xVarInfo.date_min ?? '-' }} ->
                                        {{ xVarInfo.date_max ?? '-' }}
                                    </template>
                                    <template v-else>
                                         <span class="text-weight-medium">Unique:</span>
                                        {{ xVarInfo.unique_count ?? 'unknown' }}
                                        <span
                                            v-if="
                                                xVarInfo.unique_values &&
                                                xVarInfo.unique_count &&
                                                xVarInfo.unique_values.length <
                                                    xVarInfo.unique_count
                                            "
                                        >
                                            (first {{ xVarInfo.unique_values.length }})
                                        </span>
                                    </template>
                                </div>
                                <div v-else-if="isXCross" class="text-caption text-grey-7">
                                    <span class="text-weight-medium">A:</span>
                                    {{ xCrossAVarInfo?.kind ?? '-' }}
                                    <template v-if="xCrossAVarInfo?.kind === 'numeric'">
                                         {{ xCrossAVarInfo.numeric_min ?? '-' }} ->
                                        {{ xCrossAVarInfo.numeric_max ?? '-' }}
                                    </template>
                                    <template v-else-if="xCrossAVarInfo?.kind === 'date'">
                                         {{ xCrossAVarInfo.date_min ?? '-' }} ->
                                        {{ xCrossAVarInfo.date_max ?? '-' }}
                                    </template>
                                    <template v-else-if="xCrossAVarInfo?.kind === 'categorical'">
                                         {{ xCrossAVarInfo.unique_count ?? 'unknown' }} unique
                                    </template>
                                    |
                                    <span class="text-weight-medium">B:</span>
                                    {{ xCrossBVarInfo?.kind ?? '-' }}
                                    <template v-if="xCrossBVarInfo?.kind === 'numeric'">
                                         {{ xCrossBVarInfo.numeric_min ?? '-' }} ->
                                        {{ xCrossBVarInfo.numeric_max ?? '-' }}
                                    </template>
                                    <template v-else-if="xCrossBVarInfo?.kind === 'date'">
                                         {{ xCrossBVarInfo.date_min ?? '-' }} ->
                                        {{ xCrossBVarInfo.date_max ?? '-' }}
                                    </template>
                                    <template v-else-if="xCrossBVarInfo?.kind === 'categorical'">
                                         {{ xCrossBVarInfo.unique_count ?? 'unknown' }} unique
                                    </template>
                                    <span v-if="xCrossLabelsLoading">
                                        <q-spinner size="14px" class="q-ml-xs" />
                                    </span>
                                </div>
                            </div>

                            <div v-if="!isXCross && xVarInfo" class="q-mt-sm">
                                <div v-if="xVarInfo.kind === 'categorical'" class="q-mt-sm">
                                    <div
                                        v-if="xCatGroupCount !== 'all' && !xCatUniqueValues"
                                        class="q-mt-sm"
                                    >
                                        <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                            This column has too many unique values to edit groups
                                            in the UI. Reduce cardinality or increase
                                            `AEMONITOR_MAX_UNIQUE_VALUES`.
                                        </q-banner>
                                    </div>

                                    <div
                                        v-if="xCatGroupCount !== 'all' && xCatUniqueValues"
                                        class="q-mt-md"
                                    >
                                        <div class="text-subtitle2 q-mb-sm">
                                            Group definitions (last group is Remaining)
                                        </div>

                                        <div
                                            v-for="(g, idx) in xCatGroups"
                                            :key="idx"
                                            class="q-mb-sm"
                                        >
                                            <div class="row items-center q-gutter-md">
                                                <q-input
                                                    v-model="g.name"
                                                    filled
                                                    dense
                                                    label="Name"
                                                    class="input-200"
                                                />
                                                <q-input
                                                    v-model="g.x_position"
                                                    filled
                                                    dense
                                                    type="number"
                                                    label="Pos"
                                                    class="input-120"
                                                    placeholder="Auto"
                                                />
                                                <q-select
                                                    v-model="g.values"
                                                    :options="xCatUniqueValues"
                                                    outlined
                                                    dense
                                                    options-dense
                                                    multiple
                                                    use-chips
                                                    label="Values"
                                                    style="min-width: 420px; max-width: 100%"
                                                />
                                            </div>
                                        </div>

                                        <div class="q-mb-sm">
                                            <div class="row items-center q-gutter-md">
                                                <q-input
                                                    v-model="xCatRemainingName"
                                                    filled
                                                    dense
                                                    label="Name"
                                                    class="input-200"
                                                />
                                                <q-input
                                                    v-model="xCatRemainingPosition"
                                                    filled
                                                    dense
                                                    type="number"
                                                    label="Pos"
                                                    class="input-120"
                                                    placeholder="Auto"
                                                />
                                                <q-select
                                                    :model-value="xCatRemainingValues"
                                                    :options="xCatUniqueValues"
                                                    outlined
                                                    dense
                                                    options-dense
                                                    multiple
                                                    use-chips
                                                    disable
                                                    label="Values"
                                                    style="min-width: 420px; max-width: 100%"
                                                >
                                                    <q-tooltip
                                                        v-if="xCatRemainingPreview"
                                                        anchor="top middle"
                                                        self="bottom middle"
                                                    >
                                                        {{ xCatRemainingPreview }}
                                                    </q-tooltip>
                                                </q-select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div v-else-if="isXCross" class="q-mt-sm">
                                <div v-if="xCrossTooManyUniques" class="q-mt-sm">
                                    <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                        One of the selected variables has too many unique values to
                                        edit cross groups in the UI. Reduce cardinality or increase
                                        `AEMONITOR_MAX_UNIQUE_VALUES`.
                                    </q-banner>
                                </div>

                                <div v-else class="q-mt-md">
                                    <div class="text-subtitle2 q-mb-sm">
                                        Cross group definitions (last group is Remaining)
                                    </div>

                                    <div
                                        v-for="(g, idx) in xCrossGroups"
                                        :key="`x-cross-${idx}`"
                                        class="q-mb-sm"
                                    >
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="g.name"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="g.x_position"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-checkbox v-model="g.a_any" dense label="Any A" />
                                            <q-select
                                                v-model="g.a_values"
                                                :options="xCrossALabels || []"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                label="A values"
                                                :disable="g.a_any || !xCrossALabels"
                                                style="min-width: 320px; max-width: 100%"
                                            />
                                            <q-checkbox v-model="g.b_any" dense label="Any B" />
                                            <q-select
                                                v-model="g.b_values"
                                                :options="xCrossBLabels || []"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                label="B values"
                                                :disable="g.b_any || !xCrossBLabels"
                                                style="min-width: 320px; max-width: 100%"
                                            />
                                        </div>
                                        <div
                                            v-if="g.a_any && g.b_any"
                                            class="text-negative text-caption q-mt-xs"
                                        >
                                            A group cannot be both Any A and Any B.
                                        </div>
                                    </div>

                                    <div class="q-mb-sm">
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="xCrossRemainingName"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="xCrossRemainingPosition"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-banner class="q-pa-xs bg-grey-1 text-grey-8">
                                                Remaining = everything not matched by earlier
                                                groups
                                            </q-banner>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

	                    <q-card flat bordered class="q-mt-md">
	                        <q-card-section class="q-pb-sm">
	                            <div class="text-h6">Split Variable (optional)</div>
	                            <div class="text-body2 text-grey-7">
	                                Optionally split results into multiple series by a second
	                                variable. Configure binning/grouping the same way.
	                            </div>
	                        </q-card-section>

	                        <q-card-section class="q-pt-none">
	                            <div class="row items-center q-gutter-md">
	                                <q-select
	                                    v-model="splitVarName"
	                                    :options="splitVariableOptions"
	                                    emit-value
	                                    map-options
	                                    outlined
	                                    dense
	                                    options-dense
	                                    label="Split variable"
	                                    class="input-200"
	                                    :disable="!schema || schemaLoading"
	                                    clearable
	                                />

	                                <template
	                                    v-if="
	                                        !isSplitCross &&
	                                        (splitVarInfo?.kind === 'numeric' ||
	                                            splitVarInfo?.kind === 'date')
	                                    "
	                                >
	                                    <q-select
	                                        v-model="splitNumericBinning"
	                                        :options="numericBinningOptions"
	                                        emit-value
	                                        map-options
	                                        outlined
	                                        dense
	                                        options-dense
	                                        label="Binning"
	                                        class="input-200"
	                                    />
	                                    <q-select
	                                        v-if="splitNumericBinning !== 'custom'"
	                                        v-model="splitNumericBinCount"
	                                        :options="binCountOptions"
	                                        outlined
	                                        dense
	                                        options-dense
	                                        emit-value
	                                        map-options
	                                        label="Bins"
	                                        class="input-200"
	                                    />
	                                    <q-input
	                                        v-else
	                                        v-model="splitNumericCustomEdgesRaw"
	                                        outlined
	                                        dense
	                                        label="Custom edges"
	                                        class="input-200"
	                                    />
	                                </template>

	                                <template
	                                    v-else-if="!isSplitCross && splitVarInfo?.kind === 'categorical'"
	                                >
	                                    <q-select
	                                        v-model="splitCatGroupCount"
	                                        :options="splitCategoricalGroupCountOptions"
	                                        emit-value
	                                        map-options
	                                        outlined
	                                        dense
	                                        options-dense
	                                        label="Groups"
	                                        class="input-200"
	                                    />
	                                </template>

	                                <template v-else-if="isSplitCross">
	                                    <q-select
	                                        v-model="splitCrossAName"
	                                        :options="baseVariableOptions"
	                                        emit-value
	                                        map-options
	                                        outlined
	                                        dense
	                                        options-dense
	                                        label="Variable A"
	                                        class="input-200"
	                                        :disable="!schema || schemaLoading"
	                                        clearable
	                                    />
	                                    <template
	                                        v-if="
	                                            splitCrossAVarInfo?.kind === 'numeric' ||
	                                            splitCrossAVarInfo?.kind === 'date'
	                                        "
	                                    >
	                                        <q-select
	                                            v-model="splitCrossANumericBinning"
	                                            :options="numericBinningOptions"
	                                            emit-value
	                                            map-options
	                                            outlined
	                                            dense
	                                            options-dense
	                                            label="A binning"
	                                            class="input-200"
	                                        />
	                                        <q-select
	                                            v-if="splitCrossANumericBinning !== 'custom'"
	                                            v-model="splitCrossANumericBinCount"
	                                            :options="binCountOptions"
	                                            outlined
	                                            dense
	                                            options-dense
	                                            emit-value
	                                            map-options
	                                            label="A bins"
	                                            class="input-200"
	                                        />
	                                        <q-input
	                                            v-else
	                                            v-model="splitCrossANumericCustomEdgesRaw"
	                                            outlined
	                                            dense
	                                            label="A edges"
	                                            class="input-200"
	                                        />
	                                    </template>

	                                    <q-select
	                                        v-model="splitCrossBName"
	                                        :options="baseVariableOptions"
	                                        emit-value
	                                        map-options
	                                        outlined
	                                        dense
	                                        options-dense
	                                        label="Variable B"
	                                        class="input-200"
	                                        :disable="!schema || schemaLoading"
	                                        clearable
	                                    />
	                                    <template
	                                        v-if="
	                                            splitCrossBVarInfo?.kind === 'numeric' ||
	                                            splitCrossBVarInfo?.kind === 'date'
	                                        "
	                                    >
	                                        <q-select
	                                            v-model="splitCrossBNumericBinning"
	                                            :options="numericBinningOptions"
	                                            emit-value
	                                            map-options
	                                            outlined
	                                            dense
	                                            options-dense
	                                            label="B binning"
	                                            class="input-200"
	                                        />
	                                        <q-select
	                                            v-if="splitCrossBNumericBinning !== 'custom'"
	                                            v-model="splitCrossBNumericBinCount"
	                                            :options="binCountOptions"
	                                            outlined
	                                            dense
	                                            options-dense
	                                            emit-value
	                                            map-options
	                                            label="B bins"
	                                            class="input-200"
	                                        />
	                                        <q-input
	                                            v-else
	                                            v-model="splitCrossBNumericCustomEdgesRaw"
	                                            outlined
	                                            dense
	                                            label="B edges"
	                                            class="input-200"
	                                        />
	                                    </template>

	                                    <q-select
	                                        v-model="splitCrossGroupCount"
	                                        :options="crossGroupCountOptions"
	                                        emit-value
	                                        map-options
	                                        outlined
	                                        dense
	                                        options-dense
	                                        label="Groups"
	                                        class="input-200"
	                                        :disable="!splitCrossAName || !splitCrossBName"
	                                    />
	                                </template>

	                                <q-space />
	                                <div
	                                    v-if="!isSplitCross && splitVarInfo"
	                                    class="text-caption text-grey-7"
	                                >
	                                    <span class="text-weight-medium">Type:</span>
	                                    {{ splitVarInfo.kind }}
	                                    <template v-if="splitVarInfo.kind === 'numeric'">
	                                         <span class="text-weight-medium">Range:</span>
	                                        {{ splitVarInfo.numeric_min ?? '-' }} ->
	                                        {{ splitVarInfo.numeric_max ?? '-' }}
	                                    </template>
	                                    <template v-else-if="splitVarInfo.kind === 'date'">
	                                         <span class="text-weight-medium">Range:</span>
	                                        {{ splitVarInfo.date_min ?? '-' }} ->
	                                        {{ splitVarInfo.date_max ?? '-' }}
	                                    </template>
	                                    <template v-else>
	                                         <span class="text-weight-medium">Unique:</span>
	                                        {{ splitVarInfo.unique_count ?? 'unknown' }}
	                                        <span
	                                            v-if="
	                                                splitVarInfo.unique_values &&
	                                                splitVarInfo.unique_count &&
	                                                splitVarInfo.unique_values.length <
	                                                    splitVarInfo.unique_count
	                                            "
	                                        >
	                                            (first {{ splitVarInfo.unique_values.length }})
	                                        </span>
	                                    </template>
	                                </div>
	                                <div
	                                    v-else-if="isSplitCross"
	                                    class="text-caption text-grey-7"
	                                >
	                                    <span class="text-weight-medium">A:</span>
	                                    {{ splitCrossAVarInfo?.kind ?? '-' }}
	                                    <template v-if="splitCrossAVarInfo?.kind === 'numeric'">
	                                         {{ splitCrossAVarInfo.numeric_min ?? '-' }} ->
	                                        {{ splitCrossAVarInfo.numeric_max ?? '-' }}
	                                    </template>
	                                    <template v-else-if="splitCrossAVarInfo?.kind === 'date'">
	                                         {{ splitCrossAVarInfo.date_min ?? '-' }} ->
	                                        {{ splitCrossAVarInfo.date_max ?? '-' }}
	                                    </template>
	                                    <template
	                                        v-else-if="splitCrossAVarInfo?.kind === 'categorical'"
	                                    >
	                                         {{ splitCrossAVarInfo.unique_count ?? 'unknown' }}
	                                        unique
	                                    </template>
	                                    |
	                                    <span class="text-weight-medium">B:</span>
	                                    {{ splitCrossBVarInfo?.kind ?? '-' }}
	                                    <template v-if="splitCrossBVarInfo?.kind === 'numeric'">
	                                         {{ splitCrossBVarInfo.numeric_min ?? '-' }} ->
	                                        {{ splitCrossBVarInfo.numeric_max ?? '-' }}
	                                    </template>
	                                    <template v-else-if="splitCrossBVarInfo?.kind === 'date'">
	                                         {{ splitCrossBVarInfo.date_min ?? '-' }} ->
	                                        {{ splitCrossBVarInfo.date_max ?? '-' }}
	                                    </template>
	                                    <template
	                                        v-else-if="splitCrossBVarInfo?.kind === 'categorical'"
	                                    >
	                                         {{ splitCrossBVarInfo.unique_count ?? 'unknown' }}
	                                        unique
	                                    </template>
	                                    <span v-if="splitCrossLabelsLoading">
	                                        <q-spinner size="14px" class="q-ml-xs" />
	                                    </span>
	                                </div>
	                            </div>

	                            <div v-if="!isSplitCross && splitVarInfo" class="q-mt-sm">
	                                <div
	                                    v-if="splitVarInfo.kind === 'categorical'"
	                                    class="q-mt-sm"
	                                >
	                                    <div
	                                        v-if="
	                                            splitCatGroupCount !== 'all' &&
	                                            !splitCatUniqueValues
	                                        "
	                                        class="q-mt-sm"
	                                    >
	                                        <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
	                                            This column has too many unique values to edit groups
	                                            in the UI. Reduce cardinality or increase
	                                            `AEMONITOR_MAX_UNIQUE_VALUES`.
	                                        </q-banner>
	                                    </div>

	                                    <div
	                                        v-if="
	                                            splitCatGroupCount !== 'all' &&
	                                            splitCatUniqueValues
	                                        "
	                                        class="q-mt-md"
	                                    >
	                                        <div class="text-subtitle2 q-mb-sm">
	                                            Group definitions (last group is Remaining)
	                                        </div>

	                                        <div
	                                            v-for="(g, idx) in splitCatGroups"
	                                            :key="idx"
	                                            class="q-mb-sm"
	                                        >
	                                            <div class="row items-center q-gutter-md">
	                                                <q-input
	                                                    v-model="g.name"
	                                                    filled
	                                                    dense
	                                                    label="Name"
	                                                    class="input-200"
	                                                />
	                                                <q-input
	                                                    v-model="g.x_position"
	                                                    filled
	                                                    dense
	                                                    type="number"
	                                                    label="Pos"
	                                                    class="input-120"
	                                                    placeholder="Auto"
	                                                />
	                                                <q-select
	                                                    v-model="g.values"
	                                                    :options="splitCatUniqueValues"
	                                                    outlined
	                                                    dense
	                                                    options-dense
	                                                    multiple
	                                                    use-chips
	                                                    label="Values"
	                                                    style="min-width: 420px; max-width: 100%"
	                                                />
	                                            </div>
	                                        </div>

	                                        <div class="q-mb-sm">
	                                            <div class="row items-center q-gutter-md">
	                                                <q-input
	                                                    v-model="splitCatRemainingName"
	                                                    filled
	                                                    dense
	                                                    label="Name"
	                                                    class="input-200"
	                                                />
	                                                <q-input
	                                                    v-model="splitCatRemainingPosition"
	                                                    filled
	                                                    dense
	                                                    type="number"
	                                                    label="Pos"
	                                                    class="input-120"
	                                                    placeholder="Auto"
	                                                />
	                                                <q-select
	                                                    :model-value="splitCatRemainingValues"
	                                                    :options="splitCatUniqueValues"
	                                                    outlined
	                                                    dense
	                                                    options-dense
	                                                    multiple
	                                                    use-chips
	                                                    disable
	                                                    label="Values"
	                                                    style="min-width: 420px; max-width: 100%"
	                                                >
	                                                    <q-tooltip
	                                                        v-if="splitCatRemainingPreview"
	                                                        anchor="top middle"
	                                                        self="bottom middle"
	                                                    >
	                                                        {{ splitCatRemainingPreview }}
	                                                    </q-tooltip>
	                                                </q-select>
	                                            </div>
	                                        </div>
	                                    </div>
	                                </div>
	                            </div>
	                            <div v-else-if="isSplitCross" class="q-mt-sm">
	                                <div v-if="splitCrossTooManyUniques" class="q-mt-sm">
	                                    <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
	                                        One of the selected variables has too many unique values to
	                                        edit cross groups in the UI. Reduce cardinality or increase
	                                        `AEMONITOR_MAX_UNIQUE_VALUES`.
	                                    </q-banner>
	                                </div>

	                                <div v-else class="q-mt-md">
	                                    <div class="text-subtitle2 q-mb-sm">
	                                        Cross group definitions (last group is Remaining)
	                                    </div>

	                                    <div
	                                        v-for="(g, idx) in splitCrossGroups"
	                                        :key="`split-cross-${idx}`"
	                                        class="q-mb-sm"
	                                    >
	                                        <div class="row items-center q-gutter-md">
	                                            <q-input
	                                                v-model="g.name"
	                                                filled
	                                                dense
	                                                label="Name"
	                                                class="input-200"
	                                            />
	                                            <q-input
	                                                v-model="g.x_position"
	                                                filled
	                                                dense
	                                                type="number"
	                                                label="Pos"
	                                                class="input-120"
	                                                placeholder="Auto"
	                                            />
	                                            <q-checkbox v-model="g.a_any" dense label="Any A" />
	                                            <q-select
	                                                v-model="g.a_values"
	                                                :options="splitCrossALabels || []"
	                                                outlined
	                                                dense
	                                                options-dense
	                                                multiple
	                                                use-chips
	                                                label="A values"
	                                                :disable="g.a_any || !splitCrossALabels"
	                                                style="min-width: 320px; max-width: 100%"
	                                            />
	                                            <q-checkbox v-model="g.b_any" dense label="Any B" />
	                                            <q-select
	                                                v-model="g.b_values"
	                                                :options="splitCrossBLabels || []"
	                                                outlined
	                                                dense
	                                                options-dense
	                                                multiple
	                                                use-chips
	                                                label="B values"
	                                                :disable="g.b_any || !splitCrossBLabels"
	                                                style="min-width: 320px; max-width: 100%"
	                                            />
	                                        </div>
	                                        <div
	                                            v-if="g.a_any && g.b_any"
	                                            class="text-negative text-caption q-mt-xs"
	                                        >
	                                            A group cannot be both Any A and Any B.
	                                        </div>
	                                    </div>

	                                    <div class="q-mb-sm">
	                                        <div class="row items-center q-gutter-md">
	                                            <q-input
	                                                v-model="splitCrossRemainingName"
	                                                filled
	                                                dense
	                                                label="Name"
	                                                class="input-200"
	                                            />
	                                            <q-input
	                                                v-model="splitCrossRemainingPosition"
	                                                filled
	                                                dense
	                                                type="number"
	                                                label="Pos"
	                                                class="input-120"
	                                                placeholder="Auto"
	                                            />
	                                            <q-banner class="q-pa-xs bg-grey-1 text-grey-8">
	                                                Remaining = everything not matched by earlier
	                                                groups
	                                            </q-banner>
	                                        </div>
	                                    </div>
	                                </div>
	                            </div>
	                        </q-card-section>
	                    </q-card>

	                    <q-card v-if="polyFitEligible" flat bordered class="q-mt-md">
	                        <q-card-section class="q-pb-sm">
	                            <div class="text-h6">Polynomial Best Fit (optional)</div>
	                            <div class="text-body2 text-grey-7">
	                                Optionally configure a simple polynomial best-fit for the plotted
	                                relationship.
	                            </div>
	                        </q-card-section>

	                        <q-card-section class="q-pt-none">
	                            <div class="row items-center q-gutter-md">
	                                <q-checkbox
	                                    v-model="polyEnabled"
	                                    dense
	                                    label="Enable polynomial fit"
	                                />
	                                <q-select
	                                    v-model="polyDegree"
	                                    :options="polyDegreeOptions"
	                                    outlined
	                                    dense
	                                    options-dense
	                                    emit-value
	                                    map-options
	                                    label="Degree"
	                                    class="input-200"
	                                    :disable="!polyEnabled"
	                                />
	                                <q-checkbox
	                                    v-model="polyWeighted"
	                                    dense
	                                    label="Weighted fit"
	                                    :disable="!polyEnabled"
	                                />
	                            </div>
	                        </q-card-section>
	                    </q-card>

	                    <div class="row items-center q-gutter-sm q-mt-md">
	                        <q-btn
	                            label="Analyze"
                            type="submit"
                            color="primary"
                            :disable="!canAnalyze || loading"
                            :loading="loading"
                        />
                        <div v-if="errorMsg" class="text-negative">
                            {{ errorMsg }}
                        </div>
                    </div>
                </form>
            </q-card>

            <div v-if="aeResults" class="q-mt-lg">
                <q-banner class="q-px-md q-pt-md q-pb-sm">
                    <div class="row items-center q-gutter-x-sm">
                        <span class="text-h4">Results</span>
                    </div>
                </q-banner>

                <q-card class="q-pa-md q-mt-md">
                    <div class="text-h6 q-mb-md">A/E Scatter</div>
                    
                    <q-expansion-item
                        dense
                        dense-toggle
                        expand-separator
                        label="Calculation Details"
                        class="q-mb-md"
                        header-class="text-caption text-grey-7"
                    >
                        <q-card flat bordered class="q-pa-md bg-grey-1">
                            <div class="text-body2">
                                <div class="text-weight-medium q-mb-sm">A/E Calculation (within each bin/group):</div>
                                <ul class="q-pl-md q-my-xs">
                                    <li><strong>Count:</strong> Sum of MAC / Sum of MEC<br>
                                        <span class="text-grey-7">(Total Actual Deaths / Total Expected Deaths)</span>
                                    </li>
                                    <li class="q-mt-xs"><strong>Amount:</strong> Sum of MAN / Sum of MEN<br>
                                        <span class="text-grey-7">(Total Actual Claim Amount / Total Expected Claim Amount)</span>
                                    </li>
                                </ul>
                                <div class="text-weight-medium q-mb-sm q-mt-md">95% Confidence Interval:</div>
                                <ul class="q-pl-md q-my-xs">
                                    <li>Calculated using Beta distribution with Jeffrey's prior</li>
                                    <li class="q-mt-xs"><strong>Count:</strong> Based on mortality rate within group</li>
                                    <li class="q-mt-xs"><strong>Amount:</strong> Same rate CI scaled by average claim amount per group
                                        <ul class="q-pl-md" style="list-style-type: circle;">
                                            <li>Uses actual average when deaths > 0</li>
                                            <li>Uses expected average when deaths = 0</li>
                                        </ul>
                                    </li>
                                </ul>
                            </div>
                        </q-card>
                    </q-expansion-item>

                    <div class="row q-col-gutter-md">
                        <div class="col-6">
                            <div class="text-subtitle2 q-mb-sm text-center">A/E by Count</div>
                            <AeScatterPlot
                                :rows="aeResults.rows"
                                :x-axis-kind="resultsXAxisKind"
                                :variable-name="resultsVariableName || 'Variable'"
                                :numeric-domain="resultsXDomain"
                                :split-results="aeResults.split_results || null"
                                :split-variable-name="resultsSplitVariableName"
                                :poly-fit="aeResults.poly_fit || null"
                                metric="count"
                                v-model:show-overall="scatterShowOverall"
                                v-model:split-visible="scatterSplitVisible"
                            />
                        </div>
                        <div class="col-6">
                            <div class="text-subtitle2 q-mb-sm text-center">A/E by Amount</div>
                            <AeScatterPlot
                                :rows="aeResults.rows"
                                :x-axis-kind="resultsXAxisKind"
                                :variable-name="resultsVariableName || 'Variable'"
                                :numeric-domain="resultsXDomain"
                                :split-results="aeResults.split_results || null"
                                :split-variable-name="resultsSplitVariableName"
                                :poly-fit="aeResults.poly_fit || null"
                                metric="amount"
                                v-model:show-overall="scatterShowOverall"
                                v-model:split-visible="scatterSplitVisible"
                            />
                        </div>
                    </div>
                    
                    <!-- Polynomial Fit Formula Display -->
                    <div v-if="aeResults.poly_fit || (aeResults.split_results && aeResults.split_results.some(s => s.poly_fit))" class="q-mt-md q-pa-md bg-grey-1" style="border-radius: 4px;">
                        <div class="text-subtitle2 text-weight-medium q-mb-sm">Polynomial Best Fit</div>
                        
                        <div v-if="aeResults.poly_fit && scatterShowOverall" class="q-mb-sm">
                            <div class="text-body2">
                                <span class="text-weight-medium">Overall:</span>
                                <span class="q-ml-sm" style="font-family: 'Courier New', monospace;">{{ formatPolynomialEquation(aeResults.poly_fit) }}</span>
                                <span v-if="aeResults.poly_fit.r2 !== null && aeResults.poly_fit.r2 !== undefined" class="q-ml-md text-grey-7">
                                    (R² = {{ aeResults.poly_fit.r2.toFixed(3) }})
                                </span>
                            </div>
                        </div>
                        
                        <div v-if="aeResults.split_results && aeResults.split_results.length" class="q-pl-md">
                            <template v-for="(split, idx) in aeResults.split_results" :key="`poly-${idx}`">
                                <div v-if="split.poly_fit && scatterSplitVisible[split.split_group]" class="text-body2 q-mb-xs">
                                    <span class="text-weight-medium">{{ split.split_group }}:</span>
                                    <span class="q-ml-sm" style="font-family: 'Courier New', monospace;">{{ formatPolynomialEquation(split.poly_fit) }}</span>
                                    <span v-if="split.poly_fit.r2 !== null && split.poly_fit.r2 !== undefined" class="q-ml-md text-grey-7">
                                        (R² = {{ split.poly_fit.r2.toFixed(3) }})
                                    </span>
                                </div>
                            </template>
                        </div>
                    </div>
                    
                    <q-separator class="q-my-md" />
                    <div class="text-h6 q-mb-md">A/E Analysis</div>
                    <q-tabs v-model="resultsTab" dense>
                        <q-tab name="overall" label="Overall" />
                        <q-tab
                            v-for="(s, idx) in (aeResults.split_results || [])"
                            :key="`split-tab-${idx}`"
                            :name="`split-${idx}`"
                            :label="splitTabLabel(s.split_group)"
                        />
                    </q-tabs>
                    <q-separator />
                    <q-tab-panels v-model="resultsTab" keep-alive>
                        <q-tab-panel name="overall">
                            <AeUnivariateTable
                                :rows="aeResults.rows"
                                :variable-name="resultsVariableName || 'Variable'"
                                :x-axis-kind="resultsXAxisKind"
                            />
                            <q-separator class="q-my-md" />
                            <div class="text-subtitle1 q-mb-sm">A/E Treemaps</div>
                            <div class="row q-col-gutter-md">
                                <div class="col-6">
                                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Count (Area = Policy Count)</div>
                                    <AeTreemap
                                        :rows="aeResults.rows"
                                        :variable-name="resultsVariableName || 'Variable'"
                                        :split-results="aeResults.split_results || null"
                                        :split-variable-name="resultsSplitVariableName"
                                        :split-x-axis-kind="resultsSplitXAxisKind"
                                        metric="count"
                                        v-model:show-overall="currentTreemapShowOverall"
                                        v-model:split-visible="currentTreemapSplitVisible"
                                    />
                                </div>
                                <div class="col-6">
                                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Amount (Area = Face Amount)</div>
                                    <AeTreemap
                                        :rows="aeResults.rows"
                                        :variable-name="resultsVariableName || 'Variable'"
                                        :split-results="aeResults.split_results || null"
                                        :split-variable-name="resultsSplitVariableName"
                                        :split-x-axis-kind="resultsSplitXAxisKind"
                                        metric="amount"
                                        v-model:show-overall="currentTreemapShowOverall"
                                        v-model:split-visible="currentTreemapSplitVisible"
                                    />
                                </div>
                            </div>
                        </q-tab-panel>
                        <q-tab-panel
                            v-for="(s, idx) in (aeResults.split_results || [])"
                            :key="`split-panel-${idx}`"
                            :name="`split-${idx}`"
                        >
                            <AeUnivariateTable
                                :rows="s.rows"
                                :variable-name="resultsVariableName || 'Variable'"
                                :x-axis-kind="resultsXAxisKind"
                            />
                            <q-separator class="q-my-md" />
                            <div class="text-subtitle1 q-mb-sm">A/E Treemaps</div>
                            <div class="row q-col-gutter-md">
                                <div class="col-6">
                                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Count (Area = Policy Count)</div>
                                    <AeTreemap
                                        :rows="s.rows"
                                        :variable-name="resultsVariableName || 'Variable'"
                                        :split-results="aeResults.split_results || null"
                                        :split-variable-name="resultsSplitVariableName"
                                        :split-x-axis-kind="resultsSplitXAxisKind"
                                        metric="count"
                                        v-model:show-overall="currentTreemapShowOverall"
                                        v-model:split-visible="currentTreemapSplitVisible"
                                    />
                                </div>
                                <div class="col-6">
                                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Amount (Area = Face Amount)</div>
                                    <AeTreemap
                                        :rows="s.rows"
                                        :variable-name="resultsVariableName || 'Variable'"
                                        :split-results="aeResults.split_results || null"
                                        :split-variable-name="resultsSplitVariableName"
                                        :split-x-axis-kind="resultsSplitXAxisKind"
                                        metric="amount"
                                        v-model:show-overall="currentTreemapShowOverall"
                                        v-model:split-visible="currentTreemapSplitVisible"
                                    />
                                </div>
                            </div>
                        </q-tab-panel>
                    </q-tab-panels>
                    <div v-if="aeResults.cola_m1_stacked?.causes?.length || aeResults.split_results?.some(s => s.cola_m1_stacked?.causes?.length)">
                        <q-separator class="q-my-lg" />
                        <div class="text-h6 q-mb-md">Claim Analysis by Cause of Death</div>
                        <q-tabs v-model="colaResultsTab" dense>
                            <q-tab name="overall" label="Overall" />
                            <q-tab
                                v-for="(s, idx) in (aeResults.split_results || [])"
                                :key="`cola-split-tab-${idx}`"
                                :name="`split-${idx}`"
                                :label="splitTabLabel(s.split_group)"
                            />
                        </q-tabs>
                        <q-separator />
                        <q-tab-panels v-model="colaResultsTab" keep-alive>
                            <q-tab-panel name="overall">
                                <div v-if="aeResults.cola_m1_stacked?.causes?.length">
                                    <AeColaClaimTable
                                        :data="aeResults.cola_m1_stacked"
                                        :variable-name="resultsVariableName || 'Variable'"
                                    />
                                    <div class="q-mt-lg" style="display: flex; flex-direction: column; align-items: center">
                                        <div class="text-subtitle2 q-mb-sm text-center">
                                            Visual Distribution
                                        </div>
                                        <AeColaM1StackedBars
                                            style="width: 100%"
                                            :data="aeResults.cola_m1_stacked"
                                        />
                                    </div>
                                </div>
                            </q-tab-panel>
                            <q-tab-panel
                                v-for="(s, idx) in (aeResults.split_results || [])"
                                :key="`cola-split-panel-${idx}`"
                                :name="`split-${idx}`"
                            >
                                <div v-if="s.cola_m1_stacked?.causes?.length">
                                    <AeColaClaimTable
                                        :data="s.cola_m1_stacked"
                                        :variable-name="resultsVariableName || 'Variable'"
                                    />
                                    <div class="q-mt-lg" style="display: flex; flex-direction: column; align-items: center">
                                        <div class="text-subtitle2 q-mb-sm text-center">
                                            Visual Distribution
                                        </div>
                                        <AeColaM1StackedBars
                                            style="width: 100%"
                                            :data="s.cola_m1_stacked"
                                        />
                                    </div>
                                </div>
                            </q-tab-panel>
                        </q-tab-panels>
                    </div>
                </q-card>
            </div>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import AeColaClaimTable from '@/components/AeColaClaimTable.vue';
import AeColaM1StackedBars from '@/components/AeColaM1StackedBars.vue';
import AeInsightBanner from '@/components/AeInsightBanner.vue';
import AeScatterPlot from '@/components/AeScatterPlot.vue';
import AeTreemap from '@/components/AeTreemap.vue';
import AeUnivariateTable from '@/components/AeUnivariateTable.vue';
import {
    getAeInsightsFromConfig,
    getDatasetConfig,
    getDatasetConfigSchema,
    getDatasetConfigs,
    postAeUnivariateFromConfig,
    postAeUnivariateFromCsv,
    postAeUploadSchema,
} from '@/utils/api';
import type {
    ApiAeAtomicVariable,
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateResults,
    ApiAeXVariable,
} from '@/types/ae';
import type { ApiDatasetSchemaResults } from '@/types/datasets';
import {
    isMortalityDatasetConfig,
    type ApiDatasetConfig,
} from '@/types/dataset-config';
import type { ApiAeInsightDrill, ApiAeInsightsResults } from '@/types/insights';

const route = useRoute();

const uploadedFile = ref<File | null>(null);
const schemaLoading = ref(false);
const schema = ref<ApiDatasetSchemaResults | null>(null);
const insightsLoading = ref(false);
const insightsError = ref<string | null>(null);
const insightResults = ref<ApiAeInsightsResults | null>(null);

// Dataset configs
const configs = ref<ApiDatasetConfig[]>([]);
const configsLoading = ref(false);
const selectedConfigId = ref<string | null>(null);

const selectedConfig = computed(() => {
    if (!selectedConfigId.value) return null;
    return configs.value.find(c => c.id === selectedConfigId.value) ?? null;
});

const configOptions = computed(() => {
    return configs.value.map(c => ({
        label: `${c.dataset_name} (${c.file_path})`,
        value: c.id,
    }));
});

const hasDatasetSource = computed(() => {
    return Boolean(selectedConfigId.value || uploadedFile.value);
});

// Shared scatter plot visibility state
const scatterShowOverall = ref(true);
const scatterSplitVisible = ref<Record<string, boolean>>({});

// Treemap visibility state - separate for each tab (independent from scatter plots and from each other)
const treemapStateByTab = ref<Record<string, { showOverall: boolean; splitVisible: Record<string, boolean> }>>({});

// Get treemap state for current tab
const currentTreemapShowOverall = computed({
    get: () => treemapStateByTab.value[resultsTab.value]?.showOverall ?? true,
    set: (val) => {
        if (!treemapStateByTab.value[resultsTab.value]) {
            treemapStateByTab.value[resultsTab.value] = { showOverall: true, splitVisible: {} };
        }
        treemapStateByTab.value[resultsTab.value].showOverall = val;
    }
});

const currentTreemapSplitVisible = computed({
    get: () => treemapStateByTab.value[resultsTab.value]?.splitVisible ?? {},
    set: (val) => {
        if (!treemapStateByTab.value[resultsTab.value]) {
            treemapStateByTab.value[resultsTab.value] = { showOverall: true, splitVisible: {} };
        }
        treemapStateByTab.value[resultsTab.value].splitVisible = val;
    }
});

// Column mapping state
const policyNumberColumn = ref<string | null>(null);
const faceAmountColumn = ref<string | null>(null);
const macColumn = ref<string | null>(null);
const mecColumn = ref<string | null>(null);
const manColumn = ref<string | null>(null);
const menColumn = ref<string | null>(null);
const mocColumn = ref<string | null>(null);
const colaM1Column = ref<string | null>(null);

const loading = ref(false);
const errorMsg = ref<string | null>(null);
const aeResults = ref<ApiAeUnivariateResults | null>(null);
const resultsVariableName = ref<string | null>(null);
const resultsSplitVariableName = ref<string | null>(null);
const resultsSplitXAxisKind = ref<"numeric" | "date" | "categorical" | null>(null);
const resultsXAxisKind = ref<"numeric" | "date" | "categorical">("categorical");
const resultsXDomain = ref<{ min: number; max: number } | null>(null);
const resultsTab = ref<string>("overall");
const colaResultsTab = ref<string>("overall");

type NumericBinningMode = 'uniform' | 'quintile' | 'custom';
type CategoricalGroupCount = 'all' | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

type CategoricalGroup = {
    name: string;
    values: string[];
    x_position: string;
};

const CROSS_SENTINEL = '__cross__';

const xVarName = ref<string | null>(null);
const xNumericBinning = ref<NumericBinningMode>('quintile');
const xNumericBinCount = ref<number>(5);
const xNumericCustomEdgesRaw = ref<string>('');
const xCatGroupCount = ref<CategoricalGroupCount>('all');
const xCatGroups = ref<CategoricalGroup[]>([]);
const xCatRemainingName = ref<string>('Remaining');
const xCatRemainingPosition = ref<string>('');

type CrossGroup = {
    name: string;
    a_any: boolean;
    a_values: string[];
    b_any: boolean;
    b_values: string[];
    x_position: string;
};

const xCrossAName = ref<string | null>(null);
const xCrossBName = ref<string | null>(null);
const xCrossANumericBinning = ref<NumericBinningMode>('quintile');
const xCrossANumericBinCount = ref<number>(5);
const xCrossANumericCustomEdgesRaw = ref<string>('');
const xCrossBNumericBinning = ref<NumericBinningMode>('quintile');
const xCrossBNumericBinCount = ref<number>(5);
const xCrossBNumericCustomEdgesRaw = ref<string>('');
const xCrossGroupCount = ref<CategoricalGroupCount>(2);
const xCrossGroups = ref<CrossGroup[]>([]);
const xCrossRemainingName = ref<string>('Remaining');
const xCrossRemainingPosition = ref<string>('');
const xCrossALabels = ref<string[] | null>(null);
const xCrossBLabels = ref<string[] | null>(null);
const xCrossALabelsLoading = ref(false);
const xCrossBLabelsLoading = ref(false);
const xCrossALabelError = ref<string | null>(null);
const xCrossBLabelError = ref<string | null>(null);

const splitVarName = ref<string | null>(null);
const splitNumericBinning = ref<NumericBinningMode>('quintile');
const splitNumericBinCount = ref<number>(5);
const splitNumericCustomEdgesRaw = ref<string>('');
const splitCatGroupCount = ref<CategoricalGroupCount>('all');
const splitCatGroups = ref<CategoricalGroup[]>([]);
const splitCatRemainingName = ref<string>('Remaining');
const splitCatRemainingPosition = ref<string>('');

const splitCrossAName = ref<string | null>(null);
const splitCrossBName = ref<string | null>(null);
const splitCrossANumericBinning = ref<NumericBinningMode>('quintile');
const splitCrossANumericBinCount = ref<number>(5);
const splitCrossANumericCustomEdgesRaw = ref<string>('');
const splitCrossBNumericBinning = ref<NumericBinningMode>('quintile');
const splitCrossBNumericBinCount = ref<number>(5);
const splitCrossBNumericCustomEdgesRaw = ref<string>('');
const splitCrossGroupCount = ref<CategoricalGroupCount>(2);
const splitCrossGroups = ref<CrossGroup[]>([]);
const splitCrossRemainingName = ref<string>('Remaining');
const splitCrossRemainingPosition = ref<string>('');
const splitCrossALabels = ref<string[] | null>(null);
const splitCrossBLabels = ref<string[] | null>(null);
const splitCrossALabelsLoading = ref(false);
const splitCrossBLabelsLoading = ref(false);
const splitCrossALabelError = ref<string | null>(null);
const splitCrossBLabelError = ref<string | null>(null);

const polyDegreeOptions = [
    { label: '1', value: 1 },
    { label: '2', value: 2 },
    { label: '3', value: 3 },
];
const polyEnabled = ref<boolean>(false);
const polyDegree = ref<number>(1);
const polyWeighted = ref<boolean>(true);

const columnMappingOptions = computed(() => {
    if (!schema.value || !schema.value.column_suggestions) {
        return {
            policy_number: [],
            face_amount: [],
            mac: [],
            mec: [],
            man: [],
            men: [],
            moc: [],
            cola_m1: [],
        };
    }
    const suggestions = schema.value.column_suggestions;
    return {
        policy_number: suggestions.policy_number_candidates.map((c) => ({ label: c, value: c })),
        face_amount: suggestions.face_amount_candidates.map((c) => ({ label: c, value: c })),
        mac: suggestions.mac_candidates.map((c) => ({ label: c, value: c })),
        mec: suggestions.mec_candidates.map((c) => ({ label: c, value: c })),
        man: suggestions.man_candidates.map((c) => ({ label: c, value: c })),
        men: suggestions.men_candidates.map((c) => ({ label: c, value: c })),
        moc: suggestions.moc_candidates.map((c) => ({ label: c, value: c })),
        cola_m1: suggestions.cola_m1_candidates.map((c) => ({ label: c, value: c })),
    };
});

const baseVariableOptions = computed(() => {
    if (!schema.value) return [];
    return schema.value.columns
        .filter((c) => c.name !== schema.value?.mec_column && c.name !== schema.value?.mac_column)
        .map((c) => ({
            label: `${c.name} (${c.kind})`,
            value: c.name,
        }));
});

const xVariableOptions = computed(() => {
    return [
        { label: 'Composite (A x B)', value: CROSS_SENTINEL },
        ...baseVariableOptions.value,
    ];
});

const isXCross = computed(() => xVarName.value === CROSS_SENTINEL);

const xVarInfo = computed(() => {
    if (!schema.value || !xVarName.value || isXCross.value) return null;
    return schema.value.columns.find((c) => c.name === xVarName.value) ?? null;
});

const splitVariableOptions = computed(() => {
    return [
        { label: 'None', value: null },
        { label: 'Composite (A x B)', value: CROSS_SENTINEL },
        ...baseVariableOptions.value,
    ];
});

const isSplitCross = computed(() => splitVarName.value === CROSS_SENTINEL);

const splitVarInfo = computed(() => {
    if (!schema.value || !splitVarName.value || isSplitCross.value) return null;
    return schema.value.columns.find((c) => c.name === splitVarName.value) ?? null;
});

const xCrossAVarInfo = computed(() => {
    if (!schema.value || !xCrossAName.value) return null;
    return schema.value.columns.find((c) => c.name === xCrossAName.value) ?? null;
});

const xCrossBVarInfo = computed(() => {
    if (!schema.value || !xCrossBName.value) return null;
    return schema.value.columns.find((c) => c.name === xCrossBName.value) ?? null;
});

const splitCrossAVarInfo = computed(() => {
    if (!schema.value || !splitCrossAName.value) return null;
    return schema.value.columns.find((c) => c.name === splitCrossAName.value) ?? null;
});

const splitCrossBVarInfo = computed(() => {
    if (!schema.value || !splitCrossBName.value) return null;
    return schema.value.columns.find((c) => c.name === splitCrossBName.value) ?? null;
});

const numericBinningOptions = [
    { label: 'Uniform', value: 'uniform' },
    { label: 'Quintile', value: 'quintile' },
    { label: 'Custom', value: 'custom' },
] as const;

const binCountOptions = Array.from({ length: 19 }, (_, i) => {
    const v = i + 2;
    return { label: String(v), value: v };
});

const crossGroupCountOptions = Array.from({ length: 9 }, (_, i) => {
    const v = i + 2;
    return { label: `${v} groups`, value: v as CategoricalGroupCount };
});

const xCrossLabelsLoading = computed(
    () => xCrossALabelsLoading.value || xCrossBLabelsLoading.value,
);

const splitCrossLabelsLoading = computed(
    () => splitCrossALabelsLoading.value || splitCrossBLabelsLoading.value,
);

const categoricalGroupCountOptions = computed(() => {
    const uniqueCount = xCatUniqueCount.value;
    const maxGroups = Math.max(0, Math.min(10, uniqueCount ?? 10) + 2);

    const opts: Array<{ label: string; value: CategoricalGroupCount }> = [];
    if (xCatAllUniqueAllowed.value) {
        opts.push({ label: 'All unique', value: 'all' });
    }
    for (let n = 2; n <= maxGroups; n++) {
        opts.push({ label: `${n} groups`, value: n as CategoricalGroupCount });
    }
    return opts;
});

const splitCategoricalGroupCountOptions = computed(() => {
    const uniqueCount = splitCatUniqueCount.value;
    const maxGroups = Math.max(0, Math.min(10, uniqueCount ?? 10) + 2);

    const opts: Array<{ label: string; value: CategoricalGroupCount }> = [];
    if (splitCatAllUniqueAllowed.value) {
        opts.push({ label: 'All unique', value: 'all' });
    }
    for (let n = 2; n <= maxGroups; n++) {
        opts.push({ label: `${n} groups`, value: n as CategoricalGroupCount });
    }
    return opts;
});

const xCatUniqueValues = computed(() => {
    if (!xVarInfo.value || xVarInfo.value.kind !== 'categorical') return null;
    const values = xVarInfo.value.unique_values ?? null;
    return values && values.length ? values : null;
});

const xCatUniqueCount = computed(() => {
    if (!xVarInfo.value || xVarInfo.value.kind !== 'categorical') return null;
    const n = xVarInfo.value.unique_count;
    return typeof n === 'number' && Number.isFinite(n) ? n : null;
});

const xCatAllUniqueAllowed = computed(() => {
    const n = xCatUniqueCount.value;
    if (n === null) return true;
    return n <= 11;
});

const splitCatUniqueValues = computed(() => {
    if (!splitVarInfo.value || splitVarInfo.value.kind !== 'categorical') return null;
    const values = splitVarInfo.value.unique_values ?? null;
    return values && values.length ? values : null;
});

const splitCatUniqueCount = computed(() => {
    if (!splitVarInfo.value || splitVarInfo.value.kind !== 'categorical') return null;
    const n = splitVarInfo.value.unique_count;
    return typeof n === 'number' && Number.isFinite(n) ? n : null;
});

const splitCatAllUniqueAllowed = computed(() => {
    const n = splitCatUniqueCount.value;
    if (n === null) return true;
    return n <= 11;
});

const xCatRemainingValues = computed(() => {
    const uniques = xCatUniqueValues.value;
    if (!uniques) return [];
    const chosen = new Set(xCatGroups.value.flatMap((g) => g.values));
    return uniques.filter((v) => !chosen.has(v));
});

const xCatRemainingPreview = computed(() => {
    const remaining = xCatRemainingValues.value;
    const preview = remaining.slice(0, 25);
    const suffix =
        remaining.length > preview.length
            ? ` ... (+${remaining.length - preview.length})`
            : '';
    return preview.join(', ') + suffix;
});

const splitCatRemainingValues = computed(() => {
    const uniques = splitCatUniqueValues.value;
    if (!uniques) return [];
    const chosen = new Set(splitCatGroups.value.flatMap((g) => g.values));
    return uniques.filter((v) => !chosen.has(v));
});

const splitCatRemainingPreview = computed(() => {
    const remaining = splitCatRemainingValues.value;
    const preview = remaining.slice(0, 25);
    const suffix =
        remaining.length > preview.length
            ? ` ... (+${remaining.length - preview.length})`
            : '';
    return preview.join(', ') + suffix;
});

function hasTooManyUniquesForUi(
    info: ApiDatasetSchemaResults['columns'][number] | null,
): boolean {
    if (!info || info.kind !== 'categorical') return false;
    const n = info.unique_count;
    const values = info.unique_values;
    if (typeof n !== 'number' || !Number.isFinite(n)) return false;
    if (!values) return true;
    return values.length < n;
}

const xCrossTooManyUniques = computed(() => {
    if (!isXCross.value) return false;
    if (hasTooManyUniquesForUi(xCrossAVarInfo.value)) return true;
    if (hasTooManyUniquesForUi(xCrossBVarInfo.value)) return true;
    const errs = `${xCrossALabelError.value || ''} ${xCrossBLabelError.value || ''}`;
    return errs.toLowerCase().includes('too many unique');
});

const splitCrossTooManyUniques = computed(() => {
    if (!isSplitCross.value) return false;
    if (hasTooManyUniquesForUi(splitCrossAVarInfo.value)) return true;
    if (hasTooManyUniquesForUi(splitCrossBVarInfo.value)) return true;
    const errs = `${splitCrossALabelError.value || ''} ${splitCrossBLabelError.value || ''}`;
    return errs.toLowerCase().includes('too many unique');
});

function parseNumericEdges(raw: string): number[] {
    return (raw || '')
        .split(/[ ,]+/)
        .filter(Boolean)
        .map((s) => Number(s))
        .filter((v) => Number.isFinite(v));
}

function parseDateEdges(raw: string): string[] {
    return (raw || '')
        .split(/[ ,]+/)
        .map((s) => s.trim())
        .filter(Boolean);
}

function makeAtomicVariableSpec(args: {
    info: ApiDatasetSchemaResults['columns'][number];
    name: string;
    numericBinning: NumericBinningMode;
    numericBinCount: number;
    numericCustomEdgesRaw: string;
}): ApiAeAtomicVariable {
    const { info, name, numericBinning, numericBinCount, numericCustomEdgesRaw } = args;
    if (info.kind === 'numeric') {
        return {
            kind: 'numeric',
            name,
            binning: numericBinning,
            bin_count: numericBinning === 'custom' ? null : numericBinCount,
            custom_edges:
                numericBinning === 'custom' ? parseNumericEdges(numericCustomEdgesRaw) : null,
        };
    }
    if (info.kind === 'date') {
        return {
            kind: 'date',
            name,
            binning: numericBinning,
            bin_count: numericBinning === 'custom' ? null : numericBinCount,
            custom_edges: numericBinning === 'custom' ? parseDateEdges(numericCustomEdgesRaw) : null,
        };
    }

    return {
        kind: 'categorical',
        name,
        grouping: 'all_unique',
        groups: null,
        remaining_name: 'Remaining',
        remaining_position: null,
    };
}

function normalizeCrossGroupCount(value: CategoricalGroupCount): number {
    return typeof value === 'number' && Number.isFinite(value) ? Math.max(2, value) : 2;
}

function ensureCrossGroups(count: number, groups: CrossGroup[]): CrossGroup[] {
    const desired = Math.max(2, Math.min(10, count)) - 1;
    const out = groups.slice(0, desired);
    while (out.length < desired) {
        out.push({
            name: `Group ${out.length + 1}`,
            a_any: false,
            a_values: [],
            b_any: false,
            b_values: [],
            x_position: '',
        });
    }
    return out;
}

watch(
    () => xCrossGroupCount.value,
    (next) => {
        xCrossGroups.value = ensureCrossGroups(normalizeCrossGroupCount(next), xCrossGroups.value);
    },
    { immediate: true },
);

watch(
    () => splitCrossGroupCount.value,
    (next) => {
        splitCrossGroups.value = ensureCrossGroups(
            normalizeCrossGroupCount(next),
            splitCrossGroups.value,
        );
    },
    { immediate: true },
);

const schemaSummary = computed(() => {
    if (!schema.value) return null;
    const numeric = schema.value.columns.filter((c) => c.kind === 'numeric').length;
    const date = schema.value.columns.filter((c) => c.kind === 'date').length;
    const categorical = schema.value.columns.filter(
        (c) => c.kind === 'categorical',
    ).length;
    return {
        total: schema.value.columns.length,
        numeric,
        date,
        categorical,
        mac: schema.value.mac_column,
        mec: schema.value.mec_column,
    };
});

const polyFitEligible = computed(() => {
    if (!xVarName.value) return false;
    if (isXCross.value) {
        const groupPositionsOk = xCrossGroups.value.every(
            (g) => parseOptionalNumber(g.x_position) !== null,
        );
        const remainingOk = parseOptionalNumber(xCrossRemainingPosition.value) !== null;
        return groupPositionsOk && remainingOk;
    }
    if (!xVarInfo.value) return false;
    if (xVarInfo.value.kind === 'numeric') return true;
    if (xVarInfo.value.kind === 'date') return true;
    if (xVarInfo.value.kind !== 'categorical') return false;
    if (xCatGroupCount.value === 'all') return false;
    const groupPositionsOk = xCatGroups.value.every(
        (g) => parseOptionalNumber(g.x_position) !== null,
    );
    const remainingOk = parseOptionalNumber(xCatRemainingPosition.value) !== null;
    return groupPositionsOk && remainingOk;
});

function crossGroupIsInvalid(g: CrossGroup): boolean {
    if (g.a_any && g.b_any) return true;
    if (!g.a_any && g.a_values.length === 0) return true;
    if (!g.b_any && g.b_values.length === 0) return true;
    return false;
}

const canAnalyze = computed(() => {
    if (!hasDatasetSource.value) return false;
    if (!xVarName.value) return false;
    if (loading.value) return false;

    if (isXCross.value) {
        if (!xCrossAName.value || !xCrossBName.value) return false;
        if (xCrossAName.value === xCrossBName.value) return false;
        if (xCrossTooManyUniques.value) return false;
        const count = normalizeCrossGroupCount(xCrossGroupCount.value);
        if (xCrossGroups.value.length !== count - 1) return false;
        if (xCrossGroups.value.some(crossGroupIsInvalid)) return false;
        return true;
    }

    if (!xVarInfo.value) return false;
    if ((xVarInfo.value.kind === 'numeric' || xVarInfo.value.kind === 'date') && xNumericBinning.value === 'custom') {
        const edgesOk =
            xVarInfo.value.kind === 'date'
                ? parseDateEdges(xNumericCustomEdgesRaw.value).length > 0
                : parseNumericEdges(xNumericCustomEdgesRaw.value).length > 0;
        if (!edgesOk) return false;
    }
    if (
        xVarInfo.value.kind === 'categorical' &&
        xCatGroupCount.value !== 'all' &&
        !xCatUniqueValues.value
    ) {
        return false;
    }

    if (isSplitCross.value) {
        if (!splitCrossAName.value || !splitCrossBName.value) return false;
        if (splitCrossAName.value === splitCrossBName.value) return false;
        if (splitCrossTooManyUniques.value) return false;
        const count = normalizeCrossGroupCount(splitCrossGroupCount.value);
        if (splitCrossGroups.value.length !== count - 1) return false;
        if (splitCrossGroups.value.some(crossGroupIsInvalid)) return false;
    } else if (splitVarName.value) {
        if (!splitVarInfo.value) return false;
        if ((splitVarInfo.value.kind === 'numeric' || splitVarInfo.value.kind === 'date') && splitNumericBinning.value === 'custom') {
            const edgesOk =
                splitVarInfo.value.kind === 'date'
                    ? parseDateEdges(splitNumericCustomEdgesRaw.value).length > 0
                    : parseNumericEdges(splitNumericCustomEdgesRaw.value).length > 0;
            if (!edgesOk) return false;
        }
        if (
            splitVarInfo.value.kind === 'categorical' &&
            splitCatGroupCount.value !== 'all' &&
            !splitCatUniqueValues.value
        ) {
            return false;
        }
    }

    return true;
});

function parseOptionalNumber(raw: string): number | null {
    const s = (raw || '').trim();
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
}

function clearCrossState(which: 'x' | 'split') {
    if (which === 'x') {
        xCrossAName.value = null;
        xCrossBName.value = null;
        xCrossGroups.value = [];
        xCrossRemainingName.value = 'Remaining';
        xCrossRemainingPosition.value = '';
        return;
    }
    splitCrossAName.value = null;
    splitCrossBName.value = null;
    splitCrossGroups.value = [];
    splitCrossRemainingName.value = 'Remaining';
    splitCrossRemainingPosition.value = '';
}

async function applyAtomicVariableToState(
    which: 'x' | 'split',
    variable: ApiAeAtomicVariable | null,
) {
    if (which === 'x') {
        xVarName.value = variable?.name ?? null;
    } else {
        splitVarName.value = variable?.name ?? null;
    }
    clearCrossState(which);
    await nextTick();

    if (variable === null) {
        return;
    }

    if (which === 'x') {
        if (variable.kind === 'numeric' || variable.kind === 'date') {
            xNumericBinning.value = variable.binning;
            xNumericBinCount.value = variable.bin_count ?? 5;
            xNumericCustomEdgesRaw.value = (variable.custom_edges ?? []).join(', ');
            return;
        }
        xCatGroupCount.value = variable.grouping === 'custom'
            ? (variable.groups?.length ?? 0) + 1
            : 'all';
        xCatGroups.value = (variable.groups ?? []).map((group) => ({
            name: group.name,
            values: [...group.values],
            x_position:
                group.x_position === null || group.x_position === undefined
                    ? ''
                    : String(group.x_position),
        }));
        xCatRemainingName.value = variable.remaining_name ?? 'Remaining';
        xCatRemainingPosition.value =
            variable.remaining_position === null || variable.remaining_position === undefined
                ? ''
                : String(variable.remaining_position);
        return;
    }

    if (variable.kind === 'numeric' || variable.kind === 'date') {
        splitNumericBinning.value = variable.binning;
        splitNumericBinCount.value = variable.bin_count ?? 5;
        splitNumericCustomEdgesRaw.value = (variable.custom_edges ?? []).join(', ');
        return;
    }
    splitCatGroupCount.value = variable.grouping === 'custom'
        ? (variable.groups?.length ?? 0) + 1
        : 'all';
    splitCatGroups.value = (variable.groups ?? []).map((group) => ({
        name: group.name,
        values: [...group.values],
        x_position:
            group.x_position === null || group.x_position === undefined
                ? ''
                : String(group.x_position),
    }));
    splitCatRemainingName.value = variable.remaining_name ?? 'Remaining';
    splitCatRemainingPosition.value =
        variable.remaining_position === null || variable.remaining_position === undefined
            ? ''
            : String(variable.remaining_position);
}

async function loadInsightsForConfig(configId: string) {
    insightsLoading.value = true;
    insightsError.value = null;
    insightResults.value = null;
    try {
        insightResults.value = await getAeInsightsFromConfig(configId);
    } catch (err) {
        insightsError.value =
            err instanceof Error ? err.message : 'Failed to load insights';
    } finally {
        insightsLoading.value = false;
    }
}

async function applyInsightDrill(drill: ApiAeInsightDrill) {
    await applyAtomicVariableToState('x', drill.x_variable);
    await applyAtomicVariableToState('split', drill.split_variable ?? null);
    aeResults.value = null;
    errorMsg.value = null;
    await nextTick();
    await onAnalyze();
}

async function onAnalyze() {
    if (!hasDatasetSource.value) return;
    if (!xVarName.value) return;
    loading.value = true;
    errorMsg.value = null;
    aeResults.value = null;

    try {
        const makeSingleVariableSpec = (which: "x" | "split"): ApiAeXVariable => {
            const info = which === "x" ? xVarInfo.value : splitVarInfo.value;
            const name = which === "x" ? xVarName.value : splitVarName.value;
            if (!info || !name) {
                throw new Error("Variable is missing");
            }

            if (info.kind === "numeric") {
                const binning =
                    which === "x" ? xNumericBinning.value : splitNumericBinning.value;
                const binCount =
                    which === "x" ? xNumericBinCount.value : splitNumericBinCount.value;
                const edgesRaw =
                    which === "x"
                        ? xNumericCustomEdgesRaw.value
                        : splitNumericCustomEdgesRaw.value;
                return {
                    kind: "numeric",
                    name,
                    binning,
                    bin_count: binning === "custom" ? null : binCount,
                    custom_edges:
                        binning === "custom" ? parseNumericEdges(edgesRaw) : null,
                };
            }

            if (info.kind === "date") {
                const binning =
                    which === "x" ? xNumericBinning.value : splitNumericBinning.value;
                const binCount =
                    which === "x" ? xNumericBinCount.value : splitNumericBinCount.value;
                const edgesRaw =
                    which === "x"
                        ? xNumericCustomEdgesRaw.value
                        : splitNumericCustomEdgesRaw.value;
                return {
                    kind: "date",
                    name,
                    binning,
                    bin_count: binning === "custom" ? null : binCount,
                    custom_edges:
                        binning === "custom" ? parseDateEdges(edgesRaw) : null,
                };
            }

            const groupCount =
                which === "x" ? xCatGroupCount.value : splitCatGroupCount.value;
            const grouping = groupCount === "all" ? "all_unique" : "custom";
            const groups =
                which === "x" ? xCatGroups.value : splitCatGroups.value;
            const remainingName =
                which === "x" ? xCatRemainingName.value : splitCatRemainingName.value;
            const remainingPos =
                which === "x"
                    ? xCatRemainingPosition.value
                    : splitCatRemainingPosition.value;
            return {
                kind: "categorical",
                name,
                grouping,
                groups:
                    grouping === "custom"
                        ? groups.map((g) => ({
                              name: g.name,
                              values: g.values,
                              x_position: parseOptionalNumber(g.x_position),
                          }))
                        : null,
                remaining_name: remainingName,
                remaining_position: parseOptionalNumber(remainingPos),
            };
        };

        const makeCrossVariableSpec = (which: "x" | "split"): ApiAeXVariable => {
            const isX = which === "x";
            const aName = isX ? xCrossAName.value : splitCrossAName.value;
            const bName = isX ? xCrossBName.value : splitCrossBName.value;
            const aInfo = isX ? xCrossAVarInfo.value : splitCrossAVarInfo.value;
            const bInfo = isX ? xCrossBVarInfo.value : splitCrossBVarInfo.value;
            if (!aName || !bName || !aInfo || !bInfo) {
                throw new Error("Composite variables are missing");
            }
            if (aName === bName) {
                throw new Error("Composite variables must be different");
            }

            const aVar = makeAtomicVariableSpec({
                info: aInfo,
                name: aName,
                numericBinning: isX
                    ? xCrossANumericBinning.value
                    : splitCrossANumericBinning.value,
                numericBinCount: isX
                    ? xCrossANumericBinCount.value
                    : splitCrossANumericBinCount.value,
                numericCustomEdgesRaw: isX
                    ? xCrossANumericCustomEdgesRaw.value
                    : splitCrossANumericCustomEdgesRaw.value,
            });
            const bVar = makeAtomicVariableSpec({
                info: bInfo,
                name: bName,
                numericBinning: isX
                    ? xCrossBNumericBinning.value
                    : splitCrossBNumericBinning.value,
                numericBinCount: isX
                    ? xCrossBNumericBinCount.value
                    : splitCrossBNumericBinCount.value,
                numericCustomEdgesRaw: isX
                    ? xCrossBNumericCustomEdgesRaw.value
                    : splitCrossBNumericCustomEdgesRaw.value,
            });

            const groups = isX ? xCrossGroups.value : splitCrossGroups.value;
            const remainingName = isX
                ? xCrossRemainingName.value
                : splitCrossRemainingName.value;
            const remainingPos = isX
                ? xCrossRemainingPosition.value
                : splitCrossRemainingPosition.value;

            return {
                kind: "cross",
                a_variable: aVar,
                b_variable: bVar,
                groups: groups.map((g) => ({
                    name: g.name,
                    a_any: g.a_any,
                    a_values: g.a_values,
                    b_any: g.b_any,
                    b_values: g.b_values,
                    x_position: parseOptionalNumber(g.x_position),
                })),
                remaining_name: remainingName,
                remaining_position: parseOptionalNumber(remainingPos),
            };
        };

        const xVariable: ApiAeXVariable = isXCross.value
            ? makeCrossVariableSpec("x")
            : makeSingleVariableSpec("x");

        resultsVariableName.value = isXCross.value
            ? `${xCrossAName.value || "A"} x ${xCrossBName.value || "B"}`
            : xVarName.value;

        const splitVariable: ApiAeXVariable | null = splitVarName.value
            ? isSplitCross.value
                ? makeCrossVariableSpec("split")
                : splitVarInfo.value
                  ? makeSingleVariableSpec("split")
                  : null
            : null;

        resultsSplitVariableName.value = splitVarName.value
            ? isSplitCross.value
                ? `${splitCrossAName.value || "A"} x ${splitCrossBName.value || "B"}`
                : splitVarName.value
            : null;

        // All binned variables (numeric, date, categorical) are treated as categorical for scatter plots
        resultsSplitXAxisKind.value = splitVarName.value ? 'categorical' : null;

        // All binned variables are categorical
        resultsXAxisKind.value = 'categorical';

        // No numeric domain needed for categorical axes
        resultsXDomain.value = null;

        resultsTab.value = "overall";
        
        const request = {
            x_variable: xVariable,
            split_variable: splitVariable,
            poly_fit: polyFitEligible.value && polyEnabled.value
                ? { degree: polyDegree.value as 1 | 2 | 3, weighted: polyWeighted.value }
                : null,
        };

        if (selectedConfigId.value) {
            const params: ApiAeUnivariateFromConfigParameters = {
                config_id: selectedConfigId.value,
                ...request,
            };
            aeResults.value = await postAeUnivariateFromConfig(params);
        } else if (uploadedFile.value) {
            aeResults.value = await postAeUnivariateFromCsv(uploadedFile.value, {
                dataset_name: '',
                ...request,
                column_mapping: {
                    policy_number_column: policyNumberColumn.value,
                    face_amount_column: faceAmountColumn.value,
                    mac_column: macColumn.value,
                    mec_column: mecColumn.value,
                    man_column: manColumn.value,
                    men_column: menColumn.value,
                    moc_column: mocColumn.value,
                    cola_m1_column: colaM1Column.value,
                },
            });
        }
    } catch (err) {
        errorMsg.value = err instanceof Error ? err.message : String(err);
    } finally {
        loading.value = false;
    }
}

function splitTabLabel(group: string): string {
    const nm = (resultsSplitVariableName.value || '').trim();
    // For categorical split variables, don't prepend the variable name
    if (resultsSplitXAxisKind.value === 'categorical') {
        return group;
    }
    return nm ? `${nm} ${group}` : group;
}

function formatPolynomialEquation(polyFit: { degree: number; coefficients: number[]; weighted: boolean }): string {
    const coeffs = polyFit.coefficients;
    if (!coeffs || coeffs.length === 0) return '';
    
    // Polynomial coefficients are in descending order: [a_n, a_{n-1}, ..., a_1, a_0]
    // For degree 1: [a, b] → y = a*x + b
    // For degree 2: [a, b, c] → y = a*x² + b*x + c
    // For degree 3: [a, b, c, d] → y = a*x³ + b*x² + c*x + d
    
    const formatCoeff = (val: number): string => {
        return val >= 0 ? val.toFixed(4) : val.toFixed(4);
    };
    
    const terms: string[] = [];
    const degree = coeffs.length - 1;
    
    for (let i = 0; i <= degree; i++) {
        const power = degree - i;
        const coeff = coeffs[i];
        
        if (Math.abs(coeff) < 1e-10) continue; // Skip near-zero terms
        
        const sign = coeff >= 0 ? '+' : '-';
        const absCoeff = Math.abs(coeff);
        
        let term = '';
        if (power === 0) {
            // Constant term
            term = `${sign} ${formatCoeff(absCoeff)}`;
        } else if (power === 1) {
            // Linear term
            term = `${sign} ${formatCoeff(absCoeff)}x`;
        } else if (power === 2) {
            // Quadratic term
            term = `${sign} ${formatCoeff(absCoeff)}x²`;
        } else if (power === 3) {
            // Cubic term
            term = `${sign} ${formatCoeff(absCoeff)}x³`;
        }
        
        terms.push(term);
    }
    
    if (terms.length === 0) return 'y = 0';
    
    // Remove leading + sign
    let equation = 'y = ' + terms.join(' ');
    equation = equation.replace('y = +', 'y = ').replace('y = -', 'y = -');
    
    return equation;
}

async function onLoadUploadedSchema() {
    if (!selectedConfigId.value && !uploadedFile.value) return;
    
    schemaLoading.value = true;
    errorMsg.value = null;
    schema.value = null;
    
    // Only clear column mappings if no config is selected
    if (!selectedConfigId.value) {
        policyNumberColumn.value = null;
        faceAmountColumn.value = null;
        macColumn.value = null;
        mecColumn.value = null;
        manColumn.value = null;
        menColumn.value = null;
        mocColumn.value = null;
        colaM1Column.value = null;
    }
    
    try {
        if (selectedConfigId.value) {
            schema.value = await getDatasetConfigSchema(selectedConfigId.value);
        } else if (uploadedFile.value) {
            schema.value = await postAeUploadSchema(uploadedFile.value);
        }
        
        // Auto-select first candidate for each column if available (only if no config selected)
        if (!selectedConfigId.value && schema.value.column_suggestions) {
            const suggestions = schema.value.column_suggestions;
            policyNumberColumn.value = suggestions.policy_number_candidates[0] || null;
            faceAmountColumn.value = suggestions.face_amount_candidates[0] || null;
            macColumn.value = suggestions.mac_candidates[0] || schema.value.mac_column;
            mecColumn.value = suggestions.mec_candidates[0] || schema.value.mec_column;
            manColumn.value = suggestions.man_candidates[0] || null;
            menColumn.value = suggestions.men_candidates[0] || null;
            mocColumn.value = suggestions.moc_candidates[0] || null;
            colaM1Column.value = suggestions.cola_m1_candidates[0] || null;
        }
    } catch (err) {
        schema.value = null;
        errorMsg.value = err instanceof Error ? err.message : String(err);
    } finally {
        schemaLoading.value = false;
    }
}

watch(
    () => uploadedFile.value,
    () => {
        // Clear schema when file changes
        schema.value = null;
        errorMsg.value = null;
        // Note: We don't clear column mappings here because they might be from a selected config
    },
);

watch(
    () => xVarName.value,
    () => {
        if (!isXCross.value) return;
        const desired = normalizeCrossGroupCount(xCrossGroupCount.value);
        if (xCrossGroups.value.length !== desired - 1) {
            xCrossGroups.value = ensureCrossGroups(desired, xCrossGroups.value);
        }
    },
    { immediate: true },
);

watch(
    () => splitVarName.value,
    () => {
        if (!isSplitCross.value) return;
        const desired = normalizeCrossGroupCount(splitCrossGroupCount.value);
        if (splitCrossGroups.value.length !== desired - 1) {
            splitCrossGroups.value = ensureCrossGroups(desired, splitCrossGroups.value);
        }
    },
    { immediate: true },
);

watch(
    () => xCatGroupCount.value,
    () => {
        if (xCatGroupCount.value === 'all') {
            xCatGroups.value = [];
            xCatRemainingName.value = 'Remaining';
            xCatRemainingPosition.value = '';
            return;
        }
        const groupsToDefine = Math.max(0, Number(xCatGroupCount.value) - 1);
        const next: CategoricalGroup[] = [];
        for (let i = 0; i < groupsToDefine; i++) {
            next.push({
                name: `Group ${i + 1}`,
                values: [],
                x_position: '',
            });
        }
        xCatGroups.value = next;
    },
    { immediate: true },
);

watch(
    () => categoricalGroupCountOptions.value,
    (opts) => {
        const allowed = new Set(opts.map((o) => o.value));
        if (allowed.size === 0) return;
        if (!allowed.has(xCatGroupCount.value)) {
            xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
        }
    },
    { immediate: true },
);

watch(
    () => splitCatGroupCount.value,
    () => {
        if (splitCatGroupCount.value === 'all') {
            splitCatGroups.value = [];
            splitCatRemainingName.value = 'Remaining';
            splitCatRemainingPosition.value = '';
            return;
        }
        const groupsToDefine = Math.max(0, Number(splitCatGroupCount.value) - 1);
        const next: CategoricalGroup[] = [];
        for (let i = 0; i < groupsToDefine; i++) {
            next.push({
                name: `Group ${i + 1}`,
                values: [],
                x_position: '',
            });
        }
        splitCatGroups.value = next;
    },
    { immediate: true },
);

watch(
    () => splitCategoricalGroupCountOptions.value,
    (opts) => {
        const allowed = new Set(opts.map((o) => o.value));
        if (allowed.size === 0) return;
        if (!allowed.has(splitCatGroupCount.value)) {
            splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
        }
    },
    { immediate: true },
);
watch(
    () => xVarInfo.value?.kind,
    (kind) => {
        if (!kind) return;
        if (kind === 'numeric') {
            xCatGroupCount.value = 'all';
            xCatGroups.value = [];
            xCatRemainingName.value = 'Remaining';
            xCatRemainingPosition.value = '';
        } else {
            xNumericBinning.value = 'quintile';
            xNumericBinCount.value = 5;
            xNumericCustomEdgesRaw.value = '';
            xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
        }
    },
);

watch(
    () => xVarName.value,
    () => {
        xNumericBinning.value = 'quintile';
        xNumericBinCount.value = 5;
        xNumericCustomEdgesRaw.value = '';
        xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
        xCatGroups.value = [];
        xCatRemainingName.value = 'Remaining';
        xCatRemainingPosition.value = '';
    },
);

watch(
    () => splitVarInfo.value?.kind,
    (kind) => {
        if (!kind) return;
        if (kind === 'numeric') {
            splitCatGroupCount.value = 'all';
            splitCatGroups.value = [];
            splitCatRemainingName.value = 'Remaining';
            splitCatRemainingPosition.value = '';
        } else {
            splitNumericBinning.value = 'quintile';
            splitNumericBinCount.value = 5;
            splitNumericCustomEdgesRaw.value = '';
            splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
        }
    },
);

watch(
    () => splitVarName.value,
    () => {
        splitNumericBinning.value = 'quintile';
        splitNumericBinCount.value = 5;
        splitNumericCustomEdgesRaw.value = '';
        splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
        splitCatGroups.value = [];
        splitCatRemainingName.value = 'Remaining';
        splitCatRemainingPosition.value = '';
    },
);

// Reset scatter plot and treemap visibility when new results are loaded
watch(
    () => aeResults.value,
    () => {
        scatterShowOverall.value = true;
        scatterSplitVisible.value = {};
        treemapStateByTab.value = {};
    },
);

// Sync treemap visibility with tab selection
watch(
    () => resultsTab.value,
    (newTab) => {
        if (!aeResults.value) return;
        
        // Initialize tab state if needed
        if (!treemapStateByTab.value[newTab]) {
            treemapStateByTab.value[newTab] = { showOverall: true, splitVisible: {} };
        }
        
        if (newTab === 'overall') {
            // Overall tab: show overall, hide all splits
            treemapStateByTab.value[newTab].showOverall = true;
            const allHidden: Record<string, boolean> = {};
            (aeResults.value.split_results || []).forEach(s => {
                allHidden[s.split_group] = false;
            });
            treemapStateByTab.value[newTab].splitVisible = allHidden;
        } else if (newTab.startsWith('split-')) {
            // Split tab: hide overall, show only this split group
            const splitIdx = parseInt(newTab.slice('split-'.length), 10);
            const splitResults = aeResults.value.split_results || [];
            
            if (splitIdx >= 0 && splitIdx < splitResults.length) {
                const targetGroup = splitResults[splitIdx].split_group;
                
                treemapStateByTab.value[newTab].showOverall = false;
                const splitVisible: Record<string, boolean> = {};
                splitResults.forEach(s => {
                    splitVisible[s.split_group] = s.split_group === targetGroup;
                });
                treemapStateByTab.value[newTab].splitVisible = splitVisible;
            }
        }
    },
);

// Load dataset configs
async function loadConfigs() {
    configsLoading.value = true;
    try {
        const result = await getDatasetConfigs();
        configs.value = result.configs;
    } catch (err) {
        console.error('Failed to load dataset configs:', err);
    } finally {
        configsLoading.value = false;
    }
}

// Watch for config selection to apply column mappings
watch(
    () => selectedConfigId.value,
    async (configId) => {
        if (!configId) {
            // Cleared selection - don't reset anything
            return;
        }

        schema.value = null;
        aeResults.value = null;
        errorMsg.value = null;
        insightsError.value = null;
        insightResults.value = null;
        uploadedFile.value = null;

        try {
            const config = await getDatasetConfig(configId);
            if (!isMortalityDatasetConfig(config)) {
                throw new Error('Selected configuration is not a mortality A/E config.');
            }

            // Apply column mappings from config
            const mapping = config.module_config;
            policyNumberColumn.value = mapping.policy_number_column;
            faceAmountColumn.value = mapping.face_amount_column;
            macColumn.value = mapping.mac_column;
            mecColumn.value = mapping.mec_column;
            manColumn.value = mapping.man_column;
            menColumn.value = mapping.men_column;
            mocColumn.value = mapping.moc_column;
            colaM1Column.value = mapping.cola_m1_column;

            await onLoadUploadedSchema();
            await loadInsightsForConfig(configId);
        } catch (err) {
            errorMsg.value = err instanceof Error ? err.message : 'Failed to load configuration';
        }
    },
);

// Load configs on mount and check URL parameter
onMounted(async () => {
    await loadConfigs();
    
    // Check if config ID provided in URL
    const configId = route.query.config;
    if (configId && typeof configId === 'string') {
        selectedConfigId.value = configId;
    }
});
</script>

<style scoped>
.main-container {
    width: 100%;
    max-width: 100%;
}

.input-200 {
    width: 200px;
    max-width: 100%;
}

.input-300 {
    width: 300px;
    max-width: 100%;
}

.input-600 {
    width: 600px;
    max-width: 100%;
}

.input-120 {
    width: 120px;
    max-width: 100%;
}
</style>
