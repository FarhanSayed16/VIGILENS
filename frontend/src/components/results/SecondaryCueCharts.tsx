import { motion, useReducedMotion } from "framer-motion";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WindowPoint } from "../../api/results";
import { formatElapsed } from "../../api/topics";

type Props = {
  windows: WindowPoint[];
};

export function SecondaryCueCharts({ windows }: Props) {
  const reduceMotion = useReducedMotion();
  const data = windows.map((w) => ({
    t: (w.start_sec + w.end_sec) / 2,
    head_down: w.head_down_cue_pct,
    hand_raise: w.hand_raise_events ?? 0,
  }));
  const enter = reduceMotion
    ? { initial: false as const, transition: { duration: 0 } }
    : {
        initial: { opacity: 0, y: 8 },
        transition: { delay: 0.08, duration: 0.3 },
      };

  return (
    <div className="secondary-charts">
      <motion.div
        className="chart-card"
        initial={enter.initial}
        animate={{ opacity: 1, y: 0 }}
        transition={enter.transition}
      >
        <h2>Looking down</h2>
        <p className="chart-sub">
          Share of clear samples with head tilted down — posture only, not boredom
          or attention.
        </p>
        <div style={{ width: "100%", height: 160 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d5dee6" />
              <XAxis
                dataKey="t"
                type="number"
                tickFormatter={(v) => formatElapsed(Number(v))}
                fontSize={10}
                stroke="#5a6b7d"
              />
              <YAxis domain={[0, "auto"]} fontSize={10} width={28} stroke="#5a6b7d" />
              <Tooltip
                formatter={(v: number) => [`${Number(v).toFixed(1)}%`, "Head-down"]}
                labelFormatter={(v) => formatElapsed(Number(v))}
              />
              <Line
                type="monotone"
                dataKey="head_down"
                stroke="#64748b"
                strokeWidth={1.75}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      <motion.div
        className="chart-card"
        initial={enter.initial}
        animate={{ opacity: 1, y: 0 }}
        transition={
          reduceMotion
            ? { duration: 0 }
            : { delay: 0.14, duration: 0.3 }
        }
      >
        <h2>Hand raises</h2>
        <p className="chart-sub">
          Raises counted each half-minute — separate from “faced the front.”
        </p>
        <div style={{ width: "100%", height: 160 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d5dee6" />
              <XAxis
                dataKey="t"
                type="number"
                tickFormatter={(v) => formatElapsed(Number(v))}
                fontSize={10}
                stroke="#5a6b7d"
              />
              <YAxis allowDecimals={false} fontSize={10} width={28} stroke="#5a6b7d" />
              <Tooltip
                formatter={(v: number) => [v, "Hand-raises"]}
                labelFormatter={(v) => formatElapsed(Number(v))}
              />
              <Line
                type="stepAfter"
                dataKey="hand_raise"
                stroke="#0d9488"
                strokeWidth={1.75}
                dot={{ r: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  );
}
