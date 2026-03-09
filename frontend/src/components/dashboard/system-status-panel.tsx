"use client";

import {
  Bot,
  Brain,
  Cpu,
  Wrench,
} from "lucide-react";

import type { SystemStatus } from "@/core/dashboard";
import { cn } from "@/lib/utils";

export interface SystemStatusPanelProps {
  status: SystemStatus | null;
  isLoading?: boolean;
  className?: string;
}

/**
 * SystemStatusPanel - Displays system information
 * Shows: Models, Skills, Tools, Memory
 */
export function SystemStatusPanel({
  status,
  isLoading,
  className,
}: SystemStatusPanelProps) {
  return (
    <div className={cn("bg-card flex flex-col rounded-lg border", className)}>
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center gap-2">
          <Cpu className="text-muted-foreground size-4" />
          <h3 className="font-semibold">System Status</h3>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-4 overflow-auto p-4">
        {isLoading || !status ? (
          // Loading skeleton
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="bg-muted h-4 w-24 animate-pulse rounded" />
                <div className="bg-muted h-8 w-full animate-pulse rounded" />
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Models Section */}
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Brain className="text-muted-foreground size-3.5" />
                <h4 className="text-sm font-medium">Models</h4>
                <span className="text-muted-foreground text-xs">
                  ({status.models.length})
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {status.models.slice(0, 5).map((model) => (
                  <span
                    key={model.id}
                    className="bg-secondary text-secondary-foreground inline-flex items-center rounded-md px-2 py-1 text-xs"
                  >
                    {model.display_name}
                  </span>
                ))}
                {status.models.length > 5 && (
                  <span className="text-muted-foreground text-xs">
                    +{status.models.length - 5} more
                  </span>
                )}
              </div>
            </div>

            {/* Skills Section */}
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Bot className="text-muted-foreground size-3.5" />
                <h4 className="text-sm font-medium">Skills</h4>
                <span className="text-muted-foreground text-xs">
                  ({status.skills.filter((s) => s.enabled).length} enabled)
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {status.skills
                  .filter((s) => s.enabled)
                  .slice(0, 5)
                  .map((skill) => (
                    <span
                      key={skill.name}
                      className="bg-primary/10 text-primary inline-flex items-center rounded-md px-2 py-1 text-xs"
                    >
                      {skill.name}
                    </span>
                  ))}
                {status.skills.filter((s) => s.enabled).length > 5 && (
                  <span className="text-muted-foreground text-xs">
                    +
                    {status.skills.filter((s) => s.enabled).length - 5} more
                  </span>
                )}
              </div>
            </div>

            {/* Tools Section */}
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Wrench className="text-muted-foreground size-3.5" />
                <h4 className="text-sm font-medium">Tools</h4>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {status.toolGroups.map((tool) => (
                  <span
                    key={tool}
                    className="bg-secondary text-secondary-foreground inline-flex items-center rounded-md px-2 py-1 text-xs"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* Memory Section */}
            <div className="border-t pt-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="text-muted-foreground size-3.5" />
                  <h4 className="text-sm font-medium">Memory</h4>
                </div>
                <span className="text-sm tabular-nums">
                  {status.memoryFacts} facts stored
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
