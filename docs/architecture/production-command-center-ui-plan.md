# Production Command Center UI/UX Plan

Date: 2026-05-19  
Status: planning baseline for MVP-1 through MVP-4

## Purpose

Make Ariadne's UI/UX a real capture command and management workspace, not another scaffold or passive dashboard. The production Command Center should let one capture professional see the state of an Opportunity, understand what matters next, approve AI/capability work, review outputs, route results, and improve the Living Milestone Decision Briefing Packet, call/engagement prep, actions, risks, evidence, and artifacts without tool sprawl.

## Readiness Judgment

Ariadne is ready to plan and start the production UI skeleton, but not ready for final visual polish or a full frontend migration detached from workflow proof.

The next UI work should start in MVP-1 as a production-shaped Next.js shell around the assisted capture loop. MVP-4 should then harden and complete that UI after route-first orchestration, AI/skills integration, and work-product routing prove the interaction model.

## Research Inputs

### Project Theseus Lessons

Project Theseus is a final-solicitation Capture Workbench. Useful patterns to adapt:

- **Capture Chat with Shipley mentor**: use as inspiration for a goal-scoped mentor panel, not as a generic chat-first UI.
- **Intel Panels**: adapt into packet/workstream panels that expose actionable slices such as gaps, risks, customer signals, evidence, call-plan needs, and artifact blockers.
- **Document drawer**: adapt into source and provenance drawers that keep evidence close without dominating the workspace.
- **Knowledge graph viewer**: defer as central UI; use relationship previews and source chips now, full graph later.
- **Studio artifact library**: adapt into a read-only output/provenance drawer with preview, download, origin run, and "why this output?" inspection.
- **Skill/MCP integration**: adapt the idea that skills are runtime capabilities, but keep Ariadne routes product-led rather than toolchain-led.
- **Trace chain**: preserve the artifact -> run -> source/chunk/evidence chain in two or three clicks.

Do not copy Theseus wholesale. Theseus focuses on final RFP ingestion and proposal intelligence. Ariadne focuses on active capture management before, during, and after opportunity pursuit.

### Web UX Pattern Lessons

- Dashboard quality comes from information architecture, not many charts.
- Command centers need structured decision loops: signal, severity, owner, action, status, feedback.
- Enterprise SaaS UI should reduce cognitive load through grouping, stable layout, readable lists, and clear conflict/exception indicators.
- AI-native UX must show uncertainty, provenance, review state, and user feedback loops.
- Human-in-the-loop systems need risk-tiered review, durable interrupt/resume, confidence/routing thresholds, and closed feedback loops.
- Complex systems need role/task mapping. Ariadne has one main user, but that user switches modes: scout, analyst, capture lead, reviewer, artifact owner, and mentor/operator.

## Product Design Thesis

The Command Center should be an **operating cockpit**, not a reporting dashboard.

Default screen should answer:

1. What is the state of this Opportunity?
2. Where does this Opportunity sit in my broader portfolio?
3. Which Living Packet fields are answered, weak, stale, or missing?
4. What can Ariadne do now for each important gap?
5. What needs my review?
6. What work product changed?
7. What evidence or vault knowledge supports it?

## Primary Workspace Shape

### Desktop Layout

- **Left rail: Opportunity and work mode navigation**
  - Opportunity switcher.
  - Portfolio states: active, future/watchlist, held, archived, won, lost.
  - Lifecycle/gate state.
  - Work modes: Packet, Actions, Engagement, Research, Documents, Artifacts, Capability Studio.
  - Knowledge Vault entry.
  - Badges for review needs and blockers.

- **Center: Living Milestone Decision Briefing Packet workspace**
  - Packet readiness header.
  - Section navigation using Canonical Packet Section Model.
  - Packet Field Action Matrix with compact answer/gap/risk/recommendation blocks.
  - Field-level answer status, evidence status, answer paths, recommended routes, and action menu.
  - Evidence status, confidence, assumptions, gaps, and source chips.
  - Inline "improve this" actions routed through Capability Modules.

