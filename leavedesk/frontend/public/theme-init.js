// Same-origin script (CSP script-src 'self'): applies the saved theme before
// first paint. Keep in sync with src/lib/theme.ts. Failure means System mode.
try {
  var t = localStorage.getItem("leavedesk-theme");
  if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
} catch (e) {
  /* storage blocked: stay on System */
}
