import { useState } from "react";
import { applyTheme, readTheme, saveTheme, THEME_MODES, type ThemeMode } from "../../lib/theme";

const LABEL: Record<ThemeMode, string> = { system: "System", light: "Light", dark: "Dark" };
const ICON: Record<ThemeMode, string> = { system: "◐", light: "☀", dark: "☾" };

/** Cycles System, Light, Dark. Label names the current mode and what a press does. */
export function ThemeToggle() {
  const [mode, setMode] = useState<ThemeMode>(readTheme);
  const next = THEME_MODES[(THEME_MODES.indexOf(mode) + 1) % THEME_MODES.length];
  return (
    <button
      type="button"
      className="icon-btn"
      aria-label={`Theme: ${LABEL[mode]}. Switch to ${LABEL[next]}`}
      onClick={() => {
        setMode(next);
        applyTheme(next);
        saveTheme(next);
      }}
    >
      <span aria-hidden="true">{ICON[mode]}</span>
    </button>
  );
}
