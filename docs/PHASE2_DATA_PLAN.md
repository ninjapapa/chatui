# Phase 2 Detailed Plan — Structured Public Data

This document expands the phase-2 note from `docs/NORTHSTAR.md` and `docs/MVP_PROJECT_PLAN.md` into an implementation plan.

## Phase 2 goal

Add a **small, high-confidence structured data layer** that materially improves answer quality for the most valuable question types, without turning the MVP into a data engineering project.

The North Star says phase 2 should focus first on:
- **drug price**
- **drug relationships**

Based on the source research, the practical interpretation should be:
- implement **drug identity + drug relationships first**
- add **price context** conservatively using public reference/payment data where available
- avoid pretending we can provide personalized market-wide price predictions

---

## 1) What Phase 2 should unlock

Phase 2 should add structured answers for these question families:

### A. Drug identity and relationship questions
Examples:
- “What is this drug?”
- “What is the generic for X?”
- “Are A and B the same active ingredient?”
- “What does this NDC represent?”

### B. Provider identity questions
Examples:
- “Who is this provider / organization?”
- “What type of provider is this NPI?”
- “What specialty is this billing entity registered under?”

### C. Marketplace / insurance structure questions
Examples:
- “What’s the difference between Bronze and Silver?”
- “What plan fields matter when comparing plans?”
- “How do deductible and out-of-pocket max relate?”

### D. Medicare payment-context questions
Examples:
- “What does Medicare usually allow for this category of service?”
- “What does this reimbursement concept mean?”

### E. Early price-context questions, with guardrails
Examples:
- “Is this a list price, allowed amount, or out-of-pocket estimate?”
- “What public price references exist for this service or drug?”

Not in scope for Phase 2:
- exact personalized cost estimation
- broad hospital negotiated-rate normalization
- broad CPT-explainer productization
- commercial claims-based shopping tools

---

## 2) Exact data package for Phase 2

## Required sources

### 1) openFDA NDC
**Purpose:**
- identify drug products and packages
- resolve NDC-based user queries
- provide product/manufacturer/package facts

**Used for:**
- `drug_identity`
- `drug_label_lookup`
- partial `drug_price_context`

### 2) openFDA drug label
**Purpose:**
- attach official labeling context to drug answers
- support cited answers about what a drug is and what its label says

**Used for:**
- `drug_label_lookup`
- `drug_identity`

### 3) RxNorm / NLM clinical tables
**Purpose:**
- normalize names
- map brand ↔ generic ↔ ingredient relationships
- improve search recall

**Used for:**
- `drug_relationships`
- `drug_identity`

### 4) NPPES / NPI registry
**Purpose:**
- identify providers and organizations
- support NPI lookups and taxonomy explanation

**Used for:**
- `provider_identity`
- `provider_specialty`

### 5) Healthcare.gov / Exchange public-use files
**Purpose:**
- ground plan-structure comparisons and Marketplace education
- later support plan-level browsing/comparison

**Used for:**
- `marketplace_plan_basics`
- `cost_sharing_explainer`

### 6) Selected CMS provider summary + fee schedule data
**Purpose:**
- provide Medicare payment-context facts
- support explanations of provider/service reimbursement concepts

**Used for:**
- `provider_payment_context`
- `billing_concepts`
- `facility_price_context` (limited)

---

## 3) Product architecture for Phase 2

Phase 2 should introduce a clear split between:

### A. Retrieval layer
For human-readable explanations and citations:
- CMS pages
- Healthcare.gov pages
- MedlinePlus
- selected CDC/AHRQ/HRSA pages

### B. Structured lookup layer
For exact, normalized factual lookup:
- openFDA
- RxNorm
- NPPES
- Exchange PUFs
- selected CMS datasets

### C. Answer orchestration layer
At answer time, the app should:
1. classify the question
2. decide whether structured lookup is needed
3. query the relevant structured source(s)
4. retrieve supporting explanatory citations
5. generate an answer that clearly distinguishes:
   - normalized facts
   - explanatory context
   - limitations / uncertainty

