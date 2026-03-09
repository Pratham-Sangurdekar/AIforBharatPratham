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

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col md:ml-[220px]">
          {/* Floating burger – mobile only, matches notification bell style */}
          <MobileMenuButton />
          <main className="flex-1 overflow-y-auto p-4 pt-4 md:p-6 md:pt-8">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
