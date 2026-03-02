# North Star / Ambition — “Develop-by-Using” Software (POC)

## 1) Why this project exists

This project is a **proof of concept** for a future kind of software that is **built and evolved primarily from direct user feedback**, rather than from a traditional up-front requirements document.

The core bet:
- The product can ship a useful first version.
- After that, it **improves itself daily** by collecting feedback inside the product, then using agents to plan + implement + deploy changes.

## 2) The North Star (end state)

A software system that:

- **Collects feedback in-product** (feature requests, bug reports, confusion points, “I wish it did X”).
- **Aggregates and stores** that feedback (with context).
- Uses an agent loop to:
  1. analyze feedback
  2. dedupe + cluster
  3. ask clarifying questions when needed
  4. prioritize (eventually)
  5. generate an implementation plan
  6. implement changes in a sandbox
  7. validate (tests/lint/smoke)
  8. deploy
  9. publish a changelog back into the product

In this world, the “persona” of:
- product management
- UX research
- requirements writing

…is **reduced toward zero** (or moved behind the scenes), with agents handling much of that work autonomously.

## 3) What we’re proving (POC goals)

This POC is successful if we can demonstrate:

1. **Feedback → action pipeline**
   - Feedback submitted from the UI reliably becomes an actionable work item.

2. **Agent-assisted product evolution loop**
   - An agent can turn that work item into:
     - a small spec
     - code changes
     - a deployed update

3. **Cadence**
   - Updates can ship on a **daily / nightly** rhythm (not just “whenever a human has time”).

4. **Quality guardrails**
   - Even with automation, the system has minimum safeguards (build passes, basic tests, rollback path).

## 4) The first concrete use-case (so it’s not abstract)

To avoid a vague “platform project,” we start with a specific product:

### Product: a chat interface for learning the US healthcare system

A chat-based UI where a user can ask questions ranging from basic to detailed, such as:

- “Who pays for what in US healthcare?”
- “How do different insurance types work?”
- “How does Medicare work, and when does it kick in?”
- “What does this billing/procedure code mean?”
- “What does this host system term mean?”

The initial purpose is **education and explanation**.

### Content strategy (evolution)

Phase 1 (start):
- Start with **internet-searchable** / broadly available info (summarized and explained in plain language).

Phase 2 (add structured public data):
- Incorporate **public-domain structured data** to answer more precise questions, e.g.:
  - “How many dollars did Medicare pay provider X last year for procedure Y?”
  - Other public datasets that enrich the answers with specific, verifiable numbers.

Phase 3 (expand):
- Add additional datasets and “deep-dive” features as driven by usage and feedback.

## 5) Functional requirements (initial)

These are the “typical requirements” we still need to start with, even though the product will evolve beyond them:

### User-facing
- A working **chat UI**
- Ability to **submit feedback/feature requests** from inside the product
- A simple **feature request list** / status view (even if only for one user)
- A **changelog** view (what shipped last night)

### System
- Persist feedback items (store + retrieve)
- Persist agent artifacts (summaries/specs/plans/patches/build logs)
- A repeatable “nightly” run that:
  - pulls new feedback
  - proposes changes
  - implements and validates
  - deploys

## 6) Non-goals (for now)

- Multi-user scale
- Sophisticated prioritization algorithms
- Formal product management rituals
- Perfect UX
- Full compliance/regulatory posture (this is educational and a POC)

## 7) Expected limitations (explicit constraints)

This is a **personal side project**.

- **Single user at the beginning** (Bo / ninjapapa)
- We can keep prioritization lightweight initially (because there’s only one user)
- The key is proving the loop, not building a polished enterprise platform

## 8) Expected outcomes / what “good” looks like

After an initial deployment (“v0”), the system should:

- Improve itself nightly based on real usage feedback.
- Become increasingly aligned with what the user actually needs.
- Demonstrate that “requirements” can emerge from usage + feedback rather than being fully specified up front.

## 9) Open questions (to resolve as we build)

- What feedback schema do we store (text only vs. structured: page, timestamp, conversation snippet, screenshot)?
- How much autonomy do we allow the agent initially (auto-merge vs. human approval)?
- What’s the minimum validation gate for nightly deploys (unit tests, e2e smoke, lint, typecheck)?
- Which structured public datasets should we integrate first for Medicare/payment questions?
- How do we keep answers grounded (citations, sources, confidence)?
