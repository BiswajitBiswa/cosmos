"""The Atlas as one page: every diagram and document in cosmos's look, navigable, readable by people.

`cosmos atlas` writes .cosmos/ledger/atlas/atlas.html next to the Markdown by default (`--format md`, or atlas.format
"md" in config.json, writes only the Markdown). The Markdown stays the source: agents, dreams and the ledger read it;
this page is how a person looks at it. Self-contained apart from Mermaid from a CDN; without it every diagram shows
as its source. Diagrams pan (drag), zoom (wheel, + and -), fit and go full screen; the sidebar lists every document
and its sections, and follows the one you are reading.
"""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import List, Tuple

from .config import Config, git_head
from .store import today

DOCS = ["system-context", "containers", "data-flow", "deployment", "dependencies", "api", "inventory", "lanes"]
TITLES = {"system-context": "System context", "containers": "Containers", "data-flow": "Data flow", "deployment": "Deployment",
          "dependencies": "Dependencies", "api": "API surface", "inventory": "Inventory", "lanes": "Lanes"}


def _js_function(source: str, name: str) -> str:
    """One function from the console's script, by matching braces, so both pages share the same Mermaid fixes."""
    start = source.index("function %s(" % name)
    depth, i = 0, source.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(source[i], 0)
        if depth == 0:
            return source[start:i + 1]
        i += 1


def _inline(text: str) -> str:
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(\S[^*\n]*?\S)\*(?![\w*])|(?<!\w)_(\S[^_\n]*?\S)_(?!\w)", lambda m: f"<i>{m.group(1) or m.group(2)}</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "section"


def markdown_to_html(md: str, doc: str) -> Tuple[str, List[Tuple[str, str]], int]:
    """(html, [(anchor, heading)], diagrams) for the Markdown subset the Atlas uses: headings, paragraphs, lists,
    tables, fenced code and Mermaid. Everything is escaped; nothing in a document runs as markup."""
    md = re.sub(r"^---\n.*?\n---\n", "", md, count=1, flags=re.S)
    out: List[str] = []
    toc: List[Tuple[str, str]] = []
    lines = md.splitlines()
    i, para, lst, diagrams = 0, [], None, 0

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>"); para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{tag}>"); lst = None

    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^```(\w*)\s*$", line)
        if fence:
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            body = "\n".join(lines[i + 1:j])
            if fence.group(1) == "mermaid":
                diagrams += 1
                did = f"{doc}-d{diagrams}"
                out.append(f'<figure class="dia" id="{did}"><div class="bar"><span>Diagram {diagrams}</span><span class="sp"></span>'
                           '<button data-z="in" title="Zoom in">+</button><button data-z="out" title="Zoom out">−</button>'
                           '<button data-z="fit" title="Fit">Fit</button><button data-z="full" title="Full screen">⤢</button></div>'
                           f'<div class="stage"><div class="pan"><pre class="src">{html.escape(body)}</pre></div></div></figure>')
                toc.append((did, f"Diagram {diagrams}"))
            else:
                out.append(f"<pre>{html.escape(body)}</pre>")
            i = j + 1
            continue
        h = re.match(r"^(#{1,3})\s+(.+)$", line)
        if h:
            flush()
            level, text = len(h.group(1)), h.group(2).strip()
            if level == 1:
                i += 1; continue                       # the document title is the section's own heading
            aid = f"{doc}-{_slug(text)}"
            out.append(f'<h{level + 1} id="{aid}">{_inline(text)}</h{level + 1}>')
            if level == 2:
                toc.append((aid, re.sub(r"[`*_]", "", text)))
            i += 1; continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            flush()
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")]); j += 1
            out.append('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
            i = j; continue
        item = re.match(r"^\s*(?:[-*]|(\d+)\.)\s+(.+)$", line)
        if item:
            if para:
                flush()
            tag = "ol" if item.group(1) else "ul"
            if not lst or lst[0] != tag:
                flush(); lst = (tag, [])
            lst[1].append(item.group(2)); i += 1; continue
        if not line.strip():
            flush(); i += 1; continue
        if lst:
            flush()
        para.append(line.strip()); i += 1
    flush()
    return "\n".join(out), toc, diagrams


def render(cfg: Config) -> str:
    from .ui import HTML as CONSOLE
    d = cfg.paths.ledger / "atlas"
    sections, nav, count = [], [], 0
    for doc in DOCS:
        f = d / f"{doc}.md"
        if not f.exists():
            continue
        body, toc, n = markdown_to_html(f.read_text(errors="ignore"), doc)
        count += n
        title = TITLES.get(doc, doc)
        sections.append(f'<section class="doc" id="{doc}"><h2>{html.escape(title)}</h2>{body}</section>')
        sub = "".join(f'<a class="sub" href="#{a}">{html.escape(t)}</a>' for a, t in toc)
        nav.append(f'<a class="top" href="#{doc}">{html.escape(title)}{f" <em>{n}</em>" if n else ""}</a>{sub}')
    mmd_fix = _js_function(CONSOLE, "mmdFix")
    repo = html.escape(cfg.paths.root.name)
    empty = '<section class="doc"><h2>No Atlas yet</h2><p>Run <code>cosmos atlas</code> in the repository.</p></section>'
    return PAGE.replace("__REPO__", repo).replace("__META__", f"{count} diagram{'s' if count != 1 else ''} · generated {today()} at {html.escape(git_head(cfg.paths.root) or '?')}") \
               .replace("__NAV__", "".join(nav)).replace("__BODY__", "".join(sections) or empty).replace("__MMDFIX__", mmd_fix)


def write(cfg: Config) -> Path:
    p = cfg.paths.ledger / "atlas" / "atlas.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(cfg))
    return p


def wanted(cfg: Config, fmt: str = "") -> bool:
    return (fmt or str(cfg.get("atlas.format", "html"))).lower() != "md"


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atlas · __REPO__</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&family=DM+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
/* cosmos's own look: near-black, ivory text, one warm gold; glass panels over a quiet night sky */
:root{--bg:#050506;--panel:rgba(13,13,16,.72);--panel2:rgba(20,20,24,.82);--line:rgba(236,234,228,.10);--fg:#ECEAE4;--mut:#A9A79E;--dim:#8A8984;--acc:#E8CFA0;--acc2:#F4E4C4;color-scheme:dark}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:radial-gradient(1200px 700px at 78% -10%,rgba(27,54,70,.55),transparent 60%),radial-gradient(900px 600px at 0% 100%,rgba(27,54,70,.35),transparent 60%),var(--bg);background-attachment:fixed;
 color:var(--fg);font:15px/1.65 "DM Sans",-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--acc);text-decoration:none}code,pre{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}
