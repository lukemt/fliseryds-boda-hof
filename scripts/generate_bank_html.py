#!/usr/bin/env python3
"""Generate a self-contained printable HTML bank version from Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "businessplan_robert_anna_walter.md"
OUTPUT = ROOT / "output/html/businessplan_robert_anna_walter_bankversion.html"

DEEP_GREEN = "#1E3A2F"
GREEN = "#2D6A4F"
MINT = "#52B788"
GOLD = "#B5892A"
WARM = "#F5F0E8"
LIGHT_GREEN = "#EBF5EE"
LINE = "#D9D0C0"
INK = "#1A1A1A"
CONFIDENTIAL = "Vertraulich - nur zur internen Prüfung und Finanzierungsvorbereitung"
DOC_TITLE = "Businessplan Robert & Anna Walter"


@dataclass
class TableBlock:
    rows: list[list[str]]
    aligns: list[str]


@dataclass
class CoverFields:
    title: str
    subtitle: str
    founders: str
    location: str
    investment: str
    credit_request: str
    motto: str


def normalize_text(text: str) -> str:
    return text.replace("\u00a0", " ").replace("\u2011", "-").replace("\ufeff", "").strip()


def inline_markdown(text: str) -> str:
    escaped = html.escape(normalize_text(text), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_table_separator(row: list[str]) -> bool:
    return bool(row) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in row)


def table_aligns(separator: list[str], count: int) -> list[str]:
    aligns = []
    for cell in separator[:count]:
        cell = cell.strip()
        if cell.startswith(":") and cell.endswith(":"):
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    return aligns + ["left"] * (count - len(aligns))


def chapter_label(text: str, level: int) -> str:
    match = re.match(r"Teil\s+(\d+)", text)
    if match:
        return f"{int(match.group(1)):02d}"
    if text.startswith("Anhang"):
        return "A"
    return " " if level else "&bull;"


def german_date(today: date) -> str:
    months = [
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    return f"{today.day}. {months[today.month - 1]} {today.year}"


def find_first_after(lines: list[str], marker: str, pattern: str, default: str) -> str:
    start = 0
    for idx, line in enumerate(lines):
        if marker in line:
            start = idx
            break
    for line in lines[start:]:
        match = re.search(pattern, normalize_text(line))
        if match:
            return match.group(0)
    return default


def extract_cover_fields(lines: list[str]) -> CoverFields:
    title = "Businessplan"
    subtitle = ""
    founders = "Robert Walter & Anna Walter"
    motto = "Das war kein Urlaub, das war Freiheit."
    found_title = False
    for index, line in enumerate(lines):
        stripped = normalize_text(line)
        if stripped.startswith("# ") and not found_title:
            title = stripped[2:].strip()
            found_title = True
        elif stripped.startswith("## ") and not subtitle:
            subtitle = stripped[3:].strip()
        elif stripped.startswith("**Gründer:**"):
            founders = stripped.replace("**Gründer:**", "").strip()
        elif stripped.startswith(">") and motto == "Das war kein Urlaub, das war Freiheit.":
            motto = stripped.lstrip(">").strip(" „“")
        if index > 45:
            break

    return CoverFields(
        title=title,
        subtitle=subtitle,
        founders=founders,
        location="Fliseryds-Boda, Mönsterås, Schweden",
        investment=find_first_after(lines, "Geschätzter Gesamtinvestitionsbedarf", r"ca\. [\d.]+ SEK", "ca. 3.000.000 SEK"),
        credit_request=find_first_after(lines, "Erste Finanzierungsstufe", r"≈ [\d.]+ SEK", "≈ 2.000.000 SEK"),
        motto=motto,
    )


def body_lines_without_cover_intro(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if normalize_text(line).startswith("# Teil 1"):
            return lines[index:]
    return lines


def render_table(block: TableBlock) -> str:
    col_count = max(len(row) for row in block.rows)
    rows = [row + [""] * (col_count - len(row)) for row in block.rows]
    head = rows[0]
    body = rows[1:]
    header_cells = "".join(f"<th>{inline_markdown(cell)}</th>" for cell in head)
    body_rows = []
    for row in body:
        cells = []
        for idx, cell in enumerate(row):
            align = block.aligns[idx] if idx < len(block.aligns) else "left"
            cells.append(f'<td class="align-{align}">{inline_markdown(cell)}</td>')
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return f'<table class="data-table"><thead><tr>{header_cells}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'


def render_kv_table(rows: list[tuple[str, str]]) -> str:
    rendered = []
    for key, value in rows:
        rendered.append(f"<tr><th>{inline_markdown(key)}</th><td>{inline_markdown(value)}</td></tr>")
    return f'<table class="kv-table">{"".join(rendered)}</table>'


def render_list(items: list[str], ordered: bool = False) -> str:
    parts = []
    for index, item in enumerate(items, start=1):
        marker = f"{index}." if ordered else "&#x2022;"
        parts.append(f'<p class="bullet"><span>{marker}&nbsp;&nbsp;</span>{inline_markdown(item)}</p>')
    return "".join(parts)


def render_profile_lines(lines: list[str]) -> str:
    blocks: dict[str, list[str]] = {"Robert Walter": [], "Anna Walter": []}
    current: str | None = None
    paragraph_lines: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if current and paragraph_lines:
            blocks[current].append(f'<p class="body-left">{" ".join(inline_markdown(line) for line in paragraph_lines)}</p>')
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if current and list_items:
            blocks[current].append(render_list(list_items))
            list_items = []

    for raw in lines:
        line = normalize_text(raw)
        if not line:
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^###\s+(.+)$", line)
        if heading and heading.group(1) in blocks:
            flush_paragraph()
            flush_list()
            current = heading.group(1)
            continue
        bullet = re.match(r"^-\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            list_items.append(bullet.group(1))
            continue
        flush_list()
        paragraph_lines.append(line)
    flush_paragraph()
    flush_list()

    return (
        '<div class="profile-header">GRÜNDERPROFILE</div>'
        '<div class="profile-cards">'
        f'<section><h3>Robert Walter</h3>{"".join(blocks["Robert Walter"])}</section>'
        f'<section><h3>Anna Walter</h3>{"".join(blocks["Anna Walter"])}</section>'
        "</div>"
    )


def parse_body(lines: list[str]) -> tuple[str, list[dict[str, str | int]]]:
    parts: list[str] = []
    toc_entries: list[dict[str, str | int]] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []
    heading_counter = 0
    first_h1 = True

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            parts.append(f'<p>{" ".join(inline_markdown(line) for line in paragraph_lines)}</p>')
            paragraph_lines = []

    def flush_lists() -> None:
        nonlocal list_items, ordered_items
        if list_items:
            parts.append(render_list(list_items))
            list_items = []
        if ordered_items:
            parts.append(render_list(ordered_items, ordered=True))
            ordered_items = []

    def flush_all() -> None:
        flush_paragraph()
        flush_lists()

    index = 0
    while index < len(lines):
        line = normalize_text(lines[index].rstrip())
        if not line:
            flush_all()
            index += 1
            continue

        if line == "---":
            flush_all()
            parts.append('<div class="section-rule"><span></span></div>')
            index += 1
            continue

        if line.startswith("|") and "|" in line[1:]:
            flush_all()
            table_lines = []
            while index < len(lines):
                candidate = normalize_text(lines[index].rstrip())
                if not (candidate.startswith("|") and "|" in candidate[1:]):
                    break
                table_lines.append(candidate)
                index += 1
            rows = [split_table_row(row) for row in table_lines]
            if len(rows) >= 2 and is_table_separator(rows[1]):
                aligns = table_aligns(rows[1], len(rows[0]))
                table_rows = [rows[0], *rows[2:]]
            else:
                aligns = ["left"] * len(rows[0])
                table_rows = rows
            parts.append(render_table(TableBlock(table_rows, aligns)))
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading_match:
            flush_all()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            heading_counter += 1
            target_id = f"heading-{heading_counter}"
            toc_entries.append({"level": min(level - 1, 3), "label": chapter_label(text, level - 1), "title": text, "id": target_id})
            if level == 1:
                page_class = "" if first_h1 else " page-break-before"
                first_h1 = False
                parts.append(f'<h1 id="{target_id}" class="part-hdr{page_class}">{inline_markdown(text)}</h1>')
            else:
                parts.append(f'<h{level} id="{target_id}">{inline_markdown(text)}</h{level}>')
                if level == 2 and text == "Gründerprofil":
                    profile_lines = []
                    lookahead = index + 1
                    while lookahead < len(lines):
                        candidate = normalize_text(lines[lookahead].rstrip())
                        if re.match(r"^(#{1,2})\s+.+$", candidate):
                            break
                        profile_lines.append(candidate)
                        lookahead += 1
                    parts.append(render_profile_lines(profile_lines))
                    index = lookahead
                    continue
            index += 1
            continue

        bullet_match = re.match(r"^-\s+(.+)$", line)
        if bullet_match:
            flush_paragraph()
            if ordered_items:
                flush_lists()
            list_items.append(bullet_match.group(1))
            index += 1
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered_match:
            flush_paragraph()
            if list_items:
                flush_lists()
            ordered_items.append(ordered_match.group(1))
            index += 1
            continue

        if line.startswith(">"):
            flush_all()
            parts.append(f'<blockquote>{inline_markdown(line.lstrip(">").strip())}</blockquote>')
            index += 1
            continue

        flush_lists()
        paragraph_lines.append(line)
        index += 1

    flush_all()
    return "\n".join(parts), [entry for entry in toc_entries if int(entry["level"]) <= 1]


def render_toc(entries: list[dict[str, str | int]]) -> str:
    rows = []
    for entry in entries:
        level = int(entry["level"])
        title = str(entry["title"])
        target_id = str(entry["id"])
        rows.append(
            "<tr "
            f'class="toc-level-{level}">'
            f'<td class="toc-label">{entry["label"]}</td>'
            f'<td class="toc-title"><a href="#{target_id}">{inline_markdown(title)}</a></td>'
            f'<td class="toc-page" data-target="{target_id}">-</td>'
            "</tr>"
        )
    return (
        '<section class="toc-section">'
        '<p class="toc-kicker">INHALTSVERZEICHNIS</p>'
        '<h2 class="toc-heading">Struktur des Businessplans</h2>'
        '<div class="section-rule toc-rule"><span></span></div>'
        f'<table class="toc-table">{"".join(rows)}</table>'
        "</section>"
    )


def css() -> str:
    return f"""
