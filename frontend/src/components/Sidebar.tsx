"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/SidebarContext";
import { X, ChevronsLeft, ChevronsRight } from "lucide-react";
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
  const { isOpen, close, collapsed, toggleCollapsed } = useSidebar();

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
          "fixed left-0 top-0 z-50 flex h-screen flex-col border-r border-[var(--color-border)] bg-black transition-all duration-300 ease-in-out",
          /* Desktop width: collapsed 64px, expanded 220px */
          collapsed ? "md:w-[64px]" : "md:w-[220px]",
          /* Mobile: always 220px when open */
          "w-[220px]",
          /* Desktop: always visible */
          "md:translate-x-0",
          /* Mobile: slide in/out */
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo + close/collapse buttons */}
        <div className="flex h-16 items-center justify-between px-1 border-b border-[var(--color-border)] overflow-hidden">
          {collapsed ? (
            <div className="flex w-full items-center justify-center">
              <img
                src="/logo-thunder.png"
                alt="E"
                className="h-8 w-8 object-contain"
              />
            </div>
          ) : (
            <img
              src="/logo-thunder.png"
              alt="Engauge"
              className="w-full h-auto object-contain"
            />
          )}
          {/* Mobile close */}
          <button
            onClick={close}
            className="mr-2 rounded-lg p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)] md:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={close}
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      "flex items-center rounded-xl text-sm font-medium transition-all duration-200",
                      collapsed
                        ? "justify-center px-0 py-2.5"
                        : "gap-3 px-3 py-2.5",
                      isActive
                        ? "bg-[var(--color-primary)] text-white shadow-lg glow-primary"
                        : "text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)] hover:text-white"
                    )}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Collapse toggle – desktop only */}
        <div className="hidden md:flex border-t border-[var(--color-border)] p-2">
          <button
            onClick={toggleCollapsed}
            className="flex w-full items-center justify-center gap-2 rounded-xl py-2 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)] hover:text-white transition-colors"
          >
            {collapsed ? (
              <ChevronsRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronsLeft className="h-4 w-4" />
                <span className="text-xs">Collapse</span>
              </>
            )}
          </button>
        </div>

        {/* Footer – hide text when collapsed */}
        <div className={cn("border-t border-[var(--color-border)] p-4", collapsed && "md:px-2 md:py-3")}>
          {collapsed ? (
            <p className="hidden md:block text-[10px] text-center text-[var(--color-text-muted)]">v0.1</p>
          ) : (
            <>
              <p className="text-xs text-[var(--color-text-muted)]">ENGAUGE v0.1</p>
              <p className="text-xs text-[var(--color-text-muted)]">AI Performance Engine</p>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
