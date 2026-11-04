// Design-token theme. Render <Theme/> once near the root; style via var(--…). Both light and
// dark are wired (prefers-color-scheme + [data-theme] override). Lives in the template so
// artifacts never re-emit the token block by hand (single source of truth, can't drift).
//
// Palette: brand=indigo (the one accent) · signal=amber #ffc533 (highlight, sparingly)
// · neutrals = gray ramp · add/rm = diff green/red. Swap these hexes to re-skin everything.
// Every text/accent token clears 4.5:1 on its own --surface in both themes; --surface sits a
// visible step off --bg so cards read without leaning on --border. Re-check both if you re-skin.

const CSS = `
:root{
  --bg:#fafbfb; --surface:#ffffff; --border:#e3e6e8; --border-hi:#d1d5d9;
  --ink:#414448; --ink-2:#62676c; --ink-3:#6f767d;
  --brand:#4f46e5; --brand-ink:#4338ca; --brand-soft:#eef2ff;
  --signal:#ffc533; --signal-soft:#fff0cc;
  --add:#1a7f52; --add-soft:#e7f6ee; --rm:#c2415a; --rm-soft:#fbe9ed;
  --code-bg:#1a1d23; --code-ink:#e6e8ef;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#0e0f11; --surface:#1c1e20; --border:#303336; --border-hi:#4a4e53;
  --ink:#e6e9ec; --ink-2:#b4bac1; --ink-3:#8b929b;
  --brand:#8b93fa; --brand-ink:#a6acff; --brand-soft:#24224a;
  --signal:#ffc533; --signal-soft:#3a2c09;
  --add:#4ddca0; --add-soft:#132d22; --rm:#f2879f; --rm-soft:#301a23;
  --code-bg:#0a0b0d; --code-ink:#dfe3ee;
}}
:root[data-theme="light"]{
  --bg:#fafbfb; --surface:#ffffff; --border:#e3e6e8; --border-hi:#d1d5d9;
  --ink:#414448; --ink-2:#62676c; --ink-3:#6f767d;
  --brand:#4f46e5; --brand-ink:#4338ca; --brand-soft:#eef2ff;
  --signal:#ffc533; --signal-soft:#fff0cc;
  --add:#1a7f52; --add-soft:#e7f6ee; --rm:#c2415a; --rm-soft:#fbe9ed;
  --code-bg:#1a1d23; --code-ink:#e6e8ef;
}
:root[data-theme="dark"]{
  --bg:#0e0f11; --surface:#1c1e20; --border:#303336; --border-hi:#4a4e53;
  --ink:#e6e9ec; --ink-2:#b4bac1; --ink-3:#8b929b;
  --brand:#8b93fa; --brand-ink:#a6acff; --brand-soft:#24224a;
  --signal:#ffc533; --signal-soft:#3a2c09;
  --add:#4ddca0; --add-soft:#132d22; --rm:#f2879f; --rm-soft:#301a23;
  --code-bg:#0a0b0d; --code-ink:#dfe3ee;
}
body{background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
`

export function Theme() {
  return <style dangerouslySetInnerHTML={{ __html: CSS }} />
}
