"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { initTheme } from "@/lib/theme-store";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Tax data changes when a person changes it, not on a timer. Refetching on
            // window focus would re-pull a 40-row determination list every alt-tab.
            refetchOnWindowFocus: false,
            staleTime: 30_000,
            retry: 1,
          },
        },
      }),
  );

  useEffect(() => {
    initTheme();
  }, []);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
