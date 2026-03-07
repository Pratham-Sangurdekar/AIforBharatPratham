"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, FileText, ImageIcon, Video, Music, X, ChevronUp, ArrowRight } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { getHistory, getAnalysisDetail } from "@/services/api";

/* ------------------------------------------------------------------ */
/*  Mock data for when backend is not running                          */
/* ------------------------------------------------------------------ */
const MOCK_HISTORY = Array.from({ length: 8 }, (_, i) => ({
  id: i + 1,
  content_id: i + 1,
  content_type: ["text", "image", "video", "text"][i % 4],
  text_preview: [
    "AI is transforming how we create content. The secret most creators miss...",
    "New study shows 73% of viral posts use curiosity hooks in the first line...",
    "Unpopular opinion: short-form content is overrated for building real audience...",
    "Here is the morning routine that helped me grow from 0 to 100K followers...",
    "The hidden psychology behind every viral tweet — a thread...",
    "Why most content strategies fail and what data says actually works...",
    "Breaking: AI tools are now outperforming human copywriters in engagement...",
    "Stop making this mistake with your content. It is costing you thousands...",
  ][i],
  media_url: null,
  virality_score: [78, 65, 82, 55, 91, 43, 72, 60][i],
  created_at: new Date(Date.now() - i * 86400000).toISOString(),
}));

function getTypeIcon(type: string) {
  switch (type) {
    case "image": return <ImageIcon className="h-4 w-4" />;
    case "video": return <Video className="h-4 w-4" />;
    case "audio": return <Music className="h-4 w-4" />;
    default: return <FileText className="h-4 w-4" />;
  }
}

/* ------------------------------------------------------------------ */
/*  Detail Modal with swipe-up reveal                                  */
/* ------------------------------------------------------------------ */

function DetailModal({ item, onClose }: { item: any; onClose: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    getAnalysisDetail(item.id)
      .then(setDetail)
      .catch(() => {
        // Mock detail data
        setDetail({
          ...item,
          explanation: "This content uses a curiosity hook and references trending AI topics, creating strong engagement potential.",
          predicted_metrics: { likes: 1200, shares: 340, comments: 85 },
          content_dna: {
            hook: "curiosity hook",
            emotion: "surprise",
            structure: "hook build payoff",
            psychological_triggers: ["curiosity gap", "relatability"],
          },
          trend_alignment: { matched_topics: ["AI tools", "productivity"], relevance_score: 0.72 },
          suggestions: [
            "Strengthen the opening hook",
            "Add a clearer payoff",
            "Reference a current meme",
          ],
          optimized_variants: [
            "Nobody talks about this — and it changes everything.",
            "You will not believe what I discovered about AI content creation.",
            "Stop scrolling. This one insight is worth more than any course.",
          ],
        });
      });
  }, [item.id]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 40 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 40 }}
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto glass-card p-6 mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 hover:bg-[var(--color-bg-card-hover)] transition-colors z-10"
        >
          <X className="h-5 w-5 text-[var(--color-text-muted)]" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-[var(--color-primary)]/20 p-2">{getTypeIcon(item.content_type)}</div>
          <div className="flex-1">
            <p className="text-sm font-medium">{item.text_preview || "Media content"}</p>
            <p className="text-xs text-[var(--color-text-muted)]">
              Analyzed {new Date(item.created_at).toLocaleDateString()}
            </p>
          </div>
          <ScoreBadge score={item.virality_score} size="md" />
        </div>

        {/* Swipe up to reveal — click toggle for desktop */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent)] transition-colors mb-4"
        >
          <ChevronUp className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
          {expanded ? "Collapse details" : "Reveal full analysis"}
        </button>

        <AnimatePresence>
          {expanded && detail && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              {/* Explanation */}
              <div className="mb-4 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
                <p className="text-sm text-[var(--color-text-muted)]">{detail.explanation}</p>
              </div>

              {/* Predicted Metrics */}
              {detail.predicted_metrics && (
                <div className="mb-4 flex gap-4">
                  {Object.entries(detail.predicted_metrics as Record<string, number>).map(([key, val]) => (
                    <div key={key} className="flex-1 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-center">
                      <p className="text-lg font-bold text-[var(--color-accent)]">{val.toLocaleString()}</p>
                      <p className="text-xs text-[var(--color-text-muted)] capitalize">{key}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Content DNA */}
              {detail.content_dna && (
                <div className="mb-4 grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                    <p className="text-xs text-[var(--color-text-muted)]">Hook</p>
                    <p className="text-sm font-medium mt-1 capitalize">{detail.content_dna.hook}</p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                    <p className="text-xs text-[var(--color-text-muted)]">Emotion</p>
                    <p className="text-sm font-medium mt-1 capitalize">{detail.content_dna.emotion}</p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                    <p className="text-xs text-[var(--color-text-muted)]">Structure</p>
                    <p className="text-sm font-medium mt-1 capitalize">{detail.content_dna.structure}</p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                    <p className="text-xs text-[var(--color-text-muted)]">Triggers</p>
                    <p className="text-sm font-medium mt-1 capitalize">
                      {detail.content_dna.psychological_triggers?.join(", ")}
                    </p>
                  </div>
                </div>
              )}

              {/* Suggestions */}
              {detail.suggestions && (
                <div className="mb-4">
                  <p className="text-sm font-semibold mb-2">Suggestions</p>
                  <ul className="space-y-2">
                    {detail.suggestions.map((s: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
                        <ArrowRight className="h-4 w-4 text-[var(--color-accent)] flex-shrink-0 mt-0.5" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Optimized Variants */}
              {detail.optimized_variants && (
                <div>
                  <p className="text-sm font-semibold mb-2">Optimized Versions</p>
                  <div className="space-y-2">
                    {detail.optimized_variants.map((v: string, i: number) => (
                      <div
                        key={i}
                        className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text-muted)]"
                      >
                        {v}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  History Page                                                       */
/* ------------------------------------------------------------------ */

export default function HistoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then((data) => setItems(data.items))
      .catch(() => setItems(MOCK_HISTORY))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <Clock className="h-5 w-5 text-[var(--color-accent)]" />
        <h2 className="text-lg font-semibold">Analysis History</h2>
        <span className="text-sm text-[var(--color-text-muted)]">({items.length} items)</span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <GlassCard className="text-center py-12">
          <p className="text-[var(--color-text-muted)]">No analysis history yet. Submit content on the Home tab to get started.</p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <GlassCard hover onClick={() => setSelectedItem(item)}>
                <div className="flex items-start justify-between mb-3">
                  <div className="rounded-lg bg-[var(--color-primary)]/20 p-2">
                    {getTypeIcon(item.content_type)}
                  </div>
                  <ScoreBadge score={item.virality_score} size="sm" />
                </div>
                <p className="text-sm line-clamp-3 text-[var(--color-text-muted)] mb-3">
                  {item.text_preview || "Media content"}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {new Date(item.created_at).toLocaleDateString()}
                </p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedItem && (
          <DetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
