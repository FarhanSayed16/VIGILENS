import { useCallback, useLayoutEffect, useRef, useState } from "react";
import type { BoxRegion } from "../../api/rooms";
import "./seat-canvas.css";

export type DrawTool = "select" | "seat" | "target" | "click_target";

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

type StageBox = { left: number; top: number; width: number; height: number };

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

/** Match CSS object-fit: contain — regions must sit on the image, not letterbox bars. */
function containedStage(
  wrapW: number,
  wrapH: number,
  natW: number,
  natH: number,
): StageBox {
  if (wrapW <= 0 || wrapH <= 0 || natW <= 0 || natH <= 0) {
    return { left: 0, top: 0, width: wrapW, height: wrapH };
  }
  const nat = natW / natH;
  const box = wrapW / wrapH;
  if (nat > box) {
    const height = wrapW / nat;
    return { left: 0, top: (wrapH - height) / 2, width: wrapW, height };
  }
  const width = wrapH * nat;
  return { left: (wrapW - width) / 2, top: 0, width, height: wrapH };
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
  const imgRef = useRef<HTMLImageElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [stage, setStage] = useState<StageBox>({
    left: 0,
    top: 0,
    width: 0,
    height: 0,
  });

  const recomputeStage = useCallback(() => {
    const wrap = wrapRef.current;
    const img = imgRef.current;
    if (!wrap) return;
    const wr = wrap.getBoundingClientRect();
    if (!img || !img.naturalWidth) {
      setStage({ left: 0, top: 0, width: wr.width, height: wr.height });
      return;
    }
    setStage(
      containedStage(wr.width, wr.height, img.naturalWidth, img.naturalHeight),
    );
  }, []);

  useLayoutEffect(() => {
    recomputeStage();
    const wrap = wrapRef.current;
    if (!wrap || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => recomputeStage());
    ro.observe(wrap);
    return () => ro.disconnect();
  }, [recomputeStage, imageUrl]);

  const toNorm = useCallback(
    (clientX: number, clientY: number) => {
      const el = wrapRef.current;
      if (!el || stage.width < 1 || stage.height < 1) return { x: 0, y: 0 };
      const r = el.getBoundingClientRect();
      const x = (clientX - r.left - stage.left) / stage.width;
      const y = (clientY - r.top - stage.top) / stage.height;
      return { x: clamp01(x), y: clamp01(y) };
    },
    [stage],
  );

  function onPointerDown(e: React.PointerEvent) {
    if (tool === "select") return;
    const p = toNorm(e.clientX, e.clientY);
    if (tool === "click_target") {
      const w = 0.36;
      const h = 0.16;
      const x = Math.min(1 - w, Math.max(0, p.x - w / 2));
      const y = Math.min(1 - h, Math.max(0, p.y - h / 2));
      onTargetChange({
        type: "box",
        id: "teaching_target",
        label: "Board / screen",
        x,
        y,
        w,
        h,
      });
      return;
    }
    (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
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
      className={`seat-canvas${tool !== "select" ? " drawing" : ""}${
        tool === "click_target" ? " click-target" : ""
      }`}
      ref={wrapRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={() => setDrag(null)}
    >
      {imageUrl ? (
        <img
          ref={imgRef}
          src={imageUrl}
          alt="Calibration frame"
          draggable={false}
          onLoad={recomputeStage}
        />
      ) : (
        <div className="seat-canvas-empty">
          Upload a calibration frame (classroom photo or paused video frame)
        </div>
      )}

      {imageUrl && stage.width > 0 ? (
        <div
          className="seat-canvas-stage"
          style={{
            left: stage.left,
            top: stage.top,
            width: stage.width,
            height: stage.height,
          }}
        >
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
      ) : null}
    </div>
  );
}
