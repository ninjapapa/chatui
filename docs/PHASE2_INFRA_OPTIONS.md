# Phase 2 Infrastructure Options

This document evaluates infrastructure options for the structured-data layer described in:
- `docs/NORTHSTAR.md`
- `docs/PUBLIC_DATA_SOURCES_RESEARCH.md`
- `docs/SOURCE_REGISTRY.md`
- `docs/PHASE2_DATA_PLAN.md`

It assumes the following product direction:
- the **data pipeline is batch-oriented**
- the batch pipeline runs **daily**
- each daily run may add new source content, refresh changed datasets, or skip work when nothing changed
- the **serving layer must be flexible enough for evolving schema and new user requirements**
- the app remains focused on **grounded, cited answers**, not a rigid analytics warehouse UI

---

## 1) Infra goals

The infrastructure for Phase 2 should support these needs:

### A. Daily batch ETL
- scheduled run once per day
- fetch new/changed data only when needed
- produce versioned outputs / snapshots
- validate before publish
- keep historical versions for rollback/debugging

### B. Low-friction serving for the app
- answer-time reads should be simple and reliable
- backend should query a stable serving interface
- structured facts should be retrievable with provenance

### C. Flexible schema evolution
The product will evolve from user feedback, so the data layer must tolerate:
- new source types
- new question types
- new fields added over time
- incomplete / uneven source data
- mixed shapes across sources

### D. Small-team / MVP practicality
- simple to operate
- not too expensive
- easy to inspect manually
- compatible with local app development and future cloud deployment

### E. Separation of concerns
- **SMV2** should own ETL and publishing
- the **app backend** should own request-time answer orchestration
- the serving layer should sit between them cleanly

---

## 2) Architectural baseline

Recommended baseline architecture:

1. **Source acquisition**
   - public datasets / APIs / reference pages
2. **SMV2 batch ETL**
   - normalize
   - validate
   - version
   - produce serving outputs
3. **Cloud-hosted serving layer**
   - exposes read-friendly structured data to the app
4. **App backend**
   - query serving layer
   - combine with retrieval/citation layer
   - generate final answer
5. **Local SQLite**
   - app state, transcripts, feedback, answer provenance, source health metadata

In short:
- **heavy data processing happens offline in daily batch**
- **request-time app logic only reads prepared outputs**

This is the right shape for the project because it keeps the user-facing app fast while allowing the data model to evolve.

---

## 3) Core requirement: batch pipeline design

The data pipeline should be treated as a **daily batch pipeline**, not a streaming system.

## Why batch is the right fit
- public healthcare data sources usually update daily, weekly, monthly, or ad hoc — not second-by-second
- product value comes from correctness and traceability more than low-latency ingest
- daily runs fit the North Star’s nightly/daily evolution loop
- batch makes validation, backfills, and rollback much easier

## Recommended daily batch behavior
Each daily run should:
1. check source availability and metadata
2. determine which sources changed
3. fetch only needed deltas or new snapshots where possible
4. run SMV2 normalization/transforms
5. run quality checks
6. publish a new serving version only if validation passes
7. record provenance and run metadata
8. optionally skip publish if no meaningful change occurred

## Required batch artifacts
Each run should produce:
- run id
- start/end timestamps
- source ids processed
- input versions / checksums / source timestamps
- output artifact versions
- row counts / summary metrics
- validation results
- publish status

---

## 4) Core requirement: flexible schema serving layer

The serving layer should not assume that every source can be flattened into one rigid schema forever.

Why this matters:
- openFDA, RxNorm, NPPES, Marketplace files, and CMS datasets all have different shapes
- new user requests may require adding fields that are not known today
- source structures may drift over time
- some answer flows need strongly typed fields, while others benefit from semi-structured metadata

## Recommendation
Use a serving design that supports **hybrid schema**:
- a small set of **typed, stable columns** for common/high-value fields
- a **flexible JSON/metadata column** for source-specific or evolving attributes

This gives the product:
- strong support for common lookups
- freedom to add fields without full migrations every time
- better survivability as the app evolves from feedback

---

# 5) Infrastructure options

## Option A — Hosted Postgres as the serving layer

### Shape
- SMV2 publishes normalized tables into hosted Postgres
- app backend queries Postgres directly or through a thin internal API
- flexible fields are stored in JSONB columns where needed

### Why this is attractive
- excellent fit for mixed structured + semi-structured data
- JSONB gives schema flexibility
- supports indexes on high-value lookup fields
- easy to add version/provenance tables
- familiar operational model
- works well for app-style query patterns

### Good fit for this project
Very good.

