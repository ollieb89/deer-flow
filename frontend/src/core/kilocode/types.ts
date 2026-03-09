/**
 * Types for kilocode model discovery API
 */

export interface KilocodeProvider {
  id: string;
  name: string;
  display_name: string | null;
  description: string | null;
  model_count: number;
}

export interface ModelCapabilities {
  vision: boolean;
  thinking: boolean;
  tool_calling: boolean;
  streaming: boolean;
}

export interface ModelPricing {
  prompt: string | null;
  completion: string | null;
}

export interface KilocodeModel {
  id: string;
  model_id: string;
  name: string;
  provider: KilocodeProvider;
  capabilities: ModelCapabilities;
  context_length: number | null;
  max_output_tokens: number | null;
  pricing: ModelPricing | null;
  is_active: boolean;
  is_featured: boolean;
  last_synced_at: string;
}

export interface ModelsListResponse {
  models: KilocodeModel[];
  total: number;
  providers: KilocodeProvider[];
}

export interface DryRunResponse {
  total_models: number;
  provider_count: number;
  providers: Array<{
    name: string;
    display_name: string;
    models: Array<{
      model_id: string;
      name: string;
      context_length?: number;
      pricing?: ModelPricing;
    }>;
  }>;
  sample_models: Array<{
    id: string;
    name: string;
    owned_by: string;
  }>;
}

export interface SyncRequest {
  dry_run: boolean;
}

export interface SyncResponse {
  operation: string;
  models_found: number;
  models_added: number;
  models_updated: number;
  models_unchanged: number;
  providers_created: number;
}

export interface SyncLogEntry {
  id: string;
  operation: string;
  status: string;
  models_found: number | null;
  models_added: number | null;
  models_updated: number | null;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}
