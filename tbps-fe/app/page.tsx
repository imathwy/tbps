"use client";

import { useState } from "react";
import { TheoremSearch } from "@/components/TheoremSearch";
import { HealthStatus } from "@/components/HealthStatus";
import { ServerSelector } from "@/components/ServerSelector";

export default function Home() {
  const [selectedServer, setSelectedServer] = useState<"mock" | "production">(
    "mock",
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Theorem Similarity Search
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-6">
            Find similar theorems using edit distance and Weisfeiler-Leman
            kernels
          </p>

          {/* Server Selector and Health Status */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
            <ServerSelector
              selectedServer={selectedServer}
              onServerChange={setSelectedServer}
            />
            <HealthStatus selectedServer={selectedServer} />
          </div>
        </div>

        {/* Main Search Interface */}
        <TheoremSearch selectedServer={selectedServer} />
      </div>
    </div>
  );
}
