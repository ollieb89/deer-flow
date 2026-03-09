"use client";

import { useCallback, useEffect, useState } from "react";
import { CloudDownload, Database, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toast } from "sonner";
import { SettingsSection } from "@/components/workspace/settings/settings-section";
import {
  fetchKilocodeModels,
  toggleModelActive,
  type KilocodeModel,
  type KilocodeProvider,
} from "@/core/kilocode";

import { ModelList } from "./model-list";
import { SyncDialog } from "./sync-dialog";

export function ModelSettingsPage() {

  const [models, setModels] = useState<KilocodeModel[]>([]);
  const [providers, setProviders] = useState<KilocodeProvider[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncDialogOpen, setIsSyncDialogOpen] = useState(false);

  const loadModels = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetchKilocodeModels();
      setModels(response.models);
      setProviders(response.providers);
    } catch (err) {
      toast.error("Failed to load models", {
        description: err instanceof Error ? err.message : "An error occurred",
      });
      // Set empty arrays to prevent UI from hanging
      setModels([]);
      setProviders([]);
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleToggleModel = async (modelId: string) => {
    try {
      const updated = await toggleModelActive(modelId);
      setModels((prev) =>
        prev.map((m) => (m.model_id === modelId ? updated : m))
      );
      toast.success(updated.is_active ? "Model activated" : "Model deactivated", {
        description: `${updated.name} is now ${updated.is_active ? "active" : "inactive"}`,
      });
    } catch (err) {
      toast.error("Failed to toggle model", {
        description: err instanceof Error ? err.message : "An error occurred",
      });
    }
  };

  const handleSyncComplete = () => {
    loadModels();
  };

  const activeModelsCount = models.filter((m) => m.is_active).length;

  return (
    <SettingsSection
      title="Model Discovery"
      description="Browse and manage AI models available through the kilocode gateway."
    >
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Models</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{models.length}</div>
              <p className="text-xs text-muted-foreground">
                From {providers.length} providers
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Models</CardTitle>
              <Database className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeModelsCount}</div>
              <p className="text-xs text-muted-foreground">
                Available for use in conversations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sync Status</CardTitle>
              <CloudDownload className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {models.length > 0 ? "Synced" : "Not Synced"}
              </div>
              <p className="text-xs text-muted-foreground">
                {models.length > 0
                  ? "Last synced recently"
                  : "Run sync to fetch models"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Sync Button */}
        <div className="flex justify-end">
          <Button onClick={() => setIsSyncDialogOpen(true)}>
            <CloudDownload className="mr-2 h-4 w-4" />
            Sync from Kilocode
          </Button>
        </div>

        {/* Model List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : models.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No Models Found</CardTitle>
              <CardDescription>
                You haven&apos;t synced any models from kilocode yet. Click the
                button above to get started.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center py-8">
              <Database className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground text-center max-w-md">
                Syncing will fetch all available AI models from the kilocode
                gateway, including models from Anthropic, OpenAI, Mistral, and
                more.
              </p>
            </CardContent>
          </Card>
        ) : (
          <ModelList
            models={models}
            providers={providers}
            onToggleModel={handleToggleModel}
            onRefresh={loadModels}
            isLoading={isLoading}
          />
        )}
      </div>

      <SyncDialog
        open={isSyncDialogOpen}
        onOpenChange={setIsSyncDialogOpen}
        onSyncComplete={handleSyncComplete}
      />
    </SettingsSection>
  );
}
