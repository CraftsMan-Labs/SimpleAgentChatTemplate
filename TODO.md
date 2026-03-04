# TODO - YAML-to-Chat Platform (Vue + FastAPI + OpenAI-Compatible API)

## Current Progress Snapshot

- **Completed foundations:** P1, P2 (core schema), P3 (primary endpoints), P4 (starter registry), P5 (starter bundle), P8/P9 (desktop-first UI baseline).
- **In progress:** P6/P7 streaming refinement and richer persistence semantics.
- **Next focus:** P10 (responsive hardening), P12 (broader test coverage), P14 (release hardening).

## Root Program Task (P0)

### P0. Build a production-ready YAML-driven chat platform
- **Value:** Converts editable YAML workflows into a usable chat product with strong UX, persistence, and compatibility.
- **Outcome:** A split-stack system (Vue frontend, FastAPI backend, PostgreSQL) that runs SimpleAgents workflows through OpenAI-compatible endpoints.
- **Relation to Parent:** Top-level objective; all tasks below are direct sub-tasks of this root.

#### P0 Sub-Tasks

##### P0.1 Define architecture and boundaries
- **Value:** Reduces rework by deciding stack split and contracts early.
- **Outcome:** Confirmed split architecture: Vue frontend, FastAPI backend, Postgres persistence, OpenAI-compatible backend endpoints.
- **Relation to Parent:** Establishes the foundational technical direction for P0.

##### P0.2 Define phased delivery plan
- **Value:** Enables predictable execution with clear dependencies.
- **Outcome:** Implementation roadmap across scaffolding, API, registry, execution, streaming, UI parity, and polish.
- **Relation to Parent:** Converts P0 from idea to executable schedule.

##### P0.3 Define v1 scope guardrails
- **Value:** Prevents scope creep while keeping extensibility.
- **Outcome:** Desktop-first with responsive behavior, mobile deferred; no Jaeger; OpenAI-compatible endpoints required.
- **Relation to Parent:** Keeps P0 focused on deliverable v1 outcomes.

##### P0.4 Define acceptance criteria
- **Value:** Creates a shared definition of done.
- **Outcome:** Platform runs at least one simple YAML workflow and one grouped bundle workflow via `/v1/chat/completions`.
- **Relation to Parent:** Provides measurable completion criteria for P0.

---

## Parent Task P1 - Repository and Runtime Scaffolding
- **Value:** Creates a stable baseline for parallel frontend/backend development.
- **Outcome:** New project structure with isolated frontend/backend services and shared environment setup.
- **Relation to Parent:** Implements P0.1 architecture decisions in code layout.

### P1 Sub-Tasks

#### P1.1 Create frontend workspace (`frontend/`)
- **Value:** Starts UI delivery quickly with modern tooling.
- **Outcome:** Vue 3 + Vite + TypeScript project scaffolded and runnable.
- **Relation to Parent:** Implements the frontend half of P1.

#### P1.2 Create backend workspace (`backend/`)
- **Value:** Isolates API and workflow runtime logic.
- **Outcome:** FastAPI app skeleton with modular folder structure (`api`, `core`, `models`, `schemas`, `services`).
- **Relation to Parent:** Implements the backend half of P1.

#### P1.3 Add environment configuration templates
- **Value:** Standardizes local setup and deployment inputs.
- **Outcome:** `.env.example` files for frontend and backend covering DB, workflow paths, provider credentials, and app flags.
- **Relation to Parent:** Connects both service scaffolds with consistent configuration.

#### P1.4 Add local orchestration (`docker-compose`)
- **Value:** Reduces setup friction for repeatable development.
- **Outcome:** Compose stack for frontend, backend, and Postgres with named volumes and health checks.
- **Relation to Parent:** Makes the P1 scaffolds operational together.

---

## Parent Task P2 - Database Foundation and Migrations
- **Value:** Enables durable chat memory, run tracking, and analytics without external tracing.
- **Outcome:** Postgres schema with migration workflow and indexed tables for conversation and workflow execution data.
- **Relation to Parent:** Realizes P0 persistence requirements.

### P2 Sub-Tasks

#### P2.1 Set up SQLAlchemy + Alembic
- **Value:** Provides maintainable schema evolution.
- **Outcome:** Migration pipeline initialized and wired to backend settings.
- **Relation to Parent:** Core migration infrastructure for all P2 schema work.

