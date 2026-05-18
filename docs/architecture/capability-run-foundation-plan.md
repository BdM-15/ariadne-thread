# Capability Run Foundation Plan

Date: 2026-05-18  
Status: completed on `06-build/capability-run-foundation`; ready for next-epic planning

## Selected Epic

Build the **Capability Run Foundation + Assisted Execution Command Surface** vertical slice after the completed SAM.gov Enrichment Profile epic.

Suggested epic branch: `06-build/capability-run-foundation`.

Suggested progression branches:

- `06-build/01-capability-run-domain-store`
- `06-build/02-capability-catalog-validation-run`
- `06-build/03-local-admin-model-probe-run`
- `06-build/04-capability-run-review-decisions`
- `06-build/05-capability-studio-command-surface`

The slice should create durable Capability Run and Capability Run Output records before adding new external integrations, autonomous agent runtimes, or third-party capability installation.

## Product Thesis

Ariadne now has a local Capability Catalog and multiple product workflows that produce review-gated candidates, but it does not yet have a durable record for what happened when a capability ran. Without that record, future Hermes learning, CLI harness execution, skill-chain tracing, model rationale, MCP diagnostics, artifact generation, and source-grounded reasoning would scatter across product workflows.

The next slice should make one execution unit visible and reviewable: what capability ran, why it ran, what inputs it used, what outputs it produced, what evidence or assumptions grounded it, what gaps remain, and what the user decided next.

## Decisions Resolved

- Build **Capability Run Foundation + Assisted Execution Command Surface** as the next vertical epic.
- Do not adopt Microsoft Agent Framework now. Treat it only as a candidate future Hermes or multi-agent workflow runtime adapter.
- Use **Capability Run** for one execution of a Capability Module and **Capability Run Output** for reviewable outputs from that execution.
- Use a separate local-first **Capability Run Store**, likely under `.ariadne/capability-runs`, instead of storing runs in the Capability Catalog or Evidence Store.
- Keep the **Capability Catalog** responsible for what can run, the **Capability Run Store** responsible for what happened when something ran, and the **Evidence Store** responsible for trusted source/support records.
- Use **Capability Provenance** and **Capability Reasoning View** as Ariadne-native tracing concepts inspired by Project Theseus source tracing, skill-run chain tracing, and reasoning views.
- Preserve model-assisted reasoning as **Model Rationale Summaries**: user-facing evidence, assumptions, logic, alternatives, uncertainty, gaps, and review needs. Do not require durable storage of raw hidden model reasoning.
- Treat CLI-Anything as one executor style for repeatable, batchable, tool-facing, or agent-facing workflows with deterministic JSON output, not as the whole product workflow.
- The first required tracer bullet is deterministic **Capability Catalog validation** and must work without Ollama, hosted models, external APIs, Hermes, Agent Framework, LangGraph, or third-party installation.
- A second optional tracer can run **Local Admin Model readiness/probe** through existing `OLLAMA_HOST`, `LOCAL_DAILY_MODEL`, and `LOCAL_ADMIN_MODEL_TIMEOUT_SECONDS` settings.
- Ollama availability must not be required for the epic. The optional probe should record `used`, `unavailable`, or `invalid_response` style outcomes as Capability Run provenance.
- Capability Run Outputs in the first epic land in review only. They may recommend downstream destinations but must not automatically create trusted Evidence Items, Packet Field Answers, Action Plan Items, Risk Register Items, Call Plan signals, Opportunity Knowledge, reusable insights, or final artifacts.
- First-epic outputs may carry autonomy recommendation metadata such as `review_required`, `ask_before_running`, or `safe_to_auto_handle_later`, but Ariadne should not act on it automatically.
- Later **Graduated Autonomy** can move selected low-risk outputs toward automatic handling only after reliability, provenance quality, reversibility, sensitivity limits, and user-approved autonomy rules are proven.
- Hermes may recommend Graduated Autonomy changes through Improvement Proposals, but it must not silently expand its own permissions.
- Place the first detailed UI in **Capability Studio**, with lightweight Command Center entries for launching runs and reviewing outputs.
- Record these decisions in this architecture plan rather than a new ADR because the slice follows existing local-first, Capability Module, and review-gated-promotion architecture. Create an ADR only if a later decision adopts a runtime framework, changes the storage engine, enables automatic trusted writes, or makes a graph/workflow engine the Capability Run runtime.

## First Capability Run Record Shape

The first durable record should stay small but future-ready:

- `run_id`
- `capability_id`
- `capability_type`: skill, cli_harness, mcp_tool, parser, renderer, model_workflow, adapter, or manual_record
- `executor_kind`: deterministic_python, cli_anything, local_admin_model, mcp, hosted_model, or future_agent_runtime
- `session_context`: product, studio, or exploratory
- optional `opportunity_id`
- `product_workflow`: capability_catalog, quick_capture, document_intake, packet, action_plan, risk_register, call_plan, or related workflow key
- `status`: planned, running, succeeded, failed, unavailable, canceled, or needs_review
- `inputs_summary`
- `input_refs`: evidence IDs, draft part IDs, document intake IDs, profile IDs, packet field IDs, or other Ariadne refs
- one or more `CapabilityRunOutput` records
- provenance: sources, prompts/tool names, versions, model name when used, command/harness name when used, timestamps, assumptions, transformations, gaps, and review decisions
- review state: pending, accepted, refined, discarded, routed, or promoted
- `created_at` and optional `completed_at`

Store summaries, stable refs, and safe provenance by default. Do not store raw secrets, full sensitive prompts, or giant blobs inside the first Capability Run record. Private source material should remain behind existing source refs whenever possible.

## First Tracer Bullets

