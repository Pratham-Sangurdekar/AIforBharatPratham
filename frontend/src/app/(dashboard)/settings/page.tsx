"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Settings as SettingsIcon, Moon, Bell, Globe, Cpu, Database, Shield } from "lucide-react";
import GlassCard from "@/components/GlassCard";

interface ToggleProps {
  enabled: boolean;
  onChange: (v: boolean) => void;
}

function Toggle({ enabled, onChange }: ToggleProps) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative h-6 w-11 rounded-full transition-colors ${
        enabled ? "bg-[var(--color-primary)]" : "bg-[var(--color-border)]"
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
          enabled ? "translate-x-5" : ""
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    darkMode: true,
    notifications: true,
    autoAnalyze: false,
    trendAlerts: true,
    platformSync: false,
    dataRetention: "30 days",
    aiModel: "standard",
    language: "English",
  });

  const updateSetting = (key: string, value: any) =>
    setSettings((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Appearance */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Moon className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">Appearance</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Dark Mode</p>
                <p className="text-xs text-[var(--color-text-muted)]">Use dark theme across the dashboard</p>
              </div>
              <Toggle enabled={settings.darkMode} onChange={(v) => updateSetting("darkMode", v)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Language</p>
                <p className="text-xs text-[var(--color-text-muted)]">Dashboard display language</p>
              </div>
              <select
                value={settings.language}
                onChange={(e) => updateSetting("language", e.target.value)}
                className="rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-1.5 text-sm outline-none"
              >
                <option>English</option>
                <option>Spanish</option>
                <option>French</option>
                <option>Hindi</option>
              </select>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Notifications */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Bell className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">Notifications</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Push Notifications</p>
                <p className="text-xs text-[var(--color-text-muted)]">Receive alerts about analysis results</p>
              </div>
              <Toggle enabled={settings.notifications} onChange={(v) => updateSetting("notifications", v)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Trend Alerts</p>
                <p className="text-xs text-[var(--color-text-muted)]">Get notified when relevant topics trend</p>
              </div>
              <Toggle enabled={settings.trendAlerts} onChange={(v) => updateSetting("trendAlerts", v)} />
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* AI Configuration */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">AI Configuration</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Auto-Analyze on Upload</p>
                <p className="text-xs text-[var(--color-text-muted)]">Automatically analyze content when uploaded</p>
              </div>
              <Toggle enabled={settings.autoAnalyze} onChange={(v) => updateSetting("autoAnalyze", v)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">AI Model</p>
                <p className="text-xs text-[var(--color-text-muted)]">Select analysis model quality</p>
              </div>
              <select
                value={settings.aiModel}
                onChange={(e) => updateSetting("aiModel", e.target.value)}
                className="rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-1.5 text-sm outline-none"
              >
                <option value="fast">Fast (Lower quality)</option>
                <option value="standard">Standard</option>
                <option value="advanced">Advanced (Slower)</option>
              </select>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Integration */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Globe className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">Platform Integration</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Platform Sync</p>
                <p className="text-xs text-[var(--color-text-muted)]">Sync analysis data with connected platforms</p>
              </div>
              <Toggle enabled={settings.platformSync} onChange={(v) => updateSetting("platformSync", v)} />
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Data */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Database className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="text-sm font-semibold">Data Management</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Data Retention</p>
                <p className="text-xs text-[var(--color-text-muted)]">How long to keep analysis history</p>
              </div>
              <select
                value={settings.dataRetention}
                onChange={(e) => updateSetting("dataRetention", e.target.value)}
                className="rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-1.5 text-sm outline-none"
              >
                <option>7 days</option>
                <option>30 days</option>
                <option>90 days</option>
                <option>1 year</option>
                <option>Forever</option>
              </select>
            </div>
            <div className="pt-2 border-t border-[var(--color-border)]">
              <button className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-400 hover:bg-red-500/20 transition-colors">
                Clear All Data
              </button>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
