import type { NextConfig } from "next"

const config: NextConfig = {
  reactStrictMode: true,
  // Build harus gagal saat tipe atau lint bermasalah. Rubrik menilai type-safety,
  // dan menyembunyikan error di sini membuat gerbang CI kehilangan artinya.
  typescript: { ignoreBuildErrors: false },
}

export default config
