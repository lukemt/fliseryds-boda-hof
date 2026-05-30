#!/usr/bin/env python3
"""Locale helpers for bank artefact generators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class BankLocale:
    code: str
    html_lang: str
    doc_title: str
    confidential: str
    cover_description: str
    cover_label: str
    toc_kicker: str
    toc_title: str
    toc_placeholder: str
    profile_header: str
    founders_label: str
    location_label: str
    investment_label: str
    credit_request_label: str
    document_label: str
    document_value: str
    date_label: str
    location_value: str
    founder_markers: tuple[str, ...]
    part_prefix: str
    appendix_prefix: str
    default_title: str
    default_motto: str
    investment_markers: tuple[str, ...]
    investment_patterns: tuple[str, ...]
    investment_default: str
    credit_markers: tuple[str, ...]
    credit_patterns: tuple[str, ...]
    credit_default: str
    months: tuple[str, ...]
    core_comments: str

    def format_date(self, today: date) -> str:
        if self.code == "sv":
            return f"{today.day} {self.months[today.month - 1]} {today.year}"
        return f"{today.day}. {self.months[today.month - 1]} {today.year}"


LOCALES: dict[str, BankLocale] = {
    "de": BankLocale(
        code="de",
        html_lang="de",
        doc_title="Businessplan Robert & Anna Walter",
        confidential="Vertraulich - nur zur internen Prüfung und Finanzierungsvorbereitung",
        cover_description="Erwerb und Entwicklung eines naturnahen Erlebnis-, Bildungs- und Begegnungshofes",
        cover_label="Businessplan zur Bankeinreichung",
        toc_kicker="INHALTSVERZEICHNIS",
        toc_title="Struktur des Businessplans",
        toc_placeholder="Inhaltsverzeichnis in Word aktualisieren",
        profile_header="GRÜNDERPROFILE",
        founders_label="Gründer",
        location_label="Standort",
        investment_label="Investitionsvolumen",
        credit_request_label="Kreditanfrage",
        document_label="Dokument",
        document_value="Bankversion des Businessplans",
        date_label="Stand",
        location_value="Fliseryds-Boda, Mönsterås, Schweden",
        founder_markers=("**Gründer:**",),
        part_prefix="Teil",
        appendix_prefix="Anhang",
        default_title="Businessplan",
        default_motto="Das war kein Urlaub, das war Freiheit.",
        investment_markers=("Geschätzter Gesamtinvestitionsbedarf",),
        investment_patterns=(r"ca\. [\d.]+ SEK",),
        investment_default="ca. 3.000.000 SEK",
        credit_markers=("Erste Finanzierungsstufe",),
        credit_patterns=(r"≈ [\d.]+ SEK",),
        credit_default="≈ 2.000.000 SEK",
        months=(
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
        ),
        core_comments="Aus Markdown generierte Word-Bankversion",
    ),
    "sv": BankLocale(
        code="sv",
        html_lang="sv",
        doc_title="Affärsplan Robert & Anna Walter",
        confidential="Konfidentiellt - endast för intern granskning och finansieringsförberedelse",
        cover_description="Förvärv och utveckling av en naturnära upplevelse-, utbildnings- och mötesgård",
        cover_label="Affärsplan för bankinlämning",
        toc_kicker="INNEHÅLLSFÖRTECKNING",
        toc_title="Affärsplanens struktur",
        toc_placeholder="Uppdatera innehållsförteckningen i Word",
        profile_header="GRUNDARPROFILER",
        founders_label="Grundare",
        location_label="Plats",
        investment_label="Investeringsvolym",
        credit_request_label="Kreditbehov",
        document_label="Dokument",
        document_value="Bankversion av affärsplanen",
        date_label="Datum",
        location_value="Fliseryds-Boda, Mönsterås, Sverige",
        founder_markers=("**Grundare:**", "**Gründer:**"),
        part_prefix="Del",
        appendix_prefix="Bilaga",
        default_title="Affärsplan",
        default_motto="Det var ingen semester, det var frihet.",
        investment_markers=("Uppskattat totalt investeringsbehov", "Totalt investeringsbehov"),
        investment_patterns=(r"cirka [\d.]+ SEK", r"ca\. [\d.]+ SEK"),
        investment_default="cirka 3.000.000 SEK",
        credit_markers=("Första finansieringssteg", "Första finansieringssteg:"),
        credit_patterns=(r"≈ [\d.]+ SEK",),
        credit_default="≈ 2.000.000 SEK",
        months=(
            "januari",
            "februari",
            "mars",
            "april",
            "maj",
            "juni",
            "juli",
            "augusti",
            "september",
            "oktober",
            "november",
            "december",
        ),
        core_comments="Word-bankversion genererad från svensk Markdown",
    ),
}


def resolve_locale(source: Path, lines: list[str], requested: str = "de") -> BankLocale:
    if requested != "auto":
        return LOCALES[requested]
    if source.name.endswith(".sv.md") or any(line.startswith("# Del 1") or line.startswith("**Grundare:**") for line in lines[:80]):
        return LOCALES["sv"]
    return LOCALES["de"]
