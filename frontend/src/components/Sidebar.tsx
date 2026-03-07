"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Home,
  PenTool,
  Clock,
  BarChart3,
  Image,
  User,
  Settings,
  TrendingUp,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/home", label: "Home", icon: Home },
  { href: "/editor", label: "Editor", icon: PenTool },
  { href: "/history", label: "History", icon: Clock },
  { href: "/metrics", label: "Metrics", icon: BarChart3 },
  { href: "/gallery", label: "Gallery", icon: Image },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/trends", label: "Trends", icon: TrendingUp },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[220px] flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-6 border-b border-[var(--color-border)]">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
          <TrendingUp className="h-4 w-4 text-white" />
        </div>
        <span className="text-lg font-bold tracking-tight">
          ENG<span className="text-[var(--color-accent)]">AUGE</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-[var(--color-primary)] text-white shadow-lg glow-primary"
                      : "text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)] hover:text-white"
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--color-border)] p-4">
        <p className="text-xs text-[var(--color-text-muted)]">ENGAUGE v0.1</p>
        <p className="text-xs text-[var(--color-text-muted)]">AI Performance Engine</p>
      </div>
    </aside>
  );
}
