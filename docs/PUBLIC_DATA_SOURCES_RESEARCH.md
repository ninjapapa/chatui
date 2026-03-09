# Public Data Source Research for the Healthcare Chat MVP

## Why this doc exists

This is a research summary for the product described in `docs/NORTHSTAR.md`:
- a **chat interface for learning the US healthcare system**
- answers should be **grounded and cited**
- phase 1 can start with **web / document retrieval with citations**
- phase 2 should add **structured public data**, especially around **drug price and drug relationships**

## Key takeaway

For this product, the best initial strategy is **not** to start with one giant healthcare dataset.

Instead, use a **layered source strategy**:

1. **Authoritative public reference content** for answer grounding and citations
   - CMS
   - Healthcare.gov
   - MedlinePlus / NIH / NLM
   - CDC
   - AHRQ
   - HRSA
2. **Structured public/open datasets** for factual lookups
   - drug identifiers and labels
   - Medicare payment and utilization data
   - provider registries
   - Marketplace plan data
   - workforce / shortage area data
3. **Explicitly avoid or defer proprietary / hard-to-use sources**
   - CPT licensing
   - commercial claims datasets
   - sources that require paid access / DUAs for MVP

The app should answer consumer questions by combining:
- a **retrieval layer** over authoritative public documents
- a **small curated structured-data layer** for common factual questions
- strong citations + uncertainty language

---

## Important terminology: “public domain” vs “publicly available”

In healthcare data, these are not the same thing.

### Strict public-domain / US government content
Many federal publications, webpages, and some datasets are effectively the safest starting point for MVP use, especially from:
- CMS
- NIH / NLM
- CDC
- AHRQ
- HRSA
- Healthcare.gov

### Publicly available / open / public-use data
Some highly useful sources are publicly downloadable or queryable, but may still have:
- terms of use
- attribution expectations
- redistribution caveats
- rate limits
- application / public-use agreements

For implementation, the safest approach is:
- treat **federal reference pages and APIs** as the default source class
- for each dataset, record:
  - owner
  - access method
  - update cadence
  - allowed uses
  - known limitations

---

## What the North Star implies for data strategy

From `docs/NORTHSTAR.md`, the product needs to answer questions like:
- who pays for what in US healthcare
- how insurance types work
- how to save money / what to expect financially
- what billing / procedure codes mean
- later: drug price and drug relationships

That means the source stack needs to support **five distinct jobs**:

1. **Healthcare-system explainer content**
   - Medicare / Medicaid / Marketplace / employer coverage basics
2. **Consumer cost / coverage information**
   - plan structure, cost-sharing, payment concepts, preventive coverage, etc.
3. **Drug lookup**
   - drug names, ingredients, labels, NDCs, normalized concepts, generic / brand relationships
4. **Provider / organization lookup**
   - NPI, specialty, organization identity, basic location / participation signals
5. **Billing / code interpretation**
   - diagnosis / procedure / service code context, with strong caveats on what is and is not public

No single source covers all five well.

---

# Recommended source inventory

## A. Best sources for authoritative consumer-facing answer grounding

These are the best **phase-1 citation sources**.

### 1) CMS / Medicare / Medicaid pages
**Best for:**
- Medicare basics
- payment concepts
- provider types
- coverage rules
- public policy explanations

**Why useful:**
- highly authoritative for large parts of the US healthcare system
- strong fit for questions like “who pays for what,” Medicare, provider billing, and reimbursement structure

**Examples:**
- CMS Data Available to Everyone  
  https://www.cms.gov/data-research/cms-data/data-available-everyone
- CMS provider data catalog  
  https://data.cms.gov/provider-data/
- Physician Fee Schedule  
  https://www.cms.gov/medicare/medicare-fee-for-service-payment/physicianfeesched
- Prospective Payment Systems  
  https://www.cms.gov/medicare/payment/prospective-payment-systems
- Hospital Price Transparency  
  https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency

**Assessment:** Must-have.

### 2) Healthcare.gov
**Best for:**
- ACA Marketplace concepts
- plan metal tiers
- premiums / deductibles / out-of-pocket basics
- eligibility and enrollment explanations

**Examples:**
- Health and dental plan datasets for researchers and issuers  
  https://www.healthcare.gov/health-and-dental-plan-datasets-for-researchers-and-issuers/

**Assessment:** Must-have for consumer insurance questions.

