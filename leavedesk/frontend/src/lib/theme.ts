export type ThemeMode = "system" | "light" | "dark";

export const THEME_KEY = "leavedesk-theme";
export const THEME_MODES: ThemeMode[] = ["system", "light", "dark"];

/** Saved choice; System when nothing valid is stored or storage throws. Never sent to the API. */
export function readTheme(): ThemeMode {
  try {
    const v = localStorage.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

/** Sets data-theme (absent for System, so prefers-color-scheme applies). tokens.css sets color-scheme from it. */
export function applyTheme(mode: ThemeMode): void {
  const root = document.documentElement;
  if (mode === "system") {
    delete root.dataset.theme;
  } else {
    root.dataset.theme = mode;
  }
}

export function saveTheme(mode: ThemeMode): void {
  try {
    if (mode === "system") localStorage.removeItem(THEME_KEY);
    else localStorage.setItem(THEME_KEY, mode);
  } catch {
    /* storage blocked: the choice lasts for this page view only */
  }
}
