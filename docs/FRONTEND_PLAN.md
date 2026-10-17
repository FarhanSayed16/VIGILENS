# VIGILENS — Complete Frontend Plan

| | |
|---|---|
| **Document status** | **Authoritative frontend plan (no code)** |
| **Date** | 17 October 2026 |
| **Stack** | React · Vite · TypeScript · modern chart + motion libraries |
| **Companion docs** | `VIGILENS_COMPLETE_IDEA.md` · `BACKEND_PLAN.md` · `AIML_CONFIRMATION.md` |
| **Next** | Master plan (frontend + backend + AIML combined) |

> **Scope:** every page, route, navigation pattern, design system, colour theme, typography, icons, motion, component map, state flow, responsive behaviour, and build order.  
> **No source code** — structure and design decisions only.  
> Frontend consumes the backend API contract from `BACKEND_PLAN.md` §9.

---

## 1. Frontend purpose (one paragraph)

The frontend is the **lecturer’s reflection workspace**. It lets a teacher set up a room, capture or upload a lecture, mark topics and teaching modes, run analysis, and read a clear **class-level TTOI timeline** with coverage honesty and candidate decline events — never student rankings, never emotion labels, never surveillance chrome. It must feel like a **calm academic instrument**: professional, readable, trustworthy, and scalable as more sessions and rooms appear.

---

## 2. Locked frontend stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **React 18+** (Vite) | Proper SPA; matches product plan |
| Language | **TypeScript** | Scalable contracts with backend DTOs |
| Routing | **React Router** | Multi-page app structure |
| Styling | **CSS variables + modular CSS** (or CSS Modules) | Theme tokens without heavy UI-kit lock-in |
| Charts | One chart library (e.g. Recharts / Visx / Chart.js — pick at implement time) | Timeline + coverage |
| Icons | **Lucide** (or Phosphor) — outline academic set | Consistent, professional, no emoji UI |
| Motion | **Motion / Framer Motion** (or CSS + View Transitions) | Page and panel transitions |
| HTTP | **Fetch** or Axios wrapper + typed API client | JWT attachment |
| Forms | React Hook Form or controlled forms | Room polygons, session create |
| Date/time | Lightweight formatter | Lecture clocks and window labels |
| QR | Small QR generator for pulse link | Student pulse page |

**Not used as product UI:** Streamlit · generic purple SaaS kits · emoji-heavy dashboards · dark-neon “security camera” look.

---

## 3. Product personality & visual direction

### 3.1 Brand character
| Attribute | Direction |
|---|---|
| Mood | Clear, calm, academic — “a clearer lens on learning” |
| Metaphor | Optics / lens / lecture timeline — **not** CCTV / alarm red |
| Trust | Coverage grey zones and honest empty states are first-class UI |
| Density | Reflection tool: charts readable at a glance; not a trading terminal |

### 3.2 Theme name (working)
**“Daylight Lecture”** — light primary surface, deep slate text, teal-cyan accent for orientation (signal of “facing target”), warm amber only for **attention to review** (candidate declines), soft graphite for insufficient evidence.

### 3.3 Colour system (CSS variables — locked intent)

