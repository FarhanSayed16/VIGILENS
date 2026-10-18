# Orientation annotation guide (pilot)

Annotators label **what is visible** about body/head orientation toward the teaching target.  
They do **not** judge emotion, attention, boredom, or student quality.

## Allowed labels (examples)

| label | Meaning |
|---|---|
| `orientation_decline` | Clear multi-seat / class-level turn-away or head-down cluster vs prior facing |
| `visible_yaw_away` | Many seats facing clearly away from board/target |
| `head_down_cluster` | Many heads down (use mode context: note_taking may be expected) |
| `unobservable_stretch` | Too dark / occluded / far to judge |

## Forbidden

`bored`, `distracted`, `lazy`, `not paying attention`, emotion words, grades, names.

## CSV format

```csv
start_sec,end_sec,label,note
310,350,orientation_decline,Visible yaw-away across front rows
```

Example file: `tests/fixtures/pilot/human_marks_example.csv`

## Timing

Compare to machine `events` with **±30 seconds** honesty (`worker/scripts/compare_declines.py`).
