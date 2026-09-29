"""Excel workbooks with the standard library: flares, facts, rules, lanes, endpoints, playbooks.

An .xlsx file is a zip of XML parts. Cells are inline strings or numbers, so nothing a flare's text contains is ever
run as a formula; the header row is bold, frozen and filtered. `cosmos export` writes one; the console serves the same
workbook at /api/export.xlsx.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .config import Config
from .store import Ledger, Observations

Sheet = Tuple[str, List[str], List[Sequence[Any]]]
SHEETS = ["flares", "facts", "rules", "lanes", "endpoints", "playbooks"]
_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MAX_CELL = 32767                                          # Excel's limit for one cell's text


def _esc(v: Any) -> str:
    s = _BAD_XML.sub("", str(v))[:MAX_CELL]
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _col(i: int) -> str:
    name = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        name = chr(65 + r) + name
    return name


def _cell(ref: str, v: Any, style: int = 0) -> str:
    st = f' s="{style}"' if style else ""
    if isinstance(v, bool) or v is None:
        v = "" if v is None else ("yes" if v else "no")
    if isinstance(v, (int, float)):
        return f'<c r="{ref}"{st}><v>{v}</v></c>'
    return f'<c r="{ref}" t="inlineStr"{st}><is><t xml:space="preserve">{_esc(v)}</t></is></c>'


def _sheet_xml(header: List[str], rows: List[Sequence[Any]]) -> str:
    widths = [min(60, max([len(h)] + [len(str(r[i])) for r in rows[:500] if i < len(r)]) + 2) for i, h in enumerate(header)]
    cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
    lines = ['<row r="1">' + "".join(_cell(f"{_col(i)}1", h, 1) for i, h in enumerate(header)) + "</row>"]
    for n, r in enumerate(rows, start=2):
        lines.append(f'<row r="{n}">' + "".join(_cell(f"{_col(i)}{n}", v) for i, v in enumerate(r)) + "</row>")
    last = f"{_col(max(0, len(header) - 1))}{max(1, len(rows) + 1)}"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            f'<cols>{cols}</cols><sheetData>{"".join(lines)}</sheetData><autoFilter ref="A1:{last}"/></worksheet>')


def workbook(sheets: Iterable[Sheet]) -> bytes:
    sheets = [(re.sub(r"[\[\]:*?/\\]", "-", n)[:31], h, r) for n, h, r in sheets]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
                   + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{_esc(n)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, (n, _, _) in enumerate(sheets))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets)))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
                   '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
                   '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
                   '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                   '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
                   '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                   '</styleSheet>')
        for i, (_, h, r) in enumerate(sheets):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(h, r))
    return buf.getvalue()


# ---------------------------------------------------------------- what goes in the workbook
def _join(xs: Iterable[Any]) -> str:
    return " · ".join(str(x) for x in xs if x)


def flares_sheet(mems: Dict) -> Sheet:
    from .audit import findings
    head = ["id", "severity", "status", "title", "area", "lane", "locations", "what", "impact", "fix", "other sections",
            "found at", "fixed at", "status note", "status on", "created", "updated", "source", "memory id"]
    rows = []
    for m in findings(mems):
        sec = {str(a).lower(): str(b) for a, b in m.details}
        other = _join(f"{a}: {b}" for a, b in m.details if str(a).lower() not in ("what", "impact", "fix"))
        rows.append([m.meta.get("audit_id", ""), m.meta.get("severity", ""), m.meta.get("finding_status", "open"), m.text, m.meta.get("area", ""),
                     m.lane, m.meta.get("locations") or _join(m.files), sec.get("what", ""), sec.get("impact", ""), sec.get("fix", ""), other,
                     m.meta.get("found_commit", ""), m.meta.get("fixed_commit", ""), m.meta.get("status_note", ""), m.meta.get("status_at", ""),
                     m.created, m.updated, m.meta.get("source_doc", ""), m.id])
    return ("Flares", head, rows)


def facts_sheet(mems: Dict) -> Sheet:
    head = ["id", "category", "lane", "status", "fact", "files", "confidence", "importance", "source", "seen", "authors", "created", "updated", "verified", "reason"]
    rows = [[m.id, m.category, m.lane, m.status, m.text, _join(m.files), round(m.confidence, 2), round(m.importance, 2), m.source, m.evidence_count,
             _join(m.authors), m.created, m.updated, m.last_verified, m.reason]
            for m in sorted(mems.values(), key=lambda m: (m.category, m.lane or "", m.id)) if m.category != "finding"]
    return ("Facts", head, rows)


def rules_sheet(cfg: Config, mems: Dict) -> Sheet:
    from .charter import body, rules
    rows = [["ledger", m.category, m.text, _join(m.files), m.created, m.id] for m in rules(mems)]
    section = ""
    for line in body(cfg).splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.lstrip().startswith("- ") and section:
            rows.append(["charter", section, line.strip()[2:], "", "", ""])
    return ("Rules", ["where", "kind / section", "rule", "files", "created", "id"], rows)


def lanes_sheet(cfg: Config, mems: Dict) -> Sheet:
    from .lanes import lane_report
    rows = [[r["lane"], r["facts"], r["findings_open"], _join(c["name"] for c in r["contributors"]), "yes" if r["overlap"] else ""]
            for r in lane_report(cfg, mems, Observations(cfg.paths).iter_all())]
    return ("Lanes", ["lane", "facts", "open flares", "people", "overlap"], rows)


def endpoints_sheet(cfg: Config) -> Sheet:
    p = cfg.paths.ledger / "atlas" / "atlas.json"
    inv = json.loads(p.read_text()) if p.exists() else {}
    rows = [[m, path, a.get("spec", "")] for a in inv.get("api", []) for m, path in a.get("endpoints", [])]
    return ("Endpoints", ["method", "path", "declared in"], rows)


def playbooks_sheet(cfg: Config) -> Sheet:
    from .playbooks import detect
    return ("Playbooks", ["command", "file", "title", "kind"], [["/" + p["name"], p["path"], p["title"], p["kind"]] for p in detect(cfg)])


def build(cfg: Config, which: Sequence[str] = SHEETS) -> bytes:
    mems = Ledger(cfg.paths).load()
    make = {"flares": lambda: flares_sheet(mems), "facts": lambda: facts_sheet(mems), "rules": lambda: rules_sheet(cfg, mems),
            "lanes": lambda: lanes_sheet(cfg, mems), "endpoints": lambda: endpoints_sheet(cfg), "playbooks": lambda: playbooks_sheet(cfg)}
    return workbook([make[w]() for w in which if w in make])


def write(cfg: Config, out: Path, which: Sequence[str] = SHEETS) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build(cfg, which))
    return out
