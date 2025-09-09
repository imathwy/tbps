"use client";

import useSWR from "swr";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Database,
  Server,
} from "lucide-react";
import { HealthResponse, ServerType, API_URLS } from "@/lib/api";

interface HealthStatusProps {
  selectedServer: ServerType;
}

export function HealthStatus({ selectedServer }: HealthStatusProps) {
  const {
    data: health,
    error,
    isLoading,
    mutate,
  } = useSWR<HealthResponse>(`${API_URLS[selectedServer]}/health`, {
    refreshInterval: 30000, // Auto-refresh every 30 seconds
    revalidateOnFocus: false,
  });

  const getStatusIcon = (status: string) => {
    if (status === "healthy") {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    } else if (status === "degraded") {
      return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    } else {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    if (status === "healthy")
      return "bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800";
    if (status === "degraded")
      return "bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800";
    return "bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800";
  };

  if (isLoading && !health) {
    return (
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span className="text-sm">Checking health...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-700 dark:text-red-300">
              Connection failed
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => mutate()}
            disabled={isLoading}
          >
            {isLoading ? (
              <RefreshCw className="w-3 h-3 animate-spin" />
            ) : (
              "Retry"
            )}
          </Button>
        </div>
      </Card>
    );
  }

  if (!health) return null;

  return (
    <Card className={`p-4 transition-colors ${getStatusColor(health.status)}`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {getStatusIcon(health.status)}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium capitalize">
                {health.status}
              </span>
              <Badge variant="outline" className="text-xs">
                {health.version}
              </Badge>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex items-center gap-1">
                <Database className="w-3 h-3" />
                <span className="text-xs">
                  DB:{" "}
                  {health.database_connected ? (
                    <span className="text-green-600 dark:text-green-400">
                      ✓
                    </span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400">✗</span>
                  )}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <Server className="w-3 h-3" />
                <span className="text-xs">
                  Lean:{" "}
                  {health.lean_available ? (
                    <span className="text-green-600 dark:text-green-400">
                      ✓
                    </span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400">✗</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">
            {new Date().toLocaleTimeString()}
          </span>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => mutate()}
            disabled={isLoading}
            className="h-8 w-8 p-0"
          >
            <RefreshCw
              className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
      </div>
    </Card>
  );
}