- **Right rail: Command and review rail**
  - Assisted capture goal selector.
  - Next route recommendations.
  - Active runs and queued work.
  - Review queue grouped by destination: Evidence, Packet, Actions, Call Plan, Risk, Artifact.
  - Approval controls for external calls, broad research, final export, and sensitive actions.

- **Bottom or drawer layer: Provenance and output inspection**
  - Source drawer.
  - Capability run reasoning view.
  - Artifact/output preview.
  - "Why this output?" trace.

### Mobile/Small Screen Layout

Mobile is secondary but should not break. Use top opportunity header, segmented work modes, bottom action bar, and drawers for provenance/review. Do not attempt dense command-center parity on small screens.

## Core Interaction Loops

### 1. Assisted Capture Start

User chooses goal:

- Prepare milestone/gate review.
- Improve Living MS Briefing Packet.
- Prepare customer call/engagement.
- Resolve evidence gaps.
- Research customer/competitor/teaming/pricing issue.
- Process documents.
- Prepare artifact/export.

Ariadne returns:

- top needs.
- recommended routes.
- required approvals.
- expected work-product updates.

### 2. Route Recommendation

Each route card should show:

- need: what problem this solves.
- route: Product Workflow and Capability Module or skill chain.
- input refs: context, evidence, source profile, draft part, document span, or packet field.
- output destination: packet, call plan, action, evidence, risk, artifact, research.
- risk/autonomy tier.
- approval requirement.
- expected time/cost if known.

Primary actions: run, inspect inputs, edit route, defer, discard.

### 3. Capability Run And Skill Chain

Show a visible staged chain:

1. Prepare inputs.
2. Run capability or skill.
3. Summarize output.
4. Review output.
5. Route accepted result.

Never hide the chain behind a magical "AI did stuff" state. AI can do more work, but the user should know what is running and where output will land.

### 4. Review And Routing

Review cards should be destination-first:

- Evidence candidate.
- Packet update.
- Action item.
- Call/engagement prep.
- Risk signal.
- Artifact block.
- Follow-up route.

Each card needs: summary, source support, assumptions, gaps, confidence, model/capability provenance, destination, and actions: accept, edit, route, defer, discard, needs evidence.

### 5. Work Product Update

After review, UI should show what changed:

- packet field updated.
- readiness improved or still blocked.
- action created.
- call-plan prep improved.
- artifact draft refreshed.
- export readiness changed.

Use visible "before -> after" for important updates.

## Production UI Information Architecture

Top-level product areas:

1. **Command Center**: day-to-day workspace and assisted capture loop.
2. **Opportunity Portfolio**: multiple Opportunities across active, future/watchlist, held, archived, won, and lost states.
3. **Opportunity Workspace**: one Opportunity, centered on Living MS Briefing Packet.
4. **Knowledge Vault**: browsable/searchable accepted knowledge, source material, packet answers, source profiles, capability outputs, reusable insights, and projections.
5. **Action Plan**: outcome tasks, urgency, timelines, ownership, AI support.
6. **Engagement**: call plans, customer meetings, stakeholder prep, follow-up commitments.
7. **Research**: capture research briefs, findings, source collection, lenses, candidates.
8. **Documents**: intake queue, extraction bundles, source spans, parser-required items.
9. **Artifacts**: drafts, renderer readiness, DOCX, XLSX, huashu-design outputs.
10. **Capability Studio**: advanced inventory, runs, artifacts, provenance, validation.

Default landing should be Command Center, not a marketing page or static dashboard.

## Design System Direction

- Dark, calm, cyberpunk-leaning command aesthetic: deep black/blue surfaces, cyan/magenta accents, restrained glow.
- Dense but scannable. Avoid decorative card overload.
- Use semantic color: blocked, needs review, trusted, running, ready, risk.
- Use icons for repeated actions, with tooltips.
- Stable dimensions for packet sections, route cards, review cards, run states, and output previews.
- No nested cards inside cards.
- No giant hero sections.
- No passive metric wall.
- No text walls where a structured action surface is needed.

## Anti-Convoluted Rules

