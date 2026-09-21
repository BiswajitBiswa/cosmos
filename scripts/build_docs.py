"""Render README.md and docs/*.md into docs/*.html for GitHub Pages. Standard library only."""
import html, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = os.environ.get("COSMOS_REPO_URL", "")
CSS = """
:root{--bg:#050506;--panel:#0d0d10;--panel2:#121216;--line:#1f2024;--fg:#ECEAE4;--fg2:#B9B7B0;--mut:#8A8984;--warm:#E8CFA0;--warm2:#F4E4C4;color-scheme:dark}
*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 "DM Sans","Inter",-apple-system,sans-serif;font-weight:300}
.mast{border-bottom:1px solid var(--line)}.mast .wrap{display:flex;justify-content:space-between;align-items:center;padding:22px 28px;gap:16px;flex-wrap:wrap}
.brand{font-family:"Cormorant Garamond",serif;font-size:26px;letter-spacing:.42em;color:var(--fg);text-decoration:none;display:inline-flex;align-items:center}
.md-hero img,.md-wide img{width:100%;height:auto;display:block}.md-center{text-align:center}.md-center img{display:inline-block}table img{vertical-align:middle}h2 img,h3 img{vertical-align:middle;margin-right:.4em}.brand img{width:22px;height:34px;margin:0 .1em 0 .12em}
nav{display:flex;gap:28px;font-size:11px;letter-spacing:.26em;text-transform:uppercase}nav a{color:var(--fg2);text-decoration:none}nav a:hover{color:var(--fg)}
.wrap{max-width:860px;margin:0 auto;padding:0 28px}main{padding:56px 0 96px}
h1,h2,h3{font-family:"Cormorant Garamond",serif;font-weight:400;color:var(--fg);margin:2.2em 0 .5em;line-height:1.15}h1{font-size:52px;margin-top:0}h2{font-size:34px;padding-top:.4em}h3{font-size:24px}
p,li{color:var(--fg2)}a{color:var(--warm2)}strong{color:var(--fg);font-weight:500}
code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.86em;background:var(--panel2);padding:1px 6px;border-radius:3px;color:var(--warm2)}
pre{background:var(--panel);border-radius:4px;padding:18px 20px;overflow-x:auto;font-size:13.5px;line-height:1.6}pre code{background:transparent;padding:0;color:var(--fg2)}
table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:15px}th{text-align:left;font-size:10.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--mut);font-weight:400;padding:12px 14px;border-bottom:1px solid var(--line)}td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top;color:var(--fg2)}td:first-child{color:var(--fg)}
blockquote{border-left:1px solid var(--warm);margin:1.2em 0;padding:4px 20px;color:var(--fg2)}
ul,ol{padding-left:22px}li{margin:4px 0}hr{border:0;border-top:1px solid var(--line);margin:3em 0}
.toc{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:40px}.toc a{color:var(--mut);text-decoration:none}.toc a:hover{color:var(--fg)}
footer{border-top:1px solid var(--line);padding:26px 0;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--mut)}
"""
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=DM+Sans:wght@300;400;500&family=IBM+Plex+Mono:wght@400&display=swap">'

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2).replace(".md", ".html") if not m.group(2).startswith("http") else m.group(2)}">{m.group(1)}</a>', t)
    return t

def md_to_html(src):
    out, lines, i = [], src.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("<"):
            j = i; buf = []
            while j < len(lines) and lines[j].strip():
                buf.append(lines[j]); j += 1
            out.append("\n".join(buf)); i = j; continue
        if ln.startswith("```"):
            j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>"); i = j + 1; continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip("|").split("|")]; j = i + 2; rows = []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip("|").split("|")]); j += 1
            out.append("<table><tr>" + "".join(f"<th>{inline(h)}</th>" for h in head) + "</tr>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</table>"); i = j; continue
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            lvl, text = len(m.group(1)), m.group(2)
            hid = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append(f'<h{lvl} id="{hid}">{inline(text)}</h{lvl}>'); i += 1; continue
        if re.match(r"^\s*[-*]\s+", ln):
            j = i; items = []
            while j < len(lines) and re.match(r"^\s*[-*]\s+", lines[j]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[j])); j += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"); i = j; continue
        if re.match(r"^\s*\d+\.\s+", ln):
            j = i; items = []
            while j < len(lines) and re.match(r"^\s*\d+\.\s+", lines[j]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[j])); j += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); i = j; continue
        if ln.startswith(">"):
            out.append(f"<blockquote>{inline(ln.lstrip('> '))}</blockquote>"); i += 1; continue
        if ln.strip() in ("---", "***"):
            out.append("<hr>"); i += 1; continue
        if not ln.strip():
            i += 1; continue
        j = i; buf = []
        while j < len(lines) and lines[j].strip() and not re.match(r"^(#{1,3}\s|```|\||\s*[-*]\s|\s*\d+\.\s|>|<)", lines[j]):
            buf.append(lines[j]); j += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>"); i = j
    return "\n".join(out)

def page(title, body, nav_items):
    nav = "".join(f'<a href="{h}">{t}</a>' for t, h in nav_items)
    repo_link = (' · <a href="' + REPO_URL + '">' + REPO_URL.replace("https://", "") + '</a>') if REPO_URL else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · cosmos</title><link rel="icon" href="favicon.svg" type="image/svg+xml">{FONTS}<style>{CSS}</style></head><body>
<div class="mast"><div class="wrap"><a class="brand" href="index.html">cosm<img src="favicon.svg" alt="">s</a><nav>{nav}</nav></div></div>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">cosmos · MIT{repo_link}</div></footer></body></html>'''

def main():
    docs = ROOT / "docs"
    guides = sorted(p for p in docs.glob("*.md"))
    nav = [("Home", "index.html"), ("README", "readme.html"), ("Guides", "guides.html")] + ([("GitHub", REPO_URL)] if REPO_URL else [])
    readme = (ROOT / "README.md").read_text().replace('src="docs/', 'src="').replace("](docs/", "](")
    (docs / "readme.html").write_text(page("README", md_to_html(readme), nav))
    idx = ["<h1>Guides</h1>", "<p>Everything in <code>docs/</code>, rendered.</p>", "<ul>"]
    for g in guides:
        title = next((l[2:] for l in g.read_text().splitlines() if l.startswith("# ")), g.stem)
        (docs / f"{g.stem}.html").write_text(page(title, md_to_html(g.read_text()), nav))
        idx.append(f'<li><a href="{g.stem}.html">{html.escape(title)}</a></li>')
    idx.append("</ul>")
    (docs / "guides.html").write_text(page("Guides", "\n".join(idx), nav))
    print(f"rendered readme.html, guides.html and {len(guides)} guides")

if __name__ == "__main__":
    main()
