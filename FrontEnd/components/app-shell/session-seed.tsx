"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { sessionKey } from "@/lib/api/client"
import type { Session } from "@/lib/api/schemas"

// The layout already fetched the session on the server. Seeding the query cache
// with it gives client mutations their CSRF token without a second /api/auth/me.
// Like HydrationBoundary, it only writes during render when the cache has nothing
// yet, so no mounted observer is updated in the middle of a render.
export function SessionSeed({ session }: { session: Session }) {
  const queryClient = useQueryClient()
  useState(() => {
    if (queryClient.getQueryData(sessionKey) === undefined) {
      queryClient.setQueryData(sessionKey, session)
    }
  })
  return null
}
