"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Image as ImageIcon, Video, FileText, Music, Filter, X, ArrowRight, Sparkles } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { getGallery, getAnalysisDetail } from "@/services/api";

const FILTERS = [
  { id: undefined, label: "All" },
  { id: "image", label: "Images" },
  { id: "video", label: "Videos" },
  { id: "text", label: "Text Posts" },
];

const MOCK_GALLERY = Array.from({ length: 12 }, (_, i) => ({
  id: i + 1,
  content_type: ["text", "image", "video", "text", "image", "text"][i % 6],
  text_preview: [
    "AI is transforming content creation...",
    "The secret to viral hooks...",
    "Morning routine for productivity...",
    "Why short-form content wins...",
    "Data-driven content strategies...",
    "Building authentic audience connections...",
  ][i % 6],
  media_url: null,
  virality_score: [72, 85, 58, 91, 44, 67, 78, 53, 88, 61, 75, 82][i],
  analysis_id: i + 1,
  created_at: new Date(Date.now() - i * 86400000).toISOString(),
}));

function getTypeIcon(type: string) {
  switch (type) {
    case "image": return <ImageIcon className="h-8 w-8" />;
    case "video": return <Video className="h-8 w-8" />;
    case "audio": return <Music className="h-8 w-8" />;
    default: return <FileText className="h-8 w-8" />;
  }
}

function getTypeBg(type: string) {
  switch (type) {
    case "image": return "from-blue-900/40 to-indigo-900/40";
    case "video": return "from-purple-900/40 to-pink-900/40";
    case "audio": return "from-green-900/40 to-teal-900/40";
    default: return "from-[var(--color-primary)]/40 to-slate-900/40";
  }
}

