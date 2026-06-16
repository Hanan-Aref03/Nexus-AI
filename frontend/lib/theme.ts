/** Shared theme helpers for the global workspace surface. */

export type SurfacePreference = "system" | "dark" | "light";
export type SurfaceMode = "dark" | "light";

export const SURFACE_STORAGE_KEY = "nexusai-surface-mode";

export function sanitizeSurfacePreference(value: string | null | undefined): SurfacePreference {
  if (value === "system" || value === "dark" || value === "light") {
    return value;
  }

  return "system";
}

export function resolveSurfaceMode(preference: SurfacePreference, prefersLight: boolean): SurfaceMode {
  if (preference === "system") {
    return prefersLight ? "light" : "dark";
  }

  return preference;
}

export function buildSurfaceBootstrapScript(): string {
  return `(() => {
    try {
      const storageKey = ${JSON.stringify(SURFACE_STORAGE_KEY)};
      const stored = window.localStorage.getItem(storageKey);
      const preference = stored === "system" || stored === "dark" || stored === "light" ? stored : "system";
      const resolved = preference === "system"
        ? (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark")
        : preference;
      const root = document.documentElement;
      root.dataset.surfacePreference = preference;
      root.dataset.surface = resolved;
      root.style.colorScheme = resolved;
    } catch {
      // Ignore bootstrap failures so the page can still render normally.
    }
  })();`;
}