---

## 4) Proposed backend components

Recommended new backend modules:

### `backend/sources/registry.py`
Loads the machine-readable source registry and exposes:
- source lookup by `source_id`
- filter by question type
- filter by `mode` / `priority` / `status`

### `backend/sources/types.py`
Shared schemas for:
- `SourceRecord`
- `CitationRecord`
- `LookupResult`
- `ProvenanceRecord`

### `backend/ingest/`
Ingestion jobs by source family:
- `openfda.py`
- `rxnorm.py`
- `nppes.py`
- `marketplace.py`
- `cms_provider.py`

### `smv2/`
Use **SMV2** as the Phase 2 ETL/data-processing layer.

Recommended responsibilities:
- source extraction jobs
- normalization/transformation logic
- dataset versioning and snapshot production
- validation checks before publish
- export of app-serving artifacts/tables

Practical role split:
- **SMV2** builds and refreshes the structured datasets
- the **app backend** reads from the published outputs / serving tables and uses them at answer time

This keeps heavy ETL concerns out of the request path and makes the data pipeline easier to rerun independently.

### Cloud-hosted structured data serving layer
Although the MVP app deploy target is local, Phase 2 should **consider a cloud host for serving structured data**.

Recommended model:
- run ETL with SMV2
- publish normalized outputs to a cloud-hosted data service / database / object store
- let the app consume that hosted data through a stable API or read-optimized tables

Why this is useful:
- avoids shipping large datasets with the local app runtime
- makes refreshes/versioning easier
- keeps data serving decoupled from UI/backend deploy cadence
- creates a cleaner path to later multi-user or remote deployment if needed

### `backend/retrieval/`
For reference content retrieval/indexing:
- `crawler.py`
- `chunker.py`
- `index.py`
- `citation.py`

### `backend/qa/grounding.py`
Validation helpers:
- every answer has citations
- every structured fact has provenance
- disallowed source types are not cited

### `backend/orchestrator/answer.py`
Main answer orchestration:
- classify question
- route to retrieval/lookup/hybrid flow
- assemble final answer package

---

## 5) Proposed data model additions

The current MVP decision is SQLite. That is still the right choice for the local app runtime and app-owned artifacts.

However, for Phase 2 structured data, the plan should explicitly allow a split architecture:
- **local SQLite** for app state, transcripts, feedback, and answer provenance
- **cloud-hosted data serving layer** for larger normalized structured datasets produced by SMV2

Recommended Phase 2 tables:

## `sources`
Stores approved source metadata and runtime state.

Suggested columns:
- `source_id` TEXT PRIMARY KEY
- `name`
- `owner`
- `category`
- `mode`
- `domain`
- `base_url`
- `trust_level`
- `consumer_safe`
- `citation_allowed`
- `retrieval_allowed`
- `priority`
- `status`
- `last_checked_at`
- `last_ingested_at`
- `last_version`
- `last_error`

## `source_documents`
Stores retrieved reference documents/pages.

Suggested columns:
- `doc_id`
- `source_id`
- `url`
- `title`
- `content_type`
- `fetched_at`
- `published_at` (nullable)
- `checksum`
- `raw_text`
- `metadata_json`

## `document_chunks`
Stores chunked retrieval units.

Suggested columns:
- `chunk_id`
- `doc_id`
- `source_id`
- `chunk_index`
- `text`
- `token_count`
- `embedding_ref` (nullable if embeddings are external)
- `metadata_json`

## `dataset_snapshots`
Tracks structured dataset versions.

Suggested columns:
- `snapshot_id`
- `source_id`
- `version_label`
- `release_date`
- `ingested_at`
- `row_count`
- `artifact_path`
- `metadata_json`

## `drug_concepts`
Normalized medication entities.

Suggested columns:
- `drug_id`
- `rxcui`
- `name`
- `tty`
- `ingredient_name`
- `brand_name`
- `generic_name`
- `ndc_list_json`
- `source_snapshot_id`

## `provider_entities`
Provider / organization identity layer.

