import { useEffect, useRef } from "react";
import { useToast } from "../components/toast/ToastProvider";

/** Toast on query error / empty-data conditions once per key change. */
export function useQueryErrorToast(
  error: unknown,
  fallback = "Request failed",
) {
  const { error: toastError } = useToast();
  const last = useRef<string>("");

  useEffect(() => {
    if (!error) return;
    const message = error instanceof Error ? error.message : fallback;
    if (last.current === message) return;
    last.current = message;
    toastError(message);
  }, [error, fallback, toastError]);
}

export function useEmptyDataToast(
  ready: boolean,
  isEmpty: boolean,
  message: string,
  key: string,
) {
  const { error: toastError } = useToast();
  const shown = useRef<string>("");

  useEffect(() => {
    if (!ready || !isEmpty) return;
    if (shown.current === key) return;
    shown.current = key;
    toastError(message, "No data");
  }, [ready, isEmpty, message, key, toastError]);
}