:root {{
  --deep-green: {DEEP_GREEN};
  --green: {GREEN};
  --mint: {MINT};
  --gold: {GOLD};
  --warm: {WARM};
  --light-green: {LIGHT_GREEN};
  --line: {LINE};
  --ink: {INK};
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #cfcfcf; color: var(--ink); font-family: Helvetica, Arial, sans-serif; }}
body {{ font-size: 10pt; line-height: 1.5; }}
.paper {{
  position: relative;
  width: 210mm;
  height: 297mm;
  margin: 10mm auto;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 2mm 8mm rgba(0,0,0,.22);
}}
.cover-page {{ background: var(--deep-green); }}
#cover-canvas {{ display: block; width: 210mm; height: 297mm; }}
.body-page .header {{
  position: absolute;
  left: 0;
  top: 0;
  width: 210mm;
  height: 14mm;
  background: var(--deep-green);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22mm 0 28mm;
  font-size: 8.2pt;
}}
.body-page .header strong {{ font-family: Helvetica, Arial, sans-serif; font-weight: 700; font-size: 8.8pt; }}
.body-page .footer {{
  position: absolute;
  left: 0;
  bottom: 0;
  width: 210mm;
  height: 12mm;
  border-top: 1.15pt solid var(--gold);
  background: var(--line);
  color: #4E544F;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22mm 0 28mm;
  font-size: 7.4pt;
}}
.body-page .footer .page-number {{ font-weight: 700; font-size: 7.6pt; }}
.page-content {{
  position: absolute;
  left: 28mm;
  right: 22mm;
  top: 39mm;
  bottom: 37mm;
  overflow: hidden;
}}
#source-content {{ display: none; }}
p {{ margin: 0 0 6.7pt; text-align: justify; orphans: 2; widows: 2; }}
.body-left {{ text-align: left; }}
strong {{ font-family: Helvetica, Arial, sans-serif; font-weight: 700; }}
.part-hdr {{
  margin: 0 0 9pt;
  min-height: 18mm;
  padding: 10pt 14pt 10pt 10mm;
  border-left: 4mm solid var(--gold);
  border-radius: 2.2mm;
  background: var(--deep-green);
  color: #fff;
  font-size: 15pt;
  line-height: 1.2;
  font-weight: 700;
}}
.page-break-before {{ break-before: page; }}
h2 {{
  margin: 16pt 0 7pt;
  color: var(--green);
  font-size: 12pt;
  line-height: 15pt;
  font-weight: 700;
  text-align: left;
}}
h3 {{
  margin: 10pt 0 5pt;
  color: var(--mint);
  font-size: 10.5pt;
  line-height: 13.5pt;
  font-weight: 700;
  text-align: left;
}}
h4 {{
  margin: 8pt 0 4pt;
  color: var(--mint);
  font-size: 9.8pt;
  line-height: 12.5pt;
  font-weight: 700;
  text-align: left;
}}
.bullet {{
  margin: 0 0 2.2pt;
  padding-left: 16pt;
  text-indent: -10pt;
  text-align: left;
  line-height: 14pt;
}}
blockquote {{
  margin: 8pt 28pt 11pt;
  padding: 8pt;
  border: .45pt solid var(--line);
  background: var(--light-green);
  color: var(--green);
  font-size: 11.5pt;
  line-height: 16pt;
  font-style: italic;
  text-align: center;
}}
.section-rule {{ display: flex; align-items: center; height: 4mm; margin: 1mm 0 2mm; }}
.section-rule::before {{ content: ""; width: 26mm; border-top: 1.2pt solid var(--gold); }}
.section-rule span {{ flex: 1; margin-left: 3mm; border-top: .45pt solid var(--line); }}
.kv-table, .data-table, .toc-table {{ width: 100%; border-collapse: collapse; margin: 3pt 0 10pt; page-break-inside: avoid; }}
.kv-table th, .kv-table td {{
  border: .5pt solid var(--line);
  padding: 5pt 8pt;
  font-size: 9.5pt;
  line-height: 12.3pt;
  vertical-align: middle;
}}
.kv-table th {{ width: 34%; background: var(--light-green); color: #3A3A3A; font-size: 8.5pt; font-weight: 700; text-align: left; }}
.kv-table td {{ width: 66%; background: var(--warm); }}
.data-table th, .data-table td {{
  border: .5pt solid var(--line);
  padding: 5pt 8pt;
  font-size: 9.5pt;
  line-height: 12.3pt;
  vertical-align: middle;
}}
.data-table th {{
  border-bottom: 2pt solid var(--gold);
  background: var(--deep-green);
  color: #fff;
  font-weight: 700;
  text-align: left;
}}
.data-table tbody tr:nth-child(even) {{ background: var(--warm); }}
.align-right {{ text-align: right; }}
.align-center {{ text-align: center; }}
.toc-section {{ page-break-after: always; }}
.toc-kicker {{ margin: 0 0 13pt; color: var(--gold); font-size: 8.5pt; line-height: 10pt; font-weight: 700; text-align: left; }}
.toc-heading {{ margin: 0 0 6pt; color: var(--deep-green); font-size: 20pt; line-height: 24pt; }}
.toc-rule::before {{ width: 42mm; }}
.toc-table {{ margin-top: 7pt; }}
.toc-table td {{ padding: 4.6pt 0; vertical-align: middle; border-bottom: .45pt solid transparent; }}
.toc-table .toc-level-0 td {{ padding-bottom: 6pt; border-bottom-color: var(--line); }}
.toc-label {{ width: 20mm; color: var(--gold); font-size: 9pt; line-height: 12pt; font-weight: 700; }}
.toc-title {{ font-size: 9.2pt; line-height: 12pt; font-weight: 700; }}
.toc-level-1 .toc-label {{ color: var(--mint); font-size: 8pt; }}
.toc-level-1 .toc-title {{ padding-left: 5mm; font-size: 8.1pt; line-height: 10pt; font-weight: 400; color: #404842; }}
.toc-title a {{ color: inherit; text-decoration: none; }}
.toc-page {{ width: 12mm; text-align: right; font-size: 9.2pt; line-height: 12pt; font-weight: 700; }}
.toc-level-1 .toc-page {{ font-size: 8.1pt; line-height: 10pt; font-weight: 400; color: #404842; }}
.profile-header {{
  margin-top: 3pt;
  padding: 6pt 8pt;
  border-bottom: 2pt solid var(--gold);
  background: var(--deep-green);
  color: #fff;
  font-size: 9.5pt;
  line-height: 12.3pt;
  font-weight: 700;
}}
.profile-cards {{ display: grid; grid-template-columns: 1fr 1fr; margin-bottom: 11pt; border: .5pt solid var(--line); border-top: 0; page-break-inside: avoid; }}
.profile-cards section {{ padding: 8pt 10pt; }}
.profile-cards section:first-child {{ background: var(--light-green); border-right: .5pt solid var(--line); }}
.profile-cards section:last-child {{ background: var(--warm); }}
.profile-cards h3 {{ margin-top: 0; }}
@media screen {{
  #print-root:empty::before {{
    content: "Das Dokument wird paginiert ...";
    display: block;
    width: 210mm;
    margin: 20mm auto;
    color: #333;
    font-size: 12pt;
  }}
}}
@media print {{
  html, body {{ width: 210mm; background: #fff; }}
  .paper {{ margin: 0; box-shadow: none; break-after: page; page-break-after: always; }}
  .paper:last-child {{ break-after: auto; page-break-after: auto; }}
}}
"""


def js(fields: CoverFields) -> str:
    payload = {
        "fields": asdict(fields),
        "confidential": CONFIDENTIAL,
        "docTitle": DOC_TITLE,
        "colors": {
            "deepGreen": DEEP_GREEN,
            "green": GREEN,
            "mint": MINT,
            "gold": GOLD,
            "warm": WARM,
            "lightGreen": LIGHT_GREEN,
            "line": LINE,
        },
    }
    return f"""
const DOCUMENT_DATA = {json.dumps(payload, ensure_ascii=False)};

function mm(value) {{
  return value * 96 / 25.4;
}}

function fitLines(ctx, text, maxWidth, maxLines) {{
  const words = text.split(/\\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {{
    const candidate = (current + " " + word).trim();
    if (!current || ctx.measureText(candidate).width <= maxWidth) {{
      current = candidate;
    }} else {{
      lines.push(current);
      current = word;
      if (lines.length === maxLines - 1) break;
    }}
  }}
  if (current && lines.length < maxLines) lines.push(current);
  return lines;
}}

function drawCover() {{
  const {{ fields, colors, confidential }} = DOCUMENT_DATA;
  const canvas = document.getElementById("cover-canvas");
  const scale = 3;
  canvas.width = Math.round(mm(210) * scale);
  canvas.height = Math.round(mm(297) * scale);
  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);
  const w = mm(210);
  const h = mm(297);
  ctx.fillStyle = colors.deepGreen;
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = colors.green;
  ctx.fillRect(0, 0, w, h / 2);
  ctx.fillStyle = colors.gold;
  ctx.fillRect(0, 0, mm(9), h);

  ctx.lineWidth = 2;
  ctx.strokeStyle = colors.gold;
  ctx.beginPath();
  ctx.arc(w - mm(30), mm(36), mm(18), 0, Math.PI * 2);
  ctx.stroke();
  ctx.lineWidth = 1.25;
  ctx.strokeStyle = colors.lightGreen;
  ctx.beginPath();
  ctx.arc(w - mm(23), mm(43), mm(13), 0, Math.PI * 2);
  ctx.stroke();

  const x = mm(25);
  let y = mm(75);
  ctx.fillStyle = "#fff";
  ctx.font = "700 30pt Helvetica, Arial, sans-serif";
  ctx.fillText(fields.title, x, y);
  ctx.fillStyle = colors.lightGreen;
  ctx.font = "700 18pt Helvetica, Arial, sans-serif";
  for (const line of fitLines(ctx, fields.subtitle, w - x - mm(30), 4)) {{
    y += mm(8.5);
    ctx.fillText(line, x, y);
  }}

  y += mm(14);
  ctx.strokeStyle = colors.gold;
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(w - mm(35), y);
  ctx.stroke();
  y += mm(12);
  ctx.fillStyle = "#fff";
  ctx.font = "400 11pt Helvetica, Arial, sans-serif";
  const description = "Erwerb und Entwicklung eines naturnahen Erlebnis-, Bildungs- und Begegnungshofes";
  for (const line of fitLines(ctx, description, mm(128), 3)) {{
    ctx.fillText(line, x, y);
    y += mm(5.5);
  }}

  let infoY = y + mm(9);
  const rows = [
    ["GRÜNDER", fields.founders],
    ["STANDORT", fields.location],
    ["INVESTITIONSVOLUMEN", fields.investment],
    ["KREDITANFRAGE", fields.credit_request],
  ];
  for (const [label, value] of rows) {{
    ctx.fillStyle = colors.gold;
    ctx.font = "700 9pt Helvetica, Arial, sans-serif";
    ctx.fillText(label, x, infoY);
    ctx.fillStyle = "#fff";
    ctx.font = "400 11pt Helvetica, Arial, sans-serif";
    ctx.fillText(value, x + mm(48), infoY);
    infoY += mm(8.4);
  }}

  ctx.fillStyle = colors.lightGreen;
  ctx.font = "italic 12pt Helvetica, Arial, sans-serif";
  ctx.textAlign = "right";
  ctx.fillText(fields.motto, w - mm(24), h - mm(27));
  ctx.textAlign = "left";
  ctx.fillStyle = "#C8D0CA";
  ctx.font = "400 8.2pt Helvetica, Arial, sans-serif";
  ctx.fillText(confidential, mm(25), h - mm(18));
}}

function makeBodyPage() {{
  const root = document.getElementById("print-root");
  const page = document.createElement("section");
  page.className = "paper body-page";
  page.innerHTML = `
    <header class="header"><strong>BUSINESSPLAN</strong><span>${{DOCUMENT_DATA.docTitle}}</span></header>
    <main class="page-content"></main>
    <footer class="footer"><span>${{DOCUMENT_DATA.confidential}}</span><span class="page-number"></span></footer>
  `;
  root.appendChild(page);
  return page.querySelector(".page-content");
}}

function paginate() {{
  const root = document.getElementById("print-root");
  const source = document.getElementById("source-content");
  root.innerHTML = "";
  const cover = document.createElement("section");
  cover.className = "paper cover-page";
  cover.innerHTML = '<canvas id="cover-canvas" width="2480" height="3508"></canvas>';
  root.appendChild(cover);
  drawCover();

  let pageContent = makeBodyPage();
  const children = Array.from(source.children).map((node) => node.cloneNode(true));
  for (const node of children) {{
    if (node.classList.contains("page-break-before") && pageContent.children.length > 0) {{
      pageContent = makeBodyPage();
    }}
    pageContent.appendChild(node);
    if (pageContent.scrollHeight > pageContent.clientHeight + 1) {{
      pageContent.removeChild(node);
      pageContent = makeBodyPage();
      node.classList.remove("page-break-before");
      pageContent.appendChild(node);
    }}
  }}

  const pages = Array.from(root.querySelectorAll(".paper"));
  const total = pages.length;
  pages.forEach((page, idx) => {{
    page.dataset.pageNumber = String(idx + 1);
    const number = page.querySelector(".page-number");
    if (number) number.textContent = `Seite ${{idx + 1}} von ${{total}}`;
    page.querySelectorAll("[id]").forEach((el) => {{
      el.dataset.pageNumber = String(idx + 1);
    }});
  }});

  document.querySelectorAll(".toc-page[data-target]").forEach((cell) => {{
    const target = document.getElementById(cell.dataset.target);
    const page = target ? target.closest(".paper") : null;
    cell.textContent = page ? page.dataset.pageNumber : "-";
  }});
}}

window.addEventListener("load", paginate);
window.addEventListener("beforeprint", paginate);
"""


def build_html(source: Path, output: Path) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    fields = extract_cover_fields(lines)
    body_html, toc_entries = parse_body(body_lines_without_cover_intro(lines))
    front_info = render_kv_table(
        [
            ("Dokument", "Bankversion des Businessplans"),
            ("Gründer", fields.founders),
            ("Standort", fields.location),
            ("Investitionsvolumen", fields.investment),
            ("Kreditanfrage", fields.credit_request),
            ("Stand", german_date(date.today())),
        ]
    )
    document = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(DOC_TITLE)}</title>
  <style>{css()}</style>
</head>
<body>
  <div id="print-root"></div>
  <div id="source-content" aria-hidden="true">
    {render_toc(toc_entries)}
    {front_info}
    {body_html}
  </div>
  <script>{js(fields)}</script>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    build_html(args.source, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
