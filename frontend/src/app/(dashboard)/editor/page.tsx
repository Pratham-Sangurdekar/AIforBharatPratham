"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  Upload,
  ImageIcon,
  Video,
  Music,
  FileText,
  X,
  Eye,
  Wrench,
  MessageSquare,
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { analyzeContent } from "@/services/api";

/* ------------------------------------------------------------------ */
/*  Platform config                                                    */
/* ------------------------------------------------------------------ */

const PLATFORMS = [
  { id: "twitter", label: "Twitter", icon: Monitor, charLimit: 280 },
  { id: "instagram", label: "Instagram", icon: Smartphone, charLimit: 2200 },
  { id: "linkedin", label: "LinkedIn", icon: Monitor, charLimit: 3000 },
  { id: "youtube", label: "YouTube", icon: Monitor, charLimit: 5000 },
] as const;

/* ------------------------------------------------------------------ */
/*  Platform Preview                                                   */
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
          className={`text-xs font-medium tabular-nums ${overLimit ? "text-red-400" : "text-[var(--color-text-muted)]"
            }`}
        >
          {used} / {platform.charLimit}
        </span>
      </div>
      <div className="h-1 rounded-full bg-[var(--color-bg-card)] mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${overLimit ? "bg-red-500" : "bg-[var(--color-primary)]"
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
/*  Media Analysis Panel — shows AI's interpretation of images/video   */
/* ------------------------------------------------------------------ */

