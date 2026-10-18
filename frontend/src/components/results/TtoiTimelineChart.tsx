import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DeclineEvent, WindowPoint } from "../../api/results";
import type { Topic } from "../../api/topics";
import { formatElapsed } from "../../api/topics";

export type ChartRow = {
  t: number;
  ttoi: number | null;
  ttoi_lo: number | null;
  ttoi_hi: number | null;
  coverage_pct: number | null;
  windowId: number;
  label: string;
};

type Props = {
  windows: WindowPoint[];
  events: DeclineEvent[];
  topics: Topic[];
  selectedWindowId: number | null;
  onSelectWindow: (id: number) => void;
  lowCoverageThreshold?: number;
};

function mergeLowCoverageSpans(
  windows: WindowPoint[],
  threshold: number,
): { x1: number; x2: number }[] {
  const spans: { x1: number; x2: number }[] = [];
  let cur: { x1: number; x2: number } | null = null;
  for (const w of windows) {
    const low =
      w.coverage_pct != null &&
      w.coverage_pct < threshold &&
      (w.data_quality_note === "insufficient_coverage" ||
        w.coverage_pct < threshold);
    if (low) {
      if (!cur) cur = { x1: w.start_sec, x2: w.end_sec };
      else cur.x2 = w.end_sec;
    } else if (cur) {
      spans.push(cur);
      cur = null;
    }
  }
  if (cur) spans.push(cur);
  return spans;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ChartRow }[];
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "0.5rem 0.75rem",
        fontSize: 12,
        boxShadow: "var(--shadow-soft)",
      }}
    >
      <div style={{ fontWeight: 650, marginBottom: 4 }}>{row.label}</div>
      <div>TTOI: {row.ttoi != null ? row.ttoi.toFixed(1) : "—"}</div>
      <div>
        Band:{" "}
        {row.ttoi_lo != null && row.ttoi_hi != null
          ? `${row.ttoi_lo.toFixed(0)}–${row.ttoi_hi.toFixed(0)}`
          : "—"}
      </div>
      <div>
        Coverage:{" "}
        {row.coverage_pct != null ? `${row.coverage_pct.toFixed(0)}%` : "—"}
      </div>
    </div>
  );
}

export function TtoiTimelineChart({
  windows,
  events,
  topics,
  selectedWindowId,
  onSelectWindow,
  lowCoverageThreshold = 70,
}: Props) {
  const data: ChartRow[] = useMemo(
    () =>
      windows.map((w) => ({
        t: (w.start_sec + w.end_sec) / 2,
        ttoi: w.ttoi,
        ttoi_lo: w.ttoi_lo,
        ttoi_hi: w.ttoi_hi,
        coverage_pct: w.coverage_pct,
        windowId: w.id,
        label: `${formatElapsed(w.start_sec)}–${formatElapsed(w.end_sec)}`,
      })),
    [windows],
  );

  const domainX = useMemo((): [number, number] => {
    if (!windows.length) return [0, 60];
    const max = Math.max(...windows.map((w) => w.end_sec));
    return [0, Math.max(60, max)];
  }, [windows]);

  const lowSpans = useMemo(
    () => mergeLowCoverageSpans(windows, lowCoverageThreshold),
    [windows, lowCoverageThreshold],
  );

  const selected = windows.find((w) => w.id === selectedWindowId);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      style={{ width: "100%", height: 320 }}
    >
      <ResponsiveContainer>
        <ComposedChart
          data={data}
          margin={{ top: 12, right: 12, left: 0, bottom: 8 }}
          onClick={(state) => {
            const id = (
              state?.activePayload?.[0]?.payload as ChartRow | undefined
            )?.windowId;
            if (id != null) onSelectWindow(id);
          }}
        >
          <defs>
            <pattern
              id="lowCoverageHatch"
              width="6"
              height="6"
              patternUnits="userSpaceOnUse"
              patternTransform="rotate(-45)"
            >
              <rect width="6" height="6" fill="#e8eef2" />
              <line
                x1="0"
                y1="0"
                x2="0"
                y2="6"
                stroke="#94a3b8"
                strokeWidth="2"
              />
            </pattern>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#d5dee6" />
          <XAxis
            dataKey="t"
            type="number"
            domain={domainX}
            tickFormatter={(v) => formatElapsed(Number(v))}
            stroke="#5a6b7d"
            fontSize={11}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#5a6b7d"
            fontSize={11}
            width={36}
            label={{
              value: "TTOI",
              angle: -90,
              position: "insideLeft",
              style: { fill: "#5a6b7d", fontSize: 11 },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {lowSpans.map((s, i) => (
            <ReferenceArea
              key={`low-${i}`}
              x1={s.x1}
              x2={s.x2}
              y1={0}
              y2={100}
              fill="url(#lowCoverageHatch)"
              strokeOpacity={0}
              ifOverflow="extendDomain"
            />
          ))}

          {events.map((e) => (
            <ReferenceArea
              key={`ev-${e.id}`}
              x1={e.start_sec}
              x2={e.end_sec}
              y1={0}
              y2={100}
              fill="rgba(194, 120, 3, 0.18)"
              stroke="rgba(194, 120, 3, 0.45)"
              strokeOpacity={0.6}
            />
          ))}

          {topics.map((t) => (
            <ReferenceLine
              key={`topic-${t.id}`}
              x={t.start_sec}
              stroke="#5a6b7d"
              strokeDasharray="4 3"
              label={{
                value: t.label.length > 18 ? `${t.label.slice(0, 16)}…` : t.label,
                position: "insideTopLeft",
                fill: "#5a6b7d",
                fontSize: 10,
              }}
            />
          ))}

          {selected ? (
            <ReferenceArea
              x1={selected.start_sec}
              x2={selected.end_sec}
              y1={0}
              y2={100}
              fill="rgba(15, 118, 110, 0.08)"
              stroke="#0f766e"
              strokeOpacity={0.5}
            />
          ) : null}

          <Area
            type="monotone"
            dataKey="ttoi_hi"
            stroke="none"
            fill="rgba(15, 118, 110, 0.2)"
            isAnimationActive
            animationDuration={500}
          />
          <Area
            type="monotone"
            dataKey="ttoi_lo"
            stroke="none"
            fill="var(--bg-surface)"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="ttoi"
            stroke="#0f766e"
            strokeWidth={2.25}
            dot={{ r: 3, strokeWidth: 0, fill: "#0f766e" }}
            activeDot={{ r: 5, fill: "#0d9488" }}
            isAnimationActive
            animationDuration={550}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
