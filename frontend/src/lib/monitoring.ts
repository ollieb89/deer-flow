/**
 * Centralized error reporting and monitoring utility.
 * In the future, this can be integrated with external services like Sentry, LogRocket, or OpenTelemetry.
 */

export interface ErrorReportMetadata {
  digest?: string;
  componentStack?: string;
  tags?: Record<string, string | number | boolean>;
}

export const monitorError = (error: Error | unknown, metadata?: ErrorReportMetadata) => {
  const isProd = process.env.NODE_ENV === "production";
  
  // 1. Log to console for local development
  console.group("🚨 Error Monitored");
  console.error("Error/Exception:", error instanceof Error ? error.message : "Caught non-error object");
  console.error("Metadata:", metadata);
  if (error instanceof Error) console.error("Stack Trace:", error.stack);
  console.groupEnd();

  // 2. Implementation for external logging (Placeholder)
  if (isProd) {
    // This is where you would call:
    // Sentry.captureException(error, { extra: metadata });
    // Or send to your custom logging endpoint:
    // fetch('/api/log-error', { method: 'POST', body: JSON.stringify({ error, metadata }) });
    
    // For now, let's just log it to stdout on the server if it's SSR
    if (typeof window === "undefined") {
      process.stdout.write(`[PROD ERROR] ${new Date().toISOString()}: ${error instanceof Error ? error.stack : String(error)}\n`);
    } else {
       // On client, we could send it to a tracking pixel or analytics endpoint
    }
  }
};
