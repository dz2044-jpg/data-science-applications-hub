# Binary Feature Mortality A/E — Full LLM/AI Implementation Plan

## 1. Goal

Add an enterprise-grade AI capability to the **Binary Feature Mortality A/E** module that helps users interpret the current triage surface, while preserving the existing trust boundary:

- the uploaded ruleset already contains core A/E and confidence interval metrics
- Python derives deterministic triage signals
- AI interprets those deterministic outputs
- AI never becomes a second actuarial calculator

This AI layer must be:

- grounded
- deterministic where it matters
- auditable
- failure-tolerant
- cost-controlled
- knowledge-ready for future rule reference files

---

## 2. Core design principles

### 2.1 Single source of truth
The AI layer must use the exact same deterministic backend pipeline as the UI:

- `prepare_rule_df`
- `_project_perspective`
- `apply_filters`
- `_sort_rows`

No separate DuckDB AI query path.
No alternate ranking logic.
No duplicate calculation path.

### 2.2 AI is interpretation only
AI must never:

- compute A/E
- compute confidence intervals
- modify significance class
- modify confidence band
- modify impact score
- modify row ordering
- invent final underwriting or actuarial actions

### 2.3 Explicit trigger only
AI must run only when the user clicks a button.
It must not run automatically when filters change.

### 2.4 Structured output only
The frontend must not parse raw markdown to find row ids.
The model must return structured JSON.

### 2.5 Deterministic fallback always available
If the model fails, times out, returns invalid JSON, or becomes stale, the system must still show a useful deterministic summary.

### 2.6 Knowledge-ready from day one
The architecture must support future optional upload of rule reference knowledge, but the initial AI feature must work perfectly without it.

---

## 3. Product scope

## 3.1 MVP features

### Feature 1 — Summarize current filtered view
User action:
- click `Summarize View`

Behavior:
- summarize the currently visible rules
- describe the current perspective and CI level
- highlight top elevated rules, below-expected rules, uncertain rules
- call out materiality and concentration patterns
- include structured evidence references to rules

### Feature 2 — Explain focused rule
User action:
- select/focus one rule
- click `Explain Focused Rule`

Behavior:
- explain why the rule stands out
- interpret significance, CI width, impact, scale, and dominant COLA
- place the rule relative to the visible set
- return clickable evidence references

### Feature 3 — Compare selected rules
User action:
- select multiple rows or use pinned rules
- click `Compare Rules`

Behavior:
- compare the selected rules
- explain which ones appear more material, more stable, or more uncertain
- focus on relative interpretation rather than final decisions

### Feature 4 — Analyze count vs amount divergence
User action:
- focus a rule
- click `Analyze Count vs Amount`

Behavior:
- explain differences between count and amount perspectives for the same rule
- describe how significance, A/E, impact, and claim mix differ
- this is the signature capability of this module

---

## 3.2 Future capability (not required in first release)

### Optional Rule Knowledge Pack
Purpose:
Allow users to attach optional structured or unstructured rule-definition files later, so the AI can interpret rule meaning better.

Initial release status:
- architecture support: yes
- uploader and retrieval implementation: optional / later
- required for MVP: no

---

## 4. Non-goals

Do not implement:

- free-form chatbot for this page
- LLM-generated ranking
- LLM-generated actuarial metrics
- automatic recommendations that sound final
- prompt stuffing with raw files
- brittle markdown parsing to power UI interactions

---

## 5. High-level architecture

## 5.1 Backend layers

### Shared AI core
Create shared LLM infrastructure under `app/core/llm/`

Responsibilities:
- provider client
- retries / timeout handling
- structured-response execution
- telemetry
- caching
- prompt versioning
- model config
- redaction / safety helpers

### Module AI layer
Create Binary Feature AI orchestration under `app/modules/binary_feature_ae/`

Responsibilities:
- reconstruct current deterministic state
- build context packets
- compute relative baselines
- call shared LLM core
- validate response grounding
- return fallback if needed

---

## 5.2 Frontend layers

### Analysis page integration
Add a dedicated AI panel into Binary Feature analysis page.

Responsibilities:
- show action buttons
- manage loading / stale / fallback state
- render narrative text
- render evidence chips
- wire chips back to focus/select rows