| Token | Role | Guidance |
|---|---|---|
| `--bg-canvas` | App background | Soft cool off-white with subtle paper grain or faint radial wash (not flat #FFF only; not cream #F4F1EA cliché) |
| `--bg-surface` | Panels / sheets | Clean white / near-white |
| `--bg-muted` | Side rails, table zebra | Cool grey-blue mist |
| `--text-primary` | Body / titles | Deep slate-ink (near charcoal, not pure black) |
| `--text-secondary` | Hints, captions | Muted slate |
| `--accent` | Primary actions, links, TTOI line | **Teal / deep cyan** (academic, distinct from purple AI defaults) |
| `--accent-soft` | Selected nav, chips | Washed teal |
| `--signal-ok` | Healthy coverage | Soft green-teal |
| `--signal-review` | Candidate decline markers | **Amber / soft copper** — “review this,” not “alarm” |
| `--signal-weak` | Low coverage / unobservable | Neutral graphite + hatch pattern |
| `--border` | Dividers | Hairline cool grey |
| `--danger` | Destructive only (delete session / purge) | Restrained red — rare |
| `--focus-ring` | Keyboard focus | Accent at reduced opacity |

**Hard avoids (per project design discipline):** purple-on-white / indigo glow SaaS; terracotta-on-cream serif brochure; newspaper broadsheet density; neon cyberpunk; camera-red surveillance UI.

### 3.4 Typography

| Role | Direction |
|---|---|
| Display / brand | Distinct **humanist sans or soft geometric** (e.g. family like Fraunces only for wordmark *or* a display sans — pick one; avoid Inter/Roboto/Arial as the hero face) |
| UI / body | Readable professional sans (e.g. Source Sans / IBM Plex Sans / similar) |
| Data / charts / timestamps | Tabular figures; mono optional for seconds (`18:30`) |
| Hierarchy | Brand wordmark strong in shell; page titles clear but not louder than product name in chrome |

### 3.5 Iconography
- Outline icons, 1.5–2px stroke, rounded joins  
- Domain set: lens, chalkboard, seats grid, upload, webcam, phone, timeline, flag (topic), layers (mode), download (CSV), shield/privacy, play-analysis, alert-triangle (decline — amber)  
- **No** face-scan icons, skull, siren, eye-tracking horror motifs  
- Empty states: custom simple illustration (lens + lecture hall silhouette) — not clipart spam  

### 3.6 Surfaces & layout language
- App shell = left nav + top context bar + main stage  
- Prefer **sheets and sections** over card grids in dashboards  
- Cards **only** where interaction needs a container (session pickers, source chooser, job progress)  
- Charts are full-bleed within the results stage — dominant visual for reflection  
- Generous whitespace; one job per screen region  

### 3.7 Motion & transitions (required presence)

| Motion | Where | Feel |
|---|---|---|
| Route transition | Page enter/exit | Soft fade + 8–12px upward settle (150–220ms) |
| Nav active | Sidebar indicator | Sliding pill / bar, spring-light |
| Panel expand | Filters, event drawer | Height + opacity |
| Timeline scrub | Hover/focus on TTOI | Crosshair + tooltip fade |
| Coverage hatch | Low-coverage bands | Appear with chart draw |
| Job progress | Analysis running | Determinate bar + subtle pulse on % (not infinite spinner forever) |
| Success | Job done | Brief accent flash → timeline mounts with stagger |
| Micro | Buttons, icon buttons | 100ms colour/scale; respect `prefers-reduced-motion` |

**Ship at least:** (1) route transitions, (2) timeline mount animation, (3) job-progress motion. More polish after MVP.

---

## 4. Information architecture

### 4.1 User roles in UI
| Role | Surfaces |
|---|---|
| **Lecturer (authenticated)** | All operator pages |
| **Student (anonymous)** | Pulse check page only (public link / QR) |

### 4.2 Primary mental model (lecturer journey)
```text
Login
  → Home / Sessions
      → (optional) Rooms setup
      → New Session wizard
            → Source (upload / webcam / phone)
            → Topics & modes (during / after)
            → Run analysis
            → Results workspace (timeline)
                  → Export / purge / pulse QR
```

---

## 5. Complete page & route map

| # | Route (conceptual) | Page name | Auth | Purpose |
|---|---|---|---|---|
| 1 | `/login` | Login | Public | Lecturer JWT |
| 2 | `/` or `/sessions` | Sessions home | JWT | List past sessions; start new |
| 3 | `/rooms` | Rooms library | JWT | List / manage room configs |
| 4 | `/rooms/new` | Create room | JWT | Name + calibration frame + seats + target |
| 5 | `/rooms/:id/edit` | Edit room | JWT | Update geometry / camera defaults |
| 6 | `/sessions/new` | New session wizard | JWT | Title, room, source type |
| 7 | `/sessions/:id` | Session hub | JWT | Overview: status, actions, summary chips |
| 8 | `/sessions/:id/setup` | Capture & source | JWT | Upload / webcam preview / phone URL |
| 9 | `/sessions/:id/live` | Live controls (optional MVP+) | JWT | Topic + mode buttons during class |
| 10 | `/sessions/:id/analysis` | Analysis runner | JWT | Start job + progress |
| 11 | `/sessions/:id/results` | Results workspace | JWT | **Main product screen** — TTOI timeline |
| 12 | `/sessions/:id/events` | Events focus (or tab) | JWT | Candidate declines list |
| 13 | `/sessions/:id/export` | Export & retention | JWT | CSV + purge video |
| 14 | `/sessions/:id/pulse` | Pulse setup | JWT | QR + link for class |
| 15 | `/pulse/:sessionId` | Student pulse | Public | 1–5 anonymous score |
| 16 | `/privacy` | Privacy notice | Public/JWT | Purpose, retention, consent reminder |
| 17 | `/settings` | Settings (light MVP) | JWT | Account hint, thresholds display-only later |
| 18 | `*` | Not found | — | Friendly 404 |

**MVP must-have pages:** Login · Sessions home · Rooms create/edit · New session · Capture/source · Analysis · Results · Export · Student pulse · Privacy notice.  
**Can start as tabs inside Session hub:** Events · Pulse QR · Live controls.

---

## 6. Page-by-page specification

### 6.1 Login
**Goal:** Fast entry for one lecturer.  
**Layout:** Split or centered sheet on atmospheric canvas (subtle lens/gradient — not purple). Brand wordmark **VIGILENS** dominant; short line: *A clearer lens on learning*.  
**Elements:** Username, password, Sign in, link to privacy notice.  
**States:** Loading, invalid credentials, backend unreachable.  
**Motion:** Gentle sheet entrance.

### 6.2 Sessions home
**Goal:** “What lectures do I have?”  
**Elements:**  
- Top: New session CTA  
- Filters: room, date range, status (draft / complete / error)  
- List or compact table: title, room, date, coverage badge, event count, status pill  
- Empty state: first-run guidance → create room → new session  
**Nav:** Primary landing after login.

### 6.3 Rooms library
**Goal:** Reusable classroom geometries.  
**Elements:** Room cards/rows (name, seat count, last used), Create room, Edit.  
**Empty state:** Explain seat regions + teaching target once.

### 6.4 Create / Edit room (calibration studio)
**Goal:** Draw the room once; reuse forever.  
**Layout:**  
- Left/top: calibration image or paused video frame  
- Overlay tools: draw seat polygons, draw teaching-target ROI  
- Side panel: seat list, expected facing notes, camera defaults (webcam index / default RTSP hint)  
- Actions: Save room, Cancel  
**UX rules:** Clear tool modes (Select / Draw seat / Draw target / Delete). Undo last shape.  
**Copy:** Remind that regions are **seats**, not named students.

### 6.5 New session wizard
**Steps:**  
1. Title + select room config  
2. Choose source type: Upload · Webcam · Phone stream  
3. Confirm privacy banner (local processing, purge after analysis)  
4. Create → land on Session hub / Setup  

**Progress:** Step indicator with short transitions.

### 6.6 Session hub
**Goal:** Mission control for one lecture.  
**Elements:**  
- Header: title, room, status, started/ended  
- Summary chips (after analysis): mean TTOI, coverage, decline count  
- Action tiles/links: Setup source · Live markers · Run analysis · Results · Export · Pulse QR · Delete session  
- Honesty strip: “Class-level observable orientation — not attention scores.”

### 6.7 Capture & source setup
**Goal:** Get a usable video into the system.  
**Modes:**  
| Source | UI |
|---|---|
| Upload | Drag-drop zone, file picker, size limit hint (~2 GB), progress |
| Webcam | Device select, live preview, record-or-attach note (MVP: preview + “file will be uploaded after record” or path per backend capability) |
| Phone | URL field (IP Webcam / DroidCam / RTSP), Test connection, preview if possible |

**States:** Uploading, ready, failed, oversize.

### 6.8 Live controls (during class)
**Goal:** Timestamp topics and modes without leaving the flow.  
**Elements:** Large “New topic” (prompt for label), mode segmented control (Explanation / Note-taking / Q&A / Discussion), elapsed clock, optional pulse QR peek.  
**Design:** Big tap targets; low cognitive load while teaching.

### 6.9 Analysis runner
**Goal:** Start and trust the job.  
**Elements:** Preconditions checklist (source ready, room set), Run analysis button, progress %, stage labels (Ingest → Vision → Aggregate → Done), error panel with message from API, Re-run (supersede) confirmation.  
**Motion:** Determinate progress; on complete auto-navigate or strong CTA to Results.

### 6.10 Results workspace (hero product screen)
**Goal:** Answer the three product questions: when did orientation change, how reliable, which topic.  

**Layout (desktop):**  
```text
┌─ Context bar: session · mode · export · privacy ───────────┐
├─ Summary strip: mean TTOI · coverage · events · quality ───┤
├─ Main chart: TTOI over time ───────────────────────────────┤
│    · teal TTOI line + confidence band                      │
│    · grey hatch = low coverage (no fake story)             │
│    · amber spans = candidate declines                      │
│    · topic markers as vertical ticks / bands               │
├─ Secondary row: head-down rate · hand-raise (separate) ────┤
├─ Right or bottom drawer: selected window / event detail ───┤
└─ Disclaimer footer (always visible) ───────────────────────┘
```

**Interactions:**  
- Hover/click window → detail (coverage, mode, topic, quality note)  
- Click decline event → zoom/highlight span  
- Toggle: show/hide secondary cues  
- Filter: only windows with coverage ≥ threshold  

**Mobile:** Chart first; details in bottom sheet; summary chips scroll horizontally.

### 6.11 Events focus
**Goal:** Review-only list of candidate orientation declines.  
**Elements:** Table/timeline list: time range, depth (points dropped), coverage, topic, mode, note. Click → jump into Results chart.  
**Copy:** Always “possible orientation decline” — never “students were bored.”

### 6.12 Export & retention
**Goal:** Take data away; remove raw video.  
**Elements:** Download CSV, explain what’s inside / excluded, Purge video (confirm modal), status “video purged — aggregates kept.”  
**Danger actions:** Confirm with typed or checkbox acknowledgment.

### 6.13 Pulse setup (lecturer)
**Goal:** Show QR + copy link for `/pulse/:sessionId`.  
**Elements:** Large QR, open link, short student instructions (“anonymous, 1–5, no name”).

### 6.14 Student pulse (public)
**Goal:** 10-second interaction on phone.  
**Layout:** Minimal — brand small, one question, 1–5 control, Submit, thank-you. No login. No PII fields ever.  
**Motion:** Soft success check.

### 6.15 Privacy notice
**Goal:** Institutional trust surface.  
**Content blocks:** Purpose, class-level only, no face recognition, no grading, retention/purge, consent already obtained reminder, contact placeholder.  
Linked from login, shell footer, and session wizard.

### 6.16 Settings (light)
**Goal:** Future-proof slot. MVP: lecturer display name optional, logout, link to privacy, app version. Threshold editing can be read-only “from server config” later.

### 6.17 404 / error boundary
Friendly message, link home, no stack traces in UI.

---

## 7. App shell & navigation

### 7.1 Authenticated shell
```text
┌────────┬──────────────────────────────────────────────┐
│ Brand  │ Context: page title · session crumb · user   │
│ VIGIL… ├──────────────────────────────────────────────┤
│        │                                              │
│ Nav:   │              Main stage                      │
│ Home   │                                              │
│ Rooms  │                                              │
│ (Sess) │                                              │
│ Privacy│                                              │
│ ─────  │                                              │
│ Logout │                                              │
└────────┴──────────────────────────────────────────────┘
```

| Nav item | Goes to |
|---|---|
| Sessions | Sessions home |
| Rooms | Rooms library |
| Privacy | Privacy notice |
| Logout | Clear token → Login |

**Session-scoped subnav** (when inside `/sessions/:id/*`): Hub · Setup · Live · Analysis · Results · Export · Pulse — as tabs or secondary horizontal nav under context bar.

### 7.2 Navigation rules
- Persist last session in local UI state for quick return  
- Block Results with empty state + CTA if analysis not done  
- Unsaved room geometry: confirm on navigate away  
- Deep links supported for all JWT routes  

### 7.3 Mobile navigation
- Collapsible sidebar → bottom tab or hamburger  
- Results chart remains usable via horizontal pan/zoom  
- Live controls optimized for phone in lecturer pocket  

---

## 8. Component inventory (scalable design system)

### 8.1 Foundations
- Theme tokens (colours, type, space, radius, shadow-minimal)  
- Grid / stack / cluster layout primitives  
- Icon wrapper  
- Focus ring utilities  
- Reduced-motion utilities  

### 8.2 Primitives
- Button (primary / secondary / ghost / danger)  
- Icon button  
- Input, Textarea, Select, Segmented control  
- Checkbox, Radio  
- Modal / Dialog  
- Drawer / Sheet (mobile details)  
- Toast / Inline alert  
- Badge / Status pill  
- Progress bar  
- Empty state  
- Skeleton loaders  
- Tooltip  
- Tabs  

### 8.3 Domain components
| Component | Role |
|---|---|
| `BrandMark` | Wordmark + optional lens glyph |
| `PrivacyBanner` | Persistent honesty strip |
| `SessionStatusPill` | draft / analyzing / complete / error |
| `CoverageBadge` | % + weak/ok |
| `TtoiSummaryStat` | Mean TTOI with plain-language caption |
| `SeatRegionCanvas` | Draw/edit polygons on frame |
| `TargetRoiCanvas` | Teaching target overlay |
| `SourceChooser` | Upload / webcam / phone cards |
| `UploadDropzone` | File ingest UX |
| `WebcamPreview` | Live aim preview |
| `JobProgressPanel` | Stages + % |
| `TtoiTimelineChart` | Core chart |
| `CoverageBandOverlay` | Grey hatch regions |
| `DeclineMarkerLayer` | Amber event spans |
| `TopicMarkerLayer` | Vertical topic ticks |
| `EventDetailPanel` | Selected event copy |
| `ModeSwitcher` | Teaching modes |
| `TopicQuickAdd` | New topic control |
| `PulseQrPanel` | QR + link |
| `ExportPanel` | CSV + purge |
| `ConfirmDestructive` | Purge/delete modals |
| `DisclaimerFooter` | Always-on proxy wording |

### 8.4 Scalability rules
- Domain components talk to **typed API hooks**, not raw fetch scattered in pages  
- Charts accept normalized view-models (`WindowPoint`, `DeclineEvent`)  
- Theme tokens only — no one-off hex in feature files  
- New Phase-2 cues (phone, drowsiness) = new optional series on same timeline, not new apps  

---

## 9. State, data, and API mapping

### 9.1 Client state layers
| Layer | Holds |
|---|---|
| Auth store | JWT, lecturer identity, login/logout |
| Server cache | Sessions, rooms, windows, events, jobs (React Query / SWR recommended) |
| UI ephemeral | Wizard step, selected chart window, sidebar open, unsaved canvas |
| Preferences | Reduced motion already from OS; optional chart density |

### 9.2 Page → API mapping (high level)

| Page | Primary APIs |
|---|---|
| Login | `POST /auth/login` |
| Sessions home | `GET /sessions` |
| Rooms | `GET/POST/PUT /rooms` |
| New session | `POST /sessions` |
| Upload / source | `POST .../upload`, `PUT .../source` |
| Topics / modes | `POST .../topics`, `POST .../mode` |
| Analysis | `POST .../analysis`, `GET /jobs/{id}` (poll) |
| Results | `GET .../summary`, `.../windows`, `.../events`, `.../topics` |
| Export | `GET .../export`, `DELETE .../video` |
| Pulse public | `POST /pulse/{session_id}` |
| Delete session | `DELETE /sessions/{id}` |

### 9.3 Polling
- While job `queued`/`running`: poll job status every ~1s  
- Stop on `done`/`error`  
- Optional later: WebSocket without redesigning Results page  

---

## 10. Content & microcopy standards

| Situation | Required wording style |
|---|---|
| Metric name | **TTOI** / Teaching-Target Orientation Index |
| Declines | **Candidate orientation decline** / “possible orientation decline” |
| Low coverage | **Insufficient visual evidence** — suppress alarm styling |
| Never say | Bored, lazy, cheating, attention score, focus grade, student ranking |
| Empty results | Explain next step (run analysis / improve camera) |
| Errors | Human sentence + optional technical detail expand |

Persistent disclaimer on Results:  
> Observable class-level orientation trends — not a measure of learning, interest, or individual performance.

---

## 11. Responsive & accessibility plan

| Breakpoint | Behaviour |
|---|---|
| Desktop (≥1100px) | Sidebar + full results layout |
| Tablet | Collapsible nav; chart stacked above detail |
| Mobile | Bottom nav / hamburger; pulse page mobile-first |

**A11y:**  
- Keyboard for all primary actions  
- Focus visible  
- Chart has text/table alternative (simple window table toggle)  
- Colour not sole decline signal (icon + label + amber)  
- `prefers-reduced-motion` disables non-essential animation  
- Contrast AA for text and key chart lines  

---

## 12. Folder structure (frontend)

```text
frontend/
├── package.json
├── vite.config.*
├── index.html
├── public/                    # favicon, og optional
└── src/
    ├── main.tsx
    ├── app/                   # providers, router, shell
    ├── pages/                 # one folder per route page
    │   ├── login/
    │   ├── sessions/
    │   ├── rooms/
    │   ├── session-hub/
    │   ├── setup/
    │   ├── live/
    │   ├── analysis/
    │   ├── results/
    │   ├── export/
    │   ├── pulse-setup/
    │   ├── pulse-public/
    │   ├── privacy/
    │   └── settings/
    ├── components/
    │   ├── ui/                # primitives
    │   ├── domain/            # VIGILENS-specific
    │   └── charts/            # timeline pieces
    ├── features/              # optional feature modules (room-editor, timeline)
    ├── api/                   # client, endpoints, types
    ├── hooks/
    ├── stores/                # auth / ui
    ├── styles/                # tokens, global, motion
    ├── assets/                # brand glyph, empty-state art
    └── utils/                 # time, download blob, qr helpers
```

---

## 13. Design quality bar (definition of “professional”)

1. First authenticated screen looks intentional — brand + calm hierarchy, not a default Vite starter  
2. Results page readable in under 10 seconds for a lecturer  
3. Low-coverage regions never look like “bad students”  
4. Motion supports orientation; nothing decorative that distracts from the chart  
5. Same components reused across rooms/sessions — no one-off page CSS chaos  
6. Works on laptop projector for demo and on phone for pulse  
7. Privacy notice one click away from anywhere in shell  

---

## 14. Explicitly out of frontend MVP

| Item | Note |
|---|---|
| Student ranking / heatmaps per named seat | Forbidden |
| Emotion smileys / emoji mood meters | Forbidden |
| PDF export UI | Phase 2 |
| Full design-system Storybook (optional later) | Nice-to-have |
| Dark mode | Not default; optional later if requested |
| Multi-lecturer admin console | Later |
| Complex annotation labelling suite | Phase 2+ research tooling |
| Marketing landing microsite | Separate from app; optional |

---

## 15. Frontend implementation order

### F0 — Foundation
1. Vite + React + TS + router + theme tokens  
2. App shell + typography + icons  
3. Auth login + token storage + protected routes  
4. API client skeleton  

### F1 — Data shells
1. Sessions home (list + empty states)  
2. Rooms list + create/edit canvas (can start with box regions before polygons polish)  
3. New session wizard + session hub  

### F2 — Capture & jobs
1. Upload dropzone + source forms  
2. Analysis page + job polling UI  
3. Privacy banner + notice page  

### F3 — Results (core value)
1. TTOI timeline chart + coverage overlay + topic markers  
2. Decline markers + detail panel  
3. Secondary cue charts  
4. Motion: chart mount + route transitions  

### F4 — Close the loop
1. Export + purge flows  
2. Pulse QR + public pulse page  
3. Live topic/mode controls  
4. Responsive pass + a11y pass + empty/error polish  

### F5 — Demo hardening
1. Projector-friendly Results density  
2. Microcopy review with professor wording  
3. Performance: large window arrays  

---

## 16. Definition of done (frontend MVP)

1. Lecturer can log in and navigate shell confidently  
2. Room seats + target can be configured visually  
3. Session can be created; video uploaded or source set  
4. Topics/modes can be added  
5. Analysis progress is visible end-to-end  
6. Results show TTOI + coverage + candidate declines + topics  
7. CSV download and video purge work from UI  
8. Student pulse page works from QR without login  
9. Privacy wording visible; no forbidden “attention grade” language  
10. Desktop + mobile usable; reduced-motion respected  

---

## 17. How this connects to other plans

| Plan | Connection |
|---|---|
| **Backend plan** | Every page maps to §9 APIs |
| **AIML confirmation** | UI displays TTOI/coverage — never claims model mind-reading |
| **Master plan** | Will sequence F0–F5 with backend B0–B5 and AIML phases |

---

## 18. Confirmation checklist

- [x] Full page/route map defined  
- [x] Professional **Daylight Lecture** theme (teal accent, amber review, graphite uncertainty)  
- [x] Shell + session subnav defined  
- [x] Results workspace specified as hero screen  
- [x] Icons, type, motion, a11y, responsive covered  
- [x] Component inventory for scalability  
- [x] No code — planning only  
- [x] Ready for master plan merge  

---

**End of frontend plan.**  
Reply **“Frontend confirmed”** when this matches; next step is the **master plan** combining frontend + backend + AIML.
