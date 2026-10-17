# VIGILENS — DB enum / status values (MVP)

Stored as `VARCHAR` strings (not Postgres ENUM types) for easy migration.

| Field | Allowed values |
|---|---|
| `sessions.source_type` | `upload` · `webcam` · `phone_rtsp` |
| `sessions.status` | `draft` · `ready` · `analyzing` · `complete` · `error` · `purged_video` |
| `mode_changes.mode` / `sessions.current_mode` / window `teaching_mode` | `explanation` · `note_taking` · `qa` · `discussion` |
| `analysis_jobs.status` | `queued` · `running` · `done` · `error` · `cancelled` |
| `windows.data_quality_note` | `null` · `insufficient_coverage` · `partial_window` |

**Never stored:** face embeddings, face crops, names, roll numbers, student IDs.
