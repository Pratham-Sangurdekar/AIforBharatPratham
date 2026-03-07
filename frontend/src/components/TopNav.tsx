"use client";

import { usePathname } from "next/navigation";
import { Bell, Search } from "lucide-react";

const TITLES: Record<string, string> = {
  "/home": "Dashboard",
  "/editor": "Content Editor",
  "/history": "Analysis History",
  "/metrics": "Performance Metrics",
  "/gallery": "Media Gallery",
  "/profile": "Creator Profile",
  "/settings": "Settings",
  "/trends": "Trending Topics",
};

export default function TopNav() {
  const pathname = usePathname();
  const title = TITLES[pathname] || "ENGAUGE";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md px-6">
      <h1 className="text-xl font-semibold tracking-tight">{title}</h1>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="flex items-center gap-2 rounded-xl bg-[var(--color-bg-card)] px-3 py-2 border border-[var(--color-border)]">
          <Search className="h-4 w-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent text-sm outline-none placeholder:text-[var(--color-text-muted)] w-48"
          />
        </div>

        {/* Notifications */}
        <button className="relative rounded-xl p-2 hover:bg-[var(--color-bg-card-hover)] transition-colors">
          <Bell className="h-5 w-5 text-[var(--color-text-muted)]" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--color-accent)]" />
        </button>

        {/* Avatar */}
        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center text-xs font-bold text-white">
          C
        </div>
      </div>
    </header>
  );
}
