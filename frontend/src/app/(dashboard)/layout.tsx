"use client";

import { Menu } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { SidebarProvider, useSidebar } from "@/context/SidebarContext";

function MobileMenuButton() {
  const { toggle } = useSidebar();
  return (
    <button
      onClick={toggle}
      className="fixed top-4 left-4 z-30 rounded-xl p-2 hover:bg-white/10 transition-colors md:hidden"
    >
      <Menu className="h-5 w-5 text-white/70" />
    </button>
  );
}

function MainContent({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebar();
  return (
    <div
      className="flex flex-1 flex-col transition-all duration-300"
      style={{ marginLeft: undefined }}
    >
      {/* Responsive margin: 0 on mobile, adapts to sidebar width on desktop */}
      <style jsx>{`
        @media (min-width: 768px) {
          div { margin-left: ${collapsed ? '64px' : '220px'}; }
        }
      `}</style>
      <MobileMenuButton />
      <main className="flex-1 overflow-y-auto p-4 pt-4 md:p-6 md:pt-8">
        {children}
      </main>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <MainContent>{children}</MainContent>
      </div>
    </SidebarProvider>
  );
}