---

## 6. Required project structure

## 6.1 Backend

```text
app/
  core/
    llm/
      __init__.py
      client.py
      config.py
      schema_runner.py
      cache.py
      telemetry.py
      prompt_registry.py
      safety.py
      types.py

  modules/
    binary_feature_ae/
      models/
        triage.py
        ai.py
        knowledge.py          # placeholder for future knowledge pack support

      service/
        binary_calc.py        # existing deterministic pipeline
        ai_orchestrator.py
        ai_packets.py
        ai_baselines.py
        ai_fallbacks.py
        ai_validation.py
        ai_prompting.py
        knowledge_matcher.py  # placeholder/future
        knowledge_packets.py  # placeholder/future

      routers/
        binary_feature.py     # existing
        ai.py
        knowledge.py          # placeholder/future
```

## 6.2 Frontend

```text
client/src/modules/binary-feature-ae/
  api.ts
  api-ai.ts
  api-knowledge.ts          # placeholder/future

  types-ai.ts
  types-knowledge.ts        # placeholder/future

  composables/
    useBinaryFeatureAi.ts
    useBinaryFeatureKnowledge.ts   # placeholder/future

  components/
    BinaryFeatureAiPanel.vue
    BinaryFeatureAiSummaryCard.vue
    BinaryFeatureAiCompareCard.vue
    BinaryFeatureAiStateBanner.vue
    BinaryFeatureEvidenceChips.vue
    BinaryFeatureKnowledgeStatus.vue  # placeholder/future
```

## 6.3 Tests

```text
tests/
  service/
    test_binary_feature_ai_packets.py
    test_binary_feature_ai_baselines.py
    test_binary_feature_ai_validation.py
    test_binary_feature_ai_fallbacks.py

  routers/
    test_binary_feature_ai.py
```

---

## 7. Backend implementation design

## 7.1 Data contracts

Create `app/modules/binary_feature_ae/models/ai.py`

Define request/response models for four actions:

- summarize view
- explain rule
- compare rules
- analyze divergence

### Base request fields
All requests should include:

- `config_id: str`
- `perspective: Literal["count", "amount"]`
- `ci_level: Literal["95", "90", "80"]`
- `categories: list[str]`
- `significance_values: list[str]`
- `search_text: str | None`
- `min_hit_count: float | None`
- `min_claim_count: float | None`

Additional fields by action:
- explain rule: `row_id`
- compare rules: `row_ids`
- divergence: `row_id`

### Base response fields
All responses should include:

- `action_type`
- `state_fingerprint`
- `source_mode` = `llm` or `fallback`
- `summary_text`
- `key_findings`
- `caution_flags`
- `next_review_steps`
- `evidence_refs`
- `used_reference_context: bool`
- `reference_sources: list[str]`

### Evidence refs
Each evidence ref should contain:

- `row_id`
- `rule_label`
- `reason_type`
- `reason_label`
- `severity`

Severity allowed values:
- `high`
- `medium`
- `low`
- `neutral`

Reason types:
- `top_impact`
- `elevated_95`
- `elevated_90`
- `elevated_80`
- `below_expected`
- `wide_uncertainty`
- `dominant_cola_concentration`
- `count_amount_divergence`
- `selected_for_comparison`

---

## 7.2 AI routers

Create `app/modules/binary_feature_ae/routers/ai.py`

Endpoints:

- `POST /api/binary-feature-ae/ai/summarize-view`
- `POST /api/binary-feature-ae/ai/explain-rule`
- `POST /api/binary-feature-ae/ai/compare-rules`
- `POST /api/binary-feature-ae/ai/analyze-divergence`

Each router should:
- validate request
- call orchestrator
- return structured response
- convert `ValueError` to `400`
- convert provider failure to fallback response, not server crash

---

## 7.3 Orchestrator

Create `app/modules/binary_feature_ae/service/ai_orchestrator.py`

Responsibilities:

1. rebuild deterministic analysis state from request
2. generate state fingerprint
3. check cache
4. build action-specific packet
5. call LLM through shared schema runner
6. validate grounding
7. return validated result
8. if anything fails, return deterministic fallback

Public functions:

- `summarize_view_ai(...)`
- `explain_rule_ai(...)`
- `compare_rules_ai(...)`
- `analyze_divergence_ai(...)`

---

## 7.4 Reuse deterministic pipeline

In `ai_orchestrator.py`, reconstruct state using existing pipeline:

1. call `_load_prepared_df_from_config(config_id=...)`
2. call `_project_perspective(...)`
3. call `apply_filters(...)`
4. call `_sort_rows(...)`

For divergence:
- project once for count
- project once for amount
- locate the same `row_id` in both projections

Do not create a second path.

---

## 7.5 State fingerprint

Create deterministic fingerprint generation in `ai_packets.py`

Fingerprint inputs must include:

- `config_id`
- `perspective`
- `ci_level`
- normalized categories
- normalized significance values
- normalized search text
- `min_hit_count`
- `min_claim_count`
- `row_id` or sorted `row_ids` when relevant
- visible row ids in current sorted order
- prompt version

Implementation guidance:
- normalize values to canonical strings
- serialize to sorted JSON
- hash with SHA-256
- store full hash or shortened stable prefix

Purpose:
- stale response detection
- caching
- audit logging
- regression reproducibility

---

## 7.6 Context packet builders

Create `app/modules/binary_feature_ae/service/ai_packets.py`

Functions:

- `build_summarize_view_packet(...)`
- `build_explain_rule_packet(...)`
- `build_compare_rules_packet(...)`
- `build_divergence_packet(...)`

### Packet rules
All packets must contain:

- deterministic metadata
- no raw uploaded file blobs
- current visible KPIs
- visible-set size
- active filters
- state fingerprint
- optional empty reference context fields

### 7.6.1 Summarize-view packet
Include:
- current perspective
- current CI level
- KPI block
- significance distribution counts
- top N rows using current deterministic sorted order
- top N should be small and configurable, default 20
- category distribution if useful
- concentration / uncertainty summary

### 7.6.2 Explain-rule packet
Include:
- full focused row
- visible-set KPI block
- relative baseline metrics for this row
- rank/percentile metrics
- whether rule is top decile or quartile for impact
- whether CI width is high relative to visible set
- whether dominant COLA concentration is high
- optional matched reference context fields, empty by default

### 7.6.3 Compare-rules packet
Include:
- selected rows
- same aligned fields for all selected rows
- comparison summary fields
- highest impact among selected
- most uncertain among selected
- strongest divergence among selected
- optional matched reference context per rule, empty by default

### 7.6.4 Divergence packet
Include:
- count projection row
- amount projection row
- side-by-side comparison of:
  - A/E
  - significance
  - CI width
  - impact
  - dominant COLA
  - claim count
  - claim amount
- explicit instruction that the model must explain difference without causal claims

---

## 7.7 Relative baseline calculations

Create `app/modules/binary_feature_ae/service/ai_baselines.py`

Provide helper functions for visible-set relative metrics:

- percentile rank of `impact_score`
- percentile rank of `hit_count`
- percentile rank of `claim_count`
- percentile rank of `claim_amount`
- percentile rank of `ci_width`
- significance rarity within visible set
- dominant COLA concentration threshold flag
- low-volume caution flag
- divergence strength between count and amount perspectives

These values should be computed numerically and added to the packet so the LLM does not infer them loosely.

---

## 7.8 Prompting

Create `app/modules/binary_feature_ae/service/ai_prompting.py`

Define one prompt builder per action.

All prompts must enforce:

- deterministic triage metrics are primary evidence
- reference context is optional and secondary
- if no reference context exists, do not invent rule meaning
- do not compute actuarial metrics
- do not claim causality
- do not recommend pricing, suppression, or underwriting changes
- use actuarial-safe vocabulary only
- keep answers concise and operationally useful

### Allowed phrasing
Use language like:
- elevated relative to expected
- below expected
- uncertain because the confidence interval crosses 1.0
- material within the visible rule set
- candidate for review
- wide uncertainty
- concentrated claim mix
- divergence between count and amount perspectives

### Forbidden phrasing
Do not use:
- caused by
- proves
- definitely risky
- should reprice
- root cause
- should change underwriting rules
- the model discovered
- this confirms

### Output instructions
Require strict JSON matching the response schema.
Narrative text should be short and plain.
All rule references must appear in `evidence_refs`, not embedded as clickable markdown hacks.