### 3) MedlinePlus (NLM / NIH)
**Best for:**
- plain-language medical / medication explanations
- patient education references
- linking health topics to reliable source content

**Examples:**
- MedlinePlus XML files  
  https://medlineplus.gov/xml.html

**Assessment:** Strong source for understandable patient-facing citations.

### 4) CDC
**Best for:**
- public health facts
- prevalence / surveillance context
- risk-factor / prevention explanations

**Examples:**
- NHIS / NCHS survey content  
  https://www.cdc.gov/nchs/nhis/index.htm

**Assessment:** Good supporting source, especially for population-level context.

### 5) AHRQ
**Best for:**
- healthcare utilization / quality / spending context
- evidence-based explainers and survey data

**Examples:**
- AHRQ data and surveys  
  https://www.ahrq.gov/data/index.html

**Assessment:** Strong supporting source for cost / utilization context.

### 6) HRSA
**Best for:**
- provider shortage areas
- safety-net / federally supported provider ecosystem
- workforce access context

**Examples:**
- HRSA data portal  
  https://data.hrsa.gov/

**Assessment:** Good for access-to-care questions.

---

## B. Best structured data sources for MVP and phase 2

## 1) openFDA drug APIs
**Best for:**
- drug NDC lookup
- drug labeling content
- product / package metadata

**Examples:**
- Drug NDC API  
  https://open.fda.gov/apis/drug/ndc/
- Drug label API  
  https://open.fda.gov/apis/drug/label/

**Why it matters:**
The North Star explicitly calls out **drug price and drug relationships** as the first structured-data expansion. openFDA is one of the cleanest public sources for:
- NDCs
- label text
- manufacturer / product metadata

**Limitations:**
- not a direct consumer price source
- label data can be messy / uneven
- not enough alone for generic-vs-brand relationship logic

**Assessment:** Must-have.

## 2) RxNorm (NLM)
**Best for:**
- normalized drug names
- ingredient / brand / generic relationships
- mapping multiple drug naming systems to one normalized concept

**Examples:**
- RxNorm overview  
  https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- NLM Clinical Tables  
  https://clinicaltables.nlm.nih.gov/

**Why it matters:**
If the app needs to answer things like:
- “Is this the generic version?”
- “What is the active ingredient?”
- “Are these two drugs the same thing under different brands?”

…RxNorm is far more useful than raw label text alone.

**Limitations:**
- requires some terminology / mapping work
- not a price database

**Assessment:** Must-have for the drug-data phase.

## 3) CMS physician / practitioner / provider public data
**Best for:**
- provider characteristics
- utilization summaries
- payment summaries
- provider-facing Medicare data

**Examples:**
- CMS provider data catalog  
  https://data.cms.gov/provider-data/
- Medicare Physician & Other Practitioners theme/search  
  https://data.cms.gov/provider-data/search?theme=Medicare%20Physician%20and%20Other%20Practitioners

**Why it matters:**
Useful for questions like:
- what kinds of services a provider commonly bills for
- Medicare-allowed amounts / utilization summaries
- provider specialties and characteristics

**Limitations:**
- Medicare data is not the whole market
- can be hard for consumers to interpret without explanation

**Assessment:** High-value, but best exposed through carefully designed explanations.

## 4) NPPES / NPI Registry
**Best for:**
- provider identity lookup
- organization identity lookup
- specialty / taxonomy basics

**Examples:**
- NPI files  
  https://download.cms.gov/nppes/NPI_Files.html
- NPI Registry  
  https://npiregistry.cms.hhs.gov/search

**Why it matters:**
This is the backbone for answering:
- who is this provider / organization
- what specialty are they registered under
- what is this billing entity

**Limitations:**
- registry quality varies
- not enough for quality or coverage decisions by itself

**Assessment:** Must-have for provider lookup.

## 5) Healthcare.gov Marketplace plan datasets
**Best for:**
- plan availability
- premiums / deductibles / cost-sharing fields
- issuer and plan-level comparison work

**Examples:**
- Healthcare.gov plan datasets  
  https://www.healthcare.gov/health-and-dental-plan-datasets-for-researchers-and-issuers/
- CMS Exchange public use files  
  https://www.cms.gov/marketplace/resources/data/public-use-files

**Why it matters:**
Useful for user questions about:
- ACA plan structure
- how plan tiers differ
- plan comparison concepts

**Limitations:**
- Marketplace-only, not employer coverage
- may need significant normalization across years / states