code{font-size:.86em;background:rgba(255,255,255,.06);padding:1px 6px;border-radius:4px;color:var(--acc2)}
#app{display:grid;grid-template-columns:260px minmax(0,1fr);min-height:100vh}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:26px 16px;background:rgba(5,5,6,.72);border-right:1px solid var(--line);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}
.brand{font:400 26px "Cormorant Garamond",serif;letter-spacing:.3em;padding:0 8px 4px}.brand small{display:block;font:400 10px "DM Sans";letter-spacing:.28em;color:var(--dim);text-transform:uppercase;margin-top:4px}
.meta{color:var(--dim);font-size:12px;padding:6px 8px 18px}
#q{width:100%;height:34px;border-radius:9px;border:1px solid rgba(236,234,228,.15);background:rgba(255,255,255,.035);color:var(--fg);padding:0 12px;font:inherit;font-size:13px;margin-bottom:14px}
#q:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px rgba(232,207,160,.16)}
nav a{display:block;border-radius:7px;color:var(--mut)}nav a.top{padding:7px 10px;margin-top:6px;color:var(--fg);font-weight:500}
nav a.top em{float:right;font-style:normal;font-size:11px;color:var(--acc);background:rgba(232,207,160,.10);border-radius:999px;padding:1px 8px;margin-top:2px}
nav a.sub{padding:4px 10px 4px 22px;font-size:13px}nav a:hover{background:rgba(255,255,255,.05);color:var(--fg)}
nav a.on{background:rgba(232,207,160,.10);color:var(--acc2);box-shadow:inset 3px 0 0 var(--acc)}
main{padding:34px 40px 80px;min-width:0}
h1{font:400 40px/1.1 "Cormorant Garamond",serif;margin:0 0 6px}.lede{color:var(--mut);margin:0 0 28px}
.doc{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:26px 30px;margin:0 0 26px;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);scroll-margin-top:20px}
.doc h2{font:400 32px/1.15 "Cormorant Garamond",serif;margin:0 0 14px;color:var(--fg)}.doc h3{font:500 17px "DM Sans";margin:24px 0 8px;color:var(--acc2)}.doc h4{font:500 15px "DM Sans";margin:18px 0 6px}
.doc p,.doc li{color:#DDD9CE}.doc ul,.doc ol{padding-left:22px}
pre{background:rgba(5,5,6,.72);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto;font-size:12.5px;color:var(--mut)}
.tbl{overflow:auto;margin:10px 0}table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--acc);font-weight:500}
.dia{margin:14px 0 22px;border:1px solid var(--line);border-radius:12px;background:rgba(5,5,6,.55);overflow:hidden;scroll-margin-top:20px}
.dia .bar{display:flex;align-items:center;gap:6px;padding:8px 10px;border-bottom:1px solid var(--line);font-size:12px;color:var(--dim)}.dia .sp{flex:1}
.dia button{all:unset;cursor:pointer;min-width:30px;height:28px;padding:0 8px;box-sizing:border-box;text-align:center;border-radius:7px;border:1px solid rgba(236,234,228,.15);background:rgba(255,255,255,.05);color:var(--fg);font:500 13px/28px "DM Sans"}
.dia button:hover{border-color:rgba(236,234,228,.3);background:rgba(255,255,255,.1)}.dia button:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.stage{height:min(62vh,640px);overflow:hidden;cursor:grab;position:relative;touch-action:none}.stage:active{cursor:grabbing}
.pan{transform-origin:0 0;display:inline-block;padding:20px}.pan svg{max-width:none!important;height:auto}
.src{margin:0;border:0;background:none;white-space:pre}
.dia.full{position:fixed;inset:12px;z-index:50;margin:0;background:rgba(5,5,6,.96)}.dia.full .stage{height:calc(100% - 45px)}
.err{color:#E6A29C;font-size:12.5px;padding:10px 14px 0}
@media(max-width:860px){#app{grid-template-columns:1fr}nav{position:static;height:auto;max-height:none}main{padding:22px 16px 60px}.doc{padding:20px}}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important}}
</style></head><body><div id="app">
<nav><div class="brand">atlas<small>__REPO__</small></div><div class="meta">__META__</div><input id="q" placeholder="Filter…" aria-label="Filter the sections">__NAV__</nav>
<main><h1>Atlas</h1><p class="lede">Architecture generated from the repository by cosmos. Drag a diagram to move it, scroll or use + and − to zoom, Fit to see all of it.</p>__BODY__</main></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>
__MMDFIX__
if(window.mermaid)mermaid.initialize({startOnLoad:false,suppressErrorRendering:true,theme:'base',flowchart:{curve:'basis',padding:14,nodeSpacing:44,rankSpacing:60,htmlLabels:true},
 themeVariables:{primaryColor:'#141418',primaryTextColor:'#ECEAE4',primaryBorderColor:'#E8CFA0',lineColor:'#8a8577',secondaryColor:'#0d0d10',tertiaryColor:'#0a0a0c',clusterBkg:'#0b0b0e',clusterBorder:'#2c2c34',edgeLabelBackground:'#0d0d10',titleColor:'#E8CFA0',fontFamily:'DM Sans, sans-serif',fontSize:'14px'}});
function view(fig){const st=fig.querySelector('.stage'),pan=fig.querySelector('.pan');let s=1,x=0,y=0,drag=null;
 const set=()=>{pan.style.transform=`translate(${x}px,${y}px) scale(${s})`};
 const fit=()=>{const svg=pan.firstElementChild;if(!svg)return;s=1;x=0;y=0;set();const b=svg.getBoundingClientRect(),r=st.getBoundingClientRect();s=Math.min(2,Math.max(.2,Math.min((r.width-20)/b.width,(r.height-20)/b.height)));x=(r.width-b.width*s)/2;y=Math.max(0,(r.height-b.height*s)/2);set()};
 const zoom=(k,cx,cy)=>{const r=st.getBoundingClientRect();cx=cx??r.width/2;cy=cy??r.height/2;const n=Math.min(6,Math.max(.15,s*k));x=cx-(cx-x)*n/s;y=cy-(cy-y)*n/s;s=n;set()};
 st.addEventListener('wheel',e=>{e.preventDefault();const r=st.getBoundingClientRect();zoom(e.deltaY<0?1.12:1/1.12,e.clientX-r.left,e.clientY-r.top)},{passive:false});
 st.addEventListener('pointerdown',e=>{drag={px:e.clientX,py:e.clientY,x,y};st.setPointerCapture(e.pointerId)});
 st.addEventListener('pointermove',e=>{if(!drag)return;x=drag.x+e.clientX-drag.px;y=drag.y+e.clientY-drag.py;set()});
 st.addEventListener('pointerup',()=>drag=null);st.addEventListener('dblclick',fit);
 fig.querySelectorAll('[data-z]').forEach(b=>b.onclick=()=>{const z=b.dataset.z;if(z==='in')zoom(1.25);else if(z==='out')zoom(.8);else if(z==='fit')fit();else{fig.classList.toggle('full');setTimeout(fit,30)}});
 return fit}
async function draw(fig){const pre=fig.querySelector('.src'),src=pre.textContent,fit=view(fig);if(!window.mermaid)return;
 for(const cand of [mmdFix(src),src]){try{await mermaid.parse(cand);const o=await mermaid.render('m'+Math.random().toString(36).slice(2),cand);fig.querySelector('.pan').innerHTML=o.svg;requestAnimationFrame(fit);return}catch(e){var err=e}}
 const m=document.createElement('div');m.className='err';m.textContent='This diagram has a Mermaid syntax error, so it is shown as text: '+String((err&&err.message)||err).split('\n')[0];fig.insertBefore(m,fig.querySelector('.stage'))}
document.querySelectorAll('.dia').forEach(draw);
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.dia.full').forEach(f=>f.classList.remove('full'))});
const links=[...document.querySelectorAll('nav a')];
const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){links.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+en.target.id))}}),{rootMargin:'-20% 0px -70% 0px'});
document.querySelectorAll('.doc[id],.dia[id],.doc h3[id]').forEach(el=>io.observe(el));
document.getElementById('q').oninput=e=>{const q=e.target.value.toLowerCase();links.forEach(a=>{a.style.display=!q||a.textContent.toLowerCase().includes(q)?'':'none'})};
</script></body></html>"""
