# ADR 0007: Upstream Federal Data MCPs

Status: accepted  
Date: 2026-05-16

## Context

Ariadne needs public federal contracting data for recompete-first capture work: incumbent history, award values, customers, vehicles, spending patterns, wage and rate context, policy changes, and regulatory signals. The 1102tools federal contracting ecosystem already provides hardened MCP servers for these data sources, while its companion skill repository keeps deliverable orchestration separate from deterministic API access.

Writing Ariadne-specific MCP servers or one-off direct API clients would duplicate battle-tested upstream work and risk scattering data access logic through product workflows. At the same time, Ariadne still needs its own command-and-control layer so public data becomes traceable capture intelligence only through review, provenance, and promotion gates.

## Decision

Ariadne will integrate upstream `1102tools/federal-contracting-mcps` servers as external read-only Federal Data Capabilities instead of creating unique Ariadne MCP servers for the same public data sources.

The initial integration direction is to make the eight upstream MCPs available as pinned capability declarations, while building deep Ariadne product behavior one MCP at a time. The first deep product slice will focus on USAspending because recompete capture depends heavily on award history, incumbents, customer buying behavior, vehicles, obligations, and timing signals.

The companion `1102tools/federal-contracting-skills` repository remains the source for acquisition deliverable skills. Ariadne should use those skills as capability modules when a product workflow needs their deliverable logic, not as replacements for deterministic data MCPs.

## Consequences

- Ariadne avoids reinventing federal data MCP servers and can benefit from upstream hardening, tests, packaging, and cross-client conventions.
- Public federal data access stays behind capability boundaries instead of leaking raw API calls into the Command Center, evidence model, or capture workflows.
- Ariadne can register all eight federal data streams for future use while preserving quality by deeply integrating one source at a time.
- USAspending becomes the first deep Recompete Intelligence Intake source, with other MCPs deferred for their own product slices or enrichment steps.
- Capability outputs remain review-gated; upstream MCP results are not trusted opportunity knowledge until Ariadne records provenance and the user accepts, routes, or promotes them.
- Firecrawl, custom web research, skill chaining, LangGraph, and 1102 deliverable skills remain later slices that can consume or enrich the data foundation established here.
