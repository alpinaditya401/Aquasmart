import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { cache } from "react"
import type { z } from "zod"
import { ApiError, ContractError } from "./client"
import { ApiErrorBody, Session } from "./schemas"

// Server Components read from PHP directly instead of looping back through the BFF:
// the BFF exists for the browser, and a server-to-server call skips one hop. Only
// the PHP session cookie is forwarded, never the rest of the browser's cookies.
const SESSION_COOKIE = "aquasmart_session"

type ApiPath = `/api/${string}`

function backendUrl(): string {
  const url = process.env.AQUASMART_API_URL
  if (!url) throw new Error("AQUASMART_API_URL belum di-set")
  return url
}

export async function serverRequest<S extends z.ZodType>(
  path: ApiPath,
  schema: S,
): Promise<z.output<S>> {
  const session = (await cookies()).get(SESSION_COOKIE)
  const headers = new Headers({ Accept: "application/json" })
  if (session) headers.set("Cookie", `${SESSION_COOKIE}=${session.value}`)

  const response = await fetch(`${backendUrl()}${path}`, { headers, cache: "no-store" })
  const isJson = response.headers.get("content-type")?.includes("application/json") ?? false
  const payload: unknown = isJson ? await response.json() : null

  if (!response.ok) {
    const error = ApiErrorBody.safeParse(payload)
    throw error.success
      ? new ApiError(response.status, error.data.error.code, error.data.error.message)
      : new ApiError(
          response.status,
          "unexpected_response",
          `Server membalas HTTP ${response.status}.`,
        )
  }
  const parsed = schema.safeParse(payload)
  if (!parsed.success) throw new ContractError(path, parsed.error)
  return parsed.data
}

// cache() dedupes the call within one render, so the layout and the page can both
// ask for the session without a second round trip to PHP.
export const getSession = cache(async () => {
  try {
    return await serverRequest("/api/auth/me", Session)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
})

export async function requireSession(returnTo: string) {
  const session = await getSession()
  if (!session) redirect(`/login?redirect=${encodeURIComponent(returnTo)}`)
  return session
}