**Assessment:** Very good for later insurance-comparison features.

## 6) CMS fee schedule and payment system files
**Best for:**
- understanding Medicare payment logic
- grounding explanations of reimbursement and service categories
- approximate public reference values for some services

**Examples:**
- Physician Fee Schedule  
  https://www.cms.gov/medicare/medicare-fee-for-service-payment/physicianfeesched
- Prospective Payment Systems  
  https://www.cms.gov/medicare/payment/prospective-payment-systems

**Why it matters:**
Helpful for questions like:
- what does Medicare typically allow for this kind of service
- how are services categorized / paid

**Limitations:**
- not consumer out-of-pocket price
- not commercial payer negotiated rate
- can be technically dense

**Assessment:** Valuable reference data, but requires translation into consumer language.

## 7) CMS hospital price transparency materials
**Best for:**
- directionally understanding hospital pricing disclosures
- future work on hospital service prices

**Examples:**
- Hospital Price Transparency  
  https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency
- Enforcement / data pages on data.cms.gov

**Why it matters:**
Important area for future pricing features.

**Limitations:**
- machine-readable files are inconsistent across hospitals
- hard to normalize for MVP
- real negotiated-rate comparison is nontrivial

**Assessment:** Important, but likely too messy for the first implementation.

## 8) HRSA data
**Best for:**
- shortage areas
- health center / access context
- workforce / safety-net infrastructure

**Examples:**
- https://data.hrsa.gov/

**Assessment:** Good enrichment source for access questions.

## 9) AHRQ / MEPS / utilization-and-cost survey data
**Best for:**
- consumer-oriented spending context
- utilization patterns
- retirement / planning oriented cost discussions

**Examples:**
- AHRQ data portal  
  https://www.ahrq.gov/data/index.html
- HCUP home  
  https://www.hcup-us.ahrq.gov/

**Why it matters:**
Questions like “what should I expect to spend?” are often better answered with:
- survey-based ranges
- utilization patterns
- high-level spending context

**Limitations:**
- HCUP is powerful but often not the easiest MVP source
- some AHRQ products are easier to use than others

**Assessment:** Good for later cost-context features; start carefully.

---

# Source classes to defer or avoid at MVP

## 1) CPT-based interpretation as a core feature
**Reason:** CPT is proprietary.

You can still explain billing at a high level, and you may be able to work with public Medicare-facing service references in limited ways, but a broad “explain any CPT code deeply” feature introduces licensing and product complexity.

**Recommendation:**
- defer full CPT-centric tooling
- focus first on:
  - NDC / RxNorm drug work
  - NPI / provider lookup
  - insurance / Medicare / Marketplace explanations

## 2) Commercial claims data
**Reason:** expensive, licensed, and not aligned with the MVP constraints.

## 3) HCUP-heavy workflows in phase 1
**Reason:** valuable, but more research-grade and less directly useful than simpler federal web content + lighter structured sources.

## 4) Hospital negotiated-rate normalization as an early feature
**Reason:** important, but operationally messy.

---

# Recommended phased data plan

## Phase 1: authoritative citation layer only
Use retrieval over curated public sites:
- CMS
- Healthcare.gov
- MedlinePlus
- CDC
- AHRQ
- HRSA

### Deliverables
- source allowlist by domain
- citation formatter
- answer template with uncertainty / scope guardrails
- optional page cache / snippet cache

### Why this is the right first move
This gets the product answering real user questions quickly while staying aligned with the North Star requirement to **always cite sources**.

---

## Phase 2: first structured data package

### Strong recommendation: build this exact starter set
1. **openFDA NDC**
2. **RxNorm**
3. **NPI / NPPES**
4. **Healthcare.gov / Exchange PUFs**
5. **selected CMS provider + fee schedule datasets**

### What this unlocks
- drug identity + generic/brand relationship questions
- basic provider identity lookup
- Marketplace plan structure comparisons
- Medicare payment-context answers

This is the best fit with the North Star note: **“First structured data focus: drug price & drug relationships.”**

### Important gap
This set gives strong **drug identity / relationship** coverage, but only partial **drug price** coverage.

For drug price, likely MVP approach is:
- answer with **federal/reference pricing context** where available
- be explicit that this is **not personalized pharmacy cash price prediction**
- defer retail pharmacy price comparison until a later phase unless a clean public source is identified

---

