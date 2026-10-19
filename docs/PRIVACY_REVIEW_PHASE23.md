# Lightweight privacy / security review — Phase 23

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Scope** | MVP lecturer API + React UI (local stack) |
| **Status** | **PASSED** for demo / Checkpoint C prep |

---

## Checklist

| Check | Result | Evidence |
|---|---|---|
| No student identity / face embeddings stored | **OK** | Schema has no identity tables; YAML `store_face_crops/embeddings: false` |
| Export has no faces / names / video paths | **OK** | `export_service.py` header + column set; Checkpoint A asserts |
| Public pulse rejects extra PII fields | **OK** | `PulseSubmit` `extra="forbid"`; journey test `student_name` → 422 |
| Public auth does not leak username | **OK** | `/auth/public-info` has no `username_hint` |
| RTSP credentials not returned in clear | **OK** | `session_service._redact_source_url` |
| Pulse rate-limit fail-closed | **OK** | Redis down → 503 |
| Class-level aggregates only in Results/CSV | **OK** | Product copy + export scope |
| Purge keeps aggregates, removes video | **OK** | retention + media purge |

## Residual risks (accepted for MVP)

- Single shared lecturer account (no multi-tenant ACL)
- Default env password must be changed for any shared demo
- Pulse is public by session id (spam mitigated by Redis rate limit)

## Sign-off

Phase 23.3 privacy review **approved** for local MVP demos.
