# VIGILENS — UI/UX Redesign Specification

> **Purpose:** A page-by-page specification to improve the clarity, usability, and information hierarchy of the existing VIGILENS interface without changing the visual identity (colour palette, typography, token system) or introducing functionality the backend does not support.
>
> **How to use this document:** Each section maps to one route or reusable component. For every element, the spec states **what exists**, **what is confusing or sub-optimal**, and **the recommended change** with implementation guidance.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Global Shell & Navigation](#2-global-shell--navigation)
3. [Sessions List (`/sessions`)](#3-sessions-list-sessions)
4. [New Session Wizard (`/sessions/new`)](#4-new-session-wizard-sessionsnew)
5. [Session Hub / Console (`/sessions/:id`)](#5-session-hub--console-sessionsid)
6. [Live Cockpit (within Session Hub)](#6-live-cockpit-within-session-hub)
7. [Topics & Modes (`/sessions/:id/live`)](#7-topics--modes-sessionsidlive)
8. [Review / Results (`/sessions/:id/results`)](#8-review--results-sessionsidresults)
9. [Setup (`/sessions/:id/setup`)](#9-setup-sessionsidsetup)
10. [Export & Retention (`/sessions/:id/export`)](#10-export--retention-sessionsidexport)
11. [Pulse QR (`/sessions/:id/pulse`)](#11-pulse-qr-sessionsidpulse)
12. [Pulse Public (`/pulse/:id`)](#12-pulse-public-pulseid)
13. [Rooms List (`/rooms`)](#13-rooms-list-rooms)
14. [Room Editor (`/rooms/:id/edit`)](#14-room-editor-roomsidedit)
15. [Settings (`/settings`)](#15-settings-settings)
16. [Privacy (`/app/privacy`)](#16-privacy-appprivacy)
17. [Responsive & Mobile Behaviour](#17-responsive--mobile-behaviour)
18. [Cross-Cutting UX Patterns](#18-cross-cutting-ux-patterns)

---

## 1. Design Principles

These principles guide every recommendation below. They are derived from the existing VIGILENS brand, target users (lecturers running sessions mid-class), and the system's constraints (single-user MVP, class-level aggregates only, privacy-first).

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Reduce cognitive load** | Lecturers interact during class. Every element visible at once competes for attention. |
| 2 | **Lead with plain language** | TTOI, coverage %, decline depth — these need human translations visible first. |
| 3 | **Show status progression, not just labels** | `Ready → Live → Complete` is a workflow. The UI should communicate *what to do next*, not just *what the state is*. |
| 4 | **Progressive disclosure** | Show the primary action and critical metric first. Detail on demand (expand, click, hover). |
| 5 | **Consistent card anatomy** | Every metric card should follow: label → value → context hint. Never value-only. |
| 6 | **Respect the privacy pledge** | Keep the privacy strip visible but not repetitive. One clear note per page, not per section. |
| 7 | **Preserve the visual identity** | Keep `--accent: #0f766e`, `--bg-canvas: #eef2f4`, `Outfit` / `DM Sans`, and the teal / grey / amber signal palette. |

---

## 2. Global Shell & Navigation

### 2.1 Sidebar

**Current state:** Three primary links (Sessions, Rooms, Privacy) + footer (Settings, Logout). The Privacy link sits in primary nav alongside functional pages.

**Issues identified:**
- Privacy is an informational page, not a daily-use destination. Placing it alongside Sessions and Rooms gives it equal weight.
- The Settings link uses a `BookOpen` icon (notebook), which doesn't connote settings.
- At the 1200 px breakpoint the sidebar collapses to an icon rail, but the brand tag disappears and nav labels vanish abruptly — no tooltip fallback.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Move Privacy to sidebar footer | Place it below Settings, above Logout. De-emphasise to secondary weight (smaller font, `text-secondary` colour). |
| Change Settings icon | Replace `BookOpen` with `Settings2` or `SlidersHorizontal` from Lucide. |
| Add icon tooltips at icon-rail width | When `font-size: 0` hides labels, add `title` attributes or CSS tooltip pseudo-elements so hover reveals the name. |
| Highlight active session in context bar | When inside `/sessions/:id/*`, show the session title and status pill in the context bar instead of the generic route name. This reduces reliance on the ← breadcrumb. |

### 2.2 Context Bar

**Current state:** Shows a computed page title and `username · lecturer workspace`.

**Issues identified:**
- The title "Live lecture" is used for the Console/Hub page even when the session is not live. Misleading.
- `lecturer workspace` is a placeholder that adds no value for a single-user MVP.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Dynamic title | Inside session pages, display `{session.title} — {tab name}` (e.g. "Week 3 Normalization — Console"). |
| Replace "lecturer workspace" | Show nothing, or show the room name when a session is active: `lecturer · Lab 202`. |

### 2.3 Session Sub-navigation Tabs

**Current state:** Tabs: Console | Review | Export | Pulse | More. Visible via `SessionSubnav` when inside a session route.

**Issues identified:**
- "More" is a vague catch-all that hides Setup and Topics & Modes — both of which are important during a lecture.
- The tab bar uses minimal visual weight; it can be confused with body headings.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Rename "More" to an icon overflow (⋯) with a dropdown | List Setup, Topics & Modes, Delete Session inside the dropdown. |
| Move "Topics & Modes" out of More if space allows | On desktop (≥1200 px), show it as a fifth tab. On narrower viewports, keep it in the overflow. |
| Active tab indicator | Use a thicker (3 px) bottom border in `--accent` and subtle background tint `var(--accent-soft)` for the active tab pill. Currently the active state is distinguishable but could be bolder. |

---

## 3. Sessions List (`/sessions`)

### 3.1 Page Header

**Current state:** Title "Sessions" with a long descriptive paragraph and a `+ New session` button.

**Issues identified:**
- The paragraph is useful on first encounter but unnecessary after the first session. It occupies prime vertical space on every visit.
- The `+ New session` button is disabled when there are no rooms, but the disabled state is styled via inline `opacity: 0.5` with no explanation.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Collapse description text | Show the paragraph only when `sessions.length === 0` or as a dismissible info-strip at the top. For returning users, the page title alone suffices. |
| Explain disabled button | When rooms count is 0, replace the disabled button with a CTA: "Create a room first to start a session" linking to `/rooms/new`. |

### 3.2 Filter Bar

**Current state:** Room and Status dropdowns, horizontally aligned.

**Issues identified:**
- Labels ("Room", "Status") are above their controls, which is fine, but there's no visual grouping to separate filters from the table.
- No indicator that filters are active (e.g. a "Clear" button or pill count).

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add "Clear filters" pill | When `filtersActive`, show a small teal pill/link to reset both dropdowns. Already exists in empty state — surface it inline beside the dropdowns. |
| Inline labels | For space efficiency, make labels inline with their `<select>`: `Room: [All rooms ▾]  Status: [All statuses ▾]`. |

### 3.3 Sessions Table

**Current state:** Standard table: Title, Room, Source, Status, Created, Delete.

**Issues identified:**
- All rows look identical except for the status pill. Completed sessions with review data and draft sessions with no data look the same — no visual cue of "has results".
- The "Delete" column uses a danger-coloured text button on every row. Destructive actions this accessible can be accidental, especially on touch.
- The "Source" column always shows "webcam" in the demo — low information density if most sessions share the same source.
- Created dates are verbose ("Oct 19, 2026, 11:07 AM") and consume horizontal space.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add a quick-metric preview column | Add a "Faced front" column showing `mean_ttoi` as `67%` or `—` for incomplete sessions. Gives an at-a-glance reason to click into a session. |
| Move Delete to row overflow menu | Replace the visible Delete button with a `⋯` (more) icon that opens a small dropdown: "View console", "Delete". Reduces accidental deletion risk. |
| Relative dates for recent sessions | Show "2 hours ago" for sessions created today; full date for older sessions. Use the existing `formatDate` util with a relative fallback. |
| Clickable row | The title column is already a `<Link>`. Make the entire row clickable (via `onClick` on `<tr>`) with cursor pointer, so users don't have to target the small title text. |

### 3.4 Empty States

**Current state:** Well-structured `empty-card` with title, body, and CTA buttons.

**No major issues.** The existing empty states are clear and contextual.

**Minor refinement:** Add an icon or illustration (e.g. a simple outlined lecture hall icon from Lucide) to make the empty state feel less stark.

---

## 4. New Session Wizard (`/sessions/new`)

### 4.1 Step Indicator

**Current state:** Three steps: `1. Title & room`, `2. Source`, `3. Privacy`. Horizontal progress bar using border-bottom highlight.

**Issues identified:**
- Steps that are completed don't show completion state (no checkmark or filled indicator).
- The privacy step is friction for repeat users who understand the system.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Show completed step checkmarks | Add a `✓` or filled dot for steps `< currentStep`. Keep the active step highlighted in teal. |
| Remember privacy acknowledgement | If `localStorage` records that the user has previously accepted, auto-check the privacy checkbox and allow immediate creation. Still show the notice, but remove the gate. |
| Pre-fill title with suggestion | Offer a placeholder like `Session — {room.name} — {today's date}` that the user can accept or overwrite. Reduces typing during class. |

### 4.2 Source Selection Cards

**Current state:** Three cards (Webcam, Upload, Phone stream) in a grid. Selected state uses teal border + soft background.

**Issues identified:**
- The explanatory text after the cards changes per selection, but it's easy to miss because it appears below the grid with no visual connection.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Contextual note inside the selected card | Expand the selected card vertically to include the hint text (e.g. "Webcam index 0 is attached automatically…"). Collapse other cards slightly. |
| Add icons to source cards | Use `Camera`, `Upload`, `Smartphone` Lucide icons inside each card for faster scanning. |

---

## 5. Session Hub / Console (`/sessions/:id`)

This is the most complex page and the one lecturers interact with mid-class. It needs the most attention.

### 5.1 Session Header / Meta Strip

**Current state:** Back link `← Sessions`, session title (as `page-kicker`), and a meta strip showing status pill, room, source, mode, and created date.

**Issues identified:**
- The title uses `page-kicker` class which gives it `text-xl` weight. But it's the session name — it should feel like a primary heading.
- The meta strip is a flat flex row of plain text separated by gaps. Low scannability.
- "Mode: —" is shown when no mode is set. Unclear what this means.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Promote session title to `<h1>` size (`text-2xl`) | Currently uses the same size as section headings. Make it the clear page title. |
| Structure meta as labelled chips | Instead of `Lab 202  Source: webcam  Mode: —  Created Oct 19…`, use small labelled pairs: `Room: Lab 202 │ Source: Webcam │ Mode: Not set │ Created: 2h ago`. |
| Hide "Mode" if null | If no mode has been set, don't show the field. Or show "Mode: Set on Topics tab →" as a link. |
| Add a "next action" prompt | Below the meta strip, based on session status, show a contextual nudge: <br>**Draft:** "Attach a video source to get started" <br>**Ready:** "Press Start lecture when you're ready" <br>**Live:** "Session is running — metrics update every 30s" <br>**Complete:** "Review your results →" |

### 5.2 KPI Chips (Faced front, Camera clear, Longer drops, Topics)

**Current state:** 4 equal-width chips in a grid. Each has a label and value.

**Issues identified:**
- All four chips have equal visual weight, but "Faced the front" is the primary metric. It should dominate.
- The "Topics: 0" chip has no context. Zero topics doesn't mean something is wrong — it means the lecturer hasn't added any yet.
- "Camera clear" is jargon. What does 33% camera clear mean to a non-technical user?

**Recommendations:**

| Change | Detail |
|--------|--------|
| Hero metric for "Faced the front" | Make it larger (matching the `review-kpi-hero` style from Results page). Put it on the left, with the other 3 chips as smaller supportive metrics on the right. |
| Add tooltip or subtitle for "Camera clear" | Below the value, add `"of frames had enough people visible"` in `text-xs text-secondary`. |
| Contextual label for "Topics: 0" | When 0, display "No topics yet · Add on Topics tab →". When > 0, show the number. |
| Add trend indicator for live sessions | During live, show a small up/down arrow or spark line for "Faced the front" if data from multiple windows exists. |

### 5.3 Live Lecture Section

**Current state:** A full `LectureCockpit` component embedded in a section titled "Live lecture" with a description paragraph.

**Issues identified:**
- The section heading "Live lecture" is redundant with the context bar title.
- The description paragraph is long and reads like documentation. During a live session, this is visual noise.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Remove or collapse the description | During live, hide it entirely. When not live, show a compact one-liner: "Start lecture to begin orientation detection." |
| Rename section heading | Use "Camera & Controls" or remove the heading entirely — the Start/Stop button and preview are self-explanatory. |

### 5.4 More Tools & Batch Analysis Toggles

**Current state:** Two collapsible toggle buttons ("Offline batch analysis" and "More tools") sit below the main content.

**Issues identified:**
- These use `<button>` elements with chevron icons, which look like accordions. But they're major navigation/action areas hidden below the fold.
- "More tools" reveals links to Setup, Topics & Modes, Export, and Pulse QR — all of which are also in the session sub-nav tabs.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Merge "More tools" links into the sub-nav | These are redundant with the tab bar. Remove the "More tools" section entirely. |
| Keep "Offline batch analysis" as a collapsible | But move it above the danger zone and give it a card border, not just a toggle button. Style as a `<details>` element with a summary: "Run batch analysis (for uploaded video)". |
| Remove the danger zone from the hub | Move "Delete session" to the overflow menu (⋯) in the sub-nav or to Settings. Having a big red delete button on the main working page is risky during live sessions. |

---

## 6. Live Cockpit (within Session Hub)

### 6.1 Toolbar (Clock, Start/Stop)

**Current state:** Session clock with elapsed time, LIVE badge, next-metrics countdown, and Start/Stop buttons.

**Issues identified:**
- The clock is small relative to its importance. During a lecture, the elapsed time should be glanceable.
- "Next metrics in 25s" is useful but competes with the LIVE badge.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Enlarge the clock | Use `text-2xl` or `text-xl` for the elapsed value. Keep the LIVE badge but make the countdown a subtle progress arc or bar under the clock instead of inline text. |
| Combine into a status ribbon | Create a horizontal ribbon: `[▶ 01:20]  LIVE  [Next update: ██████░░ 25s]  [■ Stop lecture]`. Left-aligned clock, right-aligned stop button, progress bar in the middle. |

### 6.2 Camera Preview

**Current state:** A `preview-pane` with a header ("Primary camera · webcam:0"), the video/worker preview, and a note underneath.

**Issues identified:**
- The note under the preview ("Live camera with seat boxes and people highlights — anonymous, not face identity.") is repeated across multiple states. The user doesn't need to read it every time.
- The "Starting worker preview…" placeholder with the "Loading vision model…" pill is a dead-looking grey box with dense text. It should feel more alive.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Simplify the note | Show it only once on first load or as a tooltip on a small `ℹ` icon. |
| Add a loading animation | In the placeholder state, add a subtle pulsing border or skeleton animation to indicate the system is working. Replace "Starting worker preview…" with a centered spinner + "Connecting to camera…". |
| Overlay detection badge on the preview image | The detection badge is already drawn on the canvas overlay — also show a floating pill on the worker JPEG: "1 person · 1 tracked" in a semi-transparent bar at the top of the preview. (This is already partially implemented.) |

### 6.3 Side Metrics Panel

**Current state:** Four gauges stacked vertically (Faced the front, Camera clear, People in view, Seats measured) + a honesty disclaimer.

**Issues identified:**
- The dash (`—`) shown before any data arrives is ambiguous. Is it loading? Is there an error? Is it not applicable?
- "People in view: 1 · 1 tracked" — the dot separator is confusing. What's the difference between "in view" and "tracked"?

**Recommendations:**

| Change | Detail |
|--------|--------|
| Show loading state explicitly | Before first data, show a skeleton pulse animation or "Waiting…" text instead of `—`. |
| Clarify tracked vs. in view | Use labels: "Detected: 1" and below it "In drawn seats: 1". If seats measured = 0, show "No seat data yet — first update in ~30s". |
| Colour-code the faced-front gauge | If TTOI ≥ 70 → teal, 45–69 → amber, < 45 → soft red. This gives an instant signal. |

### 6.4 Seat Map ("Who faces the front")

**Current state:** Colour-coded tiles (green/amber/red/grey) with seat IDs and orientation percentages.

**Issues identified:**
- The colour legend is described in a paragraph: "Green = facing · amber = mixed · red = looking away · grey = can't see." This should be a visual legend.
- The tile grid is flat and doesn't map to spatial layout. All seats appear in a row regardless of their position in the room.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add a compact visual legend bar | Place inline colour swatches (■ Facing ■ Mixed ■ Away ■ N/A) above the grid, similar to the chart legend on the Results page. |
| Consider spatial layout (future) | If room editor captures seat coordinates, render them approximately. For now, the grid is acceptable — just add row breaks if seats are named with zone prefixes (e.g. A1, A2, B1, B2). |
| Add a count summary above the tiles | "3/5 seats facing the front" in bold, so the lecturer doesn't have to count tiles. |

### 6.5 "What changed" Event Feed

**Current state:** A list of live alerts (cluster looking away, class facing dipped) with timestamps.

**Issues identified:**
- The feed scrolls off-screen. If the seat map and camera preview are large, alerts are below the fold.
- Alert items are plain text with a bold label. No visual severity indicator.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Float the event feed to the right sidebar | On desktop, place it in a sticky side panel next to the seat map, so it's always visible. On mobile, keep it below. |
| Add severity indicator | Use left border colour: amber for cluster patterns, red for class-wide dips. |
| Limit to 5 most recent, with "Show all" | Avoid an endlessly growing list during a long lecture. |

---

## 7. Topics & Modes (`/sessions/:id/live`)

### 7.1 Layout

**Current state:** Full-page layout with header (title + clock), active topic display, new topic form, teaching mode switcher, and two lists (topics, mode changes).

**Issues identified:**
- This page is designed to be used *during* a live lecture, but it requires navigating away from the Console/Hub where the camera preview is. The lecturer loses visual feedback.
- The clock on this page is a wall-clock elapsed timer, but it's redundant with the Console's clock.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Consider inline panel instead of separate page | On desktop, the Topics & Modes controls could be a collapsible side panel or modal overlay on the Console page. This keeps the camera preview visible while adding markers. |
| If kept as a separate page, add a mini-status bar | Show a compact strip at the top: `Session: trial12 · LIVE · 01:45 elapsed · Faced front: 72%`. This gives context without the full cockpit. |

### 7.2 Topic Form

**Current state:** Single text input + "Add topic" button. Simple and functional.

**No major issues.** Works well for the use case.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Add recent topics as quick-add chips | If the lecturer frequently reuses topic names across sessions (e.g. "Q&A", "Worked example"), show a row of recent labels they can tap to re-add. |
| Auto-focus the input | Already uses `autoComplete="off"` — also add `autoFocus` when this page loads (already `true` in wizard; add here too). |

### 7.3 Teaching Mode Switcher

**Current state:** Horizontal button group with mode names and descriptions. Active mode is highlighted.

**No major issues.** The mode buttons are clear and the hint text is helpful.

**Minor refinement:** Show the timestamp of the last mode change inline: "Active since 00:45" next to the active button.

### 7.4 Topic / Mode Lists

**Current state:** Two side-by-side panels showing recorded topics and mode changes in reverse-chronological order.

**No major issues.** Clean and functional.

**Minor refinement:** Add a subtle animation when a new entry is added (fade-in from top) so the lecturer gets feedback that their action was recorded.

---

## 8. Review / Results (`/sessions/:id/results`)

This is the most data-dense page and arguably the most important for the lecturer's reflection workflow.

### 8.1 Story Banner ("In plain words")

**Current state:** A tinted card with a kicker, lead sentence, and detail line summarising the session.

**Excellent UX pattern.** The "In plain words" approach is the strongest element of the entire interface.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Use a slightly larger font for the lead | Bump from `text-lg` to `text-xl` to ensure it's the first thing read on the page. |
| Add an emoji or icon | A subtle 📊 or chart icon next to "In plain words" to differentiate this card from error/warning banners. |

### 8.2 How-to-Read Guide (3 cards)

**Current state:** Three numbered cards: "Big number", "Chart", "Click a block". Explains the page.

**Issues identified:**
- This guide is shown on every visit. Experienced users don't need it.
- The numbering (1, 2, 3) implies a sequence, but users can interact with any element in any order.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Make dismissible | Add a small `×` to hide the guide, stored in `localStorage`. Show a "How to read this page" link in the toolbar to re-show it. |
| Change framing | Instead of numbered steps, use descriptive labels: "The big number", "The timeline", "The detail panel". |

### 8.3 KPI Block (Hero metric + Evidence chips)

**Current state:** A 2-column grid: hero KPI (Faced the teaching area: 67%) on the left, 4 evidence chips on the right.

**Issues identified:**
- The hero metric label says "Faced the teaching area" but the description below says "Average for clear time blocks only. This is not attention, grades, or who was 'good.'" The caveat is crucial but buried.
- "Camera could measure: 33%" — a low number here is alarming but the user may not understand why. There's no "what to do about it" hint.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add a quality indicator to the hero | If `mean_coverage < 50%`, show an amber warning icon next to the hero value: "⚠ Low camera clarity — results are based on limited data." |
| Make evidence chips interactive | Clicking "Camera could measure: 33%" could scroll to or highlight the grey (insufficient) blocks on the timeline chart. |
| Add context to "Longer drops: 0" | Show "No sustained dips detected ✓" in green instead of just "0". For non-zero, show "2 moments worth reviewing" with a scroll link. |

### 8.4 TTOI Timeline Chart

**Current state:** An SVG area chart with teal (measured) and grey-hatched (insufficient coverage) segments. Clickable segments update the side panel.

**Issues identified:**
- The y-axis label "Faced front %" is small and hard to read.
- There's no hover tooltip. The user must click to see details.
- The chart has no grid lines, making it hard to estimate values visually.
- Topic start markers (vertical lines) are very subtle.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add hover tooltips | On mouseover of a segment, show a floating tooltip: "00:00–00:30 · 67% faced front · 100% clear". |
| Add horizontal grid lines | Subtle dashed lines at 25%, 50%, 75%, 100% with labels on the y-axis. |
| Make topic markers more visible | Use a thicker line (2 px) with a small label flag at the top of the chart: "Topic: Intro to Bayes". |
| Add a highlighted band for "good" range | A subtle teal background band between 60–100% to show the "healthy" zone. |

### 8.5 Secondary Charts (Looking down, Hand raises)

**Current state:** Two side-by-side charts (head-down ratio, hand-raise count) in a 2-column grid.

**Issues identified:**
- These charts often have very little data (flat lines near zero). They take up significant space for low-information content.
- The "Show looking-down & hand-raises" checkbox in the toolbar defaults to checked.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Default to collapsed | Change `showSecondary` initial state to `false`. The TTOI timeline is the primary chart. Secondary cues are supplementary. |
| Combine into a single multi-line chart | If both share the same time axis, overlay them as two line series on one chart. This halves the vertical space. |

### 8.6 Longer Drops Table

**Current state:** A table inside a card showing decline events with time, duration, depth, coverage, topic, and mode.

**Issues identified:**
- "Depth: 12.3" — this number has no unit or context. Is 12 a lot? A little?
- Empty state text is clear but could be more encouraging.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add depth context | Show depth as "12 pts below recent" or use a severity label: "Mild dip" / "Significant drop" based on the threshold from `configs/default.yaml`. |
| Add feedback buttons inline | Currently feedback (Useful / False alarm / Insufficient) is only in the side panel. Add small icons (👍 / 🚫) directly in the table row for faster annotation. |

### 8.7 Selected Half-Minute Side Panel

**Current state:** A sticky sidebar showing details for the clicked time block, including per-seat orientation, mode, topic, and quality.

**Excellent UX.** This is well-structured with a clear data hierarchy.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Transition effect | Add a subtle slide-in animation when the panel content changes to signal the update. |
| Highlight the corresponding chart segment | When a half-minute is selected, add a highlighted border or glow to that segment on the chart. (Partially implemented via `selected` class — make it more obvious.) |
| Add "Previous / Next" navigation | Small arrow buttons (← →) to step through time blocks without clicking the chart. |

---

## 9. Setup (`/sessions/:id/setup`)

### 9.1 Overall Layout

**Current state:** Tab bar (Upload / Webcam / Phone) with content panels. Functional and clear.

**Issues identified:**
- The page header has a lot of text. The "kicker" + subtitle + description + webcam-already-saved CTA is dense.
- The status chip + "Video on disk" / "No file" text in the header is useful but could be more scannable.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Simplify header | One line: "Attach a video source for **{session.title}** · {room.name}". Move the status info into a compact strip below. |
| Show active source tab prominently | If the session already has a source saved, highlight that tab with a checkmark badge. |

### 9.2 Upload Dropzone

**Current state:** A styled dropzone with icon, text, file input, and progress bar.

**No major issues.** The dropzone is well-implemented.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Show file info after upload | When video is on disk, show filename, size, and upload date in a compact info bar — not just `code` path text. |
| Add "Re-upload" option | Instead of requiring purge → re-upload, allow direct re-upload with a confirmation. |

---

## 10. Export & Retention (`/sessions/:id/export`)

### 10.1 Layout

**Current state:** Two panels (Download CSV, Purge raw video) with a privacy strip.

**Issues identified:**
- The page is sparse. Two panels on a full-width layout look lonely.
- The purge modal is well-designed but the "Purge video" button is in a secondary style that doesn't communicate the destructive nature of the action.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Constrain page width | Add `max-width: 40rem` to the page container for a focused, form-like layout. |
| Use a more deliberate purge button style | Change from `btn-secondary` to `btn-danger` (or a red-tinted secondary) to communicate risk. |
| Add CSV preview | Before downloading, show a quick preview table (first 3-4 rows of what the CSV will contain) so the lecturer knows what they're exporting. |

---

## 11. Pulse QR (`/sessions/:id/pulse`)

### 11.1 Layout

**Current state:** QR code on the left, class link + instructions on the right.

**No major issues.** The layout is clean and purposeful.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Make QR code larger | Increase from 200 px to 280 px for projector visibility (this page is meant to be shown to a class). |
| Add a full-screen mode | A button that toggles the page into a centred, large QR + URL overlay for classroom projection. |
| Show pulse response count | If the API supports it, show a live counter: "3 responses received" — this confirms to the lecturer that students are submitting. |

---

## 12. Pulse Public (`/pulse/:id`)

### 12.1 Layout

**Current state:** Centred card with brand mark, title, 1–5 score buttons, submit, and privacy link.

**No major issues.** This is clean, mobile-first, and appropriate for a student-facing page.

**Minor refinements:**

| Change | Detail |
|--------|--------|
| Add descriptive anchors to scores | Below the 1–5 buttons, show `1 = Not clear` and `5 = Very clear` as scale anchors. |
| Success animation | Replace the plain "Thank you" text with a brief checkmark animation or green feedback to create a satisfying interaction. |

---

## 13. Rooms List (`/rooms`)

### 13.1 Table

**Current state:** Simple table: Name, Seats, Target (Set / —), Edit link.

**Issues identified:**
- "Target: Set" vs "—" gives no information about what the target is.
- No indication of which rooms are actively used by sessions.
- No delete action.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add session count column | "3 sessions" next to each room shows usage. Helps the lecturer understand which rooms are active. |
| Change "Target" to a status indicator | Use a green checkmark for "Set" and a yellow warning icon for "Missing" — a missing target means analysis will not work correctly. |
| Add room deletion (with guard) | Allow deletion of rooms with 0 sessions. For rooms with sessions, show "Cannot delete — used by N sessions". |

---

## 14. Room Editor (`/rooms/:id/edit`)

**Not examined in reference images.** The existing `RoomEditorPage` handles seat region drawing on a calibration frame.

**General recommendations:**

| Change | Detail |
|--------|--------|
| Add an onboarding overlay | On first visit, show numbered tooltips: "1. Draw seat rectangles", "2. Set the teaching target", "3. Save". |
| Show seat count in real-time | As the user draws regions, update a counter: "4 seats drawn". |

---

## 15. Settings (`/settings`)

### 15.1 Layout

**Current state:** Two panels: Account (username, logout) and Workspace (API URL, version, worker type, app version).

**Issues identified:**
- The page is minimal and feels like a placeholder ("Account and workspace hints for demos (MVP)").
- Thresholds reference (`configs/default.yaml`) is a developer-facing detail that shouldn't be in a user-facing page.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Remove developer references | Hide API URL, worker type, and yaml config references. Or place them behind a "Developer info" disclosure. |
| Add useful settings | If technically feasible: default privacy checkbox state, preferred source type, notification preferences. |
| Improve the logout experience | Instead of a plain `ghost-btn`, use a `btn-secondary` with a `LogOut` icon and confirmation: "Are you sure you want to log out?" |

---

## 16. Privacy (`/app/privacy`)

### 16.1 Content

**Current state:** A bulleted list of privacy principles + a contact placeholder.

**Issues identified:**
- The content is important but reads like a flat text document. No structure beyond a `<ul>`.
- The "replace this placeholder" text is a development artifact.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Structure with sections | Use cards or sections: "What we process", "What we don't do", "Data retention", "Contact". |
| Remove placeholder text | Replace "replace this placeholder before public deployment" with actual contact information or remove the paragraph. |
| Add a visual diagram | A simple mermaid flow: `Video → Local Processing → Aggregates Stored → Video Purged`. This communicates the pipeline at a glance. |

---

## 17. Responsive & Mobile Behaviour

### 17.1 Current Breakpoints

| Breakpoint | Shell behaviour |
|------------|-----------------|
| ≥ 1400 px | Full layout, wider stage padding |
| 1200–1399 px | Icon-rail sidebar |
| 720–1199 px | Icon-rail sidebar, reduced padding |
| < 720 px | Horizontal nav bar, stacked layout |

**Issues identified:**
- The session hub page has a 4-column KPI chip grid that collapses to 2 columns at 1100 px and 1 column at 520 px. This is good, but the live cockpit's `cockpit-grid` doesn't have explicit responsive rules.
- The Results page's side panel (`window-panel`) becomes `position: static` below 1100 px, which loses the sticky context during scrolling.
- Tables on mobile have no horizontal scroll indicator.

**Recommendations:**

| Change | Detail |
|--------|--------|
| Add mobile cockpit layout | Below 720 px, stack the preview and metrics panel vertically. Hide the seat map behind a disclosure. |
| Add scroll indicators for tables | On mobile, add a subtle gradient or shadow on the right edge of horizontally scrollable tables to indicate more content. |
| Test Results page at 768–1024 px (tablet) | The 2-column Results layout with the sticky panel may not fit. Consider switching to a tabbed layout (Chart / Detail) on tablets. |

---

## 18. Cross-Cutting UX Patterns

### 18.1 Loading States

**Current state:** Most pages show `<p>Loading…</p>` as plain text.

**Recommendation:** Replace with skeleton screens. For tables, show 3–4 grey pulsing rows. For charts, show a grey rectangle. This signals structure and reduces perceived load time.

### 18.2 Error States

**Current state:** Red text paragraphs (`sessions-error` class) with API error messages.

**Recommendation:** Wrap errors in a card with a red left border (like `privacy-strip` but red), an error icon, and a "Retry" button where applicable.

### 18.3 Success Feedback

**Current state:** Some pages show green text (`export-ok`, `setup-ok`) that appears and stays until the next action.

**Recommendation:** Use a toast notification that auto-dismisses after 5 seconds. This avoids stale success messages.

### 18.4 Confirmation Dialogs

**Current state:** Uses `window.confirm()` for destructive actions (delete session, purge video).

**Recommendation:** Replace with styled modal dialogs (like the existing purge modal) for all destructive actions. `window.confirm()` is inconsistent across browsers and cannot be styled.

### 18.5 Privacy Strips

**Current state:** A teal-bordered grey strip appears at the bottom of Sessions, Rooms, Console, Export, and Pulse Setup pages. Each has slightly different text.

**Issues identified:**
- Repetitive. The lecturer sees 5+ privacy disclaimers across pages. This creates banner blindness and adds visual clutter.

**Recommendation:** Show the privacy strip only on the Sessions list (first landing page) and Export (where data leaves the system). Remove it from other pages. Add a persistent footer link "Privacy notice" in the sidebar instead.

### 18.6 Keyboard Navigation

**Current state:** Focus rings are defined (`focus-ring`) and `focus-visible` is styled for nav links and ghost buttons.

**Recommendation:** Ensure all interactive elements (table rows, chart segments, mode buttons, score buttons) have `focus-visible` outlines. Test with Tab key through the entire session flow.

### 18.7 Consistent Terminology

Use these terms consistently across the interface:

| Use this | Instead of |
|----------|------------|
| "Faced the front" | "Faced the teaching area", "Target oriented", "TTOI" |
| "Camera clarity" | "Camera clear", "Coverage", "Could measure" |
| "Time block" | "Window", "Half-minute" |
| "Orientation drop" | "Decline event", "Longer drop" |
| "Live session" | "Live lecture", "Running" |
| "Review" | "Results", "Analysis" |

---

## Summary of Priority Recommendations

| Priority | Area | Impact |
|----------|------|--------|
| 🔴 High | Session Hub: Next-action prompts & hero metric | Reduces confusion during live lectures |
| 🔴 High | Loading states → skeleton screens | Professional feel, reduced perceived latency |
| 🔴 High | Delete actions → proper modals | Prevents accidental data loss |
| 🟡 Medium | Consistent terminology | Reduces cognitive load across all pages |
| 🟡 Medium | Reduce privacy strip repetition | Reduces clutter, avoids banner blindness |
| 🟡 Medium | Results chart tooltips + grid lines | Makes the timeline chart self-explanatory |
| 🟡 Medium | Session table: clickable rows + quick metric | Faster navigation, better overview |
| 🟢 Low | Dismissible "How to read" guide | Small improvement for repeat users |
| 🟢 Low | Pulse QR full-screen mode | Nice-to-have for classroom projection |
| 🟢 Low | Toast notifications | Polish for success/error feedback |

---

*Document prepared for VIGILENS — A Clearer Lens on Learning.*
*Based on analysis of 11 reference screenshots, all page source code (14 pages, 6+ components), CSS stylesheets, design tokens, and project documentation.*
