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
  4. prioritize (initially simple; later smarter)
  5. generate an implementation plan
  6. implement changes in a sandbox
  7. validate (tests + UI-level QA)
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
     - a short spec / plan
     - code changes
     - a deployed update

3. **Cadence (nightly / daily)**
   - Updates can ship on a daily rhythm **when there is new feedback**.
   - If there is **no new user feedback**, the system **skips the run** (cost and churn control).

4. **Quality guardrails**
   - Even with automation, the system has minimum safeguards:
     - build must pass
     - unit tests
     - UI-level QA via an automated “computer use” / tool-driven flow
     - rollback option

## 4) The first concrete use-case (so it’s not abstract)

To avoid a vague “platform project,” we start with a specific product.

### Product: a chat interface for learning the US healthcare system

A chat-based UI where a user can ask questions ranging from basic to detailed, such as:

- “Who pays for what in US healthcare?”
- “How do different insurance types work?”
- “Can I save money? What should I plan for when I retire?”
- “What does this billing/procedure code mean?”

The initial purpose is **information + education**, not medical or financial recommendations.

### Content strategy (phased)

**Phase 1: web search with citations (no structured datasets yet)**
- Use web search and always return answers with **citations**.
- Optionally “accumulate” useful docs from searches into local storage for reuse.

**Phase 2: add structured public data**
- First structured data focus: **drug price & drug relationships**.
- Add more structured sources later, driven by usage/feedback.

**Phase 3: expand**
- Incorporate additional datasets and deeper features over time.

## 5) Personas

### Primary persona (day 1)

- **You (Bo / ninjapapa)**, representing a “regular US middle-class” person trying to understand:
  - the healthcare system
  - confusing bills
  - how insurance works
  - how to save money
  - what to plan for at retirement

### Future personas (later)

- People like the primary persona who need **information for decisions**, such as:
  - insurance choices
  - provider choices
  - what to do for kids / family situations
  - how to find providers/resources for a health issue

Constraints for all personas:
- The product is **not** for giving medical recommendations; it’s for **grounded information**.
- **Always cite sources**.

## 6) Constraints & guardrails

### Autonomy / human-in-the-loop (HITL)

Start with human approvals, then reduce HITL over time:

- Initial mode:
  1. **approve plan**
  2. **approve PR**
  3. **approve deploy**

Future mode:
- Move toward **zero HITL**, once quality gates and trust are strong enough.

### Budget / cadence

- Target cost: **<$5/day**.
- Nightly run happens **only when there is new feedback**.

### Data retention

- Store **full chat and clickstream inside this app** (for the POC).

### Quality

- Rollback must exist and be a visible choice (at least for you as the user).
- Validation includes:
  - unit tests
  - UI-level QA via an automated computer/tool

### Deployment

- MVP deploy target: **local**.

### Scope / platform

- MVP is **single user**.
- Use **OpenAI APIs** (for now) as part of the implementation.

## 7) Functional requirements (initial)

These are the “typical requirements” we still need to start with, even though the product will evolve beyond them:

### User-facing

- A working **chat UI**
- Each answer must request feedback:
  - **thumbs up / thumbs down**
  - optional comment box
- A free-form **feedback box** (catch-all)
- Ability to submit **feature requests**
- A **feature request status** view
- A **changelog** view (what shipped last night)

### System

- Persist:
  - feedback items
  - chat transcripts
  - clickstream events (in-app)
  - agent artifacts (summaries/specs/plans/patches/build logs)
- A repeatable nightly pipeline that:
  - pulls new feedback
  - produces a plan
  - implements changes
  - validates
  - deploys (local for MVP)

## 8) Feedback → backlog → delivery loop

### Feedback capture

Minimum input:
- free-form text feedback

Additionally (from product instrumentation):
- thumbs up/down per answer
- optional comment

### Backlog & project management

- Use **GitHub Issues** as the backlog.
- Maintain an “overall project plan” as markdown under `docs/`.
- A “project manager agent” owns:
  - intake
  - feasibility assessment
  - daily selection
  - status updates

### Triage rules (initial)

- **Plan first**: agent produces a plan/spec before writing code.
- Items that are feasible within constraints are candidates for immediate work.
- Items that are not feasible go into backlog.
- Backlog is reviewed **daily**; items may become feasible later (new capabilities, new data, better tooling).

### Feature verification

For feature work:
- explicitly ask the user whether the shipped feature **actually addresses the ask** (close-the-loop check).

## 9) Non-goals (for now)

- Multi-user scale
- Sophisticated prioritization algorithms (beyond the PM-agent’s simple daily selection)
- Formal product management rituals
- Perfect UX
- Full compliance/regulatory posture (this is a personal POC)

## 10) Expected outcomes / what “good” looks like

After an initial deployment (“v0”), the system should:

- Improve itself nightly based on real usage feedback.
- Become increasingly aligned with what the user actually needs.
- Demonstrate that “requirements” can emerge from usage + feedback rather than being fully specified up front.

### Success metrics (initial)

- Q&A satisfaction: **≥ 80% positive** (thumbs up) on questions.
- Feature satisfaction: **≥ 80%** of shipped features confirmed by the user as addressing the original ask.

## 11) Open questions (to resolve as we build)

- Exact schema for storing clicks/events (what’s the minimum useful without being creepy/noisy?)
- Definition of “new feedback” (what triggers a nightly run?)
- Minimum UI QA flow (what’s the smallest reliable smoke test we can automate?)
- How to keep answers grounded:
  - citations format
  - source quality bar
  - confidence/uncertainty display
- How to safely ratchet HITL down to zero (what guardrails are mandatory first?)