#### P2.2 Create `workflow_models` table
- **Value:** Central model registry powering OpenAI-compatible `model` IDs.
- **Outcome:** Stores model mappings (`model_id`, workflow path, kind, registry JSON, metadata).
- **Relation to Parent:** Enables model discovery and request routing.

#### P2.3 Create conversation/message tables
- **Value:** Preserves multi-turn context and UI thread history.
- **Outcome:** `conversations` and `messages` schema with role/content ordering and metadata.
- **Relation to Parent:** Implements core chat memory persistence.

#### P2.4 Create workflow run/event tables
- **Value:** Replaces Jaeger with first-party run telemetry.
- **Outcome:** `workflow_runs` and `workflow_events` tables for trace IDs, timings, usage, and stream events.
- **Relation to Parent:** Implements observability and auditability persistence.

#### P2.5 Add indexes and retention strategy
- **Value:** Keeps read performance acceptable at scale.
- **Outcome:** Indexes on conversation/order/model/trace fields and a documented retention policy for event rows.
- **Relation to Parent:** Hardens P2 schema for production-like workloads.

---

## Parent Task P3 - OpenAI-Compatible API Surface
- **Value:** Allows standard clients and tooling to call YAML-powered chat without custom protocol.
- **Outcome:** Fully implemented `/v1/models` and `/v1/chat/completions` contracts (streaming + non-streaming).
- **Relation to Parent:** Delivers mandatory compatibility objective from P0.

### P3 Sub-Tasks

#### P3.1 Implement `GET /v1/models`
- **Value:** Exposes discoverable model catalog for frontend and external clients.
- **Outcome:** OpenAI-style list response backed by active rows in `workflow_models`.
- **Relation to Parent:** First half of API compatibility.

#### P3.2 Implement non-stream `POST /v1/chat/completions`
- **Value:** Supports baseline synchronous chat requests.
- **Outcome:** OpenAI-compatible completion response with mapped assistant output and usage fields.
- **Relation to Parent:** Core request/response compatibility path.

#### P3.3 Implement stream `POST /v1/chat/completions` (SSE)
- **Value:** Enables token-like live UI response experience.
- **Outcome:** `chat.completion.chunk` SSE events and final `[DONE]` marker.
- **Relation to Parent:** Completes real-time compatibility requirements.

#### P3.4 Implement OpenAI-style error mapping
- **Value:** Makes failures predictable for clients.
- **Outcome:** Standardized error payloads (`model_not_found`, `invalid_request_error`, `workflow_execution_error`).
- **Relation to Parent:** Ensures compatibility quality beyond success path.

#### P3.5 Support conversation continuity header
- **Value:** Preserves thread state across calls without non-standard request shape changes.
- **Outcome:** `X-Conversation-Id` request/response support tied to persisted conversation rows.
- **Relation to Parent:** Adds stateful chat behavior while preserving OpenAI body format.

---

## Parent Task P4 - YAML Workflow Registry and Loading
- **Value:** Makes workflows editable by YAML changes, not code edits.
- **Outcome:** Dynamic workflow discovery, validation, and reload mechanism.
- **Relation to Parent:** Enables the product promise of customizable YAML-driven agents.

### P4 Sub-Tasks

#### P4.1 Implement filesystem YAML scanner
- **Value:** Automatically discovers candidate workflows.
- **Outcome:** Recursive scanner for configured directories returning workflow file inventory.
- **Relation to Parent:** Input source for registry population.

#### P4.2 Parse YAML metadata and IDs
- **Value:** Produces user-facing model identities and labels.
- **Outcome:** Extracted `id`, `version`, `metadata.name`, tags, and entry node information.
- **Relation to Parent:** Converts raw files into structured registry records.

#### P4.3 Map workflows to OpenAI model IDs
- **Value:** Creates stable selection handles for client requests.
- **Outcome:** Deterministic model ID generation (e.g., `yaml/<workflow-id>`).
- **Relation to Parent:** Bridges registry data to OpenAI API layer.

#### P4.4 Implement registry reload endpoint
- **Value:** Allows runtime refresh after YAML edits.
- **Outcome:** `POST /internal/workflows/reload` updates DB-backed model registry safely.
- **Relation to Parent:** Makes registry lifecycle operational.

