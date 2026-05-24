#!/usr/bin/env python3
"""Generate a premium bank-ready PDF from the business plan Markdown file."""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "businessplan_robert_anna_walter.md"
OUTPUT = ROOT / "output/pdf/businessplan_robert_anna_walter_bankversion.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 28 * mm
RIGHT_MARGIN = 22 * mm
TOP_MARGIN = 39 * mm
BOTTOM_MARGIN = 37 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

DEEP_GREEN = colors.HexColor("#1E3A2F")
GREEN = colors.HexColor("#2D6A4F")
MINT = colors.HexColor("#52B788")
GOLD = colors.HexColor("#B5892A")
WARM = colors.HexColor("#F5F0E8")
LIGHT_GREEN = colors.HexColor("#EBF5EE")
LINE = colors.HexColor("#D9D0C0")
INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#8D948E")
WHITE = colors.white

FONTS = {
    "regular": "Helvetica",
    "bold": "Helvetica-Bold",
    "italic": "Helvetica-Oblique",
}

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


class NumberedCanvas(canvas.Canvas):
    """Canvas that adds page chrome after the total page count is known."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for page_number, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            if page_number > 1:
                self._draw_page_chrome(page_number, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_page_chrome(self, page_number: int, page_count: int) -> None:
        self.saveState()
        header_h = 14 * mm
        footer_h = 12 * mm

        self.setFillColor(DEEP_GREEN)
        self.rect(0, PAGE_HEIGHT - header_h, PAGE_WIDTH, header_h, stroke=0, fill=1)
        self.setFillColor(WHITE)
        self.setFont(FONTS["bold"], 8.8)
        self.drawString(LEFT_MARGIN, PAGE_HEIGHT - 9 * mm, "BUSINESSPLAN")
        self.setFont(FONTS["regular"], 8.2)
        self.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 9 * mm, DOC_TITLE)

        self.setFillColor(LINE)
        self.rect(0, 0, PAGE_WIDTH, footer_h, stroke=0, fill=1)
        self.setStrokeColor(GOLD)
        self.setLineWidth(1.15)
        self.line(0, footer_h, PAGE_WIDTH, footer_h)
        self.setFillColor(colors.HexColor("#4E544F"))
        self.setFont(FONTS["regular"], 7.4)
        self.drawString(LEFT_MARGIN, 4.4 * mm, CONFIDENTIAL)
        self.setFont(FONTS["bold"], 7.6)
        self.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 4.4 * mm, f"Seite {page_number} von {page_count}")
        self.restoreState()


class ChapterBand(Flowable):
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.height = 18 * mm

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height + 5 * mm

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(DEEP_GREEN)
        self.canv.roundRect(0, 0, self.width, self.height, 2.2 * mm, stroke=0, fill=1)
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, 4 * mm, self.height, stroke=0, fill=1)
        self.canv.setFillColor(WHITE)
        self.canv.setFont(FONTS["bold"], 15)
        self.canv.drawString(10 * mm, 6.2 * mm, self.text)
        self.canv.restoreState()


class SectionRule(Flowable):
    def __init__(self, width: float = 26 * mm):
        super().__init__()
        self.rule_width = width
        self.height = 4 * mm

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(GOLD)
        self.canv.setLineWidth(1.2)
        self.canv.line(0, 2 * mm, self.rule_width, 2 * mm)
        self.canv.setStrokeColor(LINE)
        self.canv.setLineWidth(0.45)
        self.canv.line(self.rule_width + 3 * mm, 2 * mm, self.width, 2 * mm)
        self.canv.restoreState()


class PremiumTableOfContents(TableOfContents):
    def wrap(self, availWidth, availHeight):
        entries = self._lastEntries or [(0, "Placeholder for table of contents", 0, None)]
        data = []
        styles = make_styles()
        for level, text, page_num, key in entries:
            if level > 1:
                continue
            label = chapter_label(text, level)
            title_style = styles["toc_entry_0"] if level == 0 else styles["toc_entry_1"]
            num_style = styles["toc_number_0"] if level == 0 else styles["toc_number_1"]
            page_style = styles["toc_page_0"] if level == 0 else styles["toc_page_1"]
            if key:
                text = f'<a href="#{key}">{html.escape(text)}</a>'
            data.append(
                [
                    Paragraph(label, num_style),
                    Paragraph(text, title_style),
                    Paragraph(str(page_num), page_style),
                ]
            )

        if not data:
            data = [[Paragraph("", styles["toc_number_0"]), Paragraph("", styles["toc_entry_0"]), Paragraph("", styles["toc_page_0"])]]

        table = Table(data, colWidths=[20 * mm, availWidth - 32 * mm, 12 * mm], repeatRows=0, hAlign="LEFT")
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4.6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.6),
        ]
        for row, (level, *_rest) in enumerate([entry for entry in entries if entry[0] <= 1]):
            if level == 0:
                commands.append(("LINEBELOW", (0, row), (-1, row), 0.45, LINE))
                commands.append(("BOTTOMPADDING", (0, row), (-1, row), 6))
        table.setStyle(TableStyle(commands))
        self._table = table
        self.width, self.height = self._table.wrapOn(self.canv, availWidth, availHeight)
        return self.width, self.height


class BankDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, cover_fields: CoverFields, **kwargs):
        super().__init__(filename, **kwargs)
        cover_frame = Frame(LEFT_MARGIN, BOTTOM_MARGIN, CONTENT_WIDTH, 5 * mm, id="cover")
        main_frame = Frame(
            LEFT_MARGIN,
            BOTTOM_MARGIN,
            CONTENT_WIDTH,
            PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
            id="main",
        )
        self.cover_fields = cover_fields
        self.addPageTemplates(
            [
                PageTemplate(id="cover", frames=[cover_frame], onPage=self.draw_cover),
                PageTemplate(id="main", frames=[main_frame]),
            ]
        )

    def draw_cover(self, c, doc) -> None:
        fields = self.cover_fields
        c.saveState()
        c.setFillColor(DEEP_GREEN)
        c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
        c.setFillColor(GREEN)
        c.rect(0, PAGE_HEIGHT / 2, PAGE_WIDTH, PAGE_HEIGHT / 2, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.rect(0, 0, 9 * mm, PAGE_HEIGHT, stroke=0, fill=1)

        c.setStrokeColor(GOLD)
        c.setLineWidth(2.0)
        c.circle(PAGE_WIDTH - 30 * mm, PAGE_HEIGHT - 36 * mm, 18 * mm, stroke=1, fill=0)
        c.setStrokeColor(LIGHT_GREEN)
        c.setLineWidth(1.25)
        c.circle(PAGE_WIDTH - 23 * mm, PAGE_HEIGHT - 43 * mm, 13 * mm, stroke=1, fill=0)

        x = 25 * mm
        y = PAGE_HEIGHT - 75 * mm
        c.setFillColor(WHITE)
        c.setFont(FONTS["bold"], 30)
        c.drawString(x, y, fields.title)
        c.setFillColor(LIGHT_GREEN)
        c.setFont(FONTS["bold"], 18)
        subtitle_lines = fit_canvas_lines(c, fields.subtitle, FONTS["bold"], 18, PAGE_WIDTH - x - 30 * mm, max_lines=4)
        for line in subtitle_lines:
            y -= 8.5 * mm
            c.drawString(x, y, line)

        y -= 14 * mm
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.4)
        c.line(x, y, PAGE_WIDTH - 35 * mm, y)
        y -= 12 * mm
        c.setFillColor(WHITE)
        c.setFont(FONTS["regular"], 11)
        description = "Erwerb und Entwicklung eines naturnahen Erlebnis-, Bildungs- und Begegnungshofes"
        for line in fit_canvas_lines(c, description, FONTS["regular"], 11, 128 * mm, max_lines=3):
            c.drawString(x, y, line)
            y -= 5.5 * mm

        info_y = y - 9 * mm
        label_x = x
        value_x = x + 48 * mm
        rows = [
            ("GRÜNDER", fields.founders),
            ("STANDORT", fields.location),
            ("INVESTITIONSVOLUMEN", fields.investment),
            ("KREDITANFRAGE", fields.credit_request),
        ]
        for label, value in rows:
            c.setFillColor(GOLD)
            c.setFont(FONTS["bold"], 9)
            c.drawString(label_x, info_y, label)
            c.setFillColor(WHITE)
            c.setFont(FONTS["regular"], 11)
            c.drawString(value_x, info_y, value)
            info_y -= 8.4 * mm

        c.setFillColor(LIGHT_GREEN)
        c.setFont(FONTS["italic"], 12)
        c.drawRightString(PAGE_WIDTH - 24 * mm, 27 * mm, fields.motto)
        c.setFillColor(colors.HexColor("#C8D0CA"))
        c.setFont(FONTS["regular"], 8.2)
        c.drawString(25 * mm, 18 * mm, CONFIDENTIAL)
        c.restoreState()

    def afterFlowable(self, flowable) -> None:
        if not hasattr(flowable, "_bookmark_name"):
            return
        text = flowable.getPlainText()
        bookmark_name = flowable._bookmark_name
        level = flowable._outline_level
        self.canv.bookmarkPage(bookmark_name)
        self.canv.addOutlineEntry(text, bookmark_name, level=level, closed=level > 0)
        if level <= 1:
            self.notify("TOCEntry", (level, text, self.page, bookmark_name))


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["body"] = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName=FONTS["regular"],
        fontSize=10,
        leading=15,
        textColor=INK,
        alignment=TA_JUSTIFY,
        spaceAfter=6.7,
    )
    styles["body_left"] = ParagraphStyle("BodyLeft", parent=styles["body"], alignment=TA_LEFT)
    styles["h2"] = ParagraphStyle(
        "Heading2",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=12,
        leading=15,
        textColor=GREEN,
        spaceBefore=16,
        spaceAfter=7,
        keepWithNext=True,
    )
    styles["h3"] = ParagraphStyle(
        "Heading3",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=10.5,
        leading=13.5,
        textColor=MINT,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )
    styles["h4"] = ParagraphStyle(
        "Heading4",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=9.8,
        leading=12.5,
        textColor=MINT,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    styles["quote"] = ParagraphStyle(
        "Quote",
        parent=styles["body_left"],
        fontName=FONTS["italic"],
        fontSize=11.5,
        leading=16,
        textColor=GREEN,
        alignment=TA_CENTER,
        leftIndent=28,
        rightIndent=28,
        spaceBefore=8,
        spaceAfter=11,
        backColor=LIGHT_GREEN,
        borderColor=LINE,
        borderWidth=0.45,
        borderPadding=8,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet",
        parent=styles["body_left"],
        fontSize=10,
        leading=14,
        leftIndent=16,
        firstLineIndent=-10,
        bulletIndent=0,
        spaceAfter=2.2,
    )
    styles["table_cell"] = ParagraphStyle(
        "TableCell",
        parent=styles["body_left"],
        fontSize=9.5,
        leading=12.3,
        spaceAfter=0,
    )
    styles["table_cell_right"] = ParagraphStyle("TableCellRight", parent=styles["table_cell"], alignment=TA_RIGHT)
    styles["table_header"] = ParagraphStyle(
        "TableHeader",
        parent=styles["table_cell"],
        fontName=FONTS["bold"],
        textColor=WHITE,
        alignment=TA_LEFT,
    )
    styles["small_label"] = ParagraphStyle(
        "SmallLabel",
        parent=styles["table_cell"],
        fontName=FONTS["bold"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#3A3A3A"),
    )
    styles["toc_title"] = ParagraphStyle(
        "TOCTitle",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=20,
        leading=24,
        textColor=DEEP_GREEN,
        spaceAfter=6,
    )
    styles["toc_kicker"] = ParagraphStyle(
        "TOCKicker",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=8.5,
        leading=10,
        textColor=GOLD,
        spaceAfter=13,
    )
    styles["toc_number_0"] = ParagraphStyle(
        "TOCNumber0",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=9,
        leading=12,
        textColor=GOLD,
    )
    styles["toc_number_1"] = ParagraphStyle("TOCNumber1", parent=styles["toc_number_0"], fontSize=8, textColor=MINT)
    styles["toc_entry_0"] = ParagraphStyle(
        "TOCEntry0",
        parent=styles["body_left"],
        fontName=FONTS["bold"],
        fontSize=9.2,
        leading=12,
        textColor=INK,
    )
    styles["toc_entry_1"] = ParagraphStyle(
        "TOCEntry1",
        parent=styles["body_left"],
        fontName=FONTS["regular"],
        fontSize=8.1,
        leading=10,
        leftIndent=5 * mm,
        textColor=colors.HexColor("#404842"),
    )
    styles["toc_page_0"] = ParagraphStyle("TOCPage0", parent=styles["toc_entry_0"], alignment=TA_RIGHT)
    styles["toc_page_1"] = ParagraphStyle("TOCPage1", parent=styles["toc_entry_1"], alignment=TA_RIGHT)
    return styles


STYLES = make_styles()


def normalize_text(text: str) -> str:
    return text.replace("\u00a0", " ").replace("\u2011", "-").replace("\ufeff", "").strip()


def inline_markdown(text: str) -> str:
    escaped = html.escape(normalize_text(text), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = escaped.replace("„", "&bdquo;").replace("“", "&ldquo;")
    return escaped


def paragraph(text: str, style_name: str = "body"):
    return Paragraph(inline_markdown(text), STYLES[style_name])


def fit_canvas_lines(c, text: str, font: str, size: float, max_width: float, max_lines: int) -> list[str]:
    words = normalize_text(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if c.stringWidth(candidate, font, size) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


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


def make_table(block: TableBlock):
    col_count = max(len(row) for row in block.rows)
    rows = [row + [""] * (col_count - len(row)) for row in block.rows]
    if col_count == 2:
        col_widths = [CONTENT_WIDTH * 0.60, CONTENT_WIDTH * 0.40]
    elif col_count == 3:
        col_widths = [CONTENT_WIDTH * 0.31, CONTENT_WIDTH * 0.24, CONTENT_WIDTH * 0.45]
    else:
        col_widths = [CONTENT_WIDTH / col_count] * col_count

    data = []
    for row_index, row in enumerate(rows):
        rendered = []
        for col_index, cell in enumerate(row):
            if row_index == 0:
                style = STYLES["table_header"]
            elif block.aligns[col_index] == "right" or (col_index > 0 and re.search(r"\d", cell)):
                style = STYLES["table_cell_right"]
            else:
                style = STYLES["table_cell"]
            rendered.append(Paragraph(inline_markdown(cell), style))
        data.append(rendered)

    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1, splitByRow=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), DEEP_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("LINEBELOW", (0, 0), (-1, 0), 2, GOLD),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for row_index in range(1, len(data)):
        commands.append(("BACKGROUND", (0, row_index), (-1, row_index), WARM if row_index % 2 == 0 else WHITE))
    for col_index, align in enumerate(block.aligns):
        if align == "right":
            commands.append(("ALIGN", (col_index, 1), (col_index, -1), "RIGHT"))
        elif align == "center":
            commands.append(("ALIGN", (col_index, 1), (col_index, -1), "CENTER"))
    table.setStyle(TableStyle(commands))
    return KeepTogether([Spacer(1, 3), table, Spacer(1, 10)])


def make_kv_table(rows: list[tuple[str, str]]):
    data = [[Paragraph(inline_markdown(k), STYLES["small_label"]), Paragraph(inline_markdown(v), STYLES["table_cell"])] for k, v in rows]
    table = Table(data, colWidths=[CONTENT_WIDTH * 0.34, CONTENT_WIDTH * 0.66], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
                ("BACKGROUND", (1, 0), (1, -1), WARM),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return KeepTogether([Spacer(1, 3), table, Spacer(1, 10)])


def render_profile_lines(lines: list[str]):
    blocks: dict[str, list] = {"Robert Walter": [], "Anna Walter": []}
    current: str | None = None
    paragraph_lines: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if current and paragraph_lines:
            blocks[current].append(paragraph(" ".join(paragraph_lines), "body_left"))
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if current and list_items:
            for item in list_items:
                blocks[current].append(Paragraph(f"•&nbsp;&nbsp;{inline_markdown(item)}", STYLES["bullet"]))
            blocks[current].append(Spacer(1, 3))
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

    header = Table(
        [[Paragraph("GRÜNDERPROFILE", STYLES["table_header"])]],
        colWidths=[CONTENT_WIDTH],
        hAlign="LEFT",
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DEEP_GREEN),
                ("LINEBELOW", (0, 0), (-1, -1), 2, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    def cell(title: str, items: list) -> list:
        return [
            Paragraph(title, STYLES["h3"]),
            Spacer(1, 2),
            *items,
        ]

    cards = Table(
        [[cell("Robert Walter", blocks["Robert Walter"]), cell("Anna Walter", blocks["Anna Walter"])]],
        colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
        hAlign="LEFT",
    )
    cards.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), LIGHT_GREEN),
                ("BACKGROUND", (1, 0), (1, 0), WARM),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [Spacer(1, 3), header, cards, Spacer(1, 11)]


def make_list(items: list[str], ordered: bool = False):
    flowables = []
    for index, item in enumerate(items, start=1):
        marker = f"{index}." if ordered else "•"
        flowables.append(Paragraph(f"{html.escape(marker)}&nbsp;&nbsp;{inline_markdown(item)}", STYLES["bullet"]))
    return KeepTogether(flowables + [Spacer(1, 4)])


def chapter_label(text: str, level: int) -> str:
    match = re.match(r"Teil\s+(\d+)", text)
    if match:
        return f"{int(match.group(1)):02d}"
    if text.startswith("Anhang"):
        return "A"
    return " " if level else "•"


def is_bank_argumentation_heading(text: str) -> bool:
    return "Bankargumentation" in text or "Finanzplanung" in text or "Kreditstrategie" in text


def parse_body(lines: list[str]) -> list:
    story: list = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []
    first_h1 = True
    bookmark_counter = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            story.append(paragraph(" ".join(paragraph_lines)))
            paragraph_lines = []

    def flush_lists() -> None:
        nonlocal list_items, ordered_items
        if list_items:
            story.append(make_list(list_items, ordered=False))
            list_items = []
        if ordered_items:
            story.append(make_list(ordered_items, ordered=True))
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
            story.append(SectionRule())
            story.append(Spacer(1, 5))
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
            story.append(make_table(TableBlock(table_rows, aligns)))
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading_match:
            flush_all()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            bookmark_counter += 1
            bookmark_name = f"heading_{bookmark_counter}"

            if level == 1:
                if first_h1:
                    first_h1 = False
                else:
                    story.append(PageBreak())
                band = ChapterBand(text)
                band._bookmark_name = bookmark_name
                band._outline_level = 0
                band.getPlainText = lambda text=text: text
                story.append(band)
                story.append(Spacer(1, 9))
            else:
                if level == 2 and is_bank_argumentation_heading(text):
                    story.append(Spacer(1, 3))
                style_name = f"h{min(level, 4)}"
                heading = Paragraph(inline_markdown(text), STYLES[style_name])
                heading._bookmark_name = bookmark_name
                heading._outline_level = min(level - 1, 3)
                story.append(heading)
                if level == 2 and text == "Gründerprofil":
                    profile_lines = []
                    lookahead = index + 1
                    while lookahead < len(lines):
                        candidate = normalize_text(lines[lookahead].rstrip())
                        if re.match(r"^(#{1,2})\s+.+$", candidate):
                            break
                        profile_lines.append(candidate)
                        lookahead += 1
                    story.extend(render_profile_lines(profile_lines))
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
            quote = line.lstrip(">").strip()
            story.append(paragraph(quote, "quote"))
            index += 1
            continue

        flush_lists()
        paragraph_lines.append(line)
        index += 1

    flush_all()
    return story


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

    location = "Fliseryds-Boda, Mönsterås, Schweden"
    investment = find_first_after(lines, "Geschätzter Gesamtinvestitionsbedarf", r"ca\. [\d.]+ SEK", "ca. 3.000.000 SEK")
    credit_request = find_first_after(lines, "Erste Finanzierungsstufe", r"≈ [\d.]+ SEK", "≈ 2.000.000 SEK")
    return CoverFields(title, subtitle, founders, location, investment, credit_request, motto)


def build_toc() -> list:
    toc = PremiumTableOfContents()
    toc.dotsMinLevel = -1
    return [
        Paragraph("INHALTSVERZEICHNIS", STYLES["toc_kicker"]),
        Paragraph("Struktur des Businessplans", STYLES["toc_title"]),
        SectionRule(42 * mm),
        Spacer(1, 7),
        toc,
        PageBreak(),
    ]


def body_lines_without_cover_intro(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if normalize_text(line).startswith("# Teil 1"):
            return lines[index:]
    return lines


def build_front_matter(fields: CoverFields) -> list:
    return [
        Spacer(1, 1),
        NextPageTemplate("main"),
        PageBreak(),
        *build_toc(),
        make_kv_table(
            [
                ("Dokument", "Bankversion des Businessplans"),
                ("Gründer", fields.founders),
                ("Standort", fields.location),
                ("Investitionsvolumen", fields.investment),
                ("Kreditanfrage", fields.credit_request),
                ("Stand", german_date(date.today())),
            ]
        ),
        PageBreak(),
    ]


def build_pdf(source: Path, output: Path) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    fields = extract_cover_fields(lines)
    body_lines = body_lines_without_cover_intro(lines)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = BankDocTemplate(
        str(output),
        cover_fields=fields,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=DOC_TITLE,
        author=fields.founders,
        subject="Bankversion",
        creator="Codex / ReportLab",
    )
    story = [*build_front_matter(fields), *parse_body(body_lines)]
    doc.multiBuild(story, canvasmaker=NumberedCanvas)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    build_pdf(args.source, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