Suggested columns:
- `provider_id`
- `npi`
- `entity_type`
- `name`
- `organization_name`
- `taxonomy_code`
- `taxonomy_desc`
- `city`
- `state`
- `source_snapshot_id`

## `plan_entities`
Marketplace plan metadata.

Suggested columns:
- `plan_id`
- `year`
- `state`
- `issuer_name`
- `metal_level`
- `plan_marketing_name`
- `premium_fields_json`
- `cost_sharing_json`
- `source_snapshot_id`

## `answer_provenance`
Per-answer grounding records.

Suggested columns:
- `answer_id`
- `message_id`
- `source_id`
- `doc_id` (nullable)
- `snapshot_id` (nullable)
- `url` (nullable)
- `citation_text`
- `fact_type`
- `used_for`
- `created_at`

---

## 6) Question-routing design

Before generating an answer, classify into one of these initial routes:

### Route 1: explainer-only
Examples:
- “What is a deductible?”
- “How does Medicare Part B work?”

**Plan:**
- retrieval only
- no structured lookup required

### Route 2: drug lookup
Examples:
- “What is NDC 12345-6789?”
- “What is the generic of Lipitor?”

**Plan:**
- RxNorm + openFDA lookup
- plus explanatory citation if needed

### Route 3: provider lookup
Examples:
- “Who is NPI 1234567890?”

**Plan:**
- NPPES lookup
- optional CMS provider context lookup
- supporting explanatory citation if needed

### Route 4: insurance/plan structure
Examples:
- “What’s the difference between Bronze and Gold?”

**Plan:**
- Healthcare.gov retrieval
- optional Marketplace dataset facts

### Route 5: payment context
Examples:
- “What does Medicare allow mean?”
- “Why is billed amount different from allowed amount?”

**Plan:**
- CMS retrieval
- optional fee schedule/provider summary facts

### Route 6: risky price question
Examples:
- “What will I pay out of pocket for this procedure?”

**Plan:**
- answer with scope warning
- explain the difference between public reference amounts and personalized liability
- avoid false precision

---

## 7) Detailed implementation sequence

## Milestone 1 — source registry and contracts
**Goal:** establish the control plane for data sources.

Tasks:
- create machine-readable registry file
- define source and provenance schemas
- add source loading/validation tests
- add source status logging
- define how SMV2 job outputs map to source ids and dataset snapshots
- define the boundary between local app storage and cloud-hosted serving data

Exit criteria:
- backend can list approved sources by type and question class
- SMV2 outputs can be versioned and associated with serving artifacts

---

## Milestone 2 — drug data foundation
**Goal:** ship the most important structured-data capability first.

Tasks:
- implement SMV2 ETL for openFDA NDC inputs
- implement SMV2 ETL for openFDA label inputs
- integrate RxNorm / clinical tables for normalization
- build drug query normalization logic
- publish normalized drug-serving artifacts to the cloud-hosted serving layer
- implement answer route for drug identity / generic-brand questions
- store answer provenance

Recommended UX capability targets:
- lookup by brand name
- lookup by generic name
- lookup by ingredient
- lookup by NDC
- answer “is this the same as…” questions conservatively

Exit criteria:
- app can answer common drug-identity/relationship questions with cited support

---

## Milestone 3 — provider identity foundation
**Goal:** support simple provider/billing-entity lookups.

Tasks:
- implement SMV2 ETL for NPPES snapshot ingestion
- normalize basic fields (NPI, entity type, taxonomy, org name, location)
- publish provider-serving artifacts to the cloud-hosted serving layer
- add provider lookup route
- add answer template for provider identity answers

Exit criteria:
- app can explain what an NPI/provider entity appears to be, with caveats

---

## Milestone 4 — Marketplace structure layer
**Goal:** improve insurance-comparison and ACA explainer answers.

Tasks:
- identify minimal useful fields from Healthcare.gov / Exchange PUFs
- implement SMV2 ETL for the smallest high-value subset first
- create plan-structure vocabulary mapping
- publish plan-serving artifacts to the cloud-hosted serving layer
- improve answers to deductible/OOP/metal-tier questions

