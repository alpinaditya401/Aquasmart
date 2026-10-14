"use client"

import { useEffect, useRef } from "react"

// A destructive action asks before it acts, and the confirmation step replaces the
// button that opened it. Without this, focus falls to the body at exactly the moment
// the keyboard user needs to answer a question. Focus moves to the labelled fieldset
// rather than to the confirm button, so the question is read out and the next Enter
// does not fire the destructive action.
//
// This lives outside components/ui/styles.ts on purpose: it is behaviour, not paint.
export function useConfirmFocus(confirming: boolean) {
  const ref = useRef<HTMLFieldSetElement>(null)
  useEffect(() => {
    if (confirming) ref.current?.focus()
  }, [confirming])
  return ref
}
