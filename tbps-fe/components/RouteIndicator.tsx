"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function RouteIndicator() {
  const pathname = usePathname();

  const isOnMock = pathname === "/mock";
  const isOnProd = pathname === "/prod";

  return (
    <div className="mb-6">
      <div className="flex items-center justify-center gap-2">
        <Link href="/mock">
          <Button
            variant={isOnMock ? "default" : "outline"}
            size="sm"
            className={cn("transition-all", isOnMock && "shadow-md")}
          >
            Development Mode
          </Button>
        </Link>
        <span className="text-slate-400">|</span>
        <Link href="/prod">
          <Button
            variant={isOnProd ? "default" : "outline"}
            size="sm"
            className={cn("transition-all", isOnProd && "shadow-md")}
          >
            Production Mode
          </Button>
        </Link>
      </div>

      {isOnMock && (
        <p className="text-xs text-slate-500 text-center mt-2">
          Using simulated data - no external dependencies required
        </p>
      )}

      {isOnProd && (
        <p className="text-xs text-slate-500 text-center mt-2">
          Using real computation with database and Lean tool
        </p>
      )}
    </div>
  );
}
