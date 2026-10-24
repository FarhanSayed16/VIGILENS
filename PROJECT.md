# VIGILENS — what this project is

**A clearer lens on learning.**  
A local classroom tool that shows a lecturer *when* the class, as a group, was facing the teaching area, *how much of that reading the camera could actually see*, and *which topic* was being taught — without naming students or grading anyone.

| | |
|---|---|
| **Status** | MVP complete (Phases 1–24, Checkpoints A / B / C). Live lecture cockpit added after that. |
| **Runs on** | One Windows PC. Video stays on the machine. |
| **Date of this note** | 24 October 2026 |

---

## What we are actually trying to achieve

A lecturer cannot watch 40–100 faces and teach at the same time. After class they often remember only that “a section dragged.” They cannot say:

- **which minutes** the room’s visible behaviour shifted
- whether that happened during **a particular topic**, a long explanation, or note-taking
- whether the **camera even saw enough people** for that reading to mean anything

VIGILENS exists so the lecturer can review the lecture with evidence, then change pacing, examples, or breaks next time.

The research question we can defend:

> Can a fixed classroom camera give a reliable, privacy-preserving, class-level trend of *observable* facing-the-front, and can that trend — lined up with lecture topics — point a lecturer at time windows worth reviewing?

That is the goal. A number on a dashboard is only useful if the lecturer trusts when the camera could not see the room.

---

## The exact idea

A camera cannot measure attention, interest, boredom, or learning. Those are inside a person’s head. A camera can only see **behaviour**:

- Are bodies and heads broadly turned toward the board, the lecturer, or the screen?
- Are many heads down for a long stretch?
- Did hands go up during a question period?

So the product estimates **class-level observable orientation**, finds **candidate drops** in that orientation, attaches them to **topics and teaching modes**, and always shows **how much of the room was measurable**.

The main number is **TTOI** (Teaching-Target Orientation Index): the share of measurable people facing the teaching target in a time block. In the lecturer UI this is written in plain language as **“faced the front”** / **“faced the teaching area.”**

Three questions the system answers after a lecture:

1. **When** did visible orientation change?
2. **How reliable** was that reading (coverage)?
3. **Which topic** was active then?

### What it is

- A teaching-reflection tool for one lecturer
- Class-level only: one trend for the room, not a list of “bad students”
- Honest about weak video: grey / low coverage means “could not measure,” not a score of zero
- Context-aware: note-taking mode does not treat looking down as failure
- Privacy-first: local processing, no face recognition, no stored face crops, raw video can be purged after analysis

### What it is not

- Mind-reading, emotion AI, or a boredom detector
- Face recognition, attendance, or named rankings
- A grade, or proof that looking at the board means the student learned
- A claim to be the first “attention detector” — classroom camera studies already exist; the contribution is the combination below

### What is actually different

1. Transparent orientation (TTOI), not a fake attention score
2. Coverage shown as a first-class result
3. Class-level product only
4. Fixed seat boxes; no identity carried from one lecture to the next
5. Teaching modes (explanation, note-taking, Q&A)
6. Topic markers on the same timeline as candidate drops
7. A real application (API + database + UI), not a one-off notebook

---

## How a session works

```text
Webcam, phone stream, or uploaded MP4
        │
        ▼
Lecturer UI (React)  ── REST + login ──►  API (FastAPI)
                                              │
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                    PostgreSQL              Redis            Vision worker
                    rooms, sessions,     live snapshot,      YOLOv8-pose people
                    windows, events      job lock, preview   + head pose
                         ▲                    │                    │
                         └────────────────────┴────────────────────┘
                                        30-second blocks
                                        TTOI + coverage + drops
```

