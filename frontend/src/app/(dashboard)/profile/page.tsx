"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { User, Save, Edit3 } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ScoreBadge from "@/components/ScoreBadge";
import { getProfile, updateProfile } from "@/services/api";

const DEFAULT_PROFILE = {
  id: 1,
  name: "Creator",
  niche: "General",
  primary_platforms: ["Instagram", "Twitter", "YouTube"],
  audience_demographic: "18-35, Global",
  content_categories: ["Technology", "Entertainment", "Marketing"],
  bio: "Content creator exploring the digital landscape.",
  avatar_url: null,
  avg_virality_score: 0,
};

const PLATFORM_OPTIONS = ["Instagram", "Twitter", "YouTube", "LinkedIn", "TikTok"];
const CATEGORY_OPTIONS = ["Technology", "Entertainment", "Marketing", "Lifestyle", "Memes", "Politics", "Education", "Finance"];

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(DEFAULT_PROFILE);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<any>(DEFAULT_PROFILE);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProfile()
      .then((data) => {
        setProfile(data);
        setDraft(data);
      })
      .catch(() => {
        setProfile(DEFAULT_PROFILE);
        setDraft(DEFAULT_PROFILE);
      });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateProfile({
        name: draft.name,
        niche: draft.niche,
        primary_platforms: draft.primary_platforms,
        audience_demographic: draft.audience_demographic,
        content_categories: draft.content_categories,
        bio: draft.bio,
      });
      setProfile(draft);
      setEditing(false);
    } catch {
      // Fallback: update locally
      setProfile(draft);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const toggleArrayItem = (arr: string[], item: string): string[] => {
    return arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item];
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <GlassCard>
          <div className="flex items-center gap-6">
            <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
              {profile.name?.[0]?.toUpperCase() || "C"}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div>
                  {editing ? (
                    <input
                      value={draft.name}
                      onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                      className="text-xl font-bold bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-1 outline-none focus:border-[var(--color-primary-light)]"
                    />
                  ) : (
                    <h2 className="text-xl font-bold">{profile.name}</h2>
                  )}
                  <p className="text-sm text-[var(--color-text-muted)] mt-1">
                    Niche: {editing ? (
                      <input
                        value={draft.niche}
                        onChange={(e) => setDraft({ ...draft, niche: e.target.value })}
                        className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-2 py-0.5 text-sm outline-none w-40"
                      />
                    ) : profile.niche}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-center">
                    <p className="text-xs text-[var(--color-text-muted)]">Avg Score</p>
                    <ScoreBadge score={profile.avg_virality_score || 0} size="sm" />
                  </div>
                  <button
                    onClick={() => editing ? handleSave() : setEditing(true)}
                    className="flex items-center gap-2 rounded-xl bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:shadow-lg transition-all"
                  >
                    {editing ? (saving ? "Saving..." : <><Save className="h-4 w-4" /> Save</>) : <><Edit3 className="h-4 w-4" /> Edit</>}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Bio */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <GlassCard>
          <h3 className="text-sm font-semibold mb-3">Bio</h3>
          {editing ? (
            <textarea
              value={draft.bio}
              onChange={(e) => setDraft({ ...draft, bio: e.target.value })}
              rows={3}
              className="w-full rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 text-sm outline-none"
            />
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">{profile.bio}</p>
          )}
        </GlassCard>
      </motion.div>

      {/* Audience */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <GlassCard>
          <h3 className="text-sm font-semibold mb-3">Audience Demographic</h3>
          {editing ? (
            <input
              value={draft.audience_demographic}
              onChange={(e) => setDraft({ ...draft, audience_demographic: e.target.value })}
              className="w-full rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-2 text-sm outline-none"
            />
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">{profile.audience_demographic}</p>
          )}
        </GlassCard>
      </motion.div>

      {/* Platforms */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <GlassCard>
          <h3 className="text-sm font-semibold mb-3">Primary Platforms</h3>
          <div className="flex flex-wrap gap-2">
            {PLATFORM_OPTIONS.map((platform) => {
              const selected = (editing ? draft : profile).primary_platforms?.includes(platform);
              return (
                <button
                  key={platform}
                  disabled={!editing}
                  onClick={() => editing && setDraft({ ...draft, primary_platforms: toggleArrayItem(draft.primary_platforms, platform) })}
                  className={`rounded-xl px-4 py-2 text-sm font-medium transition-all border ${
                    selected
                      ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)]"
                      : "bg-[var(--color-bg)] text-[var(--color-text-muted)] border-[var(--color-border)]"
                  } ${editing ? "cursor-pointer hover:border-[var(--color-accent)]" : "cursor-default"}`}
                >
                  {platform}
                </button>
              );
            })}
          </div>
        </GlassCard>
      </motion.div>

      {/* Content Categories */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
        <GlassCard>
          <h3 className="text-sm font-semibold mb-3">Content Categories</h3>
          <div className="flex flex-wrap gap-2">
            {CATEGORY_OPTIONS.map((cat) => {
              const selected = (editing ? draft : profile).content_categories?.includes(cat);
              return (
                <button
                  key={cat}
                  disabled={!editing}
                  onClick={() => editing && setDraft({ ...draft, content_categories: toggleArrayItem(draft.content_categories, cat) })}
                  className={`rounded-xl px-4 py-2 text-sm font-medium transition-all border ${
                    selected
                      ? "bg-[var(--color-accent)]/20 text-[var(--color-accent)] border-[var(--color-accent)]/30"
                      : "bg-[var(--color-bg)] text-[var(--color-text-muted)] border-[var(--color-border)]"
                  } ${editing ? "cursor-pointer hover:border-[var(--color-accent)]" : "cursor-default"}`}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
