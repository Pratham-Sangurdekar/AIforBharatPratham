"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  PenTool,
  Lightbulb,
  RefreshCw,
  Sparkles,
  Monitor,
  Smartphone,
  Copy,
  Check,
  ArrowDownToLine,
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { analyzeContent } from "@/services/api";

/* ------------------------------------------------------------------ */
/*  Platform config with char limits                                  */
/* ------------------------------------------------------------------ */

const PLATFORMS = [
  { id: "twitter", label: "Twitter", icon: Monitor, charLimit: 280 },
  { id: "instagram", label: "Instagram", icon: Smartphone, charLimit: 2200 },
  { id: "linkedin", label: "LinkedIn", icon: Monitor, charLimit: 3000 },
  { id: "youtube", label: "YouTube", icon: Monitor, charLimit: 5000 },
] as const;

/* ------------------------------------------------------------------ */
/*  Platform Preview component                                        */
/* ------------------------------------------------------------------ */

function PlatformPreview({
  platform,
  text,
}: {
  platform: (typeof PLATFORMS)[number];
  text: string;
}) {
  const used = text.length;
  const pct = Math.min((used / platform.charLimit) * 100, 100);
  const overLimit = used > platform.charLimit;

  return (
    <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">
          {platform.label} Preview
        </p>
        <span
          className={`text-xs font-medium tabular-nums ${
            overLimit ? "text-red-400" : "text-[var(--color-text-muted)]"
          }`}
        >
          {used} / {platform.charLimit}
        </span>
      </div>

      {/* Character-limit bar */}
      <div className="h-1 rounded-full bg-[var(--color-bg-card)] mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            overLimit ? "bg-red-500" : "bg-[var(--color-primary)]"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="text-sm whitespace-pre-wrap">
        {text.slice(0, platform.charLimit)}
        {overLimit && (
          <span className="text-red-400/60">
            {text.slice(platform.charLimit)}
          </span>
        )}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Editor Page                                                        */
/* ------------------------------------------------------------------ */

export default function EditorPage() {
  const [content, setContent] = useState("");
  const [activePlatform, setActivePlatform] = useState("twitter");
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  /* Find the active platform config */
  const platformCfg =
    PLATFORMS.find((p) => p.id === activePlatform) ?? PLATFORMS[0];

  /* ---- Analyse ---- */
  const handleAnalyze = async () => {
    if (!content.trim()) return;
    setIsLoading(true);
    try {
      const fd = new FormData();
      fd.append("text", content);
      fd.append("platform", activePlatform);
      const data = await analyzeContent(fd);
      setAnalysis(data);
    } catch {
      // Fallback mock data when backend is not running
      setAnalysis({
        virality_score: 65,
        suggestions: [
          "Lead with a bold statistic or surprising fact to capture attention in the first 3 seconds.",
          "Consider rephrasing the opening to create a stronger curiosity gap.",
          "Add power words like 'incredible', 'transform', or 'secret' to intensify emotional response.",
          "Replace generic phrases with specific, concrete details to build credibility.",
        ],
        optimized_variants: [
          "Nobody talks about this — and it changes everything about how you create content.",
          "You will not believe what I discovered about content virality. This changes everything.",
          "Stop scrolling. This is the insight that top creators use to go viral every time.",
        ],
        platform_optimizations: PLATFORMS.map((p) => ({
          platform: p.id,
          optimized_text:
            content.length > 100 ? content.slice(0, 100) + "..." : content,
          tips: [
            "Optimize your opening line",
            "Add relevant hashtags",
            "Include a call-to-action",
          ],
        })),
      });
    } finally {
      setIsLoading(false);
    }
  };

  /* ---- Click-to-apply a variant ---- */
  const handleApplyVariant = (variant: string) => {
    setContent(variant);
  };

  /* ---- Copy variant to clipboard ---- */
  const handleCopyVariant = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1500);
  };

  /* Platform-specific optimisation from analysis */
  const platformOptimization = analysis?.platform_optimizations?.find(
    (p: any) => p.platform === activePlatform
  );

  /* Character count info */
  const charUsed = content.length;
  const overLimit = charUsed > platformCfg.charLimit;

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* ---- Left: Editable content area ---- */}
      <div className="flex-1 flex flex-col gap-4">
        <GlassCard className="flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PenTool className="h-4 w-4 text-[var(--color-accent)]" />
              <h2 className="text-sm font-semibold">Content Editor</h2>
              <span
                className={`ml-2 text-xs tabular-nums ${
                  overLimit
                    ? "text-red-400"
                    : "text-[var(--color-text-muted)]"
                }`}
              >
                {charUsed} / {platformCfg.charLimit}
              </span>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !content.trim()}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-light)] px-4 py-2 text-sm font-semibold text-white transition-all hover:shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {isLoading ? "Analyzing..." : "Analyze"}
            </button>
          </div>

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write or paste your content here..."
            className="flex-1 w-full resize-none rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4 text-sm outline-none placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary-light)] transition-colors"
          />

          {/* Platform Preview Tabs */}
          <div className="mt-4">
            <div className="flex gap-2 mb-3">
              {PLATFORMS.map((p) => {
                const Icon = p.icon;
                return (
                  <button
                    key={p.id}
                    onClick={() => setActivePlatform(p.id)}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                      activePlatform === p.id
                        ? "bg-[var(--color-primary)] text-white"
                        : "bg-[var(--color-bg)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-white"
                    }`}
                  >
                    <Icon className="h-3 w-3" />
                    {p.label}
                  </button>
                );
              })}
            </div>

            {/* Platform-specific preview */}
            <PlatformPreview platform={platformCfg} text={content} />

            {/* Platform tips from analysis */}
            {platformOptimization?.tips && (
              <div className="mt-3 flex flex-wrap gap-2">
                {platformOptimization.tips.map((tip: string, i: number) => (
                  <span
                    key={i}
                    className="text-xs rounded-md bg-[var(--color-bg-card)] px-2 py-1 text-[var(--color-text-muted)] border border-[var(--color-border)]"
                  >
                    {tip}
                  </span>
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* ---- Right: AI Suggestions Panel ---- */}
      <div className="w-[380px] flex flex-col gap-4 overflow-y-auto">
        {/* Score */}
        {analysis && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <GlassCard className="text-center">
              <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
                Virality Score
              </p>
              <ScoreBadge score={analysis.virality_score} size="lg" />
            </GlassCard>
          </motion.div>
        )}

        {/* Suggestions */}
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">AI Suggestions</h3>
          </div>
          <div className="space-y-3">
            {(
              analysis?.suggestions ?? [
                "Lead with a bold statistic or surprising fact to capture attention in the first 3 seconds.",
                "Consider rephrasing the opening to create a stronger curiosity gap.",
                "Add power words to intensify emotional response.",
                "Replace generic phrases with specific, concrete details.",
              ]
            ).map((suggestion: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3"
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 h-5 w-5 rounded-md bg-[var(--color-primary)]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs text-[var(--color-accent)]">
                      {i + 1}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {suggestion}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>

        {/* Optimised Variants */}
        {analysis?.optimized_variants && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <GlassCard>
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="h-4 w-4 text-[var(--color-accent)]" />
                <h3 className="text-sm font-semibold">Optimised Variants</h3>
              </div>
              <div className="space-y-3">
                {analysis.optimized_variants.map(
                  (variant: string, i: number) => (
                    <div
                      key={i}
                      className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text-muted)] group relative"
                    >
                      <p className="text-xs text-[var(--color-accent)] mb-1 font-medium">
                        Variant {i + 1}
                      </p>
                      <p>{variant}</p>

                      {/* Action buttons */}
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleApplyVariant(variant)}
                          className="flex items-center gap-1 text-xs rounded-md px-2 py-1 bg-[var(--color-primary)]/10 text-[var(--color-accent)] hover:bg-[var(--color-primary)]/20 transition-colors"
                        >
                          <ArrowDownToLine className="h-3 w-3" />
                          Apply
                        </button>
                        <button
                          onClick={() => handleCopyVariant(variant, i)}
                          className="flex items-center gap-1 text-xs rounded-md px-2 py-1 bg-[var(--color-bg-card)] text-[var(--color-text-muted)] hover:text-white transition-colors"
                        >
                          {copiedIdx === i ? (
                            <>
                              <Check className="h-3 w-3 text-green-400" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )
                )}
              </div>
            </GlassCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
