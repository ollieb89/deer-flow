/**
 * API client for kilocode model discovery
 */

import { getBackendBaseURL } from "@/core/config";

import type {
  DryRunResponse,
  KilocodeModel,
  ModelsListResponse,
  SyncLogEntry,
  SyncRequest,
  SyncResponse,
} from "./types";

const BASE_URL = "/api/kilocode";

function getUrl(path: string): string {
  return `${getBackendBaseURL()}${BASE_URL}${path}`;
}

/**
 * Fetch all kilocode models with optional filtering
 */
export async function fetchKilocodeModels(
  options?: {
    provider?: string;
    search?: string;
    capabilities?: string[];
  }
): Promise<ModelsListResponse> {
  const params = new URLSearchParams();
  if (options?.provider) params.set("provider", options.provider);
  if (options?.search) params.set("search", options.search);
  if (options?.capabilities?.length) {
    options.capabilities.forEach((cap) => params.append("capabilities", cap));
  }

  const query = params.toString();
  const url = getUrl(`/models${query ? `?${query}` : ""}`);

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch models: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch a specific model by ID
 */
export async function fetchKilocodeModel(modelId: string): Promise<KilocodeModel> {
  const res = await fetch(getUrl(`/models/${encodeURIComponent(modelId)}`));
  if (!res.ok) {
    throw new Error(`Failed to fetch model: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch all providers
 */
export async function fetchKilocodeProviders(): Promise<ModelsListResponse["providers"]> {
  const res = await fetch(getUrl("/providers"));
  if (!res.ok) {
    throw new Error(`Failed to fetch providers: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Perform a dry run to preview available models
 */
export async function dryRunSync(): Promise<DryRunResponse> {
  const res = await fetch(getUrl("/sync/dry-run"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Dry run failed: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Sync models from kilocode
 */
export async function syncKilocodeModels(dryRun = false): Promise<SyncResponse> {
  const body: SyncRequest = { dry_run: dryRun };
  const res = await fetch(getUrl("/sync"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Sync failed: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch sync logs
 */
export async function fetchSyncLogs(limit = 10): Promise<SyncLogEntry[]> {
  const res = await fetch(getUrl(`/sync/logs?limit=${limit}`));
  if (!res.ok) {
    throw new Error(`Failed to fetch sync logs: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Toggle model active state
 */
export async function toggleModelActive(modelId: string): Promise<KilocodeModel> {
  const res = await fetch(getUrl(`/models/${encodeURIComponent(modelId)}/toggle`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to toggle model: ${res.statusText}`);
  }
  return res.json();
}