1. The lecturer draws **seat boxes** and a **teaching target** on a room still.
2. They start a session from the webcam (or an uploaded clip), mark **topics** and **mode** (explaining, students writing, questions).
3. The worker finds people, assigns them to drawn seats, and adds temporary **Extra** slots for people outside those boxes. Seats stay anonymous (`s1`, `Extra 1`). Nothing is a name.
4. Every ~30 seconds it writes: how many faced the teaching area, how many seats were clear enough to measure, and whether a longer class-level drop started.
5. **Stop** finalizes the run. **Review** shows the story, the chart, and a click-into-a-block view of that half-minute.

Green = facing the front. Amber = mixed. Red = looking away for a sustained stretch. Grey = the camera could not measure that seat.

---

## What we have done

### Product (MVP, signed off 18 October 2026)

- Lecturer login
- Rooms: reusable seat regions and teaching-target geometry
- Sessions: create, upload or choose a camera, mark topics and teaching modes
- Analysis job: fake numbers for UI tests, or real vision on a clip
- Review: class orientation over time, coverage, candidate declines, topics
- CSV export, purge of raw video, anonymous student pulse (QR)
- Privacy copy and limitation docs so reports do not over-claim
- Sample-clip demo path (a full consented classroom fill-in is optional and is not the same as proven classroom accuracy)

### Live lecture (after the MVP)

The lecturer can **Start → watch the room → Stop → Review** without uploading a file first:

- Live camera preview with seat boxes and person highlights (anonymous)
- People count and “faced the front” updating while the lecture runs
- Seat map and a short “what changed” feed
- Windows saved as they complete; declines finalized on Stop
- Optional second camera for looking only — numbers always come from the primary camera
- Review and live screens rewritten in plain language so TTOI / ROI jargon is not what the lecturer has to read

### Engineering path (why it was built this way)

The app was finished with a **fake worker** first, so login, rooms, charts, and export worked before vision was reliable. Real YOLO and head-pose then plugged into the **same job and results shape**. The UI did not have to be rewritten when the models arrived.

---

## What we used

| Layer | Choice | Role |
|---|---|---|
| Frontend | React 18, TypeScript, Vite | Lecturer app |
| Routing / charts / motion | React Router, Recharts, Framer Motion, Lucide | Pages, timeline, icons |
| API | FastAPI, Uvicorn, Pydantic | REST, validation |
| Auth | JWT (`python-jose`), Passlib | Single lecturer login |
| Database | PostgreSQL 16, SQLAlchemy, Alembic, psycopg | Rooms, sessions, windows, events |
| Cache / live state | Redis 7 | Job lock, live snapshot, JPEG preview |
| Containers | Docker Compose | Postgres + Redis only |
| Vision | OpenCV, NumPy | Frames, geometry, overlay |
| People | Ultralytics YOLOv8-pose (`yolov8n-pose`) | Bodies and keypoints, not faces-as-identity |
| Head pose | MediaPipe Face Landmarker | Yaw / pitch when the face is large enough |
| Rules | Our own code (`aggregation`, `drop_events`) | 30s TTOI, coverage gates, candidate declines |
| Tests | pytest | Unit tests and API journeys |
| Language / runtime | Python 3.12, Node 18+ | Backend, worker, frontend |

No custom-trained “engagement” network. Stage A is **pose models plus rules**. A later classifier (Stage B), OpenVINO, PDF export, and WebSocket job progress were left out of the MVP on purpose.

---

## What “done” means — and what it does not

**Done:** a lecturer can run the stack locally, hold a live or uploaded session, and read a class-level timeline that says when people faced the teaching area and when the camera could not tell.

**Not done, and not claimed:**

- The percentage is not attention, emotion, or a grade
- Short clips and poor light often produce “could not measure”; that is correct behaviour, not a bug to hide
- One camera, one lecturer account, one analysis at a time
- Sample-clip tests are not a published accuracy number for a real 60-person hall
- Seat boxes must match the camera. People outside them show up as Extra seats, still unnamed

---

## One-line summary

VIGILENS tells a lecturer **when the class faced the teaching area, when the camera could not see enough to say, and which topic was on** — on their own computer, without identifying a single student.
