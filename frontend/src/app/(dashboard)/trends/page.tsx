"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Hash,
  Globe,
  Flame,
  RefreshCw,
  Clock,
  Zap,
  BarChart3,
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import { getTrends, getPlatformTrends } from "@/services/api";

const POLL_INTERVAL = 60_000; // 60 seconds

const CATEGORY_ICONS: Record<string, typeof TrendingUp> = {
  technology: Globe,
  memes: Flame,
  politics: Hash,
  entertainment: Flame,
  marketing: TrendingUp,
  lifestyle: Hash,
  education: BarChart3,
};

const CATEGORY_COLORS: Record<string, string> = {
  technology: "from-blue-500/20 to-cyan-500/20",
  memes: "from-pink-500/20 to-rose-500/20",
  politics: "from-amber-500/20 to-yellow-500/20",
  entertainment: "from-purple-500/20 to-violet-500/20",
  marketing: "from-green-500/20 to-emerald-500/20",
  lifestyle: "from-orange-500/20 to-red-500/20",
  education: "from-indigo-500/20 to-blue-500/20",
};

const MOCK_PLATFORM_TRENDS: Record<string, any[]> = {
  twitter: [
    { topic: "AI tools taking over", volume: "125K tweets", category: "technology" },
    { topic: "Election debate reactions", volume: "89K tweets", category: "politics" },
    { topic: "New meme format", volume: "67K tweets", category: "memes" },
  ],
  instagram: [
    { topic: "Aesthetic reels trending", volume: "2.1M posts", category: "entertainment" },
    { topic: "AI art showcase", volume: "890K posts", category: "technology" },
    { topic: "Fitness transformations", volume: "1.5M posts", category: "lifestyle" },
  ],
  youtube: [
    { topic: "AI tutorial videos", volume: "High", category: "technology" },
    { topic: "Documentary style content", volume: "High", category: "entertainment" },
    { topic: "Challenge videos", volume: "High", category: "memes" },
  ],
  linkedin: [
    { topic: "AI in the workplace", volume: "Trending", category: "technology" },
    { topic: "Leadership insights", volume: "Trending", category: "marketing" },
    { topic: "Career transition stories", volume: "Popular", category: "lifestyle" },
  ],
};