function MediaAnalysisPanel({ analysis, contentType }: { analysis: any; contentType: string }) {
  const mediaData = analysis?.media_analysis;
  const imageAnalysis = analysis?.image_analysis;
  const videoAnalysis = analysis?.video_analysis;

  if (!mediaData && !imageAnalysis && !videoAnalysis) return null;

  return (
    <GlassCard>
      <div className="flex items-center gap-2 mb-4">
        <Eye className="h-4 w-4 text-cyan-400" />
        <h3 className="text-sm font-semibold">
          {contentType === "video" ? "Video Analysis" : "Image Analysis"}
        </h3>
      </div>

      {/* AI Description */}
      {(mediaData?.caption || imageAnalysis?.description || videoAnalysis?.content_summary) && (
        <div className="mb-4 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
          <p className="text-xs text-cyan-400 uppercase tracking-wider mb-1.5">AI Description</p>
          <p className="text-sm text-[var(--color-text)]">
            {imageAnalysis?.description || videoAnalysis?.content_summary || mediaData?.caption}
          </p>
        </div>
      )}

      {/* Visual Strengths */}
      {imageAnalysis?.visual_strengths?.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-green-400 uppercase tracking-wider mb-1.5">✓ Strengths</p>
          <ul className="space-y-1">
            {imageAnalysis.visual_strengths.map((s: string, i: number) => (
              <li key={i} className="text-sm text-[var(--color-text-muted)] flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span> {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Visual Weaknesses */}
      {imageAnalysis?.visual_weaknesses?.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-amber-400 uppercase tracking-wider mb-1.5">⚠ Weaknesses</p>
          <ul className="space-y-1">
            {imageAnalysis.visual_weaknesses.map((s: string, i: number) => (
              <li key={i} className="text-sm text-[var(--color-text-muted)] flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span> {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Improvement Actions */}
      {(imageAnalysis?.improvement_actions || videoAnalysis?.improvement_actions)?.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-violet-400 uppercase tracking-wider mb-1.5">
            <Wrench className="inline h-3 w-3 mr-1" />
            How to Improve
          </p>
          <ul className="space-y-1">
            {(imageAnalysis?.improvement_actions || videoAnalysis?.improvement_actions).map(
              (s: string, i: number) => (
                <li key={i} className="text-sm text-[var(--color-text-muted)] flex items-start gap-2">
                  <span className="text-violet-400 mt-0.5">{i + 1}.</span> {s}
                </li>
              )
            )}
          </ul>
        </div>
      )}

      {/* Video-specific: Pacing & Hook */}
      {videoAnalysis && (
        <div className="grid grid-cols-2 gap-3 mt-3">
          {videoAnalysis.hook_assessment && (
            <div className="rounded-lg bg-[var(--color-bg)] p-2 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Hook</p>
              <p className="text-sm mt-1">{videoAnalysis.hook_assessment}</p>
            </div>
          )}
          {videoAnalysis.pacing_notes && (
            <div className="rounded-lg bg-[var(--color-bg)] p-2 border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)]">Pacing</p>
              <p className="text-sm mt-1">{videoAnalysis.pacing_notes}</p>
            </div>
          )}
          {videoAnalysis.audio_notes && (
            <div className="rounded-lg bg-[var(--color-bg)] p-2 border border-[var(--color-border)] col-span-2">
              <p className="text-xs text-[var(--color-text-muted)]">Audio</p>
              <p className="text-sm mt-1">{videoAnalysis.audio_notes}</p>
            </div>
          )}
        </div>
      )}

      {/* Transcript */}
      {mediaData?.transcript && (
        <div className="mt-3 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
          <p className="text-xs text-blue-400 uppercase tracking-wider mb-1.5">
            <MessageSquare className="inline h-3 w-3 mr-1" />
            Transcript
          </p>
          <p className="text-sm text-[var(--color-text-muted)] whitespace-pre-wrap">
            {mediaData.transcript}
          </p>
        </div>
      )}

      {/* Detected elements */}
      {mediaData?.detected_objects?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {mediaData.detected_objects.map((obj: string, i: number) => (
            <span
              key={i}
              className="text-xs rounded-md bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-cyan-300"
            >
              {obj}
            </span>
          ))}
        </div>
      )}
    </GlassCard>
  );
}

/* ------------------------------------------------------------------ */
/*  Editor Page                                                        */
/* ------------------------------------------------------------------ */

export default function EditorPage() {
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [activePlatform, setActivePlatform] = useState("twitter");
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const platformCfg =
    PLATFORMS.find((p) => p.id === activePlatform) ?? PLATFORMS[0];

  /* ---- File type icon ---- */
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

  /* ---- Analyse ---- */
  const handleAnalyze = async () => {
    if (!content.trim() && !file) return;
    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const fd = new FormData();
      if (content.trim()) fd.append("text", content);
      if (file) fd.append("file", file);
      fd.append("platform", activePlatform);
      const data = await analyzeContent(fd);
      setAnalysis(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Analysis failed";
      setError(
        msg.includes("failed") || msg.includes("timed out")
          ? msg
          : `Analysis failed: ${msg}. Make sure the backend is running on port 8000.`
      );
    } finally {
      setIsLoading(false);
    }
  };

  /* ---- Apply variant ---- */
  const handleApplyVariant = (variant: string) => setContent(variant);

  /* ---- Copy ---- */
  const handleCopyVariant = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1500);
  };

  const platformOptimization = analysis?.platform_optimizations?.find(
    (p: any) => p.platform === activePlatform
  );

  const charUsed = content.length;
  const overLimit = charUsed > platformCfg.charLimit;

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* ---- Left: Content area ---- */}
      <div className="flex-1 flex flex-col gap-4">
        <GlassCard className="flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PenTool className="h-4 w-4 text-[var(--color-accent)]" />
              <h2 className="text-sm font-semibold">Content Editor</h2>
              <span
                className={`ml-2 text-xs tabular-nums ${overLimit
                    ? "text-red-400"
                    : "text-[var(--color-text-muted)]"
                  }`}
              >
                {charUsed} / {platformCfg.charLimit}
              </span>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isLoading || (!content.trim() && !file)}
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
            placeholder="Write or paste your content here, or upload an image/video below..."
            className="flex-1 w-full resize-none rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4 text-sm outline-none placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary-light)] transition-colors"
          />

          {/* File upload section */}
          <div className="mt-3 flex items-center gap-3">
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
              Upload Image/Video
            </button>
            <span className="text-xs text-[var(--color-text-muted)]">
              JPG, PNG, MP4, MP3
            </span>
          </div>

          {/* File preview */}
          {file && (
            <div className="mt-2 flex items-center gap-2 rounded-lg bg-[var(--color-bg)] px-3 py-2 border border-[var(--color-border)] text-sm">
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

          {/* Error display */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mt-3 rounded-xl bg-red-500/10 border border-red-500/30 p-3 text-sm text-red-400"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Platform tabs & preview */}
          <div className="mt-4">
            <div className="flex gap-2 mb-3">
              {PLATFORMS.map((p) => {
                const Icon = p.icon;
                return (
                  <button
                    key={p.id}
                    onClick={() => setActivePlatform(p.id)}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${activePlatform === p.id
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
            <PlatformPreview platform={platformCfg} text={content} />
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

      {/* ---- Right: AI Results Panel ---- */}
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

              {/* Explanation */}
              {analysis.explanation && (
                <p className="mt-3 text-sm text-[var(--color-text-muted)] text-left leading-relaxed">
                  {analysis.explanation}
                </p>
              )}
            </GlassCard>
          </motion.div>
        )}

        {/* Media Analysis (for images/video) */}
        {analysis?.content_type && analysis.content_type !== "text" && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <MediaAnalysisPanel
              analysis={analysis}
              contentType={analysis.content_type}
            />
          </motion.div>
        )}

        {/* Suggestions - only shown when analysis exists */}
        {analysis?.suggestions?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
          >
            <GlassCard>
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-4 w-4 text-[var(--color-accent)]" />
                <h3 className="text-sm font-semibold">AI Suggestions</h3>
              </div>
              <div className="space-y-3">
                {analysis.suggestions.map((suggestion: string, i: number) => (
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
          </motion.div>
        )}

        {/* Placeholder when no analysis yet */}
        {!analysis && !isLoading && !error && (
          <GlassCard>
            <div className="text-center py-8">
              <Sparkles className="h-8 w-8 text-[var(--color-text-muted)] mx-auto mb-3 opacity-40" />
              <p className="text-sm text-[var(--color-text-muted)]">
                Write content or upload a file and click <strong>Analyze</strong> to get AI-powered suggestions.
              </p>
            </div>
          </GlassCard>
        )}

        {/* Optimised Variants */}
        {analysis?.optimized_variants?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
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
