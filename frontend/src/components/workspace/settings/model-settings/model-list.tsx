"use client";

import { useState } from "react";
import {
  Brain,
  Check,
  Eye,
  Loader2,
  RefreshCw,
  Search,
  Wrench,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { KilocodeModel, KilocodeProvider } from "@/core/kilocode";
import { cn } from "@/lib/utils";

interface ModelListProps {
  models: KilocodeModel[];
  providers: KilocodeProvider[];
  onToggleModel: (modelId: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export function ModelList({
  models,
  providers,
  onToggleModel,
  onRefresh,
  isLoading,
}: ModelListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [selectedCapability, setSelectedCapability] = useState<string>("all");

  // Filter models
  const filteredModels = models.filter((model) => {
    const matchesSearch =
      searchQuery === "" ||
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.model_id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProvider =
      selectedProvider === "all" || model.provider.name === selectedProvider;

    const matchesCapability =
      selectedCapability === "all" ||
      (selectedCapability === "vision" && model.capabilities.vision) ||
      (selectedCapability === "thinking" && model.capabilities.thinking) ||
      (selectedCapability === "tool_calling" && model.capabilities.tool_calling);

    return matchesSearch && matchesProvider && matchesCapability;
  });

  const activeModelsCount = models.filter((m) => m.is_active).length;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={selectedProvider} onValueChange={setSelectedProvider}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All providers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All providers</SelectItem>
            {providers.map((provider) => (
              <SelectItem key={provider.id} value={provider.name}>
                {provider.display_name || provider.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedCapability} onValueChange={setSelectedCapability}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All capabilities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All capabilities</SelectItem>
            <SelectItem value="vision">Vision</SelectItem>
            <SelectItem value="thinking">Thinking</SelectItem>
            <SelectItem value="tool_calling">Tool Calling</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="icon"
          onClick={onRefresh}
          disabled={isLoading}
        >
          <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
        </Button>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>
          Showing {filteredModels.length} of {models.length} models
        </span>
        <span className="text-border">|</span>
        <span>{activeModelsCount} active</span>
      </div>

      {/* Model Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Model</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Capabilities</TableHead>
              <TableHead>Context</TableHead>
              <TableHead className="text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredModels.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  No models found
                </TableCell>
              </TableRow>
            ) : (
              filteredModels.map((model) => (
                <TableRow key={model.id}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{model.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {model.model_id}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {model.provider.display_name || model.provider.name}
                  </TableCell>
                  <TableCell>
                    <TooltipProvider>
                      <div className="flex items-center gap-1">
                        {model.capabilities.vision && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="secondary" className="h-6 w-6 p-0">
                                <Eye className="h-3 w-3" />
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>Vision</TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.thinking && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="secondary" className="h-6 w-6 p-0">
                                <Brain className="h-3 w-3" />
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>Thinking</TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.tool_calling && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="secondary" className="h-6 w-6 p-0">
                                <Wrench className="h-3 w-3" />
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>Tool Calling</TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell>
                    {model.context_length
                      ? `${(model.context_length / 1000).toFixed(0)}k`
                      : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant={model.is_active ? "default" : "outline"}
                      size="sm"
                      onClick={() => onToggleModel(model.model_id)}
                      disabled={isLoading}
                    >
                      {model.is_active ? (
                        <>
                          <Check className="mr-1 h-3 w-3" />
                          Active
                        </>
                      ) : (
                        <>
                          <X className="mr-1 h-3 w-3" />
                          Inactive
                        </>
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
