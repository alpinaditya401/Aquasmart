import Link from "next/link"
import { button, heading } from "@/components/ui/styles"

// Empty state: says why the page is empty and gives the one action that fills it.
export function NoDevice({ isAdmin }: { isAdmin: boolean }) {
  return (
    <section className="rounded-panel border border-foam-line bg-surface-white p-6">
      <h1 className={heading({ level: "section" })}>Hubungkan alat pertama Anda</h1>
      <p className="mt-2 max-w-prose text-sm text-ink">
        Akun sudah aktif, tetapi belum ada perangkat AquaSmart yang terhubung. Pembacaan pH, suhu,
        dan kekeruhan muncul di sini setelah perangkat dihubungkan.
      </p>
      {isAdmin ? (
        <Link href="/dashboard/settings" className={button({ className: "mt-4" })}>
          Hubungkan perangkat di Pengaturan
        </Link>
      ) : (
        <p className="mt-4 text-sm text-muted">
          Akun viewer tidak bisa menambah perangkat. Minta admin ruang budidaya menghubungkannya.
        </p>
      )}
    </section>
  )
}
