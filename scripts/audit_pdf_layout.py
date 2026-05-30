#!/usr/bin/env python3
"""Audit PDF layout density and build thumbnail contact sheets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BUNDLED_PYTHON_PACKAGES = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python"
BUNDLED_PYTHON = BUNDLED_PYTHON_PACKAGES / "bin/python3"
if BUNDLED_PYTHON.exists() and Path(sys.executable).resolve() != BUNDLED_PYTHON.resolve():
    os.execv(str(BUNDLED_PYTHON), [str(BUNDLED_PYTHON), *sys.argv])
if BUNDLED_PYTHON_PACKAGES.exists():
    sys.path.insert(0, str(BUNDLED_PYTHON_PACKAGES))
    for site_packages in BUNDLED_PYTHON_PACKAGES.glob("lib/python*/site-packages"):
        sys.path.insert(0, str(site_packages))

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "businessplan_robert_anna_walter.md"
DEFAULT_OUTPUT = ROOT / "tmp/pdf_qa/refined"
LEAD_INS = (
    "Mögliche Themen:",
    "Ziel:",
    "Nicht:",
    "Sondern:",
    "Fokus:",
    "Start:",
    "Später:",
    "Grundsatz:",
    "Annahme:",
    "Positionierung:",
    "Beispiele:",
    "Geplant:",
    "Zusätzlich:",
    "Schätzung:",
    "Bestand:",
    "Aktuelle Nutzung:",
    "Geplante Nutzung:",
)


def clean_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.glob("*"):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def page_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [
        line
        for line in lines
        if line not in {"BUSINESSPLAN", "Businessplan Robert & Anna Walter", "Affärsplan Robert & Anna Walter"}
        and not line.startswith("Vertraulich -")
        and not line.startswith("Konfidentiellt -")
        and not line.startswith("Seite ")
    ]


def is_chapter_start(lines: list[str]) -> bool:
    if not lines:
        return False
    first = lines[0]
    return first.startswith(("Teil ", "Anhang", "Del ", "Bilaga"))


def is_lead_in_line(line: str) -> bool:
    clean = line.strip()
    return clean in LEAD_INS or bool(clean.endswith(":") and 3 <= len(clean) <= 90 and not re.match(r"^#{1,4}\s+", clean))


def looks_like_heading(line: str) -> bool:
    clean = line.strip()
    if not clean or clean.startswith(("•", "\x7f")) or clean.endswith((".", ":", ";", ",")):
        return False
    words = clean.split()
    return len(words) <= 9 and any(char.isupper() for char in clean)


def load_heading_titles(source: Path) -> set[str]:
    if not source.exists():
        return set()
    titles: set[str] = set()
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,4}\s+(.+)$", raw_line.strip())
        if match:
            titles.add(match.group(1).strip())
    return titles


def render_with_pdftoppm(pdf: Path, render_dir: Path, dpi: int) -> tuple[list[Path], str | None]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return [], "pdftoppm not found. Install Poppler with: brew install poppler"
    render_dir.mkdir(parents=True, exist_ok=True)
    prefix = render_dir / "page"
    subprocess.run(
        [pdftoppm, "-png", "-r", str(dpi), str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return sorted(render_dir.glob("page-*.png")), None


def visual_density(image_path: Path) -> float:
    image = Image.open(image_path).convert("L")
    small = image.resize((80, 114))
    pixels = list(small.getdata())
    non_white = sum(1 for pixel in pixels if pixel < 245)
    return round(non_white / len(pixels), 4)


def placeholder_thumbnail(page: dict, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=(210, 208, 202))
    draw.text((10, 10), f"Seite {page['page']}", fill=(30, 58, 47))
    draw.text((10, 32), f"Text: {page['char_count']} Zeichen", fill=(70, 70, 70))
    excerpt = page["excerpt"][:150]
    y = 58
    for chunk in [excerpt[i : i + 34] for i in range(0, len(excerpt), 34)][:7]:
        draw.text((10, y), chunk, fill=(35, 35, 35))
        y += 18
    return image


def build_contact_sheets(
    pages: list[dict],
    rendered_pages: list[Path],
    anomalies: list[dict],
    output_dir: Path,
    pages_per_sheet: int,
) -> list[Path]:
    anomaly_pages = {item["page"] for item in anomalies}
    cols = 6
    rows = max(1, pages_per_sheet // cols)
    thumb_w, thumb_h = 170, 240
    label_h = 24
    gap = 16
    margin = 18
    sheet_paths = []

    for sheet_index, start in enumerate(range(0, len(pages), pages_per_sheet), start=1):
        chunk = pages[start : start + pages_per_sheet]
        sheet = Image.new(
            "RGB",
            (margin * 2 + cols * thumb_w + (cols - 1) * gap, margin * 2 + rows * (thumb_h + label_h) + (rows - 1) * gap),
            (245, 244, 240),
        )
        draw = ImageDraw.Draw(sheet)
        for offset, page in enumerate(chunk):
            col = offset % cols
            row = offset // cols
            x = margin + col * (thumb_w + gap)
            y = margin + row * (thumb_h + label_h + gap)
            if rendered_pages:
                thumb = Image.open(rendered_pages[page["page"] - 1]).convert("RGB")
                thumb.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
                canvas = Image.new("RGB", (thumb_w, thumb_h), "white")
                canvas.paste(thumb, ((thumb_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
            else:
                canvas = placeholder_thumbnail(page, (thumb_w, thumb_h))
            sheet.paste(canvas, (x, y))
            border = (181, 38, 38) if page["page"] in anomaly_pages else (217, 208, 192)
            width = 4 if page["page"] in anomaly_pages else 1
            draw.rectangle([x, y, x + thumb_w, y + thumb_h], outline=border, width=width)
            draw.text((x, y + thumb_h + 5), f"Seite {page['page']}", fill=(30, 58, 47))
        path = output_dir / f"contact_sheet_{sheet_index:03d}.png"
        sheet.save(path)
        sheet_paths.append(path)
    return sheet_paths


def analyze_pages(reader: PdfReader, rendered_pages: list[Path], heading_titles: set[str]) -> tuple[list[dict], list[dict]]:
    pages: list[dict] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        lines = page_lines(text)
        density = visual_density(rendered_pages[index - 1]) if rendered_pages else None
        pages.append(
            {
                "page": index,
                "char_count": len(" ".join(lines)),
                "line_count": len(lines),
                "chapter_start": is_chapter_start(lines),
                "last_line": lines[-1] if lines else "",
                "first_line": lines[0] if lines else "",
                "excerpt": " ".join(lines)[:500],
                "visual_density": density,
            }
        )

    anomalies: list[dict] = []
    first_body_page = next((page["page"] for page in pages if page["chapter_start"]), len(pages) + 1)
    for index, page in enumerate(pages):
        reasons = []
        next_page = pages[index + 1] if index + 1 < len(pages) else None
        prev_page = pages[index - 1] if index > 0 else None
        front_matter = page["page"] < first_body_page
        before_chapter = bool(next_page and next_page["chapter_start"])
        visually_sparse_by_text = page["char_count"] < 320 and page["line_count"] < 16
        if page["page"] != 1 and visually_sparse_by_text and not front_matter and not page["chapter_start"] and not before_chapter:
            reasons.append("sparse non-chapter-end")
        if is_lead_in_line(page["last_line"]):
            reasons.append("orphan lead-in at page end")
        elif next_page and page["last_line"] in heading_titles and looks_like_heading(page["last_line"]) and not before_chapter:
            reasons.append("possible heading at page end")
        if page["first_line"].startswith(("•", "\x7f")) and prev_page and is_lead_in_line(prev_page["last_line"]):
            reasons.append("orphan list at page start")
        if prev_page and next_page:
            neighbor_avg = (prev_page["char_count"] + next_page["char_count"]) / 2
            if page["char_count"] < 0.42 * neighbor_avg and page["char_count"] < 520 and not front_matter and not before_chapter:
                reasons.append("low text density vs neighbors")
        if page["visual_density"] is not None and page["visual_density"] < 0.035 and page["page"] != 1 and not front_matter and not before_chapter:
            reasons.append("low visual density")
        if reasons:
            anomalies.append({"page": page["page"], "reasons": reasons, "char_count": page["char_count"], "excerpt": page["excerpt"]})
    return pages, anomalies


def write_report(output_dir: Path, pdf: Path, pages: list[dict], anomalies: list[dict], sheets: list[Path], warning: str | None) -> None:
    report = output_dir / "report.html"
    rows = "\n".join(
        f"<tr><td>{item['page']}</td><td>{', '.join(item['reasons'])}</td><td>{item['char_count']}</td><td>{item['excerpt']}</td></tr>"
        for item in anomalies
    )
    sheet_imgs = "\n".join(f'<h2>{path.name}</h2><img src="{path.name}" alt="{path.name}">' for path in sheets)
    warning_html = f"<p class='warning'>{warning}</p>" if warning else ""
    report.write_text(
        f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>PDF Layout Audit</title>
  <style>
    body {{ font-family: Helvetica, Arial, sans-serif; margin: 24px; color: #1A1A1A; }}
    .warning {{ padding: 12px; background: #F5F0E8; border-left: 4px solid #B5892A; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #D9D0C0; padding: 6px 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #1E3A2F; color: white; }}
    img {{ max-width: 100%; border: 1px solid #D9D0C0; }}
  </style>
</head>
<body>
  <h1>PDF Layout Audit</h1>
  <p><strong>Datei:</strong> {pdf}</p>
  <p><strong>Seiten:</strong> {len(pages)} | <strong>Auffälligkeiten:</strong> {len(anomalies)}</p>
  {warning_html}
  <h2>Auffälligkeiten</h2>
  <table><thead><tr><th>Seite</th><th>Grund</th><th>Zeichen</th><th>Auszug</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Contact Sheets</h2>
  {sheet_imgs}
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--dpi", type=int, default=35)
    parser.add_argument("--pages-per-sheet", type=int, default=24)
    args = parser.parse_args()

    output_dir = args.output_dir
    clean_output_dir(output_dir)
    render_dir = output_dir / "rendered_pages"
    render_dir.mkdir(parents=True, exist_ok=True)

    rendered_pages, warning = render_with_pdftoppm(args.pdf, render_dir, args.dpi)
    reader = PdfReader(str(args.pdf))
    if rendered_pages and len(rendered_pages) != len(reader.pages):
        warning = f"Rendered {len(rendered_pages)} thumbnails for {len(reader.pages)} pages; check pdftoppm output."
        rendered_pages = []
    pages, anomalies = analyze_pages(reader, rendered_pages, load_heading_titles(args.source))
    sheets = build_contact_sheets(pages, rendered_pages, anomalies, output_dir, args.pages_per_sheet)

    (output_dir / "anomalies.json").write_text(json.dumps({"warning": warning, "pages": pages, "anomalies": anomalies}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(output_dir, args.pdf, pages, anomalies, sheets, warning)
    print(output_dir / "report.html")
    if warning:
        print(warning)
    print(f"anomalies: {len(anomalies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
