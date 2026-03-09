"use client";

import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface DashboardHeaderProps {
  lastUpdated?: Date;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  className?: string;
}

/**
 * DashboardHeader - Header with title and refresh control
 * Shows page title, description, and last updated time
 */
export function DashboardHeader({
  lastUpdated,
  onRefresh,
  isRefreshing,
  className,
}: DashboardHeaderProps) {
  const formatLastUpdated = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 5) return "just now";
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      {/* Title & Description */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Mission Control</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Real-time overview of your DeerFlow operations
        </p>
      </div>

      {/* Refresh Control */}
      <div className="flex items-center gap-3">
        {lastUpdated && (
          <span className="text-muted-foreground text-xs">
            Updated {formatLastUpdated(lastUpdated)}
          </span>
        )}
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw
              className={cn("size-4", isRefreshing && "animate-spin")}
            />
            Refresh
          </Button>
        )}
      </div>
    </div>
  );
}
