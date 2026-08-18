/** Minimal theme store for `useSyncExternalStore`.
 *
 *  The architecture explorer's canvas cannot read CSS variables per frame, so it needs a
 *  boolean it can subscribe to. This is that boolean.
 */

type Theme = "light" | "dark" | "system";
type Resolved = "light" | "dark";

const KEY = "accountingai.theme";
const listeners = new Set<() => void>();
let resolved: Resolved = "light";

function computeResolved(theme: Theme): Resolved {
  if (theme !== "system") return theme;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function initTheme() {
  if (typeof window === "undefined") return;
  const stored = (window.localStorage.getItem(KEY) as Theme | null) ?? "system";
  applyTheme(stored);
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      const current = (window.localStorage.getItem(KEY) as Theme | null) ?? "system";
      if (current === "system") applyTheme("system");
    });
}

export function applyTheme(theme: Theme) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, theme);
  resolved = computeResolved(theme);
  document.documentElement.setAttribute("data-theme", resolved);
  listeners.forEach((l) => l());
}

export function subscribeResolved(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getResolvedSnapshot(): Resolved {
  return resolved;
}

export function getResolvedServerSnapshot(): Resolved {
  return "light";
}
