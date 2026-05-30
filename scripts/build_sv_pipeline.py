#!/usr/bin/env python3
"""Build Swedish bank artefacts and PDF QA report."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "businessplan_robert_anna_walter.sv.md"
HTML_OUTPUT = ROOT / "output/html/businessplan_robert_anna_walter_bankversion_sv_refined.html"
PDF_OUTPUT = ROOT / "output/pdf/businessplan_robert_anna_walter_bankversion_sv_refined.pdf"
DOCX_OUTPUT = ROOT / "output/word/businessplan_robert_anna_walter_bankversion_sv.docx"
QA_OUTPUT = ROOT / "tmp/pdf_qa/sv_refined"

BUNDLED_PYTHON_PACKAGES = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python"
BUNDLED_PYTHON = BUNDLED_PYTHON_PACKAGES / "bin/python3"


def reexec_with_bundled_python() -> None:
    if BUNDLED_PYTHON.exists() and Path(sys.executable).resolve() != BUNDLED_PYTHON.resolve():
        os.execv(str(BUNDLED_PYTHON), [str(BUNDLED_PYTHON), *sys.argv])


def run_step(args: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def main() -> int:
    reexec_with_bundled_python()
    python = sys.executable
    steps = [
        [
            python,
            "scripts/generate_bank_html_refined.py",
            "--source",
            str(SOURCE),
            "--output",
            str(HTML_OUTPUT),
            "--locale",
            "sv",
        ],
        [
            python,
            "scripts/generate_bank_pdf_refined.py",
            "--source",
            str(SOURCE),
            "--output",
            str(PDF_OUTPUT),
            "--locale",
            "sv",
        ],
        [
            python,
            "scripts/generate_bank_docx.py",
            "--source",
            str(SOURCE),
            "--output",
            str(DOCX_OUTPUT),
            "--locale",
            "sv",
        ],
        [
            python,
            "scripts/audit_pdf_layout.py",
            str(PDF_OUTPUT),
            "--source",
            str(SOURCE),
            "--output-dir",
            str(QA_OUTPUT),
        ],
    ]
    for step in steps:
        run_step(step)

    print(HTML_OUTPUT)
    print(PDF_OUTPUT)
    print(DOCX_OUTPUT)
    print(QA_OUTPUT / "report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