It maps naturally to entities like:
- `drug_concepts`
- `provider_entities`
- `plan_entities`
- `dataset_snapshots`
- `answer_provenance`

And it supports flexible columns like:
- `attributes_json`
- `source_payload_json`
- `normalized_aliases_json`

### Pros
- best all-around balance of flexibility and simplicity
- easy to join provenance/snapshots with serving entities
- straightforward to evolve over time
- good developer ergonomics
- easy to expose via FastAPI or internal SQL access

### Cons
- not ideal for very large analytical scans compared with a columnar/object-store setup
- requires schema discipline to avoid messy JSON sprawl

### Recommendation
**Strong candidate for default choice.**

---

## Option B — Object storage + Parquet + thin query/API service

### Shape
- SMV2 publishes versioned Parquet outputs to object storage
- a small cloud API/service reads those artifacts and answers app queries
- app backend calls that service

### Why this is attractive
- great for versioned batch outputs
- cheap storage
- easy rollback by artifact version
- works well with append-only / snapshot-style publishing

### Good fit for this project
Good, especially if data volume grows or we want a clean separation between ETL outputs and serving.

### Pros
- excellent for daily batch publish model
- strong versioning story
- good for larger datasets
- easy to preserve historical snapshots

### Cons
- requires a custom serving layer or query engine
- more moving parts for MVP
- request-time flexibility depends on the API/service you build on top

### Recommendation
**Good second-stage option** if we want stronger artifact/versioning discipline or larger-scale data later.

---

## Option C — DuckDB/Parquet-backed cloud service

### Shape
- SMV2 publishes Parquet datasets
- a cloud service backed by DuckDB reads them for query serving
- app backend calls that service

### Why this is attractive
- very strong batch + file-based workflow
- simple analytical serving for modest scale
- flexible with evolving data and snapshots

### Good fit for this project
Promising, but more specialized.

### Pros
- elegant for batch-generated artifacts
- good for read-heavy workloads
- easy local/cloud parity for testing
- great for snapshot-based development

### Cons
- less standard as an app-serving default than Postgres
- may need more custom operational design for concurrency/caching/API behavior
- team ergonomics depend on comfort with DuckDB-centered workflows

### Recommendation
**Interesting option**, especially if the team likes file-based analytics workflows, but probably not the simplest default.

---

## Option D — Hosted document store / flexible NoSQL store

### Shape
- SMV2 publishes normalized documents
- app reads via key-based or indexed queries

### Why this is attractive
- natural flexibility for evolving schema
- easy to store heterogeneous records

### Good fit for this project
Mixed.

### Pros
- highly flexible schema
- easy to absorb source-specific payloads
- can move fast early on

### Cons
- weaker relational/provenance ergonomics
- harder to enforce consistent semantic model
- can become messy if multiple entities need joins or version-aware queries

### Recommendation
**Not my first choice** for this app because provenance, entity linking, and mixed lookup patterns matter a lot.

---

## Option E — Thin FastAPI data service in front of storage

### Shape
- regardless of storage choice, put a small cloud FastAPI service in front
- app backend calls the service instead of querying storage directly

### Why this is attractive
- decouples app from storage internals
- lets us evolve storage later without rewriting app logic
- allows opinionated query contracts per route

### Good fit for this project
Very good as a pattern, especially if we expect schema evolution.

### Pros
- isolates storage decisions
- gives stable app-facing endpoints
- central place for provenance enforcement and caching
- easier to change backing store over time

### Cons
- one more service to operate
- still need to pick the underlying storage layer

### Recommendation
**Recommended in combination with Option A or B.**

---

# 6) Comparison summary

| Option | Flex schema | Batch friendliness | App query simplicity | Versioning | MVP ops complexity | Overall |
|---|---:|---:|---:|---:|---:|---|
| Hosted Postgres | High | Good | High | Good | Low-Med | Best default |
| Object storage + Parquet + API | High | Very high | Med | Very high | Med | Strong future option |
| DuckDB/Parquet service | High | Very high | Med | Very high | Med | Interesting, more custom |
| Document store | Very high | Good | Med | Med | Med | Too loose for provenance-heavy app |
| Thin FastAPI service (front layer) | N/A | N/A | High | N/A | Med | Great as complement |

---

# 7) Recommended target architecture

## Default recommendation

### Serving layer
- **Hosted Postgres** as the primary structured-data serving store
- use **typed columns + JSONB** for flexible schema evolution

### Service layer
- a small **FastAPI data service** in front of Postgres
- app backend queries this service instead of binding tightly to storage internals

### Batch pipeline
- **SMV2** runs daily
- writes validated, versioned outputs into serving tables
- records run metadata and dataset snapshots