#### P4.5 Add validation and conflict handling
- **Value:** Prevents silent misrouting and duplicate IDs.
- **Outcome:** Duplicate/invalid workflow reporting with explicit error logs and reload summary.
- **Relation to Parent:** Improves reliability of P4 operations.

---

## Parent Task P5 - Grouped Workflow Registries (Easy Starter)
- **Value:** Enables parent workflows to delegate to subgraphs without hardcoding integration in client UI.
- **Outcome:** Bundle models that include parent graph + registry map for subgraph tool resolution.
- **Relation to Parent:** Fulfills requirement to support grouped registries from initial release.

### P5 Sub-Tasks

#### P5.1 Define bundle model schema
- **Value:** Standardizes grouped workflow configuration.
- **Outcome:** `kind=workflow_bundle` record format with parent workflow and `registry` JSON key/path map.
- **Relation to Parent:** Data model for grouped registry support.

#### P5.2 Register starter orchestrator bundle
- **Value:** Delivers an immediately testable grouped example.
- **Outcome:** Bundle for `email-chat-orchestrator-with-subgraph-tool.yaml` + `hr-warning-email-subgraph.yaml`.
- **Relation to Parent:** First concrete implementation of grouped registry behavior.

#### P5.3 Inject registry into workflow runtime input
- **Value:** Enables parent node tool calls to resolve subgraph IDs.
- **Outcome:** Runtime path where bundle requests include `workflow_registry` map during execution.
- **Relation to Parent:** Functional execution mechanism for grouped bundles.

#### P5.4 Add grouped-registry validation
- **Value:** Prevents runtime failure from bad subgraph references.
- **Outcome:** Startup/reload checks that registry targets exist and are readable.
- **Relation to Parent:** Hardens grouped workflow operation.

#### P5.5 Add fallback behavior for missing subgraphs
- **Value:** Improves resilience and debuggability in partial config scenarios.
- **Outcome:** Clear, OpenAI-style runtime error with actionable message when subgraph lookup fails.
- **Relation to Parent:** Completes robustness for grouped registry feature.

---

## Parent Task P6 - Workflow Execution Service
- **Value:** Centralizes YAML execution logic and output normalization.
- **Outcome:** Service layer that runs workflows, supports stream/non-stream modes, and returns chat-safe assistant text.
- **Relation to Parent:** Converts API requests into runtime execution and response artifacts.

### P6 Sub-Tasks

#### P6.1 Build request-to-workflow input adapter
- **Value:** Ensures OpenAI messages can drive YAML workflows consistently.
- **Outcome:** Input adapter creates `messages` and helper fields such as last user text (for example workflows needing `email_text`).
- **Relation to Parent:** First transformation step before execution.

#### P6.2 Implement non-stream runner wrapper
- **Value:** Provides reliable blocking execution path.
- **Outcome:** Wrapper around `run_workflow_yaml` returning terminal output, trace, timings, and usage.
- **Relation to Parent:** Satisfies synchronous execution needs.

#### P6.3 Implement stream runner wrapper
- **Value:** Supports interactive UX and granular event handling.
- **Outcome:** Wrapper around streaming workflow API emitting normalized event envelopes.
- **Relation to Parent:** Satisfies real-time execution needs.

#### P6.4 Normalize terminal output to assistant content
- **Value:** Prevents UI coupling to workflow output schema variance.
- **Outcome:** Normalizer for strings, `{subject, body}` objects, and generic JSON outputs.
- **Relation to Parent:** Ensures consistent assistant message rendering.

#### P6.5 Capture execution metadata package
- **Value:** Enables observability and post-run analysis.
- **Outcome:** Unified metadata object containing trace IDs, node path, timings, and token fields.
- **Relation to Parent:** Feeds persistence and API metadata responses.

---

## Parent Task P7 - Persistence and Conversation State
- **Value:** Delivers durable multi-turn chat and reproducible run history.
- **Outcome:** End-to-end write/read pipeline for conversations, messages, runs, and optional events.
- **Relation to Parent:** Implements long-term state management for product usability.

### P7 Sub-Tasks

#### P7.1 Implement conversation resolver
- **Value:** Maintains stable thread identity across calls.
- **Outcome:** Resolver using `X-Conversation-Id` to find/create conversation row.
- **Relation to Parent:** Entry point for all stateful writes.

