"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/SidebarContext";
import { X } from "lucide-react";
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
  const { isOpen, close } = useSidebar();

  return (
    <>
      {/* Backdrop overlay – mobile only */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={close}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-[220px] flex-col border-r border-[var(--color-border)] bg-black transition-transform duration-300 ease-in-out",
          /* Desktop: always visible */
          "md:translate-x-0",
          /* Mobile: slide in/out */
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo + mobile close button */}
        <div className="flex h-16 items-center justify-between px-1 border-b border-[var(--color-border)] overflow-hidden">
          <img
            src="/logo-thunder.png"
            alt="Engauge"
            className="w-full h-auto object-contain"
          />
          <button
            onClick={close}
            className="mr-2 rounded-lg p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)] md:hidden"
          >
            <X className="h-5 w-5" />
          </button>
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
                    onClick={close}
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
    </>
  );
}
