"use client";

import { SWRConfig } from "swr";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        refreshInterval: 30000, // Refresh every 30 seconds for health checks
        dedupingInterval: 5000, // Dedupe requests within 5 seconds
        revalidateOnFocus: false,
        revalidateOnReconnect: true,
        fetcher: (url: string) =>
          fetch(url).then((res) => {
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
          }),
      }}
    >
      {children}
    </SWRConfig>
  );
}