#### P7.2 Persist inbound and outbound chat messages
- **Value:** Preserves full conversation context and audit trail.
- **Outcome:** Message repository writes with deterministic `turn_index` ordering.
- **Relation to Parent:** Core chat-history persistence behavior.

#### P7.3 Persist workflow run records
- **Value:** Connects each assistant response to concrete workflow execution artifacts.
- **Outcome:** `workflow_runs` write path with status, outputs, trace, and usage.
- **Relation to Parent:** Links chat and execution telemetry.

#### P7.4 Persist streaming events (configurable)
- **Value:** Enables replay/debug while controlling storage growth.
- **Outcome:** Optional event persistence per run with sequence numbering.
- **Relation to Parent:** Completes state capture for streaming mode.

#### P7.5 Add retrieval query helpers
- **Value:** Speeds up UI load and internal diagnostics.
- **Outcome:** Read APIs/helpers for conversation timeline and recent run summaries.
- **Relation to Parent:** Provides practical access to stored state.

---

## Parent Task P8 - Frontend Architecture and Data Layer (Vue)
- **Value:** Creates maintainable client structure for rapid UI iteration.
- **Outcome:** Vue application with stores, API client, routing, and reusable components.
- **Relation to Parent:** Builds the frontend foundation required for design implementation.

### P8 Sub-Tasks

#### P8.1 Initialize Vue app with TS + Pinia + Router
- **Value:** Provides scalable app architecture.
- **Outcome:** Project scaffolding with state and route conventions in place.
- **Relation to Parent:** Base framework for all frontend tasks.

#### P8.2 Implement OpenAI API client adapter
- **Value:** Encapsulates protocol details and error handling.
- **Outcome:** Typed client methods for `/v1/models` and `/v1/chat/completions` (stream + non-stream).
- **Relation to Parent:** Data transport layer connecting frontend to backend.

#### P8.3 Implement chat store/state model
- **Value:** Keeps UI deterministic and testable.
- **Outcome:** Store for current model, conversation ID, messages, stream state, and theme.
- **Relation to Parent:** Core client-side state for chat UX.

#### P8.4 Implement message rendering primitives
- **Value:** Promotes consistent rendering and easier theming.
- **Outcome:** Components for user prompt cards, assistant response cards, follow-up list, and metadata chips.
- **Relation to Parent:** Foundational UI component layer.

#### P8.5 Implement streaming update flow
- **Value:** Enables live incremental text rendering.
- **Outcome:** SSE consumer merges streamed chunks into in-progress assistant message.
- **Relation to Parent:** Completes real-time behavior in frontend data layer.

---

## Parent Task P9 - Desktop UI Fidelity (Dark and Light Themes)
- **Value:** Delivers a premium, intentional UI aligned with provided design reference.
- **Outcome:** Desktop-first chat interface matching Pencil dark/light preview structure and style tokens.
- **Relation to Parent:** Implements visual/product requirements from user-provided design system.

### P9 Sub-Tasks

#### P9.1 Define design tokens from `.pen` frames
- **Value:** Guarantees color/typography consistency across components.
- **Outcome:** CSS variables for dark/light palettes, spacing, radii, and border styles.
- **Relation to Parent:** Theme foundation for all visual implementation.

#### P9.2 Build sidebar and workspace chrome
- **Value:** Recreates navigation identity and layout hierarchy.
- **Outcome:** Sidebar with brand/nav/avatar and top-bar controls matching desktop preview patterns.
- **Relation to Parent:** Implements structural shell of the desktop UI.

#### P9.3 Build thread meta and conversation feed cards
- **Value:** Matches visual communication patterns from the design.
- **Outcome:** Thread chips, prompt card, assistant cards, follow-up card with correct spacing and border language.
- **Relation to Parent:** Implements core content area fidelity.

#### P9.4 Build composer and interaction states
- **Value:** Completes primary user action area.
- **Outcome:** Themed composer with placeholder, focus, disabled, and streaming-locked states.
- **Relation to Parent:** Final required UI element for complete desktop chat flow.

#### P9.5 Implement theme toggle and persistence
- **Value:** Enables practical use of both provided themes.
- **Outcome:** Runtime dark/light switch and local preference persistence.
- **Relation to Parent:** Activates full dual-theme requirement in P9.

---

