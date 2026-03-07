"use client";

import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export default function ScoreBadge({ score, size = "md", className }: ScoreBadgeProps) {
  const scoreClass = score >= 70 ? "score-high" : score >= 40 ? "score-medium" : "score-low";

  const sizeClasses = {
    sm: "text-sm font-semibold px-2 py-0.5",
    md: "text-lg font-bold px-3 py-1",
    lg: "text-3xl font-extrabold px-4 py-2",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)]",
        sizeClasses[size],
        scoreClass,
        className
      )}
    >
      {Math.round(score)}
    </span>
  );
}