## Phase 3: enrichment sources
After the above works, consider:
- HRSA shortage/access data
- AHRQ / MEPS spending-context data
- select CDC/NCHS survey datasets
- more CMS utilization and facility data

---

# Practical implementation guidance for this repo

## 1) Build a source registry
Create a machine-readable registry for approved sources with fields like:
- `source_id`
- `name`
- `owner`
- `category` (`reference`, `api`, `dataset`)
- `domain`
- `trust_level`
- `consumer_safe` (bool)
- `license_notes`
- `update_cadence`
- `citation_pattern`
- `ingestion_method`

This will help both the app and the future PM/agent loop.

## 2) Separate “citation sources” from “lookup sources”
Not every structured dataset is a good direct citation source.

Suggested split:
- **citation sources:** CMS pages, Healthcare.gov pages, MedlinePlus, CDC, AHRQ
- **lookup sources:** openFDA, RxNorm, NPPES, Exchange PUFs, CMS provider datasets

## 3) Start with narrow, high-confidence user journeys
Recommended first supported question classes:
1. “Explain Medicare / Medicaid / ACA / deductibles / out-of-pocket max”
2. “What is this drug / ingredient / generic / brand relationship?”
3. “What kind of provider is this NPI / organization?”
4. “How do Marketplace plan tiers differ?”

## 4) Be conservative with “price” claims
For MVP, distinguish clearly between:
- billed amount
- allowed amount
- negotiated rate
- patient responsibility
- list price
- retail price

These are often conflated in healthcare questions.

## 5) Record provenance at answer time
For every answer, store:
- cited URLs
- dataset version / pull date if structured data used
- answer timestamp
- confidence notes

That fits the broader feedback → quality → improvement loop in `docs/NORTHSTAR.md`.

---

# Shortlist: what I would implement first

## Tier 1 — implement immediately
- CMS public reference pages
- Healthcare.gov reference pages and plan datasets
- MedlinePlus reference content
- openFDA drug APIs
- RxNorm / NLM clinical tables
- NPPES / NPI registry data

## Tier 2 — add after the basics work
- CMS provider summary / utilization datasets
- CMS fee schedule / payment system files
- HRSA data
- AHRQ cost / utilization context data

## Tier 3 — defer
- hospital negotiated-rate normalization
- HCUP-heavy analysis pipelines
- deep billing-code interpretation built around proprietary code systems
- commercial data products

---

# Final recommendation

For this app, the winning data architecture is:

1. **Phase 1:** curated retrieval over authoritative federal health sites with citations
2. **Phase 2:** a small structured layer centered on **openFDA + RxNorm + NPPES + Healthcare.gov/CMS datasets**
3. **Phase 3:** add cost / utilization / access enrichment once core answer quality is stable

If the goal is to move fast while preserving answer quality, the best immediate build path is:
- use public federal reference content for most answers
- add structured data only where it materially improves user value
- begin with **drug relationships**, **provider lookup**, and **insurance basics**
- defer messy pricing and proprietary coding workflows until later

---

## Source list used in this research

- `docs/NORTHSTAR.md`
- CMS data available to everyone: https://www.cms.gov/data-research/cms-data/data-available-everyone
- CMS provider data catalog: https://data.cms.gov/provider-data/
- CMS Exchange public use files: https://www.cms.gov/marketplace/resources/data/public-use-files
- Healthcare.gov plan datasets: https://www.healthcare.gov/health-and-dental-plan-datasets-for-researchers-and-issuers/
- openFDA drug NDC API: https://open.fda.gov/apis/drug/ndc/
- openFDA drug label API: https://open.fda.gov/apis/drug/label/
- NLM Clinical Tables: https://clinicaltables.nlm.nih.gov/
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- MedlinePlus XML: https://medlineplus.gov/xml.html
- NPI files: https://download.cms.gov/nppes/NPI_Files.html
- NPI Registry: https://npiregistry.cms.hhs.gov/search
- HRSA data portal: https://data.hrsa.gov/
- AHRQ data portal: https://www.ahrq.gov/data/index.html
- HCUP: https://www.hcup-us.ahrq.gov/
- CDC NHIS: https://www.cdc.gov/nchs/nhis/index.htm
- CMS Physician Fee Schedule: https://www.cms.gov/medicare/medicare-fee-for-service-payment/physicianfeesched
- CMS Prospective Payment Systems: https://www.cms.gov/medicare/payment/prospective-payment-systems
- CMS Hospital Price Transparency: https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency
