# Privacy review — Live Cockpit (Phase 32)

| | |
|---|---|
| **Date** | 19 October 2026 |
| **Scope** | Phases 25–32 live hybrid |

## Guarantees retained

- No face recognition, embeddings, or student names  
- No stored face / group evidence crops in the product path  
- Seat IDs and temporary Group labels are anonymous geometry  
- Short-lived tracking (if used in vision) is session-scoped only  
- Class TTOI remains the principal measure; per-seat O% is observable orientation  

## New surfaces reviewed

| Surface | Risk | Mitigation |
|---------|------|------------|
| Live seat heatmap | Spatial re-identification in small classes | Anonymous IDs; no roll numbers; coverage honesty |
| Group clusters | “Talking” overclaim | Copy: possible interaction pattern, not proof |
| Secondary camera | Extra PII capture | Display-only; not fused; same purge rules as primary |
| Event feedback | Lecturer notes | Enum only (`useful` / `false_alarm` / `insufficient`) |

## Sign-off

Engineering privacy review for Live Cockpit Hybrid — acceptable for consented pilot use with existing consent / purge flows.