## Parent Task P10 - Responsive Behavior (Desktop-First)
- **Value:** Keeps the desktop design usable on smaller screens before dedicated mobile design phase.
- **Outcome:** Fluid breakpoints and adaptive layout that remain functional on tablet/small-laptop widths.
- **Relation to Parent:** Satisfies requirement: desktop first, mobile later, but responsive now.

### P10 Sub-Tasks

#### P10.1 Define breakpoint strategy
- **Value:** Prevents ad-hoc responsiveness and visual regressions.
- **Outcome:** Breakpoint map for wide desktop, laptop, tablet, narrow tablet.
- **Relation to Parent:** Planning baseline for all responsive styles.

#### P10.2 Make sidebar adaptive
- **Value:** Preserves main chat readability as viewport narrows.
- **Outcome:** Collapsible or compact sidebar behavior with maintained navigation access.
- **Relation to Parent:** Critical layout adaptation for smaller widths.

#### P10.3 Make message cards and chips fluid
- **Value:** Avoids overflow and clipping across widths.
- **Outcome:** Dynamic width/typography adjustments and wrapping for chips, cards, and long content.
- **Relation to Parent:** Content-area responsiveness implementation.

#### P10.4 Ensure composer remains usable at narrow widths
- **Value:** Protects primary interaction on constrained viewports.
- **Outcome:** Responsive composer sizing and controls that do not obstruct message feed.
- **Relation to Parent:** Keeps core chat input functional in all supported widths.

#### P10.5 Document mobile-phase deferral boundaries
- **Value:** Clarifies what is intentionally postponed.
- **Outcome:** Written note on what “responsive desktop-first” includes vs future dedicated mobile UI work.
- **Relation to Parent:** Scope clarity and expectation management.

---

## Parent Task P11 - Internal Operations and Admin APIs
- **Value:** Improves operability during rapid YAML iteration.
- **Outcome:** Internal endpoints for health, workflow inventory, and registry reload diagnostics.
- **Relation to Parent:** Enables maintainable day-2 operations.

### P11 Sub-Tasks

#### P11.1 Implement `GET /health`
- **Value:** Fast liveness/readiness verification.
- **Outcome:** Health response including DB status and registry load status.
- **Relation to Parent:** Baseline operational endpoint.

#### P11.2 Implement `GET /internal/workflows`
- **Value:** Makes model/workflow mapping transparent.
- **Outcome:** Inventory endpoint with workflow models, bundle metadata, and active status.
- **Relation to Parent:** Visibility tool for debugging and product ops.

#### P11.3 Implement `POST /internal/workflows/reload`
- **Value:** Enables no-redeploy YAML update workflows.
- **Outcome:** Reload endpoint returning added/updated/disabled model counts and validation warnings.
- **Relation to Parent:** Operational control path for registry lifecycle.

#### P11.4 Add conversation inspection endpoint
- **Value:** Speeds support/debug loops.
- **Outcome:** Endpoint returning conversation transcript and associated run summaries.
- **Relation to Parent:** Completes practical introspection tooling.

#### P11.5 Add structured logging with correlation IDs
- **Value:** Improves traceability in logs without external tracing system.
- **Outcome:** Log context includes request ID, conversation ID, trace ID, model ID.
- **Relation to Parent:** Operational observability backbone.

---

## Parent Task P12 - Testing, QA, and Contract Validation
- **Value:** Prevents integration regressions and contract drift.
- **Outcome:** Automated tests covering API contract, workflow execution, persistence, and UI behavior.
- **Relation to Parent:** Ensures quality and confidence before release.

### P12 Sub-Tasks

#### P12.1 Add backend unit tests
- **Value:** Verifies critical service logic quickly.
- **Outcome:** Tests for model resolution, input adaptation, output normalization, and error mapping.
- **Relation to Parent:** Core correctness validation.

#### P12.2 Add backend integration tests
- **Value:** Confirms endpoint and DB behavior under realistic flows.
- **Outcome:** Tests for `/v1/models` and `/v1/chat/completions` (stream + non-stream) with seeded workflow models.
- **Relation to Parent:** End-to-end API contract verification.

#### P12.3 Add frontend component/store tests
- **Value:** Protects key UX behavior and stream rendering logic.
- **Outcome:** Tests for message rendering, theme switching, SSE chunk merge behavior, and error states.
- **Relation to Parent:** UI logic reliability.

