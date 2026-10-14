"use client"

import { LogIn } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useLogin } from "@/hooks/use-session"
import { LoginInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"

export function LoginForm({ redirectTo }: { redirectTo: string }) {
  const router = useRouter()
  const login = useLogin()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showPassword, setShowPassword] = useState(false)

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const parsed = LoginInput.safeParse({
      username: data.get("username"),
      password: data.get("password"),
    })
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    login.mutate(parsed.data, {
      onSuccess: () => {
        router.replace(redirectTo)
        router.refresh()
      },
    })
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <Field id="username" label="Email, nomor WA, atau username" error={errors.username}>
        <input
          name="username"
          autoComplete="username"
          className={control()}
          {...fieldProps("username", { error: errors.username })}
        />
      </Field>

      <Field id="password" label="Password" error={errors.password}>
        <div className="flex gap-2">
          <input
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            className={control()}
            {...fieldProps("password", { error: errors.password })}
          />
          <button
            type="button"
            className={button({ tone: "secondary" })}
            aria-pressed={showPassword}
            aria-controls="password"
            onClick={() => setShowPassword((shown) => !shown)}
          >
            {showPassword ? "Sembunyikan" : "Tampilkan"}
          </button>
        </div>
      </Field>

      {login.isError ? (
        <p
          role="alert"
          className="rounded-crisp border border-alarm-coral-text p-3 text-sm text-alarm-coral-text"
        >
          {login.error.message}
        </p>
      ) : null}

      <button type="submit" className={button({ className: "w-full" })} disabled={login.isPending}>
        <LogIn aria-hidden="true" className="size-5" />
        {login.isPending ? "Memeriksa akun..." : "Masuk Dashboard"}
      </button>
    </form>
  )
}