---

## 7.9 Validation

Create `app/modules/binary_feature_ae/service/ai_validation.py`

After the LLM returns structured JSON, validate:

### Structural validation
- valid schema
- required fields present
- allowed enums only

### Grounding validation
- every `row_id` in `evidence_refs` exists in packet
- `rule_label` matches packet row
- no unsupported numeric claims if not in packet
- no reference source claimed unless present in packet
- no perspective mismatch

### Language validation
- reject forbidden vocabulary
- reject overly decisive recommendations
- reject causal language
- reject claims that contradict deterministic data

If validation fails:
- do not show raw LLM output
- route to deterministic fallback

---

## 7.10 Fallbacks

Create `app/modules/binary_feature_ae/service/ai_fallbacks.py`

Functions:
- `fallback_summarize_view(...)`
- `fallback_explain_rule(...)`
- `fallback_compare_rules(...)`
- `fallback_divergence(...)`

These should use deterministic templates only.

Examples:
- “The visible set is dominated by X elevated rules and Y uncertain rules.”
- “This rule is elevated at the selected confidence level and ranks in the top X% by impact score.”
- “Among the selected rules, Rule A has the highest impact while Rule B has the widest uncertainty.”
- “This rule shows elevated count-based experience but weaker amount-based signal.”

Fallback response must still use the same response schema, with `source_mode="fallback"`.

---

## 7.11 Shared LLM core

Create `app/core/llm/`

### `config.py`
Store:
- model name
- timeout
- retry count
- max tokens
- temperature = low
- cache enable flag
- prompt version

### `client.py`
Wrapper around provider API.

Requirements:
- stateless client
- strict timeout
- retry on transient failures only
- no silent infinite retry

### `schema_runner.py`
Generic helper that:
- sends prompt
- requests structured JSON
- returns parsed model
- raises typed exceptions on failure

### `cache.py`
Cache responses by:
- action type
- state fingerprint
- model name
- prompt version

### `telemetry.py`
Log:
- action type
- state fingerprint
- model
- latency
- token counts
- cache hit or miss
- validation pass or fail
- fallback used or not

### `prompt_registry.py`
Track prompt versions centrally.

### `safety.py`
Utility checks for:
- redaction
- response filtering
- disallowed phrasing

---

## 8. Frontend implementation design

## 8.1 New API client

Create `client/src/modules/binary-feature-ae/api-ai.ts`

Functions:
- `postBinaryFeatureAiSummarizeView`
- `postBinaryFeatureAiExplainRule`
- `postBinaryFeatureAiCompareRules`
- `postBinaryFeatureAiAnalyzeDivergence`

These should call the new backend endpoints and return typed responses.

---

## 8.2 Type definitions

Create `client/src/modules/binary-feature-ae/types-ai.ts`

Mirror the backend response contract:
- action type
- state fingerprint
- source mode
- summary text
- key findings
- caution flags
- next review steps
- evidence refs
- reference sources
- used reference context

---

## 8.3 AI composable

Create `client/src/modules/binary-feature-ae/composables/useBinaryFeatureAi.ts`

Responsibilities:

- build request payload from current page state
- manage loading state per action
- maintain current AI response
- store response fingerprint
- compare returned fingerprint vs current page fingerprint
- mark stale or discard stale response
- expose action methods
- expose reset/clear methods

State to track:
- `isLoading`
- `errorMessage`
- `aiResponse`
- `isStale`
- `currentStateFingerprint`
- `lastActionType`

---

## 8.4 AI panel component

Create `BinaryFeatureAiPanel.vue`

Contents:
- action buttons
  - Summarize View
  - Explain Focused Rule
  - Compare Rules
  - Analyze Count vs Amount
- loading spinner
- stale banner
- fallback banner
- summary text
- key findings list
- caution list
- next steps list
- evidence chips
- knowledge status placeholder

### Button disable rules
- Summarize View: disabled if no visible rows
- Explain Focused Rule: disabled if no focused row
- Compare Rules: disabled if fewer than 2 selected/pinned rules
- Analyze Count vs Amount: disabled if no focused row

---

## 8.5 Evidence chips component

