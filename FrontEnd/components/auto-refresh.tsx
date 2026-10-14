"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

// Re-renders the Server Components on a timer so readings stay current without
// moving the data into client state. Paused while the tab is hidden, matching the
// old SPA, which stops work nobody is looking at.
export function AutoRefresh({ seconds }: { seconds: number }) {
  const router = useRouter()
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") router.refresh()
    }, seconds * 1000)
    return () => window.clearInterval(timer)
  }, [router, seconds])
  return null
}
