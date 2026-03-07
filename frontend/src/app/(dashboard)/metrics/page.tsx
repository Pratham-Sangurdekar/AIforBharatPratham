"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Activity, PieChart as PieIcon } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import { getMetrics } from "@/services/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

/* ------------------------------------------------------------------ */
/*  Mock metrics data                                                  */
/* ------------------------------------------------------------------ */
const MOCK_METRICS = {
  total_analyses: 24,
  avg_virality_score: 67.3,
  score_over_time: Array.from({ length: 12 }, (_, i) => ({
    date: new Date(Date.now() - (11 - i) * 86400000).toLocaleDateString(),
    score: Math.round(40 + Math.random() * 45),
  })),
  engagement_data: Array.from({ length: 12 }, (_, i) => ({
    date: new Date(Date.now() - (11 - i) * 86400000).toLocaleDateString(),
    likes: Math.round(500 + Math.random() * 2000),
    shares: Math.round(100 + Math.random() * 500),
    comments: Math.round(20 + Math.random() * 150),
  })),
  content_distribution: [
    { type: "text", count: 14 },
    { type: "image", count: 6 },
    { type: "video", count: 3 },
    { type: "audio", count: 1 },
  ],
  score_distribution: [
    { range: "0-20", count: 1 },
    { range: "21-40", count: 3 },
    { range: "41-60", count: 7 },
    { range: "61-80", count: 9 },
    { range: "81-100", count: 4 },
  ],
};

const COLORS = ["#1a237e", "#ff6d00", "#4caf50", "#f44336", "#9c27b0"];
const PIE_COLORS = ["#283593", "#ff9100", "#66bb6a", "#ef5350"];

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMetrics()
      .then(setMetrics)
      .catch(() => setMetrics(MOCK_METRICS))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
      </div>
    );
  }

  const data = metrics || MOCK_METRICS;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <GlassCard>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[var(--color-primary)]/20 p-3">
                <BarChart3 className="h-5 w-5 text-[var(--color-accent)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)]">Total Analyses</p>
                <p className="text-2xl font-bold">{data.total_analyses}</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <GlassCard>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[var(--color-primary)]/20 p-3">
                <TrendingUp className="h-5 w-5 text-[var(--color-accent)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)]">Avg Virality Score</p>
                <p className="text-2xl font-bold">{data.avg_virality_score}</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <GlassCard>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[var(--color-primary)]/20 p-3">
                <Activity className="h-5 w-5 text-[var(--color-accent)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)]">High Performers</p>
                <p className="text-2xl font-bold">
                  {data.score_distribution.find((d: any) => d.range === "81-100")?.count || 0}
                </p>
              </div>
            </div>
          </GlassCard>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <GlassCard>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[var(--color-primary)]/20 p-3">
                <PieIcon className="h-5 w-5 text-[var(--color-accent)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)]">Content Types</p>
                <p className="text-2xl font-bold">{data.content_distribution.length}</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Virality Score Over Time */}
        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Virality Score Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.score_over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: "#888899" }}
                tickFormatter={(v: string) => v.split("/").slice(0, 2).join("/")}
              />
              <YAxis tick={{ fontSize: 10, fill: "#888899" }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: "#111118",
                  border: "1px solid #1e1e2e",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#ff6d00"
                strokeWidth={2}
                dot={{ fill: "#ff6d00", r: 4 }}
                activeDot={{ r: 6, fill: "#ff9100" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* Predicted Engagement */}
        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Predicted Engagement</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.engagement_data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: "#888899" }}
                tickFormatter={(v: string) => v.split("/").slice(0, 2).join("/")}
              />
              <YAxis tick={{ fontSize: 10, fill: "#888899" }} />
              <Tooltip
                contentStyle={{
                  background: "#111118",
                  border: "1px solid #1e1e2e",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Bar dataKey="likes" fill="#283593" radius={[4, 4, 0, 0]} />
              <Bar dataKey="shares" fill="#ff6d00" radius={[4, 4, 0, 0]} />
              <Bar dataKey="comments" fill="#4caf50" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Content Type Distribution */}
        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Content Type Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={data.content_distribution}
                dataKey="count"
                nameKey="type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.content_distribution.map((_: any, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "#111118",
                  border: "1px solid #1e1e2e",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* Score Distribution */}
        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.score_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
              <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#888899" }} />
              <YAxis tick={{ fontSize: 10, fill: "#888899" }} />
              <Tooltip
                contentStyle={{
                  background: "#111118",
                  border: "1px solid #1e1e2e",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.score_distribution.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>
    </div>
  );
}