Create `BinaryFeatureEvidenceChips.vue`

Behavior:
- render each evidence ref as chip/button
- clicking a chip emits `focus-row`
- no string parsing
- use severity to style chip color

Severity mapping example:
- high -> negative/red
- medium -> warning/orange
- low -> secondary/blue-grey
- neutral -> grey

---

## 8.6 State banner component

Create `BinaryFeatureAiStateBanner.vue`

Possible states:
- AI response is based on an older filter state
- Showing deterministic fallback summary
- AI currently unavailable
- No optional rule knowledge attached

---

## 8.7 Page integration

Modify `BinaryFeatureAnalysisPage.vue`

Integrate AI panel into the right-side detail area or below it.

Pass into the AI composable:
- `selectedConfigId`
- `perspective`
- `ciLevel`
- `categories`
- `significanceValues`
- `searchText`
- `minHitCount`
- `minClaimCount`
- `rows`
- `focusedRowId`
- `selectedRowIds`
- `pinnedRuleKeys`

The composable should build the same request state as the backend receives.

Important:
Do not trigger AI requests from existing reactive watchers for calculation.
AI is button-triggered only.

---

## 9. Knowledge-ready design (optional future support)

Even though no knowledge file is required now, the architecture must support it cleanly.

## 9.1 Data model placeholder
Create `app/modules/binary_feature_ae/models/knowledge.py`

Define placeholder models:
- `knowledge_pack_id`
- `knowledge_pack_status`
- `reference_snippets`
- `reference_sources`

## 9.2 Packet schema placeholder
All AI packet builders should already include optional fields:

- `matched_rule_reference: null | object`
- `reference_snippets: []`
- `reference_sources: []`

When no knowledge pack exists:
- these remain empty
- prompts still work correctly

## 9.3 Future upload support
Planned future formats:
- structured: CSV, XLSX
- unstructured: DOCX, PDF, TXT, MD

Matching priority for future implementation:
1. exact `rule_key`
2. exact `rule`
3. exact `RuleName`
4. alias map
5. semantic retrieval as last resort

Knowledge context must always remain secondary to deterministic metrics.

---

## 10. Logging, audit, and governance

Every AI action must log:

- timestamp
- config id
- dataset name
- action type
- state fingerprint
- selected/focused row ids
- model name
- prompt version
- token usage
- latency
- cache hit or miss
- validation pass or fail
- source mode (`llm` or `fallback`)

Optional full-payload logging should be controlled by config flag only.

Never log more than needed by default.

---

## 11. Performance and cost controls

Required controls:

- explicit button-triggered execution
- short prompt packets
- top N cap for summarize-view packet
- response caching
- low temperature
- strict timeout
- deterministic fallback on timeout/failure

Recommended defaults:
- summarize view rows cap: 20
- compare rules cap: 5
- timeout: 8–12 seconds
- temperature: low / near zero
- retries: 1–2 transient retries max

---

## 12. Error handling

### LLM timeout
Return:
- fallback summary
- `source_mode="fallback"`

### Invalid JSON
Return:
- fallback summary
- telemetry record with validation failure reason

### Stale response
Frontend should:
- compare returned fingerprint to current fingerprint
- discard or mark stale
- show stale banner if retained

### Empty result set
Frontend disables summarize button and shows message.

### Missing focused row
Frontend disables rule-specific actions.

---

## 13. Testing plan

## 13.1 Unit tests

### `test_binary_feature_ai_packets.py`
Test:
- packet fields are built from deterministic pipeline
- top N ordering matches current sort
- fingerprints are deterministic
- optional reference fields are empty by default

### `test_binary_feature_ai_baselines.py`
Test:
- percentile calculations
- low-volume flags
- concentration flags
- divergence metrics

### `test_binary_feature_ai_validation.py`
Test:
- valid response passes
- invalid row id fails
- forbidden language fails
- unsupported numbers fail
- stale fingerprint mismatch handled correctly

### `test_binary_feature_ai_fallbacks.py`
Test:
- every fallback returns valid schema
- no missing fields
- deterministic summaries are sensible

---

## 13.2 Router tests

### `test_binary_feature_ai.py`
Test:
- summarize endpoint
- explain endpoint
- compare endpoint
- divergence endpoint
- invalid request returns 400
- provider failure returns fallback
- validation failure returns fallback

