# Source Registry

This document defines the source registry for the healthcare chat app.

It exists to support the product goals in `docs/NORTHSTAR.md`:
- always-cited answers
- grounded information, not medical or financial recommendations
- gradual expansion from web/document retrieval to structured public data
- future agent automation that can reason about source quality, feasibility, and freshness

This registry should become both:
1. a **human-readable operating document**
2. a **machine-readable contract** for ingestion, retrieval, citation, and QA

---

## 1) What the source registry is for

The app needs to know more than “a URL exists.”

For each approved source, we should track:
- what kind of source it is
- whether it is safe to cite directly to users
- whether it is safe only for internal lookup / enrichment
- how to ingest it
- how often it changes
- how trustworthy it is for different question types
- what caveats apply

The registry should be used by:
- retrieval
- structured lookup
- answer generation
- citation rendering
- ingestion jobs
- nightly PM / QA agent checks

---

## 2) Core design principles

### A. Separate citation sources from lookup sources
Some sources are excellent for direct user-facing citations.
Others are useful for normalization, enrichment, or lookups but are poor direct citations.

Examples:
- **Good citation source:** CMS explainer page
- **Good lookup source:** RxNorm concept mapping

### B. Track source trust explicitly
Not all public sources are equal.

Suggested trust tiers:
- `federal_primary`: official federal source, high confidence
- `federal_data`: official federal dataset/API, high confidence but may need interpretation
- `reference_partner`: trusted government-adjacent or official reference source
- `derived_public`: public but transformed/aggregated and needs caution
- `experimental`: not approved for production answer grounding

### C. Track consumer-safety
Some sources are technically correct but too easy to misread.
For example, Medicare reimbursement datasets are useful, but should not be shown as if they represent a user’s personal out-of-pocket cost.

### D. Track provenance and freshness
Every answer should be attributable to:
- one or more sources
- a specific fetch or ingest time
- optionally a dataset version / release date

---

## 3) Registry schema

Recommended canonical fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `source_id` | string | yes | Stable internal identifier |
| `name` | string | yes | Human-readable source name |
| `owner` | string | yes | Organization responsible for source |
| `category` | enum | yes | `reference`, `api`, `dataset`, `registry`, `search_index` |
| `mode` | enum | yes | `citation`, `lookup`, `hybrid` |
| `domain` | string | yes | Primary domain or publisher host |
| `base_url` | string | yes | Canonical home URL |
| `description` | string | yes | What the source is used for |
| `question_types` | string[] | yes | Supported question/use classes |
| `trust_level` | enum | yes | Trust tier |
| `consumer_safe` | boolean | yes | Whether raw data can be surfaced directly |
| `citation_allowed` | boolean | yes | Whether source may appear in user-facing citations |
| `retrieval_allowed` | boolean | yes | Whether source may be indexed or retrieved |
| `ingestion_method` | enum | yes | `live_api`, `bulk_download`, `manual_curation`, `web_retrieval` |
| `format` | string[] | no | Example: `html`, `json`, `csv`, `xml` |
| `update_cadence` | string | no | Daily / weekly / monthly / ad hoc / unknown |
| `versioning` | string | no | How version/release is tracked |
| `license_notes` | string | yes | Usage / redistribution notes |
| `attribution_notes` | string | no | Any attribution expectations |
| `limitations` | string[] | yes | Known caveats |
| `normalization_notes` | string | no | Mapping / cleaning requirements |
| `citation_pattern` | string | no | How to render citations |
| `priority` | enum | yes | `now`, `next`, `later`, `defer` |
| `status` | enum | yes | `approved`, `candidate`, `deferred`, `blocked` |
| `owner_notes` | string | no | Internal implementation notes |

---

## 4) Suggested machine-readable form

Recommended location:
- `config/sources.json` or `backend/config/sources.json`

Recommended top-level structure:

```json
{
  "schema_version": 1,
  "generated_at": null,
  "sources": []
}
```

Recommended per-source example:

