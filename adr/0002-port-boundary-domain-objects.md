# ADR 0002 — Outbound Ports Return Domain Objects

**Date:** 2026-06-14  
**Status:** Accepted

## Context

The system uses Hexagonal Architecture. Adapters (e.g. `OpenAIClient`, `GitLabAdapter`) fetch data from external systems and return it to the domain. The question arose whether outbound port interfaces should return adapter-internal DTOs (pydantic models matching wire formats) or domain objects.

The concrete trigger: `LLMPort.generate_code_review()` could return `CodeReviewResponseDTO` (an OpenAI-specific pydantic model) or a `CodeReview` domain value object. Choosing the DTO would mean either:
- The port interface imports from an adapter (reversing the dependency direction), or
- The orchestrator duck-types on a pydantic model owned by a specific adapter.

A second problem: the LLM result is subsequently passed to the GitLab adapter to post comments. Passing the DTO through the orchestrator would create implicit adapter-to-adapter coupling.

## Decision

**All outbound ports return domain objects.** DTOs (pydantic) are internal to each adapter and are mapped to domain types before crossing the port boundary.

Each adapter is responsible for:
1. Owning its own `dto.py` (pydantic, matching the external wire format).
2. Owning its own `mappers.py` with a `to_domain()` function.
3. Exposing only domain objects through the port interface.

## Consequences

- The domain layer and port interfaces remain free of infrastructure types.
- Two adapters can interoperate (LLM output → GitLab input) through neutral domain objects, with no knowledge of each other's wire formats.
- Every adapter must maintain a mapper. This is a small, predictable cost — the GitLab adapter already established this pattern.
- DTOs remain useful for pydantic validation of external responses (e.g., enforcing LLM JSON schema) before mapping.
