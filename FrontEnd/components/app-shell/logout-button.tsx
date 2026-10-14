"use client"

import { LogOut } from "lucide-react"
import { useRouter } from "next/navigation"
import { button } from "@/components/ui/styles"
import { useLogout } from "@/hooks/use-session"

export function LogoutButton() {
  const router = useRouter()
  const logout = useLogout()
  return (
    <div>
      <button
        type="button"
        className={button({ tone: "secondary" })}
        disabled={logout.isPending}
        onClick={() =>
          logout.mutate(undefined, {
            onSuccess: () => {
              router.replace("/login")
              router.refresh()
            },
          })
        }
      >
        <LogOut aria-hidden="true" className="size-5" />
        {logout.isPending ? "Keluar..." : "Keluar"}
      </button>
      {logout.isError ? (
        <p role="alert" className="mt-2 text-sm text-alarm-coral-text">
          {logout.error.message}
        </p>
      ) : null}
    </div>
  )
}