### Local app storage
- continue using **local SQLite** for:
  - chats
  - messages
  - answer feedback
  - freeform feedback
  - answer provenance copies / references
  - PM-agent / run summaries if needed

This gives the cleanest separation:
- SMV2 = build data
- cloud service = serve data
- app backend = consume data and answer questions

---

## Why this is the best fit

This architecture handles the two core user requirements well:

### Requirement 1: daily batch updates
Hosted Postgres + SMV2 is simple enough for daily scheduled updates and version tracking.

### Requirement 2: flexible schema for new user requirements
JSONB + a thin service layer allows us to add:
- new source-specific attributes
- new entity fields
- new lookup patterns
- new provenance details

…without redesigning the whole data model every week.

---

# 8) Recommended schema strategy

To support flexibility, use a **layered schema approach**.

## A. Stable core entity tables
Examples:
- `drug_concepts`
- `provider_entities`
- `plan_entities`
- `dataset_snapshots`
- `etl_runs`

These should contain the fields we know are high-value and repeatedly queried.

## B. Flexible metadata columns
Add JSON/JSONB columns such as:
- `attributes_json`
- `source_payload_json`
- `aliases_json`
- `quality_flags_json`
- `coverage_metadata_json`

## C. Version/provenance tables
Examples:
- `etl_runs`
- `published_versions`
- `entity_source_links`
- `dataset_snapshots`

This makes it possible to:
- trace every fact
- understand when a field was added
- support new user requirements without breaking old ones

---

# 9) Publishing model for daily batch

Recommended publish model:

## Step 1 — extract
SMV2 fetches only sources that are new/changed.

## Step 2 — transform
SMV2 normalizes into canonical entities and source-specific metadata payloads.

## Step 3 — validate
Run checks such as:
- required fields present
- row counts within expected range
- key uniqueness
- major drift warnings
- provenance completeness

## Step 4 — publish atomically
Publish a new version only after validation passes.

Recommended publish behavior:
- write to staging tables/artifacts first
- run checks
- promote to current version atomically

## Step 5 — record run metadata
Store:
- `run_id`
- source versions
- published version id
- affected entities
- warnings/errors

## Step 6 — skip if no meaningful changes
If the batch run finds no relevant updates, mark the run as skipped/no-op.

---

# 10) Cloud hosting options to consider

The user asked to consider a cloud host, so here are practical hosting shapes.

## Option 1 — Managed Postgres provider
Examples in general terms:
- any hosted Postgres platform

**Best for:**
- simplest MVP path
- flexible schema via JSONB
- easy app integration

## Option 2 — Cloud object storage + small compute service
Examples in general terms:
- object store + containerized API

**Best for:**
- artifact-heavy batch publication
- cheaper large snapshot retention

## Option 3 — Managed container/app platform hosting FastAPI + DB
**Best for:**
- one team controlling service and storage together
- easier API-centric serving model

## Recommendation
For MVP/early Phase 2, I would start with:
- **managed Postgres**
- plus a **small FastAPI data service**

If scale or snapshot complexity grows, evolve toward:
- **object storage + versioned Parquet artifacts + service layer**

---

# 11) Operational concerns

## Observability
Track:
- batch run success/failure
- source freshness
- row counts and drift
- serving query latency
- cache hit rates if added

## Rollback
Need ability to:
- roll back to previous published version
- inspect previous snapshots
- explain which version answered a user question

## Cost control
Daily batch keeps cost predictable.
Cloud serving cost can be controlled by:
- precomputing normalized tables
- indexing only high-value fields
- caching hot lookups

## Security
Even if data is public, protect:
- service credentials
- hosted DB access
- admin/control endpoints

---

# 12) Final recommendation

## Recommended Phase 2 infra stack

### Batch / ETL
- **SMV2**
- scheduled **daily batch runs**
- incremental fetch when possible
- versioned publish artifacts

### Serving
- **Hosted Postgres** with:
  - typed columns for stable fields
  - JSONB for flexible evolving attributes

### Service layer
- **FastAPI data service** in front of the serving store
- stable app-facing endpoints for lookups and provenance-aware queries

### App-local storage
- **SQLite** for app-owned state and feedback/provenance artifacts

---

## Why this recommendation wins
It is the best balance of:
- batch friendliness
- schema flexibility
- low operational complexity
- support for evolving product requirements
- clear separation between ETL and app serving

If the product later needs larger-scale snapshot management or heavier analytics, the next natural evolution is:
- keep the service layer
- move more of the published data artifacts toward **object storage + Parquet**
- preserve the same app-facing API contract

That path gives flexibility without overbuilding too early.
