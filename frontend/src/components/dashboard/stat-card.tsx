"use client";

import { cn } from "@/lib/utils";

export interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  iconClassName?: string;
  className?: string;
}

/**
 * StatCard - A card displaying a single statistic with an icon
 * Used in the dashboard stats overview grid
 */
export function StatCard({
  icon,
  label,
  value,
  iconClassName,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "bg-card flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent/50",
        className,
      )}
    >
      <div
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-md",
          iconClassName,
        )}
      >
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-muted-foreground text-xs">{label}</p>
        <p className="text-2xl font-semibold tabular-nums">{value}</p>
      </div>
    </div>
  );
}
