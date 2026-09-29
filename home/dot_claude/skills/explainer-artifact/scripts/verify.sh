#!/usr/bin/env bash
# One-call QA for a built explainer:
#
#   verify.sh <artifact-dir>          # after build.sh
#
#   1. Static checks on your code (src/, minus the kit, ui, diagrams and theme):
#      themed colors, shadows, bare grids, fixed widths, mermaid, RoughNotation, title.
#   2. Runtime probe in headless Chrome at 390 / 768 / 1280px: horizontal page
#      overflow (and which element causes it), text under 12px.
#   3. One contact sheet: all three widths × light and dark, in a single PNG.
#
# Prints ✓/✗ lines, then the sheet path. Exit 1 on any ✗. Read the sheet once;
# fix every ✗ in one edit pass, rebuild, re-run. No Chrome → steps 2–3 skip.
set -uo pipefail

ART="${1:?usage: verify.sh <artifact-dir>}"
BUNDLE="$ART/bundle.html"; SRC="$ART/src"
[ -f "$BUNDLE" ] || { echo "✗ no $BUNDLE — run build.sh first" >&2; exit 1; }
FAIL=0
bad()  { echo "✗ $1"; [ -n "${2:-}" ] && printf '%s\n' "$2" | head -6 | sed 's/^/    /'; FAIL=1; }
good() { echo "✓ $1"; }

# ---------- 1. static ----------
FILES="$(find "$SRC" -name '*.tsx' -not -path '*/components/ui/*' -not -path '*/explainer/*' \
  -not -path '*/diagrams/*' -not -name theme.tsx -not -name main.tsx 2>/dev/null)"
scan() { [ -n "$FILES" ] && grep -nE "$1" $FILES 2>/dev/null | sed "s|$SRC/||" | cut -c1-140; }

hits="$(scan '\b(bg|text|border|from|to|via|fill|stroke|ring|divide)-(white|black|gray|slate|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)(-[0-9]+)?\b')"
[ -z "$hits" ] && good "no Tailwind color classes" || bad "Tailwind color classes break dark mode — use var(--…)" "$hits"
hits="$(scan '#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b[^-]')"
[ -z "$hits" ] && good "no raw hex colors" || bad "raw hex colors — use var(--…)" "$hits"
hits="$(scan '\bshadow(-[a-z0-9]+)?\b')"
[ -z "$hits" ] && good "no shadows" || bad "shadow-* is invisible in dark — elevation is --surface + --border" "$hits"
hits="$(scan '(^|[^:a-z-])grid-cols-[2-9]')"
[ -z "$hits" ] && good "grids start at one column" || bad "bare grid-cols-N — write grid-cols-1 md:grid-cols-N" "$hits"
hits="$(scan '\b(w|min-w)-\[[0-9]+(px|vw)\]')"
[ -z "$hits" ] && good "no fixed content widths" || bad "fixed px/vw width — use max-w-* + w-full" "$hits"
hits="$(scan "from ['\"](mermaid|react-rough-notation)['\"]")"
[ -z "$hits" ] && good "no mermaid / RoughNotation" || bad "mermaid or RoughNotation imported — use diagram-design / <Mark>" "$hits"
T="$(sed -n 's|.*<title>\([^<]*\)</title>.*|\1|p' "$BUNDLE" | head -1)"
if [ -z "$T" ] || [ "$T" = "__ARTIFACT_TITLE__" ] || [ "$T" = "$(basename "$ART")" ]; then
  bad "page title is '$T' — add // @title: <Title> to App.tsx"
else good "title: $T"; fi

# ---------- 2–3. browser ----------
CH="${CHROME:-}"
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
         "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
         google-chrome google-chrome-stable chromium chromium-browser microsoft-edge; do
  [ -n "$CH" ] && break
  if [ -x "$c" ]; then CH="$c"; elif command -v "$c" >/dev/null 2>&1; then CH="$(command -v "$c")"; fi
done
if [ -z "$CH" ]; then
  echo "– no Chrome/Chromium found (set CHROME=…): skipped overflow probe and screenshots"
  exit "$FAIL"
fi

OUT="$ART/.verify"; mkdir -p "$OUT"
ABS="$(cd "$ART" && pwd)"
chrome() { "$CH" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
  --allow-file-access-from-files --virtual-time-budget=2500 "$@" 2>/dev/null; }

