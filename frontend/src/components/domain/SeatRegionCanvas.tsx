import { useCallback, useRef, useState } from "react";
import type { BoxRegion } from "../../api/rooms";
import "./seat-canvas.css";

export type DrawTool = "select" | "seat" | "target";

type Props = {
  imageUrl: string | null;
  seats: BoxRegion[];
  target: BoxRegion | null;
  tool: DrawTool;
  selectedSeatId: string | null;
  onSeatsChange: (seats: BoxRegion[]) => void;
  onTargetChange: (target: BoxRegion | null) => void;
  onSelectSeat: (id: string | null) => void;
};

type DragState = {
  startX: number;
  startY: number;
  curX: number;
  curY: number;
};

function clamp01(n: number) {
  return Math.min(1, Math.max(0, n));
}

function normBox(a: DragState): { x: number; y: number; w: number; h: number } {
  const x1 = clamp01(Math.min(a.startX, a.curX));
  const y1 = clamp01(Math.min(a.startY, a.curY));
  const x2 = clamp01(Math.max(a.startX, a.curX));
  const y2 = clamp01(Math.max(a.startY, a.curY));
  return { x: x1, y: y1, w: Math.max(0.01, x2 - x1), h: Math.max(0.01, y2 - y1) };
}

export function SeatRegionCanvas({
  imageUrl,
  seats,
  target,
  tool,
  selectedSeatId,
  onSeatsChange,
  onTargetChange,
  onSelectSeat,
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);

  const toNorm = useCallback((clientX: number, clientY: number) => {
    const el = wrapRef.current;
    if (!el) return { x: 0, y: 0 };
    const r = el.getBoundingClientRect();
    return {
      x: clamp01((clientX - r.left) / r.width),
      y: clamp01((clientY - r.top) / r.height),
    };
  }, []);

  function onPointerDown(e: React.PointerEvent) {
    if (tool === "select") return;
    const p = toNorm(e.clientX, e.clientY);
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    setDrag({ startX: p.x, startY: p.y, curX: p.x, curY: p.y });
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!drag) return;
    const p = toNorm(e.clientX, e.clientY);
    setDrag({ ...drag, curX: p.x, curY: p.y });
  }

  function onPointerUp() {
    if (!drag) return;
    const box = normBox(drag);
    setDrag(null);
    if (box.w < 0.02 || box.h < 0.02) return;

    if (tool === "seat") {
      const id = `seat_${Date.now().toString(36)}`;
      const next: BoxRegion = {
        type: "box",
        id,
        label: `Seat ${seats.length + 1}`,
        ...box,
      };
      onSeatsChange([...seats, next]);
      onSelectSeat(id);
    } else if (tool === "target") {
      onTargetChange({
        type: "box",
        id: "teaching_target",
        label: "Teaching target",
        ...box,
      });
    }
  }

  const preview = drag ? normBox(drag) : null;

  return (
    <div
      className={`seat-canvas${tool !== "select" ? " drawing" : ""}`}
      ref={wrapRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={() => setDrag(null)}
    >
      {imageUrl ? (
        <img src={imageUrl} alt="Calibration frame" draggable={false} />
      ) : (
        <div className="seat-canvas-empty">
          Upload a calibration frame (classroom photo or paused video frame)
        </div>
      )}

      {seats.map((s) => (
        <button
          key={s.id}
          type="button"
          className={`region seat${selectedSeatId === s.id ? " selected" : ""}`}
          style={{
            left: `${s.x * 100}%`,
            top: `${s.y * 100}%`,
            width: `${s.w * 100}%`,
            height: `${s.h * 100}%`,
          }}
          onClick={(e) => {
            e.stopPropagation();
            onSelectSeat(s.id);
          }}
          title={s.label ?? s.id}
        >
          <span>{s.label ?? s.id}</span>
        </button>
      ))}

      {target ? (
        <div
          className="region target"
          style={{
            left: `${target.x * 100}%`,
            top: `${target.y * 100}%`,
            width: `${target.w * 100}%`,
            height: `${target.h * 100}%`,
          }}
        >
          <span>{target.label ?? "Target"}</span>
        </div>
      ) : null}

      {preview ? (
        <div
          className={`region preview ${tool === "target" ? "target" : "seat"}`}
          style={{
            left: `${preview.x * 100}%`,
            top: `${preview.y * 100}%`,
            width: `${preview.w * 100}%`,
            height: `${preview.h * 100}%`,
          }}
        />
      ) : null}
    </div>
  );
}