```json
{
  "source_id": "cms_reference",
  "name": "CMS Reference Pages",
  "owner": "Centers for Medicare & Medicaid Services",
  "category": "reference",
  "mode": "citation",
  "domain": "cms.gov",
  "base_url": "https://www.cms.gov/",
  "description": "Authoritative consumer and policy reference pages for Medicare, Medicaid, provider payment, and healthcare system explanations.",
  "question_types": [
    "insurance_basics",
    "medicare_explainer",
    "payment_concepts",
    "provider_billing_context"
  ],
  "trust_level": "federal_primary",
  "consumer_safe": true,
  "citation_allowed": true,
  "retrieval_allowed": true,
  "ingestion_method": "web_retrieval",
  "format": ["html", "pdf"],
  "update_cadence": "ad_hoc",
  "versioning": "page fetch timestamp",
  "license_notes": "Official federal web content; still record source URL and fetch timestamp.",
  "attribution_notes": "Cite page title + publisher + URL.",
  "limitations": [
    "May describe programs and policies but not personalized cost estimates.",
    "Page-level detail varies widely."
  ],
  "normalization_notes": "Prefer page extraction to normalized snippets with canonical URL storage.",
  "citation_pattern": "[Title] (CMS, accessed/fetched date)",
  "priority": "now",
  "status": "approved",
  "owner_notes": "Primary phase-1 grounding source."
}
```

---

## 5) Source taxonomy for this app

### Question type taxonomy
Suggested initial `question_types` vocabulary:
- `insurance_basics`
- `medicare_explainer`
- `medicaid_explainer`
- `marketplace_plan_basics`
- `cost_sharing_explainer`
- `drug_identity`
- `drug_relationships`
- `drug_label_lookup`
- `drug_price_context`
- `provider_identity`
- `provider_specialty`
- `provider_payment_context`
- `billing_concepts`
- `facility_price_context`
- `care_access`
- `population_cost_context`

### Source category taxonomy
- `reference`: human-readable pages/docs meant for explanation
- `api`: live endpoint returning structured results
- `dataset`: downloadable bulk data
- `registry`: identity/roster source
- `search_index`: internal derived index built from approved sources

### Usage mode taxonomy
- `citation`: safe for direct user-facing citation
- `lookup`: best for internal normalization/facts, not usually user-facing citation alone
- `hybrid`: can serve both roles depending on the result

---

## 6) Initial approved registry entries

## Tier 1: approved now

### 1) CMS reference pages
- `source_id`: `cms_reference`
- `category`: `reference`
- `mode`: `citation`
- `trust_level`: `federal_primary`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- Medicare basics
- healthcare payment concepts
- provider billing / system explanations

**Key limitations:**
- not a personalized cost calculator
- can be technical; answer layer must translate jargon

---

### 2) Healthcare.gov reference + plan datasets
- `source_id`: `healthcare_gov_reference`
- `category`: `reference`
- `mode`: `hybrid`
- `trust_level`: `federal_primary`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- Marketplace plan basics
- premiums / deductibles / out-of-pocket concepts
- plan dataset ingestion later

**Key limitations:**
- Marketplace-focused, not employer plans generally

---

### 3) MedlinePlus
- `source_id`: `medlineplus_reference`
- `category`: `reference`
- `mode`: `citation`
- `trust_level`: `reference_partner`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- patient-friendly explanations
- medication and health-topic support content

**Key limitations:**
- not the primary source for insurance/payment policy questions

---

### 4) openFDA drug NDC
- `source_id`: `openfda_ndc`
- `category`: `api`
- `mode`: `hybrid`
- `trust_level`: `federal_data`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- NDC lookup
- product/package metadata
- manufacturer/product facts

**Key limitations:**
- not a retail or personalized drug price source
- may require normalization with RxNorm

---

### 5) openFDA drug label
- `source_id`: `openfda_label`
- `category`: `api`
- `mode`: `hybrid`
- `trust_level`: `federal_data`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- labeling content
- indications / warnings / product descriptions

**Key limitations:**
- labels can be verbose, incomplete, or inconsistent
- answer layer must avoid medical advice framing

---

### 6) RxNorm / NLM Clinical Tables
- `source_id`: `rxnorm`
- `category`: `registry`
- `mode`: `lookup`
- `trust_level`: `reference_partner`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- generic/brand relationships
- ingredient normalization
- concept mapping across drug names

**Key limitations:**
- usually not enough as a standalone user-facing citation
- requires concept mapping logic

---

### 7) NPPES / NPI Registry
- `source_id`: `nppes_npi`
- `category`: `registry`
- `mode`: `hybrid`
- `trust_level`: `federal_data`
- `priority`: `now`
- `status`: `approved`

**Use for:**
- provider identity
- organization identity
- specialty/taxonomy basics