# Headless Chrome can't size a window below 500px, so every width is measured
# inside an iframe. A probe in each frame posts its findings to the sheet page;
# one --dump-dom run reads them all, one --screenshot run captures the sheet.
PROBE='<script>addEventListener("load",()=>setTimeout(()=>{
const W=innerWidth,r=[],root=[document.body,document.documentElement];
const clipped=e=>{for(let p=e.parentElement;p&&!root.includes(p);p=p.parentElement)if(getComputedStyle(p).overflowX!=="visible")return true;return false};
let h=document.documentElement.scrollHeight;
for(const e of document.querySelectorAll("body *")){const cs=getComputedStyle(e);
 if(/(auto|scroll)/.test(cs.overflowY)&&e.clientHeight>200)h=Math.max(h,e.scrollHeight);
 const b=e.getBoundingClientRect();if(b.width&&b.right>W+1&&!clipped(e)&&!e.closest("svg"))r.push(e)}
const overflow=r.filter(e=>!r.includes(e.parentElement)).slice(0,4).map(e=>"<"+e.tagName.toLowerCase()+(typeof e.className==="string"&&e.className?" class=\""+e.className.slice(0,60)+"\"":"")+"> ends at "+Math.round(e.getBoundingClientRect().right)+"px");
let small=0;for(const t of document.querySelectorAll("p,li,td,th,span,a,code,div,h1,h2,h3,h4"))
 if(!t.closest("svg")&&[...t.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&parseFloat(getComputedStyle(t).fontSize)<12)small++;
parent.postMessage({verify:1,theme:document.documentElement.dataset.theme||"light",W,h,overflow,small},"*")},600))</script>'
python3 - "$BUNDLE" "$OUT" "$PROBE" <<'PY'
import sys
b, out, probe = sys.argv[1:4]
h = open(b, encoding='utf-8').read().replace('</body>', probe + '</body>', 1)
open(f'{out}/light.html', 'w').write(h)
open(f'{out}/dark.html', 'w').write(h.replace('<html', '<html data-theme="dark"', 1))
PY

# sheet.html?probe → 390/768/1280 light frames only, results written into the DOM.
# sheet.html?h=a,b,c → light row + dark row at those heights, for the screenshot.
cat > "$OUT/sheet.html" <<'HTML'
<!doctype html><meta charset=utf-8><style>body{margin:0;padding:12px;background:#777;font:12px system-ui;color:#fff}
.r{display:flex;gap:12px;align-items:flex-start;margin-bottom:12px}iframe{display:block;border:0;background:#fff}b{display:block;margin-bottom:4px}</style>
<body><script>
const W=[390,768,1280],q=new URLSearchParams(location.search),probe=q.has("probe"),H=(q.get("h")||"2400,2400,2400").split(",");
for(const t of probe?["light"]:["light","dark"]){const r=document.createElement("div");r.className="r";
 W.forEach((w,i)=>{r.insertAdjacentHTML("beforeend",`<div><b>${t} · ${w}px</b><iframe src="${t}.html" style="width:${w}px;height:${probe?900:H[i]}px"></iframe></div>`)});
 document.body.append(r)}
if(probe){const got=[];addEventListener("message",e=>{if(!e.data||!e.data.verify)return;got.push(e.data);
 if(got.length===W.length){const p=document.createElement("pre");p.id="__verify";p.textContent=JSON.stringify(got.sort((a,b)=>a.W-b.W));document.body.append(p)}})}
</script>
HTML

J="$(chrome --window-size=2500,1000 --dump-dom "file://$ABS/.verify/sheet.html?probe" \
  | sed -n 's|.*<pre id="__verify">\(.*\)</pre>.*|\1|p' | sed 's/&quot;/"/g; s/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g')"
if [ -z "$J" ]; then
  bad "runtime probe got no results — the page may throw on load; open $BUNDLE"
  HS="2400,2400,2400"
else
  REPORT="$(python3 - "$J" <<'PY'
import json, sys
hs = []
for d in json.loads(sys.argv[1]):
    hs.append(str(min(d['h'], 4000)))
    if d['overflow']:
        print(f"✗ {d['W']}px: page scrolls sideways — wrap it in overflow-x-auto or let it reflow")
        for o in d['overflow']:
            print(f"    {o}")
    else:
        print(f"✓ {d['W']}px: no horizontal page overflow")
    if d['small']:
        print(f"✗ {d['W']}px: {d['small']} text elements under 12px")
print('HS=' + ','.join(hs))
PY
)"
  printf '%s\n' "$REPORT" | grep -v '^HS='
  printf '%s\n' "$REPORT" | grep -q '^✗' && FAIL=1
  HS="$(printf '%s\n' "$REPORT" | sed -n 's/^HS=//p')"
fi

MAXH="$(printf '%s' "$HS" | tr ',' '\n' | sort -n | tail -1)"
chrome --window-size=2486,$(( 2 * (MAXH + 30) + 36 )) --screenshot="$ABS/.verify/sheet.png" \
  "file://$ABS/.verify/sheet.html?h=$HS" >/dev/null
[ -f "$OUT/sheet.png" ] && echo "📸 $OUT/sheet.png  (light row, dark row × 390/768/1280 — read it once)"
exit "$FAIL"

