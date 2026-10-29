import { useEffect, useRef } from "react";

/**
 * Focuses the first invalid control (DOM order) each time a submit fails (R31d).
 * Pass RHF's `formState.submitCount` and `isValid`-independent `errorCount`.
 */
export function useFormFocusFirstError(submitCount: number, errorCount: number) {
  const formRef = useRef<HTMLFormElement>(null);
  useEffect(() => {
    if (submitCount === 0 || errorCount === 0) return;
    formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
  }, [submitCount, errorCount]);
  return formRef;
}
