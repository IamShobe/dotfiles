#!/usr/bin/env bash
# One-call QA for a built explainer:
#
#   verify.sh <artifact-dir> [repo]   # after build.sh; repo defaults to the checkout you're in
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

ART="${1:?usage: verify.sh <artifact-dir> [repo]}"
REPO_DIR="${2:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
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

# ---------- source links: every <Src> must resolve at the pinned SHA ----------
SRCS="$(python3 - $FILES <<'PY'
import re, sys
sha, out = None, []
for f in sys.argv[1:]:
    t = open(f, encoding='utf-8').read()
    m = re.search(r"sha:\s*['\"]([0-9a-f]{7,40})['\"]", t)
    sha = sha or (m and m.group(1))
    for tag in re.findall(r'<Src\b[^>]*>', t):
        p = re.search(r'path="([^"]+)"', tag); l = re.search(r'lines="([^"]+)"', tag)
        if p: out.append(f"{p.group(1)}\t{l.group(1) if l else ''}")
print(sha or '-')
print('\n'.join(out))
PY
)"
SHA="$(printf '%s\n' "$SRCS" | head -1)"; LINKS="$(printf '%s\n' "$SRCS" | tail -n +2 | sed '/^$/d')"
if [ -z "$LINKS" ]; then :
elif [ -z "$REPO_DIR" ] || [ "$SHA" = "-" ]; then
  echo "– source links not checked (run from the repo or pass it: verify.sh $ART <repo>; meta needs sha)"
else
  broken=""
  git -C "$REPO_DIR" cat-file -e "$SHA^{commit}" 2>/dev/null || broken="meta.sha $SHA is not in $REPO_DIR"
  if [ -z "$broken" ]; then
    [ -n "$(git -C "$REPO_DIR" branch -r --contains "$SHA" 2>/dev/null)" ] \
      || bad "meta.sha ${SHA:0:12} isn't on any remote branch yet: every source link will 404 until it's pushed"
    while IFS=$'\t' read -r path lines; do
      n="$(git -C "$REPO_DIR" show "$SHA:$path" 2>/dev/null | wc -l | tr -d ' ')"
      if ! git -C "$REPO_DIR" cat-file -e "$SHA:$path" 2>/dev/null; then broken="$broken"$'\n'"$path: not in ${SHA:0:12}"; continue; fi
      [ -z "$lines" ] && continue
      end="${lines##*-}"; start="${lines%%-*}"
      if ! [[ "$start" =~ ^[0-9]+$ && "$end" =~ ^[0-9]+$ ]] || [ "$start" -gt "$end" ] || [ "$end" -gt "$n" ]; then
        broken="$broken"$'\n'"$path:$lines: file has $n lines"
      fi
    done <<<"$LINKS"
  fi
  broken="$(printf '%s' "$broken" | sed '/^$/d')"
  [ -z "$broken" ] && good "$(printf '%s\n' "$LINKS" | wc -l | tr -d ' ') source links resolve at ${SHA:0:12}" \
    || bad "broken source links (fix with the ranges from gather-facts.sh)" "$broken"
