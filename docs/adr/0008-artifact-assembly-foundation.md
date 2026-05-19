# ADR 0008: Artifact Assembly Foundation

Status: accepted  
Date: 2026-05-19

## Context

Ariadne needs to turn capture knowledge, public data, research findings, action plans, and capability outputs into useful deliverables without making final renderers, freeform AI prose, or exported files the source of truth. The obvious shortcut would be to ask an AI model to generate documents or to start with DOCX, XLSX, presentation, or visual rendering integrations, but that would make artifact quality hard to review, trace, reuse, or render consistently across formats.

## Decision

Ariadne will build artifact capability through an **Artifact Assembly Foundation** before final rendering or export workflows. Artifact assembly starts from an explicit **Artifact Source Package**, captures AI-assisted or deterministic output in section-based **Artifact Drafts**, and represents content as typed **Artifact Content Blocks** with source refs, assumptions, gaps, review state, readiness metadata, and autonomy hints. **Artifact Block Review** happens at the block level, while accepted blocks become reviewed artifact content for preview or export rather than automatically becoming trusted Evidence, Packet, Action Plan, Risk Register, Call Plan, or Reusable Capture Insight records.

The first tracer will assemble a reviewable **Milestone Decision Briefing Packet** draft. Renderers, DOCX/XLSX/presentation export, huashu-design, Bidder Comparison Chart artifacts, and polished visual deliverables remain downstream adapters that consume reviewed artifact content rather than owning artifact truth.

## Consequences

- Ariadne can use AI or LLMs for coordination, synthesis, prioritization, and prose while preserving a deterministic, source-backed, reviewable schema.
- Future renderers can target one reviewed artifact structure instead of reverse-engineering freeform model output.
- Artifact drafts can draw from knowledge, data, research, actions, and capability outputs without copying those stores or becoming a second source of truth.
- Low-risk transactional block decisions can later become Graduated Autonomy candidates, but this decision does not permit auto-accept, auto-promote, or auto-export behavior.
