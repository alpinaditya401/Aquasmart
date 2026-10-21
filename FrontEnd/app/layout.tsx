import type { Metadata } from "next"
import { Providers } from "@/components/providers"
import "./globals.css"

export const metadata: Metadata = {
  title: "AquaSmart AIoT",
  description:
    "Pemantauan kualitas air akuakultur: pH, suhu, dan kekeruhan. Aktuasi perangkat belum terbukti di alat fisik.",
  keywords: ["akuakultur", "IoT", "kualitas air", "pemantauan"],
  authors: [{ name: "Alpin Aditya Pratama" }, { name: "Dimas Aryo Sejati" }],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="font-body bg-foam text-ink antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
