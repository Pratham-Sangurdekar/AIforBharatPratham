import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ENGAUGE — AI Content Performance Predictor",
  description: "Predict the virality of your content before you post it.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] antialiased">
        {children}
      </body>
    </html>
  );
}