export default function TrendsPage() {
  const [trends, setTrends] = useState<Record<string, any>>({});
  const [platformTrends, setPlatformTrends] = useState<Record<string, any[]>>(
    MOCK_PLATFORM_TRENDS
  );
  const [activeView, setActiveView] = useState<"categories" | "platforms">(
    "categories"
  );
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTrends = useCallback(async (showSpinner = false) => {
    if (showSpinner) setIsRefreshing(true);
    try {
      const data = await getTrends();
      if (data && Object.keys(data).length > 0) {
        setTrends(data);
        setLastUpdated(new Date());
      }
    } catch {
      // keep existing data
    }
    try {
      const pd = await getPlatformTrends();
      if (pd && Object.keys(pd).length > 0) setPlatformTrends(pd);
    } catch {
      // keep mock
    }
    if (showSpinner) setIsRefreshing(false);
  }, []);

  // Initial fetch + polling
  useEffect(() => {
    fetchTrends(true);
    const id = setInterval(() => fetchTrends(false), POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchTrends]);

  const categories = Object.entries(trends);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveView("categories")}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition-all ${
              activeView === "categories"
                ? "bg-[var(--color-primary)] text-white"
                : "bg-[var(--color-bg-card)] text-[var(--color-text-muted)] border border-[var(--color-border)]"
            }`}
          >
            By Category
          </button>
          <button
            onClick={() => setActiveView("platforms")}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition-all ${
              activeView === "platforms"
                ? "bg-[var(--color-primary)] text-white"
                : "bg-[var(--color-bg-card)] text-[var(--color-text-muted)] border border-[var(--color-border)]"
            }`}
          >
            By Platform
          </button>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              <Clock className="h-3 w-3" />
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={() => fetchTrends(true)}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-text-muted)] hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw
              className={`h-3 w-3 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Live indicator */}
      <div className="flex items-center gap-2">
        <div className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
        </div>
        <span className="text-xs text-[var(--color-text-muted)]">
          Live — refreshing every 60s from Reddit, Google Trends & GDELT
        </span>
      </div>

      {activeView === "categories" ? (
        /* ---------- Category View ---------- */
        categories.length === 0 ? (
          <GlassCard className="text-center py-12">
            <Zap className="h-8 w-8 mx-auto mb-3 text-[var(--color-accent)]" />
            <p className="text-[var(--color-text-muted)]">
              Loading trends… this may take a few seconds on first launch.
            </p>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {categories.map(([category, data], i) => {
              const Icon = CATEGORY_ICONS[category] || TrendingUp;
              const gradient =
                CATEGORY_COLORS[category] || "from-slate-500/20 to-gray-500/20";
              const topics: any[] = data?.topics || [];
              const keywords: string[] = data?.hot_keywords || [];
              const strength: number = data?.trend_strength || 0.5;

              return (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <GlassCard hover>
                    {/* Category header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div
                          className={`rounded-lg bg-gradient-to-br ${gradient} p-2`}
                        >
                          <Icon className="h-4 w-4 text-[var(--color-accent)]" />
                        </div>
                        <h3 className="text-sm font-semibold capitalize">
                          {category}
                        </h3>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="h-2 w-2 rounded-full bg-[var(--color-accent)] animate-pulse" />
                        <span className="text-xs text-[var(--color-text-muted)]">
                          {Math.round(strength * 100)}% active
                        </span>
                      </div>
                    </div>

                    {/* Strength bar */}
                    <div className="mb-4">
                      <div className="h-1.5 w-full rounded-full bg-[var(--color-bg)]">
                        <motion.div
                          className="h-1.5 rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-primary)]"
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.round(strength * 100)}%` }}
                          transition={{ duration: 0.8, delay: i * 0.06 }}
                        />
                      </div>
                    </div>

                    {/* Topics */}
                    <div className="mb-4 space-y-2">
                      {topics.slice(0, 5).map((topic: any, j: number) => {
                        const label =
                          typeof topic === "string"
                            ? topic
                            : topic?.text || topic?.trend_keyword || String(topic);
                        const score =
                          typeof topic === "object"
                            ? topic?.popularity_score
                            : undefined;
                        const source =
                          typeof topic === "object" ? topic?.source : undefined;
                        return (
                          <div
                            key={j}
                            className="flex items-center justify-between gap-2 text-sm"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <TrendingUp className="h-3 w-3 flex-shrink-0 text-[var(--color-accent)]" />
                              <span className="text-[var(--color-text-muted)] truncate">
                                {label}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              {score != null && (
                                <span className="rounded-md bg-[var(--color-primary)]/20 px-1.5 py-0.5 text-[10px] text-[var(--color-accent)] tabular-nums">
                                  {Math.round(score)}
                                </span>
                              )}
                              {source && (
                                <span className="rounded-md bg-[var(--color-bg)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)] border border-[var(--color-border)]">
                                  {source}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Keywords */}
                    {keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {keywords.slice(0, 6).map((kw: string) => (
                          <span
                            key={kw}
                            className="rounded-md bg-[var(--color-bg)] px-2 py-0.5 text-xs text-[var(--color-text-muted)] border border-[var(--color-border)]"
                          >
                            #{kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </GlassCard>
                </motion.div>
              );
            })}
          </div>
        )
      ) : (
        /* ---------- Platform View ---------- */
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {Object.entries(platformTrends).map(([platform, items], i) => (
            <motion.div
              key={platform}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <GlassCard>
                <h3 className="text-sm font-semibold capitalize mb-4">
                  {platform}
                </h3>
                <div className="space-y-3">
                  {(items || []).map((item: any, j: number) => (
                    <div
                      key={j}
                      className="flex items-center justify-between rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3"
                    >
                      <div>
                        <p className="text-sm">{item.topic}</p>
                        <p className="text-xs text-[var(--color-text-muted)] capitalize">
                          {item.category}
                        </p>
                      </div>
                      <span className="text-xs rounded-md bg-[var(--color-bg-card)] px-2 py-1 text-[var(--color-accent)] border border-[var(--color-border)]">
                        {item.volume}
                      </span>
                    </div>
                  ))}
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
