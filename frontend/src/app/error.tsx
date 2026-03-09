"use client";

import { useEffect } from "react";

import { monitorError } from "@/lib/monitoring";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Report the error to local monitoring service
    monitorError(error, { digest: error.digest, tags: { scope: "page" } });
  }, [error]);

  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center p-8 text-center text-white">
      <div className="max-w-xl space-y-6">
        <div className="space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-500">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="h-6 w-6"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
              />
            </svg>
          </div>
          <h2 className="text-3xl font-bold tracking-tight">Something went wrong!</h2>
          <p className="text-zinc-400">
            An error occurred while rendering this page segment. This has been logged and we&apos;re looking into it.
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 text-left font-mono text-sm shadow-xl">
          <p className="text-red-400 font-semibold mb-2">{error.name}: {error.message}</p>
          <p className="text-zinc-500 text-xs">If this persists, please contact support with the digest: {error.digest ?? 'N/A'}</p>
        </div>

        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <button
            onClick={() => reset()}
            className="w-full rounded-full bg-blue-600 px-8 py-3 font-medium text-white transition-all hover:bg-blue-700 active:scale-95 sm:w-auto"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-full border border-zinc-700 bg-transparent px-8 py-3 font-medium text-white transition-all hover:bg-zinc-800 active:scale-95 sm:w-auto"
          >
            Reload Window
          </button>
        </div>
      </div>
    </div>
  );
}
