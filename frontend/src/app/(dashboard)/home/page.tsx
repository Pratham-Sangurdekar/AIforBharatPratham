"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence, useSpring, useTransform } from "framer-motion";
import {
  TrendingUp,
  Zap,
  ArrowRight,
  X,
  Copy,
  Check,
  Bell,
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import { analyzeContent } from "@/services/api";
import { PromptInputBox } from "@/components/ui/ai-prompt-box";
import { TextShimmer } from "@/components/ui/text-shimmer";
import { EtheralShadow } from "@/components/ui/etheral-shadow";

/* ------------------------------------------------------------------ */
/*  AnimatedScore — spring animation from 0 → final score             */
/* ------------------------------------------------------------------ */

function AnimatedScore({ score }: { score: number }) {
  const spring = useSpring(0, { stiffness: 60, damping: 20 });
  const display = useTransform(spring, (v) => Math.round(v));
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    spring.set(score);
    const unsub = display.on("change", (v) => setCurrent(v as number));
    return () => unsub();
  }, [score, spring, display]);

  const color =
    score >= 70
      ? "text-green-400"
      : score >= 40
        ? "text-yellow-400"
        : "text-red-400";

  return (
    <div className="flex flex-col items-center gap-1">
      <span className={`text-5xl font-black tabular-nums ${color}`}>
        {current}
      </span>
      <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-widest">
        Virality Score
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  BreakdownBars — horizontal bars for each sub-score                */
/* ------------------------------------------------------------------ */

interface BreakdownProps {
  breakdown: Record<string, number>;
}

const BAR_LABELS: Record<string, string> = {
  ai_score: "AI Score",
  trend_score: "Trend Alignment",
  hook_strength: "Hook Strength",
  visual_engagement: "Visual Engagement",
  emotion_intensity: "Emotion Intensity",
  clarity: "Clarity",
};

const BAR_COLORS: Record<string, string> = {
  ai_score: "bg-violet-500",
  trend_score: "bg-blue-500",
  hook_strength: "bg-amber-500",
  visual_engagement: "bg-cyan-500",
  emotion_intensity: "bg-rose-500",
  clarity: "bg-emerald-500",
};

function BreakdownBars({ breakdown }: BreakdownProps) {
  return (
    <div className="space-y-3 mt-4">
      {Object.entries(breakdown).map(([key, value]) => (
        <div key={key}>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--color-text-muted)]">
              {BAR_LABELS[key] ?? key}
            </span>
            <span className="font-semibold">{value}</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--color-bg)] overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(value, 100)}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className={`h-full rounded-full ${BAR_COLORS[key] ?? "bg-[var(--color-primary)]"}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  TrendMatchPanel — matched trending topics                         */
/* ------------------------------------------------------------------ */

function TrendMatchPanel({ alignment }: { alignment: any }) {
  if (!alignment) return null;
  const topics: string[] = alignment.matched_topics ?? [];
  const relevance: number = alignment.relevance_score ?? 0;

  if (topics.length === 0 && relevance === 0) return null;

  return (
    <div className="mt-6 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="h-4 w-4 text-blue-400" />
        <span className="text-sm font-semibold">Trend Match</span>
        <span className="ml-auto text-xs text-[var(--color-text-muted)]">
          Relevance: {Math.round(relevance * 100)}%
        </span>
      </div>
      {topics.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {topics.map((t, i) => (
            <span
              key={i}
              className="text-xs rounded-md bg-blue-500/10 border border-blue-500/20 px-2 py-1 text-blue-300"
            >
              {t}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-xs text-[var(--color-text-muted)]">
          No strong trend matches found.
        </p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  BeforeAfter — original text vs. optimised variant                 */
/* ------------------------------------------------------------------ */

function BeforeAfter({
  original,
  variants,
}: {
  original: string;
  variants: string[];
}) {
  const [copied, setCopied] = useState<number | null>(null);

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 1500);
  };

  if (!variants || variants.length === 0) return null;

  return (
    <div className="mt-6">
      <p className="text-sm font-semibold mb-3">Before → After</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original */}
        <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
          <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
            Original
          </p>
          <p className="text-sm text-[var(--color-text)]">
            {original || "[No text provided]"}
          </p>
        </div>

        {/* Best variant */}
        <div className="rounded-xl bg-green-500/5 border border-green-500/20 p-4 relative">
          <p className="text-xs text-green-400 uppercase tracking-wider mb-2">
            Optimised (Variant 1)
          </p>
          <p className="text-sm text-[var(--color-text)]">{variants[0]}</p>
          <button
            onClick={() => handleCopy(variants[0], 0)}
            className="absolute top-3 right-3 rounded-md p-1 hover:bg-green-500/10 transition-colors"
          >
            {copied === 0 ? (
              <Check className="h-3.5 w-3.5 text-green-400" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
            )}
          </button>
        </div>
      </div>

      {/* Additional variants */}
      {variants.length > 1 && (
        <div className="mt-3 space-y-3">
          {variants.slice(1).map((v, i) => (
            <div
              key={i}
              className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text-muted)] relative"
            >
              <span className="text-xs text-[var(--color-accent)] font-medium">
                Variant {i + 2}
              </span>
              <p className="mt-1">{v}</p>
              <button
                onClick={() => handleCopy(v, i + 1)}
                className="absolute top-3 right-3 rounded-md p-1 hover:bg-[var(--color-bg-card-hover)] transition-colors"
              >
                {copied === i + 1 ? (
                  <Check className="h-3.5 w-3.5 text-green-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Enhanced Analysis Result                                           */
/* ------------------------------------------------------------------ */

function AnalysisResult({
  result,
  originalText,
  onClose,
}: {
  result: any;
  originalText: string;
  onClose: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="w-full max-w-2xl mx-auto mt-8"
    >
      <GlassCard className="relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 hover:bg-[var(--color-bg-card-hover)] transition-colors"
        >
          <X className="h-4 w-4 text-[var(--color-text-muted)]" />
        </button>

        <div className="flex items-start gap-6">
          <AnimatedScore score={result.virality_score ?? 0} />
          <div className="flex-1">
            <p className="text-sm text-[var(--color-text)] leading-relaxed">
              {result.explanation}
            </p>
            <div className="mt-4 flex gap-6">
              {result.predicted_metrics &&
                Object.entries(
                  result.predicted_metrics as Record<string, number>
                ).map(([key, val]) => (
                  <div key={key} className="text-center">
                    <p className="text-lg font-bold text-[var(--color-accent)]">
                      {val.toLocaleString()}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)] capitalize">
                      {key}
                    </p>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {result.score_breakdown && (
          <BreakdownBars breakdown={result.score_breakdown} />
        )}

        {/* Media Analysis Panel */}
        {result.content_type && result.content_type !== "text" && (
          <div className="mt-6 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
            <p className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Zap className="h-4 w-4 text-cyan-400" />
              {result.content_type === "video" ? "Video" : "Image"} Analysis
            </p>

            {(result.media_analysis?.caption || result.image_analysis?.description || result.video_analysis?.content_summary) && (
              <div className="mb-3 rounded-lg bg-[var(--color-bg-card)] p-3">
                <p className="text-xs text-cyan-400 uppercase tracking-wider mb-1">AI Description</p>
                <p className="text-sm text-[var(--color-text)]">
                  {result.image_analysis?.description || result.video_analysis?.content_summary || result.media_analysis?.caption}
                </p>
              </div>
            )}

            {result.image_analysis?.visual_strengths?.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-green-400 mb-1">✓ Strengths</p>
                <ul className="space-y-1">
                  {result.image_analysis.visual_strengths.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-[var(--color-text-muted)]">• {s}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.image_analysis?.visual_weaknesses?.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-amber-400 mb-1">⚠ Weaknesses</p>
                <ul className="space-y-1">
                  {result.image_analysis.visual_weaknesses.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-[var(--color-text-muted)]">• {s}</li>
                  ))}
                </ul>
              </div>
            )}

            {(result.image_analysis?.improvement_actions || result.video_analysis?.improvement_actions)?.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-violet-400 mb-1">🔧 How to Improve</p>
                <ul className="space-y-1">
                  {(result.image_analysis?.improvement_actions || result.video_analysis?.improvement_actions).map((s: string, i: number) => (
                    <li key={i} className="text-sm text-[var(--color-text-muted)]">{i + 1}. {s}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.video_analysis && (
              <div className="grid grid-cols-2 gap-2 mt-3">
                {result.video_analysis.hook_assessment && (
                  <div className="rounded-lg bg-[var(--color-bg-card)] p-2">
                    <p className="text-xs text-[var(--color-text-muted)]">Hook</p>
                    <p className="text-xs mt-1">{result.video_analysis.hook_assessment}</p>
                  </div>
                )}
                {result.video_analysis.pacing_notes && (
                  <div className="rounded-lg bg-[var(--color-bg-card)] p-2">
                    <p className="text-xs text-[var(--color-text-muted)]">Pacing</p>
                    <p className="text-xs mt-1">{result.video_analysis.pacing_notes}</p>
                  </div>
                )}
              </div>
            )}

            {result.media_analysis?.transcript && (
              <div className="mt-3 rounded-lg bg-[var(--color-bg-card)] p-3">
                <p className="text-xs text-blue-400 uppercase tracking-wider mb-1">Transcript</p>
                <p className="text-sm text-[var(--color-text-muted)] whitespace-pre-wrap">
                  {result.media_analysis.transcript}
                </p>
              </div>
            )}

            {result.media_analysis?.detected_objects?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {result.media_analysis.detected_objects.map((obj: string, i: number) => (
                  <span key={i} className="text-xs rounded-md bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-cyan-300">
                    {obj}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Content DNA */}
        {result.content_dna && (
          <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Hook Type</p>
              <p className="text-sm font-medium mt-1 capitalize">{result.content_dna.hook}</p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Emotion</p>
              <p className="text-sm font-medium mt-1 capitalize">{result.content_dna.emotion}</p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Structure</p>
              <p className="text-sm font-medium mt-1 capitalize">{result.content_dna.structure}</p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Triggers</p>
              <p className="text-sm font-medium mt-1 capitalize">
                {result.content_dna.psychological_triggers?.join(", ")}
              </p>
            </div>
          </div>
        )}

        <TrendMatchPanel alignment={result.trend_alignment} />

        {result.suggestions?.length > 0 && (
          <div className="mt-6">
            <p className="text-sm font-semibold mb-3">Improvement Suggestions</p>
            <ul className="space-y-2">
              {result.suggestions.map((s: string, i: number) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]"
                >
                  <ArrowRight className="h-4 w-4 text-[var(--color-accent)] flex-shrink-0 mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        <BeforeAfter
          original={originalText}
          variants={result.optimized_variants ?? []}
        />
      </GlassCard>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Home Page — Centered PromptInputBox                           */
/* ------------------------------------------------------------------ */

export default function HomePage() {
  const [text, setText] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // Auto-dismiss toast after 5 seconds
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleSend = useCallback(
    async (message: string, files?: File[], provider?: string) => {
      if (!message.trim() && (!files || files.length === 0)) return;
      setIsAnalyzing(true);
      setError(null);
      setResult(null);
      setText(message);

      const formData = new FormData();
      if (message.trim()) formData.append("text", message.trim());
      if (files && files.length > 0) formData.append("file", files[0]);
      formData.append("platform", "general");
      if (provider) formData.append("llm_provider", provider);

      try {
        const data = await analyzeContent(formData);
        setResult(data);
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Analysis failed";
        if (msg.startsWith("RATE_LIMIT:")) {
          setToast(msg.replace("RATE_LIMIT:", ""));
        } else {
          setError(
            msg.includes("failed") || msg.includes("timed out")
              ? msg
              : `Analysis failed: ${msg}. Make sure the backend is running on port 8000.`
          );
        }
      } finally {
        setIsAnalyzing(false);
      }
    },
    []
  );

  const hasResult = !!result;

  return (
    <div className="relative flex flex-col items-center min-h-screen -m-6 -mt-8">
      {/* Animated background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <EtheralShadow
          color="rgba(255, 109, 0, 0.6)"
          animation={{ scale: 80, speed: 60 }}
          noise={{ opacity: 0.6, scale: 1.2 }}
          sizing="fill"
        />
      </div>

      {/* Floating notification bell */}
      <div className="absolute top-4 right-4 z-20">
        <button className="relative rounded-xl p-2 hover:bg-white/10 transition-colors">
          <Bell className="h-5 w-5 text-white/70" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--color-accent)]" />
        </button>
      </div>

      {/* Toast notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -40 }}
            className="fixed top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-2xl bg-amber-500/90 backdrop-blur-md px-5 py-3 text-sm font-medium text-black shadow-lg"
          >
            <span>⚠️</span>
            <span>{toast}</span>
            <button onClick={() => setToast(null)} className="ml-2 rounded-full p-0.5 hover:bg-black/10">
              <X className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Centered hero section — pushes down when no results */}
      <motion.div
        className="relative z-10 flex flex-col items-center w-full max-w-2xl px-4"
        animate={{
          paddingTop: hasResult ? "2rem" : "35vh",
        }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      >
        {/* Shimmer heading */}
        <motion.div
          className="mb-6 text-center"
          animate={{
            scale: hasResult ? 0.85 : 1,
            opacity: hasResult ? 0.8 : 1,
          }}
          transition={{ duration: 0.4 }}
        >
          <TextShimmer
            duration={1.5}
            className="text-3xl font-bold tracking-tight [--base-color:#ffffff] [--base-gradient-color:#ff6d00] dark:[--base-color:#e0e0e0] dark:[--base-gradient-color:#ff9100]"
          >
            How can I Engauge you today?
          </TextShimmer>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            Paste text, upload images or videos — get AI-powered virality predictions
          </p>
        </motion.div>

        {/* PromptInputBox */}
        <div className="w-full">
          <PromptInputBox
            onSend={handleSend}
            isLoading={isAnalyzing}
            placeholder="Paste your content here to analyze..."
          />
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-4 w-full rounded-2xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Analysis results — full width below */}
      <AnimatePresence>
        {result && (
          <AnalysisResult
            result={result}
            originalText={text}
            onClose={() => setResult(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