### Required: Capability Catalog Validation Run

The required tracer should inspect installed local Capability Catalog entries and produce a deterministic validation report. Useful first checks include local skill metadata presence, required frontmatter, source path, capability type, maturity, validation status, related workflow metadata when available, and gaps or warnings.

The run should produce reviewable Capability Run Outputs with provenance and autonomy recommendation metadata. It should not require network access, private secrets, Ollama, hosted models, or third-party executors.

### Optional: Local Admin Model Readiness/Probe Run

The optional tracer should use the existing Local Admin Model configuration to test whether Ollama and `LOCAL_DAILY_MODEL` are usable for low-risk local admin support. It should record model name, base URL, timeout setting, status, response-shape validation, and source-mode/provenance metadata.

If Ollama is unavailable, slow, missing the configured model, or returns invalid JSON, the run should complete with an unavailable or invalid-response output rather than failing the epic.

## Review-Gated Candidate Destinations

Capability Run Outputs may recommend or prepare candidates for:

- Evidence Item candidate
- Packet Field Answer candidate
- Action Plan Item candidate
- Risk Register Item candidate
- Call Plan signal
- Follow-Up Question Route
- Improvement Proposal
- Artifact draft placeholder

None of these should become trusted downstream records without explicit user review or promotion in this epic.

## Capability Reasoning View

The first Capability Reasoning View should explain why a run output exists without making toolchain details the default capture workflow. It should show:

- source refs and evidence links
- executor kind and capability identity
- input summary and relevant input refs
- prompt/tool/command names where safe
- model name and status when a model is used
- assumptions and confidence notes
- transformations or validation logic applied
- gaps and limitations
- recommended destination and autonomy metadata
- review decision history

This view is Theseus-inspired but Ariadne-native. It should not copy Theseus UI, runtime assumptions, or raw hidden model reasoning behavior.

## Command Surface Expectations

Capability Studio should show the durable machinery:

- local Capability Catalog validation action
- run history
- run detail
- output review state
- Capability Provenance
- Capability Reasoning View
- deterministic validation findings
- optional Local Admin Model readiness/probe output

The main Command Center should stay outcome/action-first:

- show a lightweight action to run local capability validation
- show Capability Run Outputs needing review
- let the user jump to the relevant Capability Studio detail or review surface with minimal clicks
- avoid making capability management equal-weight with day-to-day capture workflows

## Explicitly Deferred

- Microsoft Agent Framework integration.
- Hermes runtime, autonomous tool choice, workflow mutation, or persistent memory.
- LangGraph orchestration or complex skill-chain execution.
- Third-party capability installation from GitHub, skills.sh, or external catalogs.
- Firecrawl, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, Regulations.gov, or other new external API product workflows.
- Project Theseus solicitation parser integration.
- MinerU, RAGAnything, LightRAG, OCR, multimodal extraction, or full Knowledge Layer adapter work.
- Artifact Renderer, DOCX, XLSX, presentation, huashu-design, or final export workflows.
- Automatic trusted downstream writes from Capability Run Outputs.
- Full Next.js UI migration.

## Acceptance Demo

The acceptance demo should show:

1. The Command Center surfaces a Capability Catalog validation action.
2. The user launches the validation action.
3. Ariadne creates a Capability Run in the Capability Run Store.
4. Deterministic local validation inspects local Capability Catalog entries.
5. Ariadne creates Capability Run Outputs with provenance, gaps, review state, and autonomy recommendation metadata.
6. Capability Studio shows run history, run detail, and a Capability Reasoning View.
7. The Command Center surfaces outputs needing review.
8. The user accepts, discards, or routes one output.
9. No trusted Evidence Item, Packet Field Answer, Action Plan Item, Risk Register Item, Call Plan signal, Opportunity Knowledge, reusable insight, or final artifact is created automatically.
10. If included, the optional Ollama probe records local model readiness or unavailability without making Ollama required.

## Implementation Trail

- #40 Persist a Capability Catalog Validation Run: added the local Capability Run Store, deterministic Capability Catalog validation runs, reviewable outputs, provenance, autonomy metadata, and API list/detail/launch surfaces.
- #41 Review Capability Run Outputs Without Trusted Writes: added output review decisions for accept, discard, and route, persisted review history, invalid transition handling, and no automatic trusted Evidence, Packet, Action Plan, Risk Register, Call Plan, Opportunity Knowledge, reusable insight, or artifact writes.
- #42 Show Capability Studio Run History and Reasoning View: added Capability Studio run history/detail pages, Capability Reasoning View, Capability Provenance display, validation findings, gaps, autonomy metadata, review history, and empty/failed/unavailable/needs-review states. User reviewed the first UI shape as good enough for this stage.
- #43 Add Optional Local Admin Model Readiness Probe: added optional Local Admin Model readiness runs through existing Ollama/local-admin settings, recording `used`, `unavailable`, `invalid_response`, and `disabled` outcomes without requiring live Ollama.
- #44 Add Command Center Launch and Review Entry Points: added Command Center launch action, review-needed Capability Run Output rows, and jump links into Capability Studio detail/review context. User reviewed the first UI shape as good enough for this stage.

Validated with `uv run ruff check src tests` and `uv run pytest -q` on the epic branch; full suite passed with 209 tests.

## Accepted Implementation Order

1. Add the Capability Run domain model and local Capability Run Store.
2. Add deterministic Capability Catalog validation run behavior.
3. Add optional Local Admin Model readiness/probe run behavior.
4. Add review decisions for Capability Run Outputs.
5. Add Capability Studio run history/detail/Capability Reasoning View and lightweight Command Center entries.
6. Add tests and update PRD/current-state docs after the implemented slice is validated. Completed after #44 review.
