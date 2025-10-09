"use client";

import { TheoremSearch } from "@/components/TheoremSearch";
import { HealthStatus } from "@/components/HealthStatus";
import { ServerType } from "@/lib/api";

interface SearchPageProps {
  serverType: ServerType;
}

export function SearchPage({ serverType }: SearchPageProps) {
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

          {/* Health Status */}
          <div className="flex justify-center mb-6">
            <HealthStatus serverType={serverType} />
          </div>
        </div>

        {/* Main Search Interface */}
        <TheoremSearch serverType={serverType} />
      </div>
    </div>
  );
}
