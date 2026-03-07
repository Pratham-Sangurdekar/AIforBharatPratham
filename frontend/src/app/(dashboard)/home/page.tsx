"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence, useSpring, useTransform } from "framer-motion";
import {
  Send,
  Upload,
  FileText,
  ImageIcon,
  Video,
  Music,
  TrendingUp,
  Zap,
  Flame,
  ArrowRight,
  X,
  Loader2,
  Copy,
  Check,
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { analyzeContent } from "@/services/api";

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
  emotion_intensity: "Emotion Intensity",
};

const BAR_COLORS: Record<string, string> = {
  ai_score: "bg-violet-500",
  trend_score: "bg-blue-500",
  hook_strength: "bg-amber-500",
  emotion_intensity: "bg-rose-500",
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
      className="mt-6"
    >
      <GlassCard className="relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 hover:bg-[var(--color-bg-card-hover)] transition-colors"
        >
          <X className="h-4 w-4 text-[var(--color-text-muted)]" />
        </button>

        <div className="flex items-start gap-6">
          {/* Animated score */}
          <AnimatedScore score={result.virality_score ?? 0} />

          {/* Explanation + predicted metrics */}
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

        {/* Score breakdown bars */}
        {result.score_breakdown && (
          <BreakdownBars breakdown={result.score_breakdown} />
        )}

        {/* Content DNA */}
        {result.content_dna && (
          <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">
                Hook Type
              </p>
              <p className="text-sm font-medium mt-1 capitalize">
                {result.content_dna.hook}
              </p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Emotion</p>
              <p className="text-sm font-medium mt-1 capitalize">
                {result.content_dna.emotion}
              </p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">
                Structure
              </p>
              <p className="text-sm font-medium mt-1 capitalize">
                {result.content_dna.structure}
              </p>
            </div>
            <div className="rounded-xl bg-[var(--color-bg)] p-3 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">
                Triggers
              </p>
              <p className="text-sm font-medium mt-1 capitalize">
                {result.content_dna.psychological_triggers?.join(", ")}
              </p>
            </div>
          </div>
        )}

        {/* Trend match panel */}
        <TrendMatchPanel alignment={result.trend_alignment} />

        {/* Suggestions */}
        {result.suggestions?.length > 0 && (
          <div className="mt-6">
            <p className="text-sm font-semibold mb-3">
              Improvement Suggestions
            </p>
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

        {/* Before / After comparison */}
        <BeforeAfter
          original={originalText}
          variants={result.optimized_variants ?? []}
        />
      </GlassCard>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Home Page                                                     */
/* ------------------------------------------------------------------ */

export default function HomePage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(async () => {
    if (!text.trim() && !file) return;
    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    if (text.trim()) formData.append("text", text.trim());
    if (file) formData.append("file", file);
    formData.append("platform", "general");

    try {
      const data = await analyzeContent(formData);
      setResult(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Analysis failed";
      setError(msg.includes("failed") || msg.includes("timed out")
        ? msg
        : `Analysis failed: ${msg}. Make sure the backend is running on port 8000.`
      );
    } finally {
      setIsAnalyzing(false);
    }
  }, [text, file]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragging(false), []);

  const fileTypeIcon = () => {
    if (!file) return null;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (["jpg", "jpeg", "png", "gif", "webp"].includes(ext || ""))
      return <ImageIcon className="h-4 w-4" />;
    if (["mp4", "mov", "avi", "webm"].includes(ext || ""))
      return <Video className="h-4 w-4" />;
    if (["mp3", "wav", "m4a", "ogg"].includes(ext || ""))
      return <Music className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      

      {/* Content Submission Interface */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Analyze Your Content</h2>
        <GlassCard
          className={`transition-all duration-300 ${
            isDragging
              ? "border-[var(--color-accent)] glow-accent"
              : ""
          }`}
        >
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your post text here, or drag and drop a file..."
              rows={5}
              className="w-full resize-none rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4 text-sm outline-none placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary-light)] transition-colors"
            />

            {file && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-[var(--color-bg)] px-3 py-2 border border-[var(--color-border)] text-sm">
                {fileTypeIcon()}
                <span className="flex-1 truncate text-[var(--color-text-muted)]">
                  {file.name}
                </span>
                <button
                  onClick={() => setFile(null)}
                  className="rounded p-0.5 hover:bg-[var(--color-bg-card-hover)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.webm,.mp3,.wav,.m4a,.ogg"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-muted)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-colors"
                >
                  <Upload className="h-4 w-4" />
                  Upload File
                </button>
                <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                  <span>Supports:</span>
                  <span className="text-[var(--color-text)]">
                    JPG, PNG, MP4, MP3
                  </span>
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={isAnalyzing || (!text.trim() && !file)}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-light)] px-6 py-2.5 text-sm font-semibold text-white transition-all hover:shadow-lg hover:shadow-[var(--color-glow-primary)] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                {isAnalyzing ? "Analyzing..." : "Analyze"}
              </button>
            </div>
          </div>
        </GlassCard>

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400"
          >
            {error}
          </motion.div>
        )}

        <AnimatePresence>
          {result && (
            <AnalysisResult
              result={result}
              originalText={text}
              onClose={() => setResult(null)}
            />
          )}
        </AnimatePresence>
      </section>
    </div>
  );
}