**Key limitations:**
- registry quality varies
- does not imply network status, quality, or price

---

## Tier 2: approved next

### 8) CMS provider summary / utilization datasets
- `source_id`: `cms_provider_summary`
- `category`: `dataset`
- `mode`: `lookup`
- `trust_level`: `federal_data`
- `priority`: `next`
- `status`: `approved`

**Use for:**
- provider payment/utilization context
- specialty and service mix summaries

**Key limitations:**
- Medicare-only lens
- easy for users to misinterpret without explanation

---

### 9) CMS fee schedule / payment system files
- `source_id`: `cms_fee_schedule`
- `category`: `dataset`
- `mode`: `lookup`
- `trust_level`: `federal_data`
- `priority`: `next`
- `status`: `approved`

**Use for:**
- Medicare allowed/payment-context references
- reimbursement explanation

**Key limitations:**
- not patient out-of-pocket price
- technically dense

---

### 10) HRSA data
- `source_id`: `hrsa_data`
- `category`: `dataset`
- `mode`: `hybrid`
- `trust_level`: `federal_data`
- `priority`: `next`
- `status`: `approved`

**Use for:**
- shortage areas
- access-to-care context
- safety-net ecosystem context

---

### 11) AHRQ data / MEPS-style cost context
- `source_id`: `ahrq_cost_context`
- `category`: `dataset`
- `mode`: `hybrid`
- `trust_level`: `federal_data`
- `priority`: `next`
- `status`: `approved`

**Use for:**
- cost context
- utilization context
- planning-oriented educational answers

**Key limitations:**
- more useful for ranges/context than direct personalized answers

---

## Tier 3: defer

### 12) Hospital price transparency raw files
- `source_id`: `hospital_price_transparency`
- `category`: `dataset`
- `mode`: `lookup`
- `trust_level`: `federal_data`
- `priority`: `later`
- `status`: `deferred`

**Reason for defer:**
- high normalization complexity
- difficult early UX

### 13) HCUP-heavy datasets
- `source_id`: `hcup`
- `category`: `dataset`
- `mode`: `lookup`
- `trust_level`: `reference_partner`
- `priority`: `later`
- `status`: `deferred`

**Reason for defer:**
- more research-heavy than MVP needs

### 14) CPT-centric code explanation data
- `source_id`: `cpt_centric_features`
- `category`: `dataset`
- `mode`: `lookup`
- `trust_level`: `experimental`
- `priority`: `defer`
- `status`: `blocked`

**Reason for block:**
- licensing / proprietary constraints

---

## 7) Answer-time provenance requirements

For every answer, persist:
- `answer_id`
- `question_text`
- `source_ids[]`
- `source_urls[]`
- `source_titles[]`
- `retrieval_timestamp`
- `dataset_versions[]` if applicable
- `citation_rendered`
- `confidence_notes`
- `warnings[]`

This is important for:
- debugging
- future PM-agent audits
- replayability
- quality review

---

## 8) Ingestion-state tracking

Each source may have a current ingest state.
Recommended operational fields:

| Field | Description |
|---|---|
| `enabled` | Whether source is active in runtime |
| `last_checked_at` | Last health check / metadata check |
| `last_ingested_at` | Last successful ingest |
| `last_version` | Last observed dataset version / release id |
| `last_row_count` | Approximate row count if relevant |
| `last_error` | Most recent ingest error |
| `quality_status` | `green`, `yellow`, `red` |

This can live in a database table rather than the static registry file.

---

## 9) Recommended repo artifacts

I recommend these follow-on files:
- `docs/SOURCE_REGISTRY.md` ← this document
- `config/sources.json` ← machine-readable registry
- `docs/PHASE2_DATA_PLAN.md` ← detailed implementation plan
- `docs/CITATION_POLICY.md` ← how citations should be rendered and when to warn users
- `docs/DATA_GLOSSARY.md` ← definitions like billed vs allowed vs negotiated vs out-of-pocket

---

## 10) Immediate next step

Implement the first machine-readable registry with these initial approved sources:
- `cms_reference`
- `healthcare_gov_reference`
- `medlineplus_reference`
- `openfda_ndc`
- `openfda_label`
- `rxnorm`
- `nppes_npi`
- `cms_provider_summary`
- `cms_fee_schedule`
- `hrsa_data`
- `ahrq_cost_context`

That gives the app a clean foundation for both phase 1 retrieval and phase 2 structured-data expansion.
