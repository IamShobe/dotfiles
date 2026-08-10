// Design-token theme. Render <Theme/> once near the root; style via var(--…). Both light and
// dark are wired (prefers-color-scheme + [data-theme] override). Lives in the template so
// artifacts never re-emit the token block by hand (single source of truth, can't drift).
//
// Palette: brand=indigo #4f46e5 (the one accent) · signal=amber #ffc533 (highlight, sparingly)
// · neutrals = gray ramp · add/rm = diff green/red. Swap these hexes to re-skin everything.

const CSS = `
:root{
  --bg:#fafbfb; --surface:#ffffff; --border:#e3e6e8; --border-hi:#d1d5d9;
  --ink:#414448; --ink-2:#62676c; --ink-3:#828990;
  --brand:#4f46e5; --brand-ink:#4338ca; --brand-soft:#eef2ff;
  --signal:#ffc533; --signal-soft:#fff0cc;
  --add:#1a7f52; --add-soft:#e7f6ee; --rm:#c2415a; --rm-soft:#fbe9ed;
  --code-bg:#1a1d23; --code-ink:#e6e8ef;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#101112; --surface:#181a1b; --border:#27282b; --border-hi:#51565a;
  --ink:#dadde1; --ink-2:#c8cdd2; --ink-3:#939aa2;
  --brand:#6366f1; --brand-ink:#818cf8; --brand-soft:#1e1b38;
  --signal:#ffc533; --signal-soft:#332708;
  --add:#4ddca0; --add-soft:#12281f; --rm:#f2879f; --rm-soft:#2b1720;
  --code-bg:#0b0d10; --code-ink:#dfe3ee;
}}
:root[data-theme="light"]{
  --bg:#fafbfb; --surface:#ffffff; --border:#e3e6e8; --border-hi:#d1d5d9;
  --ink:#414448; --ink-2:#62676c; --ink-3:#828990;
  --brand:#4f46e5; --brand-ink:#4338ca; --brand-soft:#eef2ff;
  --signal:#ffc533; --signal-soft:#fff0cc;
  --add:#1a7f52; --add-soft:#e7f6ee; --rm:#c2415a; --rm-soft:#fbe9ed;
  --code-bg:#1a1d23; --code-ink:#e6e8ef;
}
:root[data-theme="dark"]{
  --bg:#101112; --surface:#181a1b; --border:#27282b; --border-hi:#51565a;
  --ink:#dadde1; --ink-2:#c8cdd2; --ink-3:#939aa2;
  --brand:#6366f1; --brand-ink:#818cf8; --brand-soft:#1e1b38;
  --signal:#ffc533; --signal-soft:#332708;
  --add:#4ddca0; --add-soft:#12281f; --rm:#f2879f; --rm-soft:#2b1720;
  --code-bg:#0b0d10; --code-ink:#dfe3ee;
}
body{background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
`

export function Theme() {
  return <style dangerouslySetInnerHTML={{ __html: CSS }} />
}