#### P12.4 Add manual QA checklist
- **Value:** Captures visual and functional requirements not fully automated.
- **Outcome:** Checklist for dark/light fidelity, responsiveness, and grouped registry routing.
- **Relation to Parent:** Human validation layer complementing automated tests.

#### P12.5 Add sample smoke scripts
- **Value:** Provides quick confidence checks for developers.
- **Outcome:** Command set to start services, query models, send chat, and verify persistence rows.
- **Relation to Parent:** Practical verification workflow for daily development.

---

## Parent Task P13 - Documentation and Developer Experience
- **Value:** Reduces onboarding time and operational confusion.
- **Outcome:** Clear docs for setup, architecture, API usage, YAML onboarding, and troubleshooting.
- **Relation to Parent:** Makes the platform maintainable and usable by others.

### P13 Sub-Tasks

#### P13.1 Write project README
- **Value:** Single source of truth for getting started.
- **Outcome:** Root-level instructions for prerequisites, env setup, and running frontend/backend.
- **Relation to Parent:** Entry documentation for P13.

#### P13.2 Document OpenAI-compatible API usage
- **Value:** Speeds external integration.
- **Outcome:** cURL/examples for `/v1/models` and `/v1/chat/completions` (stream and non-stream).
- **Relation to Parent:** API-focused documentation deliverable.

#### P13.3 Document workflow model/bundle configuration
- **Value:** Enables users to add/edit workflows safely.
- **Outcome:** Guide covering single workflow models, grouped bundles, and registry key conventions.
- **Relation to Parent:** YAML customization documentation deliverable.

#### P13.4 Document persistence and telemetry model
- **Value:** Clarifies what data is stored and why.
- **Outcome:** Schema overview and explanation of run/event/trace storage without Jaeger.
- **Relation to Parent:** Data model documentation deliverable.

#### P13.5 Document known limitations and roadmap
- **Value:** Aligns expectations and future work.
- **Outcome:** Explicit note: desktop-first responsive now, dedicated mobile implementation later.
- **Relation to Parent:** Scope transparency and future planning.

---

## Parent Task P14 - Release and Deployment Readiness
- **Value:** Makes the project runnable beyond local machine assumptions.
- **Outcome:** Deployment-ready service configs, checks, and basic hardening.
- **Relation to Parent:** Transitions P0 from development artifact to releasable system.

### P14 Sub-Tasks

#### P14.1 Build production config profiles
- **Value:** Separates dev and production behaviors safely.
- **Outcome:** Environment-based settings for logging, CORS, database pools, and debug flags.
- **Relation to Parent:** Configuration hardening for release.

#### P14.2 Add CI checks
- **Value:** Prevents regressions reaching shared branches.
- **Outcome:** CI pipeline for lint, type checks, tests, and migration consistency.
- **Relation to Parent:** Automated quality gate for release readiness.

#### P14.3 Add startup/runbook scripts
- **Value:** Standardizes operations for local/staging bring-up.
- **Outcome:** Scripted commands for migrations, service startup, and initial workflow seed.
- **Relation to Parent:** Repeatable deployment operationalization.

#### P14.4 Validate resource and timeout defaults
- **Value:** Reduces runtime failures and hanging requests.
- **Outcome:** Tuned request timeout, stream keepalive, DB pool, and retry defaults.
- **Relation to Parent:** Runtime stability hardening.

#### P14.5 Release checklist
- **Value:** Ensures no critical step is skipped before handoff.
- **Outcome:** Final checklist covering API contract validation, UI parity checks, and rollback notes.
- **Relation to Parent:** Completion gate for P14.

---

## Dependency Map (High-Level)
- **Value:** Clarifies execution order and unblock paths.
- **Outcome:** Suggested order: `P1 -> P2 -> (P3 + P4) -> P5 -> P6 -> P7 -> (P8 + P9 + P10) -> P11 -> P12 -> P13 -> P14`.
- **Relation to Parent:** Connects all parent tasks into one coherent delivery sequence for P0.

## Initial Milestone Cut (MVP)
- **Value:** Enables fast first shippable increment.
- **Outcome:** MVP includes P1-P7 plus core parts of P8/P9 and minimal P12/P13.
- **Relation to Parent:** Produces a usable first release while preserving roadmap depth.