function DetailView({ item, onClose }: { item: any; onClose: () => void }) {
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    if (item.analysis_id) {
      getAnalysisDetail(item.analysis_id)
        .then(setDetail)
        .catch(() =>
          setDetail({
            virality_score: item.virality_score,
            explanation: "Content analysis shows moderate viral potential with room for optimization.",
            suggestions: ["Strengthen the opening hook", "Add trending topic references", "Include a call-to-action"],
            optimized_variants: [
              "Nobody talks about this — here is what you need to know.",
              "Stop scrolling. This changes everything about content creation.",
            ],
            media_analysis: null,
          })
        );
    }
  }, [item.analysis_id]);

  const media = detail?.media_analysis;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
        className="relative w-full max-w-xl max-h-[80vh] overflow-y-auto glass-card p-6 mx-4" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute right-4 top-4 rounded-lg p-1 hover:bg-[var(--color-bg-card-hover)]">
          <X className="h-5 w-5 text-[var(--color-text-muted)]" />
        </button>

        {/* Media placeholder */}
        <div className={`rounded-xl bg-gradient-to-br ${getTypeBg(item.content_type)} p-8 flex items-center justify-center mb-4`}>
          {getTypeIcon(item.content_type)}
        </div>

        <p className="text-sm mb-2">{item.text_preview || "Media content"}</p>
        <div className="flex items-center gap-3 mb-4">
          <ScoreBadge score={item.virality_score} size="md" />
          <span className="text-xs text-[var(--color-text-muted)]">{new Date(item.created_at).toLocaleDateString()}</span>
        </div>

        {/* Media Analysis Section */}
        {media && (
          <div className="mb-4 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4 space-y-3">
            <p className="text-sm font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[var(--color-accent)]" />
              Media Analysis
            </p>
            {media.caption && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Caption</p>
                <p className="text-sm">{media.caption}</p>
              </div>
            )}
            {media.transcript && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Transcript</p>
                <p className="text-sm line-clamp-4">{media.transcript}</p>
              </div>
            )}
            {media.visual_theme && (
              <div className="flex items-center gap-2">
                <p className="text-xs text-[var(--color-text-muted)]">Theme:</p>
                <span className="rounded-md bg-[var(--color-primary)]/20 px-2 py-0.5 text-xs text-[var(--color-accent)]">{media.visual_theme}</span>
              </div>
            )}
            {media.emotional_tone && (
              <div className="flex items-center gap-2">
                <p className="text-xs text-[var(--color-text-muted)]">Tone:</p>
                <span className="rounded-md bg-[var(--color-primary)]/20 px-2 py-0.5 text-xs text-[var(--color-accent)]">{media.emotional_tone}</span>
              </div>
            )}
            {media.detected_objects && media.detected_objects.length > 0 && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Detected Elements</p>
                <div className="flex flex-wrap gap-1">
                  {media.detected_objects.map((obj: string, i: number) => (
                    <span key={i} className="rounded-md bg-[var(--color-bg-card)] px-2 py-0.5 text-xs text-[var(--color-text-muted)] border border-[var(--color-border)]">{obj}</span>
                  ))}
                </div>
              </div>
            )}
            {media.detected_topics && media.detected_topics.length > 0 && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Topics</p>
                <div className="flex flex-wrap gap-1">
                  {media.detected_topics.map((t: string, i: number) => (
                    <span key={i} className="rounded-md bg-[var(--color-accent)]/20 px-2 py-0.5 text-xs text-[var(--color-accent)]">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {media.speech_pace && (
              <div className="flex items-center gap-2">
                <p className="text-xs text-[var(--color-text-muted)]">Pace:</p>
                <span className="text-xs capitalize">{media.speech_pace}</span>
              </div>
            )}
            {media.hook_strength != null && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Hook Strength</p>
                <div className="h-1.5 w-full rounded-full bg-[var(--color-bg-card)]">
                  <div className="h-1.5 rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-primary)]" style={{ width: `${Math.round(media.hook_strength * 100)}%` }} />
                </div>
              </div>
            )}
          </div>
        )}

        {detail && (
          <>
            <p className="text-sm text-[var(--color-text-muted)] mb-4">{detail.explanation}</p>
            {detail.suggestions && (
              <div className="mb-4">
                <p className="text-sm font-semibold mb-2">Suggestions</p>
                <ul className="space-y-1">
                  {detail.suggestions.map((s: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
                      <ArrowRight className="h-4 w-4 text-[var(--color-accent)] flex-shrink-0 mt-0.5" />{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {detail.optimized_variants && (
              <div>
                <p className="text-sm font-semibold mb-2">Optimized Variants</p>
                <div className="space-y-2">
                  {detail.optimized_variants.map((v: string, i: number) => (
                    <div key={i} className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text-muted)]">{v}</div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </motion.div>
    </motion.div>
  );
}

export default function GalleryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getGallery(filter)
      .then((data) => setItems(data.items))
      .catch(() => {
        const filtered = filter ? MOCK_GALLERY.filter((g) => g.content_type === filter) : MOCK_GALLERY;
        setItems(filtered);
      })
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div>
      {/* Filters */}
      <div className="flex items-center gap-3 mb-6">
        <Filter className="h-4 w-4 text-[var(--color-text-muted)]" />
        {FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => setFilter(f.id)}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition-all ${
              filter === f.id
                ? "bg-[var(--color-primary)] text-white"
                : "bg-[var(--color-bg-card)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-white"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <GlassCard className="text-center py-12">
          <p className="text-[var(--color-text-muted)]">No items in gallery. Upload content to get started.</p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {items.map((item, i) => (
            <motion.div key={item.id} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.03 }}>
              <GlassCard hover onClick={() => setSelected(item)} className="p-0 overflow-hidden">
                <div className={`bg-gradient-to-br ${getTypeBg(item.content_type)} p-6 flex items-center justify-center`}>
                  {getTypeIcon(item.content_type)}
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-[var(--color-text-muted)] capitalize">{item.content_type}</span>
                    {item.virality_score != null && <ScoreBadge score={item.virality_score} size="sm" />}
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] line-clamp-2">{item.text_preview || "Media"}</p>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {selected && <DetailView item={selected} onClose={() => setSelected(null)} />}
      </AnimatePresence>
    </div>
  );
}