fi

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
# Headless Chrome sometimes finishes its work but never exits (seen with custom
# profiles and with no keychain). So don't wait for exit: wait for the output,
# then kill it. Mock keychain avoids macOS keychain prompts. Hard cap: 60s.
#   chrome_run <out-file> <done-test> <chrome args…>
chrome_run() {
  local out="$1" done="$2"; shift 2
  rm -f "$out"
  "$CH" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
    --use-mock-keychain --password-store=basic --disable-extensions \
    --allow-file-access-from-files --virtual-time-budget=2500 "$@" >"${DUMP_TO:-/dev/null}" 2>/dev/null &
  local pid=$! t=0 last=-1 size
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$done" = html ] && grep -q '</html>' "$out" 2>/dev/null; then break; fi
    if [ "$done" = png ] && [ -s "$out" ]; then
      size="$(wc -c <"$out")"; [ "$size" = "$last" ] && break; last="$size"
    fi
    [ "$t" -ge 600 ] && { echo "✗ headless Chrome timed out after 60s" >&2; break; }
    sleep 0.1; t=$((t + 1))
  done
  kill -9 "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  return 0
}

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
const story=(()=>{const X="code,pre,nav,title,desc,style,script,[data-noprose],a.mono",root=document.querySelector("main")||document.body;
 const tw=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),seg=[];let n,txt="";
 while(n=tw.nextNode()){const el=n.parentElement;if(!el||el.closest(X)||!n.textContent.trim())continue;
  seg.push({at:txt.length,t:n.textContent,term:!!el.closest("[data-term]"),svg:!!el.closest("svg")});txt+=n.textContent+" "}
 const low=txt.toLowerCase(),defs={},dup=[],early=[];
 for(const g of seg)if(g.term){const k=g.t.trim().toLowerCase();if(k in defs)dup.push(g.t.trim());else defs[k]=g.at}
 for(const k in defs){const re=new RegExp("(^|[^a-z0-9])"+k.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"(s|es)?(?![a-z0-9])","g");const m=re.exec(low);
  if(m&&m.index+m[1].length<defs[k]){const i=m.index+m[1].length;early.push({term:k,ctx:txt.slice(Math.max(0,i-40),i+k.length+30).replace(/\s+/g," ").trim()})}}
 const OK=new Set("API APIS URL URLS UI UX DB SQL HTTP HTTPS JSON YAML CSS HTML CI CD PR PRS ID IDS CPU GPU RAM SDK CLI OK TLDR JS TS AWS GCP OS IO DNS TCP UDP TLS SSL SSH REST CRUD ORM JWT UUID CSV PDF SVG PNG MVP QA SLA SLO RPC GRPC VM VMS K8S".split(" "));
 const jar=new Set();for(const g of seg){if(g.svg||g.term)continue;
  for(const w of g.t.match(/\b[A-Z][A-Z0-9]{1,5}s?\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b|\b[a-z0-9]+_[a-z0-9_]+\b/g)||[]){
   const u=w.replace(/s$/,"").toUpperCase();if(OK.has(u)||OK.has(w.toUpperCase())||w.toLowerCase() in defs||/^[0-9]/.test(w)||/^(k|M|G|T)?(B|b|iB)$|^(ms|us|ns)$/.test(w))continue;jar.add(w)}}
 const q=e=>e?e.textContent.replace(/\s+/g," ").trim():"";
 return{thesis:q(document.querySelector("[data-thesis]")),takeaways:[...document.querySelectorAll("[data-takeaway]")].map(q),early,dup,jargon:[...jar].slice(0,10)}})();
parent.postMessage({verify:1,theme:document.documentElement.dataset.theme||"light",W,h,overflow,small,story},"*")},600))</script>'
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

DUMP_TO="$OUT/dom.html" chrome_run "$OUT/dom.html" html --window-size=2500,1000 --dump-dom "file://$ABS/.verify/sheet.html?probe"
J="$(cat "$OUT/dom.html" 2>/dev/null \
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
st = next((d['story'] for d in json.loads(sys.argv[1]) if d['W'] == 1280), None)
if st:
    if st['thesis'] or st['takeaways']:
        print("📖 takeaway test: read this as one paragraph. It must tell the whole story on its own:")
        print("    " + " → ".join(x for x in [st['thesis']] + st['takeaways'] if x))
    if st['early']:
        print("✗ terms used before their <Term> introduction (move the <Term> earlier, or reword):")
        for e in st['early'][:6]:
            print(f"    '{e['term']}' first appears in: …{e['ctx']}…")
    else:
        print("✓ every <Term> is introduced before it's used (prose and diagrams)")
    if st['dup']:
        print(f"✗ <Term> defined more than once: {', '.join(sorted(set(st['dup'])))} (define once, then use the bare word)")
    if st['jargon']:
        print(f"⚠ possible jargon never introduced: {', '.join(st['jargon'])} (wrap in <Term def=…> or <Id>, or rephrase)")
print('HS=' + ','.join(hs))
PY
)"
  printf '%s\n' "$REPORT" | grep -v '^HS='
  printf '%s\n' "$REPORT" | grep -q '^✗' && FAIL=1
  HS="$(printf '%s\n' "$REPORT" | sed -n 's/^HS=//p')"
fi

MAXH="$(printf '%s' "$HS" | tr ',' '\n' | sort -n | tail -1)"
chrome_run "$OUT/sheet.png" png --window-size=2486,$(( 2 * (MAXH + 30) + 36 )) --screenshot="$ABS/.verify/sheet.png" \
  "file://$ABS/.verify/sheet.html?h=$HS"
[ -f "$OUT/sheet.png" ] && echo "📸 $OUT/sheet.png  (light row, dark row × 390/768/1280 — read it once)"
exit "$FAIL"