---

## 13.3 Frontend tests
Test:
- button disable rules
- action triggers only on click
- evidence chip click focuses row
- stale state banner appears correctly
- fallback banner appears correctly
- no AI auto-fire on filter change

---

## 13.4 Evaluation scenarios
Create fixed test scenarios covering:

- high-impact elevated rule
- uncertain wide-CI rule
- below-expected rule
- count-vs-amount divergence rule
- compare multiple selected rules
- hidden pinned rule
- empty visible set
- stale response case
- model failure case

Judge outputs for:
- correctness
- groundedness
- usefulness
- safe language
- consistency

---

## 14. Rollout plan

## Phase 1 — Deterministic foundation
Implement:
- data contracts
- packet builders
- state fingerprinting
- baseline metrics
- deterministic fallbacks

Deliverable:
- all four actions can run in fallback-only mode

## Phase 2 — Shared LLM core
Implement:
- provider wrapper
- schema runner
- cache
- telemetry
- prompt registry

Deliverable:
- one working structured AI call in isolation

## Phase 3 — Backend endpoints
Implement:
- AI orchestrator
- action-specific routers
- validation layer
- fallback routing

Deliverable:
- backend ready for frontend

## Phase 4 — Frontend MVP
Implement:
- AI panel
- summarize view
- explain focused rule
- evidence chips
- stale/fallback banners

Deliverable:
- first usable experience

## Phase 5 — compare + divergence
Implement:
- compare rules
- analyze count vs amount
- richer evidence refs

Deliverable:
- full feature set

## Phase 6 — evaluation and hardening
Implement:
- scenario-based test set
- tune prompt language
- verify governance
- verify logs and cache

Deliverable:
- production-ready behavior

## Phase 7 — future knowledge pack
Implement later:
- knowledge upload
- knowledge matching
- reference snippet retrieval
- source-cited rule context

---

## 15. Acceptance criteria

The work is complete when:

1. AI never computes or overrides actuarial metrics
2. AI packets are built only from the existing trusted deterministic pipeline
3. each action returns structured JSON
4. invalid or stale AI responses never break the UI
5. deterministic fallback exists for every action
6. evidence chips are structured and clickable
7. count-vs-amount divergence works
8. logging and telemetry exist for every request
9. AI architecture is knowledge-ready, even with no current knowledge file
10. tests cover grounding, fallback, and stale-state behavior

---

## 16. Exact implementation checklist for Codex

Use this as the build order:

### Backend
1. create `app/core/llm/` shared infrastructure
2. create `app/modules/binary_feature_ae/models/ai.py`
3. create `ai_packets.py`
4. create `ai_baselines.py`
5. create `ai_fallbacks.py`
6. create `ai_validation.py`
7. create `ai_prompting.py`
8. create `ai_orchestrator.py`
9. create `routers/ai.py`
10. wire router into app

### Frontend
11. create `types-ai.ts`
12. create `api-ai.ts`
13. create `useBinaryFeatureAi.ts`
14. create `BinaryFeatureEvidenceChips.vue`
15. create `BinaryFeatureAiStateBanner.vue`
16. create `BinaryFeatureAiPanel.vue`
17. integrate AI panel into `BinaryFeatureAnalysisPage.vue`
18. add action buttons and disable logic
19. add stale handling
20. add fallback display

### Testing
21. add packet tests
22. add baseline tests
23. add validation tests
24. add fallback tests
25. add router tests
26. add frontend interaction tests

### Future-ready placeholders
27. add `models/knowledge.py`
28. add `routers/knowledge.py` placeholder
29. add `knowledge_matcher.py` placeholder
30. add `knowledge_packets.py` placeholder
31. add frontend `types-knowledge.ts` and `BinaryFeatureKnowledgeStatus.vue` placeholder

---

## 17. Final instruction to Codex

Implement the Binary Feature Mortality A/E AI layer as a **strict interpretation system**, not a calculator and not a chatbot. Reuse the existing deterministic pipeline as the only truth source, expose four explicit AI actions, return structured validated JSON, support deterministic fallback on every path, and keep the architecture ready for future optional rule-reference knowledge uploads without requiring them now.
