"use client";

import { Geist } from "next/font/google";
import { useEffect } from "react";

import { monitorError } from "@/lib/monitoring";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Report the error to local monitoring service
    monitorError(error, { digest: error.digest, tags: { scope: "global" } });
  }, [error]);

  return (
    <html lang="en" className={geist.variable}>
      <body className="font-sans">
        <div className="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0a] p-4 text-white">
          <div className="max-w-md space-y-6 text-center">
            <div className="space-y-2">
              <h1 className="text-4xl font-bold tracking-tight text-red-500">
                Application Crash
              </h1>
              <p className="text-zinc-400">
                A critical error occurred in the application root. This is often
                due to a missing context provider or a hydration mismatch.
              </p>
            </div>

            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 text-left font-mono text-sm overflow-auto max-h-48">
              <p className="text-red-400 font-semibold">{error.name}: {error.message}</p>
              {error.stack && (
                <pre className="mt-2 text-zinc-500 text-xs">
                  {error.stack}
                </pre>
              )}
            </div>

            <button
              onClick={() => reset()}
              className="rounded-full bg-white px-8 py-3 font-medium text-black transition-transform hover:scale-105 active:scale-95"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
