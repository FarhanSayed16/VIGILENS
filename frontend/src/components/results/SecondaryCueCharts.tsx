import { motion } from "framer-motion";
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
  const data = windows.map((w) => ({
    t: (w.start_sec + w.end_sec) / 2,
    head_down: w.head_down_cue_pct,
    hand_raise: w.hand_raise_events ?? 0,
  }));

  return (
    <div className="secondary-charts">
      <motion.div
        className="chart-card"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08, duration: 0.3 }}
      >
        <h2>Head-down cue rate</h2>
        <p className="chart-sub">
          Observable cue share — not a boredom or attention score.
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
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.14, duration: 0.3 }}
      >
        <h2>Hand-raise events</h2>
        <p className="chart-sub">Counts per window — separate from TTOI.</p>
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
