import Sidebar from "@/components/Sidebar";
import TopNav from "@/components/TopNav";
import { SidebarProvider } from "@/context/SidebarContext";

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
          {/* TopNav visible on mobile only – desktop keeps the original layout */}
          <div className="md:hidden">
            <TopNav />
          </div>
          <main className="flex-1 overflow-y-auto p-4 pt-4 md:p-6 md:pt-8">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
