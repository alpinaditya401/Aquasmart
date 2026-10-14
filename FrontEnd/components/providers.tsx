"use client"

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import { ApiError, ContractError, sessionKey } from "@/lib/api/client"

// "unauthenticated" means the PHP session is gone; mark the user as logged out so
// guarded UI reacts at once. Other 401s, such as invalid_credentials on the login
// form, say nothing about the current session.
function dropSessionOn401(client: QueryClient, error: Error) {
  if (error instanceof ApiError && error.code === "unauthenticated") {
    client.setQueryData(sessionKey, null)
  }
}

// 4xx answers and contract mismatches will not change on retry; network failures
// (status 0, raised by apiRequest when fetch itself fails) and 5xx might.
function shouldRetry(failureCount: number, error: Error) {
  if (error instanceof ContractError) return false
  if (error instanceof ApiError && error.status !== 0 && error.status < 500) return false
  return failureCount < 1
}

export function Providers({ children }: { children: React.ReactNode }) {
  // Created in state, not at module scope: one server process renders for many
  // users, and a module-level client would share its cache between them.
  const [queryClient] = useState(() => {
    const client: QueryClient = new QueryClient({
      queryCache: new QueryCache({ onError: (error) => dropSessionOn401(client, error) }),
      mutationCache: new MutationCache({
        onError: (error) => dropSessionOn401(client, error),
        // Nearly every write on the server also appends to audit_logs.
        onSuccess: () => client.invalidateQueries({ queryKey: ["audit-logs"] }),
      }),
      defaultOptions: {
        queries: { staleTime: 30_000, retry: shouldRetry, refetchOnWindowFocus: false },
        mutations: { retry: false },
      },
    })
    return client
  })

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
