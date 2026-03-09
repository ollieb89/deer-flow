"use client";

import { useState } from "react";
import {
  CloudDownload,
  Loader2,
  Play,
  RotateCcw,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import {
  dryRunSync,
  syncKilocodeModels,
  type DryRunResponse,
  type SyncResponse,
} from "@/core/kilocode";
import { cn } from "@/lib/utils";

interface SyncDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSyncComplete: () => void;
}

type SyncState = "idle" | "dry-running" | "dry-run-complete" | "syncing" | "complete" | "error";

export function SyncDialog({ open, onOpenChange, onSyncComplete }: SyncDialogProps) {

  const [syncState, setSyncState] = useState<SyncState>("idle");
  const [dryRunResult, setDryRunResult] = useState<DryRunResponse | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDryRun = async () => {
    setSyncState("dry-running");
    setError(null);

    try {
      const result = await dryRunSync();
      setDryRunResult(result);
      setSyncState("dry-run-complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry run failed");
      setSyncState("error");
      toast.error("Dry Run Failed", {
        description: err instanceof Error ? err.message : "An error occurred",
      });
    }
  };

  const handleSync = async () => {
    setSyncState("syncing");
    setError(null);

    try {
      const result = await syncKilocodeModels(false);
      setSyncResult(result);
      setSyncState("complete");
      toast.success("Sync Complete", {
        description: `Added ${result.models_added}, updated ${result.models_updated} models`,
      });
      onSyncComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
      setSyncState("error");
      toast.error("Sync Failed", {
        description: err instanceof Error ? err.message : "An error occurred",
      });
    }
  };

  const handleReset = () => {
    setSyncState("idle");
    setDryRunResult(null);
    setSyncResult(null);
    setError(null);
  };

  const handleClose = () => {
    handleReset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CloudDownload className="h-5 w-5" />
            Sync Models from Kilocode
          </DialogTitle>
          <DialogDescription>
            Fetch and synchronize available AI models from the kilocode gateway.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Action Buttons */}
          {syncState === "idle" && (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <p className="text-muted-foreground text-center max-w-md">
                First, run a dry run to preview what models are available from
                kilocode without modifying your local database.
              </p>
              <Button onClick={handleDryRun} size="lg">
                <Play className="mr-2 h-4 w-4" />
                Run Dry Run
              </Button>
            </div>
          )}

          {syncState === "dry-running" && (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground">
                Fetching available models from kilocode...
              </p>
            </div>
          )}

          {/* Dry Run Results */}
          {syncState === "dry-run-complete" && dryRunResult && (
            <>
              <div className="rounded-lg border p-4 bg-muted/50">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold">{dryRunResult.total_models}</p>
                    <p className="text-sm text-muted-foreground">Total Models</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {dryRunResult.provider_count}
                    </p>
                    <p className="text-sm text-muted-foreground">Providers</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {dryRunResult.providers.reduce(
                        (acc, p) => acc + p.models.length,
                        0
                      )}
                    </p>
                    <p className="text-sm text-muted-foreground">Ready to Sync</p>
                  </div>
                </div>
              </div>

              <ScrollArea className="h-[300px] rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead className="text-right">Models</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dryRunResult.providers.map((provider) => (
                      <TableRow key={provider.name}>
                        <TableCell className="font-medium">
                          {provider.display_name}
                        </TableCell>
                        <TableCell className="text-right">
                          {provider.models.length}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>

              <DialogFooter className="gap-2">
                <Button variant="outline" onClick={handleReset}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Start Over
                </Button>
                <Button onClick={handleSync}>
                  <CloudDownload className="mr-2 h-4 w-4" />
                  Sync to Database
                </Button>
              </DialogFooter>
            </>
          )}

          {/* Syncing */}
          {syncState === "syncing" && (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground">Syncing models to database...</p>
            </div>
          )}

          {/* Complete */}
          {syncState === "complete" && syncResult && (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <CheckCircle className="h-12 w-12 text-green-500" />
              <div className="text-center">
                <p className="font-medium">Sync Complete!</p>
                <p className="text-sm text-muted-foreground">
                  Found {syncResult.models_found} models • Added{" "}
                  {syncResult.models_added} • Updated {syncResult.models_updated}
                </p>
              </div>
              <Button onClick={handleClose}>Close</Button>
            </div>
          )}

          {/* Error */}
          {syncState === "error" && error && (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <div className="text-center">
                <p className="font-medium">Sync Failed</p>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
              <Button variant="outline" onClick={handleReset}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
