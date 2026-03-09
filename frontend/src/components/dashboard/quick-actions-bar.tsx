"use client";

import Link from "next/link";
import {
  Bot,
  MessageSquarePlus,
  Puzzle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface QuickActionsBarProps {
  className?: string;
}

/**
 * QuickActionsBar - Quick action buttons for common tasks
 * New Thread, New Agent, Install Skill
 */
export function QuickActionsBar({ className }: QuickActionsBarProps) {
  return (
    <div
      className={cn(
        "bg-card flex flex-wrap items-center gap-3 rounded-lg border p-4",
        className,
      )}
    >
      <span className="text-muted-foreground mr-2 text-sm font-medium">
        Quick Actions:
      </span>

      <Link href="/workspace/chats/new">
        <Button variant="outline" size="sm" className="gap-2">
          <MessageSquarePlus className="size-4" />
          New Thread
        </Button>
      </Link>

      <Link href="/workspace/agents/new">
        <Button variant="outline" size="sm" className="gap-2">
          <Bot className="size-4" />
          New Agent
        </Button>
      </Link>

      <Button variant="outline" size="sm" className="gap-2" disabled>
        <Puzzle className="size-4" />
        Install Skill
      </Button>
    </div>
  );
}
