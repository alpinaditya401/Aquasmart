import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"

// Hanya state tampilan. Data server (perangkat, pembacaan, alert) ditangani
// TanStack Query; mencampurnya ke sini membuat cache punya dua sumber kebenaran.
type UIState = {
  sidebarOpen: boolean
  mobileMenuOpen: boolean
  activeModal: string | null
  toggleSidebar: () => void
  closeSidebar: () => void
  toggleMobileMenu: () => void
  closeMobileMenu: () => void
  openModal: (id: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      mobileMenuOpen: false,
      activeModal: null,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      closeSidebar: () => set({ sidebarOpen: false }),
      toggleMobileMenu: () => set((state) => ({ mobileMenuOpen: !state.mobileMenuOpen })),
      closeMobileMenu: () => set({ mobileMenuOpen: false }),
      openModal: (id) => set({ activeModal: id }),
      closeModal: () => set({ activeModal: null }),
    }),
    {
      name: "aquasmart-ui",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      // Modal dan menu mobile sengaja tidak disimpan: memulihkannya saat reload
      // membuat halaman terbuka dengan overlay yang tidak diminta pengguna.
      partialize: (state) => ({ sidebarOpen: state.sidebarOpen }),
    },
  ),
)
