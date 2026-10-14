"use client"

import { Menu, X } from "lucide-react"
import { usePathname } from "next/navigation"
import { useEffect } from "react"
import { button } from "@/components/ui/styles"
import { useUIStore } from "@/store/useUIStore"
import { LogoutButton } from "./logout-button"
import { NavLinks } from "./nav-links"

// Below the lg breakpoint the sidebar folds into this labelled menu. Seven
// destinations are too many for a bottom bar, and a bare hamburger hides that a
// menu exists at all, so the button says "Menu".
export function MobileMenu({ unacknowledged }: { unacknowledged: number }) {
  const open = useUIStore((state) => state.mobileMenuOpen)
  const toggle = useUIStore((state) => state.toggleMobileMenu)
  const close = useUIStore((state) => state.closeMobileMenu)
  const pathname = usePathname()

  // A route change means the user picked a destination; leave the menu closed.
  // biome-ignore lint/correctness/useExhaustiveDependencies: pathname is the trigger, not an input.
  useEffect(() => {
    close()
  }, [pathname, close])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, close])

  return (
    <div className="lg:hidden">
      <button
        type="button"
        className={button({ tone: "secondary" })}
        aria-expanded={open}
        aria-controls="mobile-navigation"
        onClick={toggle}
      >
        {open ? (
          <X aria-hidden="true" className="size-5" />
        ) : (
          <Menu aria-hidden="true" className="size-5" />
        )}
        Menu
      </button>
      {open ? (
        <nav
          id="mobile-navigation"
          aria-label="Navigasi utama"
          className="absolute inset-x-0 top-full z-40 border-b border-foam-line bg-surface-white p-4 shadow-elevated"
        >
          <NavLinks unacknowledged={unacknowledged} onNavigate={close} />
          <div className="mt-4 border-t border-foam-line pt-4">
            <LogoutButton />
          </div>
        </nav>
      ) : null}
    </div>
  )
}
