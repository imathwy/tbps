"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Server, TestTube } from "lucide-react";
import { ServerType } from "@/lib/api";

interface ServerSelectorProps {
  selectedServer: ServerType;
  onServerChange: (server: ServerType) => void;
}

export function ServerSelector({
  selectedServer,
  onServerChange,
}: ServerSelectorProps) {
  return (
    <Card className="p-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Server:
        </span>
        <div className="flex gap-2">
          <Button
            variant={selectedServer === "mock" ? "default" : "outline"}
            size="sm"
            onClick={() => onServerChange("mock")}
            className="flex items-center gap-2"
          >
            <TestTube size={16} />
            Mock
            <Badge variant="secondary" className="ml-1 text-xs">
              :8001
            </Badge>
          </Button>
          <Button
            variant={selectedServer === "production" ? "default" : "outline"}
            size="sm"
            onClick={() => onServerChange("production")}
            className="flex items-center gap-2"
          >
            <Server size={16} />
            Production
            <Badge variant="secondary" className="ml-1 text-xs">
              :8000
            </Badge>
          </Button>
        </div>
      </div>
    </Card>
  );
}
