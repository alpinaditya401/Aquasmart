import type { z } from "zod"

// First message per top-level field, for rendering next to the input it belongs to.
export function fieldErrors(error: z.ZodError): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const issue of error.issues) {
    const key = String(issue.path[0] ?? "form")
    errors[key] ??= issue.message
  }
  return errors
}

// Only same-site paths may be used as a post-login destination; anything else
// (absolute URLs, protocol-relative //host) would turn the login page into an
// open redirect.
export function safeRedirect(target: string | undefined, fallback = "/dashboard"): string {
  if (!target?.startsWith("/") || target.startsWith("//") || target.startsWith("/\\")) {
    return fallback
  }
  return target
}