Exit criteria:
- plan-structure answers can include structured facts, not just free-text retrieval

---

## Milestone 5 — Medicare payment-context layer
**Goal:** improve reimbursement/payment explanations without overpromising pricing.

Tasks:
- choose one or two CMS datasets only
- implement SMV2 ETL for a narrow subset
- build glossary-level mapping for billed vs allowed vs paid vs patient responsibility
- publish payment-context serving artifacts to the cloud-hosted serving layer
- integrate this into payment-context answers

Exit criteria:
- app can answer common payment-context questions with better grounding and fewer ambiguities

---

## 8) What to do about drug price in Phase 2

This deserves special handling because the North Star mentions it explicitly.

## Recommendation
Treat Phase 2 drug price support as **price context**, not personalized price shopping.

### What we can responsibly do
- explain what kinds of public price references exist
- distinguish label/list/reference/payment concepts
- use public federal/reference data where available
- connect a drug to normalized identifiers and official label context

### What we should avoid claiming
- exact pharmacy cash price
- exact insured out-of-pocket amount
- “best price near you” without a validated source

### Suggested product wording
When asked a price question, answer with:
1. what kind of price the user may mean
2. what public references exist
3. what this app can and cannot infer today
4. citations

This keeps the product honest while still useful.

---

## 9) QA and safety requirements for Phase 2

Every Phase 2 answer should pass these checks:

### Grounding checks
- at least one user-facing citation when answer includes explanatory claims
- every structured fact linked to a source id
- every lookup result linked to a dataset snapshot or live query timestamp

### Safety checks
- no medical recommendation phrasing
- no personalized financial certainty claims
- explicit caution when price or coverage depends on user-specific context

### UX checks
- answer distinguishes facts from interpretation
- citations are readable
- warnings are not hidden

---

## 10) Success metrics for Phase 2

Suggested success metrics:
- drug lookup questions answered correctly and consistently in smoke tests
- structured routes produce citations/provenance 100% of the time
- reduced hallucination rate on drug/provider identity questions
- improved thumbs-up rate on drug/provider/payment-context questions
- no uncited structured claims in QA audits

---

## 11) Suggested first issue breakdown

I would break Phase 2 into these first issues:

1. **Create machine-readable source registry**
2. **Define source/provenance schemas**
3. **Implement source registry loader**
4. **Decide cloud serving shape for structured data**
5. **Implement answer provenance table + writes**
6. **Set up SMV2 ETL skeleton**
7. **Add openFDA ETL/client path**
8. **Add RxNorm normalization client + ETL mapping**
9. **Implement drug lookup route**
10. **Add NPPES ingestion pipeline**
11. **Implement provider lookup route**
12. **Define Marketplace minimal field set**
13. **Implement CMS payment glossary + narrow dataset subset**
14. **Add grounding QA checks for structured routes**

---

## 12) My recommended execution order

If we want the highest value with lowest complexity, do this exact order:

### First
- source registry
- decide cloud-hosted serving pattern
- provenance storage
- SMV2 ETL skeleton
- openFDA
- RxNorm
- drug lookup route

### Second
- NPPES
- provider lookup route

### Third
- Healthcare.gov / Exchange field subset
- insurance structure answers

### Fourth
- CMS payment-context subset

This sequence matches the North Star and gives the best chance of shipping meaningful Phase 2 value quickly.

---

## 13) Final recommendation

Phase 2 should be treated as a **precision layer**, not a giant ingestion phase.

The most important decisions are:
- keep the product scope narrow
- use **SMV2** as the ETL/data-processing layer
- consider a **cloud-hosted structured data serving layer** instead of forcing all normalized datasets into the local app runtime

Execution priorities:
- solve **drug relationships** well
- solve **provider identity** well
- improve **insurance basics** with structured support
- improve **payment context** without pretending to solve personalized pricing

If we stay disciplined, Phase 2 can materially improve user trust and answer quality while remaining small enough to support the larger develop-by-using loop.