- One primary next action per panel.
- Product workflows first, tools second.
- Show only actionable status by default; details in drawers.
- Every surfaced item must answer "so what?" or "what can I do?"
- Do not create separate pages for every store unless user workflow needs it.
- Do not make chat the only way to act.
- Do not make graph/RAG/artifact/studio views compete with the packet as center of gravity.
- Do not build a new UI surface unless it changes user decisions or work products.

## MVP UI Sequencing

### MVP-1 UI Skeleton + First Route Action

Build production-shaped Next.js shell while route-first orchestration starts:

- Opportunity workspace layout.
- Living MS Briefing Packet center panel.
- route recommendations rail.
- review/action rail.
- active capability run drawer.
- source/provenance drawer.
- first working route action: selected goal -> route recommendation -> run/review -> route accepted output into packet/action/call-plan destination.

FastAPI shell remains fallback only. New user-facing workflow screens should not keep accumulating there.

Resolved decision: MVP-1 should not be shell-only. It must prove at least one route action inside the production-shaped Next.js UI, with deterministic/demo data acceptable only as a temporary backend stand-in.

### MVP-1B Packet Field + Portfolio UI

- Opportunity Portfolio list and switcher for active, future/watchlist, held, archived, won, and lost Opportunities.
- selected Opportunity summary with lifecycle state, packet readiness, source freshness, review count, and next-action urgency.
- Living Packet rendered as required packet fields, not only section aggregates.
- field-level action surfaces showing answer status, answer paths, source support, gaps, confidence, recommended route, and action menu.
- field routes for accepted evidence/source-backed answer, research or MCP-backed answer candidate, and customer-call-plan recommendation when Ariadne cannot safely answer from data.
- review-gated field update flow into Packet Field Answers.

### MVP-1C Knowledge Vault UI

- Knowledge Vault browse/search surface scoped by Opportunity, entity, source type, trust state, freshness, and source-of-truth/projection authority.
- source/provenance drawer shared with packet fields, route outputs, and artifact drafts.
- "use as context" action from vault records into packet-field route, call-plan route, research brief, action recommendation, or artifact draft.
- reusable insight proposal and review state, keeping cross-opportunity reuse separate from opportunity-specific answers.

### MVP-2 AI/Skills UI

- Capability route cards.
- skill-chain stage view.
- model role display.
- approval prompts.
- run progress states.
- output summary and provenance.
- MCP/source-provider readiness and approval state.

### MVP-3 Work Product UI

- packet update review.
- call/engagement prep surface.
- action-plan update flow.
- risk/follow-up routing.
- work-product before/after state.

### MVP-4 Production UI Hardening

- responsive production polish.
- accessibility pass.
- keyboard navigation.
- empty/loading/error states.
- user review over first real UI shape.
- visual consistency and component library cleanup.

### MVP-5 Renderer UI

- reviewed draft preview.
- DOCX export action and status.
- XLSX export action and status.
- huashu-design visual/PPTX-capable action and status.
- Artifact Export Profile selection for private/local mappings.

## Validation Criteria

Production UI is good enough for MVP only when user can:

- open one Opportunity.
- switch among multiple Opportunities in active, future/watchlist, and past/archive states.
- understand readiness in 30 seconds.
- see which required packet fields are answered, weak, stale, or missing.
- start a field-level route from a packet data element.
- start assisted capture in one click.
- approve/run a route without hunting through tools.
- review output with evidence/provenance visible.
- route result into packet/action/call/artifact work.
- browse the Knowledge Vault and use a selected record as route context.
- see work-product change.
- export DOCX, XLSX, and first huashu-design output from reviewed content.
- recover from errors without losing context.

## Open Questions

1. Which artifact should huashu-design produce first: packet visual/PPTX output, engagement artifact, or executive gate-review visual?
2. Which packet fields should be mandatory in the first Packet Field Action Matrix demo?
3. Which portfolio states should be editable in the first UI slice versus read-only/system-derived?
4. Should Capability Studio stay fully separate, or appear as an advanced drawer inside Command Center for the single-user developer workflow?
